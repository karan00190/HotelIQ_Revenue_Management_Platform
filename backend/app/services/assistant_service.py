"""Assembles and runs the conversational agent for one /assistant/chat
request: resolves which free LLM provider is configured, builds this
request's tools (closed over its db session), and runs the LangChain agent.

Every heavy import (langchain.agents, langgraph, langchain_groq,
langchain_google_genai) happens INSIDE these functions, not at module load
time. That keeps merely importing this module - which happens whenever
app/api/assistant.py is imported at server startup - cheap; the real RAM
cost of the agent stack is only paid on the first actual chat request.

Stateless by design: no LangGraph checkpointer. The client resends its own
message history every turn, which survives Render's free-tier spin-down
(there is no server-side session to lose) at the cost of the client owning
history truncation on its side; the server independently caps how much of
that history it will feed to the model (MAX_HISTORY_MESSAGES).
"""

import json
import os
import time
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.services.assistant_tools import build_tools

DEFAULT_MODEL_SPEC = "groq:openai/gpt-oss-120b"
MAX_HISTORY_MESSAGES = 10
RECURSION_LIMIT = 12

RECURSION_LIMIT_REPLY = (
    "I wasn't able to finish gathering that information within my step limit. "
    "Could you ask a more specific question, or break it into smaller parts?"
)


class AssistantConfigError(Exception):
    """Raised when the configured provider's API key is missing."""


class AssistantProviderError(Exception):
    """Raised when the free LLM provider itself fails (rate limit, 5xx, etc)."""


def current_model_spec() -> str:
    return os.getenv("ASSISTANT_MODEL", DEFAULT_MODEL_SPEC)


def _provider_and_model() -> tuple[str, str]:
    spec = current_model_spec()
    provider, _, model_name = spec.partition(":")
    return provider, model_name


def is_configured() -> bool:
    provider, _ = _provider_and_model()
    if provider == "groq":
        return bool(os.getenv("GROQ_API_KEY"))
    if provider == "google_genai":
        return bool(os.getenv("GEMINI_API_KEY"))
    return False


def _resolve_chat_model():
    provider, model_name = _provider_and_model()

    if provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise AssistantConfigError("GROQ_API_KEY is not set")
        from langchain_groq import ChatGroq

        return ChatGroq(model=model_name, api_key=api_key, temperature=0, reasoning_effort="low")

    if provider == "google_genai":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise AssistantConfigError("GEMINI_API_KEY is not set")
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(model=model_name, api_key=api_key, temperature=0)

    raise AssistantConfigError(f"Unknown ASSISTANT_MODEL provider: {provider!r}")


SYSTEM_PROMPT_TEMPLATE = """You are the HotelIQ Assistant, a conversational aide for hotel revenue \
managers using the HotelIQ platform. You help them understand their hotels' performance and get \
pricing guidance by calling real tools - never by guessing or recalling a number from memory.

Today's real-world date is {today}. This system's historical and forecast data covers {coverage}. \
All currency figures in this system are in Indian Rupees (INR).

Rules you must always follow:
1. Every specific number you state - revenue, occupancy, a booking count, a forecast, a recommended \
price - must come from a tool call made in THIS conversation. Never state a number from memory, \
recall, or estimation.
2. If the user refers to a hotel by name, call list_hotels first to resolve the name to its \
numeric hotel_id, which every other data tool requires.
3. Use search_knowledge only for questions about how the platform works or what a term means (for \
example "what is RevPAR", "how does the pricing engine decide on a price", "why doesn't this \
system predict price elasticity"). Never use it to answer a question that needs a real figure.
4. If a tool call fails or returns an "error", say so plainly to the user. Never invent a \
plausible-sounding number or explanation to cover for a failed or missing tool result.
5. This assistant is read-only and advisory - it cannot change prices or create, modify, or cancel \
bookings, and it has no visibility into any hotel outside this demo dataset.
6. Keep answers concise and focused on what was asked.
7. Write any formulas in plain readable text, for example "RevPAR = ADR x Occupancy Rate" or \
"Occupancy Rate = Rooms Sold / Total Rooms x 100". Never use LaTeX or other math markup (no \\text{{}}, \
\\frac{{}}{{}}, or square-bracket math blocks) - this chat interface renders Markdown, not LaTeX, and \
raw LaTeX shows up as unreadable source code to the user."""


def _build_system_prompt(db: Session) -> str:
    from sqlalchemy import func

    from app.models.hotel import DailyMetrics

    min_dt, max_dt = db.query(func.min(DailyMetrics.date), func.max(DailyMetrics.date)).one()
    coverage = f"{min_dt.date().isoformat()} to {max_dt.date().isoformat()}" if min_dt and max_dt else "no data available yet"

    return SYSTEM_PROMPT_TEMPLATE.format(today=date.today().isoformat(), coverage=coverage)


def _extract_tool_calls(messages: list) -> list[dict]:
    """Pairs each AIMessage tool_call with its matching ToolMessage result
    (matched by tool_call_id) to build the "how I got this" trace the
    frontend renders. ok=False whenever the tool's own JSON payload carries
    an "error" key or the ToolMessage itself is marked as a tool error."""
    pending: dict[str, dict] = {}
    for message in messages:
        for call in getattr(message, "tool_calls", None) or []:
            pending[call["id"]] = {"tool": call["name"], "args": call["args"]}

    trace = []
    for message in messages:
        tool_call_id = getattr(message, "tool_call_id", None)
        if tool_call_id is None or tool_call_id not in pending:
            continue
        entry = pending[tool_call_id]
        raw = message.content
        try:
            parsed = json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            parsed = {"raw": raw}

        is_tool_error = bool(getattr(message, "status", None) == "error")
        has_error_key = isinstance(parsed, dict) and "error" in parsed
        trace.append(
            {
                "tool": entry["tool"],
                "args": entry["args"],
                "ok": not (is_tool_error or has_error_key),
                "summary": parsed,
            }
        )
    return trace


def _map_provider_error(exc: Exception) -> AssistantProviderError:
    message = str(exc).lower()
    if "429" in message or "rate limit" in message or "quota" in message:
        return AssistantProviderError("The free LLM tier is briefly rate-limited - please try again in about 30 seconds.")
    if "401" in message or "403" in message or "invalid api key" in message or "unauthorized" in message:
        return AssistantProviderError("The configured API key was rejected by the provider. Check the server's environment variables.")
    return AssistantProviderError(f"The AI provider returned an error: {exc}")


def run_chat(db: Session, message: str, history: Optional[list[dict]] = None) -> dict:
    if not is_configured():
        raise AssistantConfigError("Assistant is not configured - the required API key is missing")

    from langchain.agents import create_agent
    from langgraph.errors import GraphRecursionError

    start = time.time()
    model = _resolve_chat_model()
    tools = build_tools(db)
    system_prompt = _build_system_prompt(db)
    agent = create_agent(model=model, tools=tools, system_prompt=system_prompt)

    trimmed_history = (history or [])[-MAX_HISTORY_MESSAGES:]
    input_messages = [{"role": h["role"], "content": h["content"]} for h in trimmed_history]
    input_messages.append({"role": "user", "content": message})

    try:
        result = agent.invoke({"messages": input_messages}, config={"recursion_limit": RECURSION_LIMIT})
    except GraphRecursionError:
        return {
            "reply": RECURSION_LIMIT_REPLY,
            "tool_calls": [],
            "model": current_model_spec(),
            "elapsed_ms": int((time.time() - start) * 1000),
        }
    except (AssistantConfigError, AssistantProviderError):
        raise
    except Exception as exc:
        raise _map_provider_error(exc)

    out_messages = result["messages"]
    reply = out_messages[-1].content if out_messages else ""
    tool_calls = _extract_tool_calls(out_messages)

    return {
        "reply": reply,
        "tool_calls": tool_calls,
        "model": current_model_spec(),
        "elapsed_ms": int((time.time() - start) * 1000),
    }

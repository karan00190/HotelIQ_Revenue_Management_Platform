"use client";

import { useEffect, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Send, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { assistantApi, type AssistantChatMessage, type AssistantStatus, type AssistantToolCall, type Hotel } from "@/lib/api";
import { ChatMessage, TypingIndicator } from "./ChatMessage";

const STARTER_QUESTIONS = [
  "What was Grand Plaza Mumbai's revenue last December?",
  "How does the occupancy forecast look for Coastal Inn Goa over the next two weeks?",
  "What is RevPAR?",
  "Should I raise prices for a weekend booking three days from now at Heritage Stay Jaipur?",
];

interface DisplayMessage {
  role: "user" | "assistant";
  content: string;
  toolCalls?: AssistantToolCall[];
  model?: string;
}

export function AssistantPageClient({
  initialStatus,
  hotels,
}: {
  initialStatus: AssistantStatus;
  hotels: Hotel[];
}) {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const mutation = useMutation({
    mutationFn: (payload: { message: string; history: AssistantChatMessage[] }) =>
      assistantApi.chat(payload.message, payload.history),
    onSuccess: (result) => {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: result.reply, toolCalls: result.tool_calls, model: result.model },
      ]);
    },
    onError: (error) => {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: error instanceof Error ? error.message : "Something went wrong reaching the assistant.",
        },
      ]);
    },
  });

  function handleSend(text: string) {
    const trimmed = text.trim();
    if (!trimmed || mutation.isPending) return;

    const history: AssistantChatMessage[] = messages
      .slice(-10)
      .map((m) => ({ role: m.role, content: m.content }));

    setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
    setInput("");
    mutation.mutate({ message: trimmed, history });
  }

  return (
    <div className="flex w-full flex-col gap-6 p-6 md:p-10">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="flex size-10 items-center justify-center rounded-xl bg-linear-to-br from-chat-user-from to-chat-user-to text-white shadow-md ring-1 ring-white/20">
            <Sparkles className="size-5" />
          </span>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-foreground">Assistant</h1>
            <p className="text-sm text-muted-foreground">
              Ask about revenue, occupancy, forecasts, or pricing across {hotels.length} hotels — every number
              comes from a real tool call.
            </p>
          </div>
        </div>
        {initialStatus.configured && (
          <span className="flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 text-xs text-muted-foreground shadow-sm">
            <span className="relative flex size-2">
              <span className="absolute inline-flex size-full animate-ping rounded-full bg-status-good opacity-75" />
              <span className="relative inline-flex size-2 rounded-full bg-status-good" />
            </span>
            {initialStatus.knowledge_chunks} knowledge chunks
          </span>
        )}
      </div>

      {!initialStatus.configured ? (
        <div className="rounded-lg border border-status-warning/40 bg-status-warning/10 p-4 text-sm">
          <p className="font-medium text-foreground">Assistant not configured</p>
          <p className="mt-1 text-muted-foreground">
            The server is missing the API key for its configured free LLM provider ({initialStatus.model}).
            Set it in the backend environment and restart the server to enable this page.
          </p>
        </div>
      ) : (
        <>
          <div className="flex min-h-[460px] flex-col gap-5 rounded-2xl border border-border bg-linear-to-br from-assistant-bubble/50 via-muted/30 to-assistant-bubble-2/50 p-4 shadow-sm md:p-6">
            {messages.length === 0 && (
              <div className="flex flex-1 flex-col items-center justify-center gap-5 py-10 text-center">
                <div className="flex size-14 items-center justify-center rounded-2xl bg-linear-to-br from-chat-user-from to-chat-user-to text-white shadow-md ring-1 ring-white/20">
                  <Sparkles className="size-7" />
                </div>
                <div className="space-y-1">
                  <p className="text-base font-medium text-foreground">How can I help?</p>
                  <p className="text-sm text-muted-foreground">Pick a question to get started, or type your own below.</p>
                </div>
                <div className="flex flex-wrap justify-center gap-2">
                  {STARTER_QUESTIONS.map((q) => (
                    <button
                      key={q}
                      onClick={() => handleSend(q)}
                      className="rounded-full border border-border bg-card px-3.5 py-1.5 text-xs text-foreground shadow-sm transition-all duration-200 hover:border-assistant-glow/60 hover:bg-assistant-bubble hover:shadow-md"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((m, i) => (
              <ChatMessage key={i} role={m.role} content={m.content} toolCalls={m.toolCalls} model={m.model} />
            ))}

            {mutation.isPending && <TypingIndicator />}

            <div ref={bottomRef} />
          </div>

          <div className="flex items-end gap-2 rounded-2xl border border-border bg-card p-2 shadow-sm transition-all focus-within:border-assistant-glow/60 focus-within:ring-2 focus-within:ring-assistant-glow/20">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend(input);
                }
              }}
              rows={1}
              placeholder="Ask about revenue, occupancy, forecasts, or pricing..."
              className="min-h-9 flex-1 resize-none bg-transparent px-2 py-1.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none"
            />
            <Button
              onClick={() => handleSend(input)}
              disabled={mutation.isPending || !input.trim()}
              className="gap-1.5 bg-linear-to-r from-chat-user-from to-chat-user-to text-white hover:opacity-90"
            >
              <Send className="size-4" />
              Send
            </Button>
          </div>
        </>
      )}
    </div>
  );
}

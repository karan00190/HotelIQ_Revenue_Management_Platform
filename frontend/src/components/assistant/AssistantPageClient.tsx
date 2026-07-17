"use client";

import { useEffect, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { assistantApi, type AssistantChatMessage, type AssistantStatus, type AssistantToolCall, type Hotel } from "@/lib/api";
import { ChatMessage } from "./ChatMessage";

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
    <div className="flex w-full flex-col gap-4 p-6 md:p-10">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Assistant</h1>
          <p className="text-sm text-muted-foreground">
            Ask about revenue, occupancy, forecasts, or pricing across {hotels.length} hotels - every number
            comes from a real tool call, never a guess.
          </p>
        </div>
        {initialStatus.configured && (
          <span className="text-xs text-muted-foreground">
            {initialStatus.model} - {initialStatus.knowledge_chunks} knowledge chunks
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
          <div className="flex min-h-[420px] flex-col gap-4 rounded-xl border border-border bg-muted p-4 md:p-6">
            {messages.length === 0 && (
              <div className="flex flex-1 flex-col items-center justify-center gap-4 py-10 text-center">
                <p className="text-sm text-muted-foreground">Try asking:</p>
                <div className="flex flex-wrap justify-center gap-2">
                  {STARTER_QUESTIONS.map((q) => (
                    <button
                      key={q}
                      onClick={() => handleSend(q)}
                      className="rounded-full border border-border bg-card px-3 py-1.5 text-xs text-foreground shadow-sm transition-colors hover:bg-primary hover:text-primary-foreground"
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

            {mutation.isPending && (
              <ChatMessage role="assistant" content="Thinking..." />
            )}

            <div ref={bottomRef} />
          </div>

          <div className="flex items-end gap-2">
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
              className="min-h-10 flex-1 resize-none rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground"
            />
            <Button onClick={() => handleSend(input)} disabled={mutation.isPending || !input.trim()}>
              Send
            </Button>
          </div>
        </>
      )}
    </div>
  );
}

"use client";

import { Sparkles, User } from "lucide-react";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { AssistantToolCall } from "@/lib/api";

const markdownComponents: Components = {
  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
  ul: ({ children }) => <ul className="mb-2 list-disc space-y-0.5 pl-5 last:mb-0">{children}</ul>,
  ol: ({ children }) => <ol className="mb-2 list-decimal space-y-0.5 pl-5 last:mb-0">{children}</ol>,
  li: ({ children }) => <li>{children}</li>,
  a: ({ children, href }) => (
    <a href={href} target="_blank" rel="noopener noreferrer" className="text-assistant-glow underline underline-offset-2">
      {children}
    </a>
  ),
  code: ({ children }) => (
    <code className="rounded bg-foreground/10 px-1 py-0.5 font-mono text-[0.85em]">{children}</code>
  ),
  table: ({ children }) => (
    <div className="mb-2 overflow-x-auto last:mb-0">
      <table className="w-full border-collapse text-xs">{children}</table>
    </div>
  ),
  th: ({ children }) => (
    <th className="border border-border px-2 py-1 text-left font-semibold">{children}</th>
  ),
  td: ({ children }) => <td className="border border-border px-2 py-1">{children}</td>,
};

function Avatar({ isUser }: { isUser: boolean }) {
  return (
    <div
      className={cn(
        "flex size-8 shrink-0 items-center justify-center rounded-full text-white shadow-sm ring-1 ring-white/25",
        isUser
          ? "bg-linear-to-br from-chat-user-from to-chat-user-to"
          : "bg-linear-to-br from-chat-user-to to-chat-user-from",
      )}
    >
      {isUser ? <User className="size-4" /> : <Sparkles className="size-4" />}
    </div>
  );
}

function ToolCallChip({ call }: { call: AssistantToolCall }) {
  const argsText = Object.keys(call.args).length > 0 ? JSON.stringify(call.args) : "";

  return (
    <details className="rounded-md border border-border bg-background px-2 py-1">
      <summary className="flex cursor-pointer list-none items-center gap-2 text-xs">
        <Badge variant={call.ok ? "outline" : "destructive"}>{call.tool}</Badge>
        {argsText && <span className="truncate text-muted-foreground">{argsText}</span>}
        {!call.ok && <span className="font-medium text-status-critical">error</span>}
      </summary>
      <pre className="mt-2 max-h-48 overflow-auto rounded bg-muted p-2 text-[11px] text-muted-foreground">
        {JSON.stringify(call.summary, null, 2)}
      </pre>
    </details>
  );
}

export function ChatMessage({
  role,
  content,
  toolCalls,
  model,
}: {
  role: "user" | "assistant";
  content: string;
  toolCalls?: AssistantToolCall[];
  model?: string;
}) {
  const isUser = role === "user";

  return (
    <div
      className={cn(
        "flex w-full items-end gap-2.5 duration-300 animate-in fade-in slide-in-from-bottom-2",
        isUser ? "justify-end" : "justify-start",
      )}
    >
      {!isUser && <Avatar isUser={false} />}
      <div className={cn("flex max-w-[78%] flex-col gap-2", isUser ? "items-end" : "items-start")}>
        <div
          className={cn(
            "rounded-2xl px-4 py-2.5 text-sm leading-relaxed shadow-sm ring-1",
            isUser
              ? "rounded-br-md bg-linear-to-br from-chat-user-from to-chat-user-to text-white shadow-md ring-white/10"
              : "rounded-bl-md bg-linear-to-br from-assistant-bubble to-assistant-bubble-2 text-foreground ring-assistant-bubble-border",
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{content}</p>
          ) : (
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
              {content}
            </ReactMarkdown>
          )}
        </div>

        {!isUser && toolCalls && toolCalls.length > 0 && (
          <details className="w-full rounded-lg border border-border bg-card/60 px-3 py-2">
            <summary className="cursor-pointer text-xs font-medium text-muted-foreground transition-colors hover:text-foreground">
              How I got this ({toolCalls.length} tool call{toolCalls.length > 1 ? "s" : ""})
            </summary>
            <div className="mt-2 flex flex-col gap-1.5">
              {toolCalls.map((call, i) => (
                <ToolCallChip key={i} call={call} />
              ))}
            </div>
          </details>
        )}

        {!isUser && model && <span className="px-1 text-[11px] text-muted-foreground">{model}</span>}
      </div>
      {isUser && <Avatar isUser={true} />}
    </div>
  );
}

export function TypingIndicator() {
  return (
    <div className="flex w-full items-end gap-2.5 duration-300 animate-in fade-in">
      <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-linear-to-br from-chat-user-to to-chat-user-from text-white shadow-sm ring-1 ring-white/25">
        <Sparkles className="size-4" />
      </div>
      <div className="flex items-center gap-1.5 rounded-2xl rounded-bl-md bg-linear-to-br from-assistant-bubble to-assistant-bubble-2 px-4 py-3.5 shadow-sm ring-1 ring-assistant-bubble-border">
        <span className="size-1.5 animate-bounce rounded-full bg-chat-user-to" />
        <span className="size-1.5 animate-bounce rounded-full bg-chat-user-from delay-150" />
        <span className="size-1.5 animate-bounce rounded-full bg-chat-user-to delay-300" />
      </div>
    </div>
  );
}

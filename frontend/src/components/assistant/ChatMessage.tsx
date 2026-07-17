"use client";

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
    <a href={href} target="_blank" rel="noopener noreferrer" className="underline underline-offset-2">
      {children}
    </a>
  ),
  code: ({ children }) => (
    <code className="rounded bg-black/10 px-1 py-0.5 font-mono text-[0.85em] dark:bg-white/15">{children}</code>
  ),
  table: ({ children }) => (
    <div className="mb-2 overflow-x-auto last:mb-0">
      <table className="w-full border-collapse text-xs">{children}</table>
    </div>
  ),
  th: ({ children }) => (
    <th className="border border-current/20 px-2 py-1 text-left font-semibold">{children}</th>
  ),
  td: ({ children }) => <td className="border border-current/20 px-2 py-1">{children}</td>,
};

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
    <div className={cn("flex w-full", isUser ? "justify-end" : "justify-start")}>
      <div className={cn("flex max-w-[80%] flex-col gap-2", isUser ? "items-end" : "items-start")}>
        <div
          className={cn(
            "rounded-2xl px-4 py-2.5 text-sm leading-relaxed shadow-sm",
            isUser
              ? "bg-primary text-primary-foreground"
              : "border border-border bg-card text-card-foreground",
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
          <details className="w-full rounded-lg border border-border bg-muted px-3 py-2">
            <summary className="cursor-pointer text-xs font-medium text-muted-foreground">
              How I got this ({toolCalls.length} tool call{toolCalls.length > 1 ? "s" : ""})
            </summary>
            <div className="mt-2 flex flex-col gap-1.5">
              {toolCalls.map((call, i) => (
                <ToolCallChip key={i} call={call} />
              ))}
            </div>
          </details>
        )}

        {!isUser && model && <span className="text-[11px] text-muted-foreground">{model}</span>}
      </div>
    </div>
  );
}

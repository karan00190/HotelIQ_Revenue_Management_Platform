"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { AssistantToolCall } from "@/lib/api";

function ToolCallChip({ call }: { call: AssistantToolCall }) {
  const argsText = Object.keys(call.args).length > 0 ? JSON.stringify(call.args) : "";

  return (
    <details className="rounded-md border border-border bg-muted/30 px-2 py-1">
      <summary className="flex cursor-pointer list-none items-center gap-2 text-xs">
        <Badge variant={call.ok ? "outline" : "destructive"}>{call.tool}</Badge>
        {argsText && <span className="truncate text-muted-foreground">{argsText}</span>}
        {!call.ok && <span className="font-medium text-status-critical">error</span>}
      </summary>
      <pre className="mt-2 max-h-48 overflow-auto rounded bg-background p-2 text-[11px] text-muted-foreground">
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
            "whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
            isUser
              ? "bg-accent text-accent-foreground"
              : "bg-card text-card-foreground ring-1 ring-foreground/10",
          )}
        >
          {content}
        </div>

        {!isUser && toolCalls && toolCalls.length > 0 && (
          <details className="w-full rounded-lg border border-border bg-muted/20 px-3 py-2">
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

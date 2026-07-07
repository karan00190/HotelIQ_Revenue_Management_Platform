const STATUS_COLOR: Record<string, string> = {
  confirmed: "var(--status-good)",
  completed: "var(--chart-1)",
  cancelled: "var(--status-critical)",
};

export function StatusDot({ status }: { status: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span
        className="h-2 w-2 rounded-full"
        style={{ backgroundColor: STATUS_COLOR[status] ?? "var(--muted-foreground)" }}
      />
      <span className="capitalize">{status}</span>
    </span>
  );
}

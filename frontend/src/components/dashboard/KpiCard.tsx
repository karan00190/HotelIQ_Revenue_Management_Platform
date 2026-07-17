import { Card, CardContent } from "@/components/ui/card";

interface KpiCardProps {
  label: string;
  value: string;
  hint?: string;
  /** A CSS color (e.g. "var(--chart-1)") used for the accent bar. */
  accent?: string;
  /** Stagger index for the entrance animation. */
  index?: number;
}

export function KpiCard({ label, value, hint, accent = "var(--chart-1)", index = 0 }: KpiCardProps) {
  return (
    <Card
      className="relative overflow-hidden transition-all duration-300 animate-in fade-in slide-in-from-bottom-2 hover:-translate-y-0.5 hover:shadow-md"
      style={{ animationDelay: `${index * 60}ms`, animationFillMode: "backwards" }}
    >
      <span
        aria-hidden
        className="absolute inset-x-0 top-0 h-1"
        style={{ background: `linear-gradient(90deg, ${accent}, transparent 90%)` }}
      />
      <CardContent className="flex flex-col gap-1 pt-1">
        <span className="flex items-center gap-2 text-sm text-muted-foreground">
          <span className="size-2 rounded-full" style={{ background: accent }} />
          {label}
        </span>
        <span className="text-3xl font-semibold text-foreground">{value}</span>
        {hint && <span className="text-xs text-muted-foreground">{hint}</span>}
      </CardContent>
    </Card>
  );
}

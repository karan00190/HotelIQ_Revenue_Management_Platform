"use client";

import { CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DailyComparisonPoint } from "@/lib/api";
import { formatDateShort } from "@/lib/date";

// Listed in legend/reading order. Rendered in reverse so "actual" (the
// ground truth) draws last and stays visually on top of the three
// competing model lines, instead of risking being covered by them.
const SERIES = [
  { key: "actual", label: "Actual", color: "var(--foreground)", strokeWidth: 2.5 },
  { key: "xgboost", label: "XGBoost (challenger)", color: "var(--chart-2)", strokeWidth: 2 },
  { key: "prophet", label: "Prophet", color: "var(--chart-1)", strokeWidth: 2 },
  { key: "naive", label: "Naive baseline", color: "var(--chart-3)", strokeWidth: 2 },
] as const;

function ComparisonTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: { dataKey: string; value: number | string }[];
  label?: string;
}) {
  if (!active || !payload || payload.length === 0 || !label) return null;
  const byKey = Object.fromEntries(payload.map((p) => [p.dataKey, p.value]));
  return (
    <div
      style={{
        background: "var(--card)",
        border: "1px solid var(--border)",
        borderRadius: 8,
        padding: "8px 10px",
        fontSize: 12,
      }}
    >
      <p className="mb-1 font-medium text-foreground">{formatDateShort(label)}</p>
      {SERIES.map((s) => (
        <p key={s.key} className="flex items-center gap-1.5 text-muted-foreground">
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: s.color }} />
          {s.label}: {byKey[s.key] !== undefined ? `${Number(byKey[s.key]).toFixed(1)}%` : "—"}
        </p>
      ))}
    </div>
  );
}

export function ForecastComparisonChart({ data }: { data: DailyComparisonPoint[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Held-out test window: actual vs. forecast</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="h-80 px-2">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={data} margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
              <CartesianGrid stroke="var(--border)" vertical={false} />
              <XAxis
                dataKey="date"
                tickFormatter={formatDateShort}
                tick={{ fill: "var(--muted-foreground)", fontSize: 12 }}
                axisLine={{ stroke: "var(--border)" }}
                tickLine={false}
                minTickGap={32}
              />
              <YAxis
                tickFormatter={(v) => `${v}%`}
                tick={{ fill: "var(--muted-foreground)", fontSize: 12 }}
                axisLine={false}
                tickLine={false}
                width={44}
              />
              <Tooltip content={<ComparisonTooltip />} />
              {[...SERIES].reverse().map((s) => (
                <Line
                  key={s.key}
                  type="monotone"
                  dataKey={s.key}
                  stroke={s.color}
                  strokeWidth={s.strokeWidth}
                  dot={false}
                  activeDot={{ r: 4, strokeWidth: 2, stroke: "var(--card)" }}
                  isAnimationActive={false}
                />
              ))}
            </ComposedChart>
          </ResponsiveContainer>
        </div>
        <div className="flex flex-wrap items-center gap-4 px-2">
          {SERIES.map((s) => (
            <span key={s.key} className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span className="inline-block h-2 w-2 rounded-full" style={{ background: s.color }} />
              {s.label}
            </span>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

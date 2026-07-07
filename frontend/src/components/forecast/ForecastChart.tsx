"use client";

import { Area, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ForecastPrediction } from "@/lib/api";
import { formatDateShort } from "@/lib/date";

interface TooltipEntry {
  payload: ForecastPrediction;
}

function ForecastTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: TooltipEntry[];
  label?: string;
}) {
  if (!active || !payload || payload.length === 0 || !label) return null;
  const point = payload[0].payload;
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
      <p className="text-muted-foreground">Predicted: {point.predicted_occupancy.toFixed(1)}%</p>
      <p className="text-muted-foreground">
        Range: {point.lower_bound.toFixed(1)}% – {point.upper_bound.toFixed(1)}%
      </p>
    </div>
  );
}

export function ForecastChart({ predictions }: { predictions: ForecastPrediction[] }) {
  // Recharts has no native confidence-band mark, so this is the standard
  // stacked-area trick: an invisible base area up to lower_bound, then a
  // visible area sized (upper_bound - lower_bound) stacked on top of it -
  // the visible band then spans exactly [lower_bound, upper_bound].
  const chartData = predictions.map((p) => ({
    ...p,
    bandBase: p.lower_bound,
    bandSize: p.upper_bound - p.lower_bound,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>30-day occupancy forecast</CardTitle>
      </CardHeader>
      <CardContent className="h-80 px-2">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
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
            <Tooltip content={<ForecastTooltip />} />
            <Area dataKey="bandBase" stackId="band" stroke="none" fill="transparent" isAnimationActive={false} />
            <Area
              dataKey="bandSize"
              stackId="band"
              stroke="none"
              fill="var(--chart-1)"
              fillOpacity={0.12}
              isAnimationActive={false}
            />
            <Line
              type="monotone"
              dataKey="predicted_occupancy"
              stroke="var(--chart-1)"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, strokeWidth: 2, stroke: "var(--card)" }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

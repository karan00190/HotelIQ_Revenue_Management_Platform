"use client";

import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { TrendPoint } from "@/lib/api";
import { formatDateShort } from "@/lib/date";

const currencyFull = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

function formatCompact(value: number) {
  if (value >= 100_000) return `₹${(value / 100_000).toFixed(1)}L`;
  if (value >= 1_000) return `₹${(value / 1_000).toFixed(0)}K`;
  return `₹${value.toFixed(0)}`;
}

function MiniLineChart({
  data,
  dataKey,
  color,
  label,
}: {
  data: TrendPoint[];
  dataKey: "average_daily_rate" | "revenue_per_available_room";
  color: string;
  label: string;
}) {
  return (
    <div className="flex-1">
      <p className="mb-2 text-sm text-muted-foreground">{label}</p>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="var(--border)" vertical={false} />
            <XAxis
              dataKey="date"
              tickFormatter={formatDateShort}
              tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
              axisLine={{ stroke: "var(--border)" }}
              tickLine={false}
              minTickGap={40}
            />
            <YAxis
              tickFormatter={formatCompact}
              tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={52}
            />
            <Tooltip
              formatter={(value) => [currencyFull.format(Number(value)), label]}
              labelFormatter={(l) => formatDateShort(String(l))}
              contentStyle={{
                background: "var(--card)",
                border: "1px solid var(--border)",
                borderRadius: 8,
                fontSize: 12,
              }}
            />
            <Line
              type="monotone"
              dataKey={dataKey}
              stroke={color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, strokeWidth: 2, stroke: "var(--card)" }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function AdrRevparTrendChart({ data }: { data: TrendPoint[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>ADR &amp; RevPAR trends</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4 px-2 md:flex-row">
        <MiniLineChart
          data={data}
          dataKey="average_daily_rate"
          color="var(--chart-1)"
          label="Average Daily Rate (ADR)"
        />
        <MiniLineChart
          data={data}
          dataKey="revenue_per_available_room"
          color="var(--chart-2)"
          label="RevPAR"
        />
      </CardContent>
    </Card>
  );
}

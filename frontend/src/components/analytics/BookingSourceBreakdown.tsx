"use client";

import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { BookingSourceDistribution } from "@/lib/api";

const SOURCE_LABELS: Record<string, string> = {
  "booking.com": "Booking.com",
  website: "Website",
  direct: "Direct",
  expedia: "Expedia",
  makemytrip: "MakeMyTrip",
};

const SOURCE_COLORS = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
];

export function BookingSourceBreakdown({ data }: { data: BookingSourceDistribution }) {
  const chartData = data.sources.map((s) => ({
    source: SOURCE_LABELS[s.booking_source] ?? s.booking_source,
    count: s.booking_count,
    percent: s.percent_of_bookings,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Booking source breakdown</CardTitle>
      </CardHeader>
      <CardContent className="px-2" style={{ height: Math.max(180, chartData.length * 44) }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical" margin={{ top: 8, right: 32, left: 8, bottom: 0 }}>
            <CartesianGrid stroke="var(--border)" horizontal={false} />
            <XAxis
              type="number"
              tick={{ fill: "var(--muted-foreground)", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              type="category"
              dataKey="source"
              tick={{ fill: "var(--muted-foreground)", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              width={90}
            />
            <Tooltip
              formatter={(value) => [`${value} bookings`, "Count"]}
              contentStyle={{
                background: "var(--card)",
                border: "1px solid var(--border)",
                borderRadius: 8,
                fontSize: 12,
              }}
            />
            <Bar dataKey="count" radius={[0, 4, 4, 0]} maxBarSize={22}>
              {chartData.map((_, i) => (
                <Cell key={i} fill={SOURCE_COLORS[i % SOURCE_COLORS.length]} />
              ))}
              <LabelList
                dataKey="percent"
                position="right"
                formatter={(value) => `${Number(value).toFixed(0)}%`}
                style={{ fill: "var(--muted-foreground)", fontSize: 12 }}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

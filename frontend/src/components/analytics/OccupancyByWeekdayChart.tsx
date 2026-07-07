"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { TrendPoint } from "@/lib/api";
import { parseLocalDate } from "@/lib/date";

const WEEKDAY_NAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
// Present Monday -> Sunday, a more natural week reading order than the
// JS Date default (Sunday=0).
const WEEK_ORDER = [1, 2, 3, 4, 5, 6, 0];

function aggregateByWeekday(data: TrendPoint[]) {
  const sums = new Array(7).fill(0);
  const counts = new Array(7).fill(0);
  for (const point of data) {
    const day = parseLocalDate(point.date).getDay();
    sums[day] += point.occupancy_rate;
    counts[day] += 1;
  }
  return WEEK_ORDER.map((day) => ({
    weekday: WEEKDAY_NAMES[day],
    averageOccupancy: counts[day] > 0 ? Math.round((sums[day] / counts[day]) * 100) / 100 : 0,
  }));
}

export function OccupancyByWeekdayChart({ data }: { data: TrendPoint[] }) {
  const chartData = aggregateByWeekday(data);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Occupancy by day of week</CardTitle>
      </CardHeader>
      <CardContent className="h-64 px-2">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
            <CartesianGrid stroke="var(--border)" vertical={false} />
            <XAxis
              dataKey="weekday"
              tick={{ fill: "var(--muted-foreground)", fontSize: 12 }}
              axisLine={{ stroke: "var(--border)" }}
              tickLine={false}
            />
            <YAxis
              tickFormatter={(v) => `${v}%`}
              tick={{ fill: "var(--muted-foreground)", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              width={40}
            />
            <Tooltip
              formatter={(value) => [`${value}%`, "Avg occupancy"]}
              contentStyle={{
                background: "var(--card)",
                border: "1px solid var(--border)",
                borderRadius: 8,
                fontSize: 12,
              }}
            />
            <Bar dataKey="averageOccupancy" fill="var(--chart-1)" radius={[4, 4, 0, 0]} maxBarSize={24} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

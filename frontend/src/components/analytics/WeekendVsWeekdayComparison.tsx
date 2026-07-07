import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { WeekendVsWeekday } from "@/lib/api";

const currency = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

function StatBlock({ label, count, avgPrice }: { label: string; count: number; avgPrice: number }) {
  return (
    <div className="flex flex-1 flex-col gap-1 rounded-lg bg-muted/40 p-4">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-2xl font-semibold text-foreground">{currency.format(avgPrice)}</span>
      <span className="text-xs text-muted-foreground">avg price &middot; {count} bookings</span>
    </div>
  );
}

export function WeekendVsWeekdayComparison({ data }: { data: WeekendVsWeekday }) {
  const premium = data.weekend_premium_percent;
  return (
    <Card>
      <CardHeader>
        <CardTitle>Weekend vs weekday</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="flex gap-3">
          <StatBlock label="Weekday" count={data.weekday.count} avgPrice={data.weekday.average_price} />
          <StatBlock label="Weekend" count={data.weekend.count} avgPrice={data.weekend.average_price} />
        </div>
        <p className="text-sm text-muted-foreground">
          Weekend prices run{" "}
          <span
            className="font-semibold"
            style={{ color: premium >= 0 ? "var(--status-good)" : "var(--status-critical)" }}
          >
            {premium >= 0 ? "+" : ""}
            {premium.toFixed(1)}%
          </span>{" "}
          {premium >= 0 ? "higher" : "lower"} than weekday.
        </p>
      </CardContent>
    </Card>
  );
}

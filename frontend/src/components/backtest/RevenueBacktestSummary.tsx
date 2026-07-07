import { KpiCard } from "@/components/dashboard/KpiCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { BootstrapDelta, RevenueBacktestResult } from "@/lib/api";
import { formatDateShort } from "@/lib/date";

const currency = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

function DeltaSentence({
  subject,
  reference,
  delta,
}: {
  subject: string;
  reference: string;
  delta: BootstrapDelta;
}) {
  const positive = delta.point_estimate >= 0;
  return (
    <p className="text-sm text-muted-foreground">
      {subject} is{" "}
      <span className="font-semibold" style={{ color: positive ? "var(--status-good)" : "var(--status-critical)" }}>
        {positive ? "+" : ""}
        {currency.format(delta.point_estimate)}
      </span>{" "}
      {positive ? "higher" : "lower"} than {reference} (90% bootstrap range: {currency.format(delta.p5)} to{" "}
      {currency.format(delta.p95)}, {delta.p5 >= 0 || delta.p95 <= 0 ? "consistent in sign" : "straddles zero"}).
    </p>
  );
}

export function RevenueBacktestSummary({ data }: { data: RevenueBacktestResult }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          Revenue backtest &middot; {data.booking_count} real bookings &middot;{" "}
          {formatDateShort(data.test_date_range.start)} to {formatDateShort(data.test_date_range.end)}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-5">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <KpiCard
            label="Actual revenue"
            value={currency.format(data.actual_revenue)}
            hint="What the generator's own historical weekend/season pricing produced"
          />
          <KpiCard
            label="Simulated: Prophet-priced"
            value={currency.format(data.simulated_revenue_prophet)}
            hint="Same bookings, priced by the rule engine using Prophet's forecast"
          />
          <KpiCard
            label="Simulated: XGBoost-priced"
            value={currency.format(data.simulated_revenue_ml)}
            hint="Same bookings, priced by the rule engine using the XGBoost challenger's forecast"
          />
        </div>

        <div className="flex flex-col gap-1 rounded-lg bg-muted/40 p-4">
          <span className="text-xs font-medium text-muted-foreground">
            Primary comparison - identical pricing formula, identical bookings, only the forecaster differs
          </span>
          <DeltaSentence subject="XGBoost-priced revenue" reference="Prophet-priced revenue" delta={data.deltas.ml_vs_prophet} />
        </div>

        <div className="flex flex-col gap-2 rounded-lg border border-border p-4">
          <span className="text-xs font-medium text-muted-foreground">
            Secondary comparison - carries a constant-demand assumption (see below)
          </span>
          <DeltaSentence subject="XGBoost-priced revenue" reference="actual historical revenue" delta={data.deltas.ml_vs_actual} />
          <DeltaSentence subject="Prophet-priced revenue" reference="actual historical revenue" delta={data.deltas.prophet_vs_actual} />
        </div>

        <div className="flex flex-col gap-1.5 border-t border-border pt-4">
          <span className="text-xs font-medium text-muted-foreground">Methodology and assumptions</span>
          <ul className="list-disc space-y-1 pl-5 text-xs text-muted-foreground">
            {data.assumptions.map((a) => (
              <li key={a}>{a}</li>
            ))}
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}

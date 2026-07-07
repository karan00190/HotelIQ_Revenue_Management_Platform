import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ForecastPrediction } from "@/lib/api";
import { parseLocalDate } from "@/lib/date";
import { HIGH_DEMAND_THRESHOLD } from "@/lib/forecastThresholds";

// Sequential single-hue ramp (blue), same as OccupancyHeatmap in Module 12.
const RAMP = [
  "var(--seq-100)",
  "var(--seq-200)",
  "var(--seq-300)",
  "var(--seq-400)",
  "var(--seq-500)",
  "var(--seq-600)",
  "var(--seq-700)",
];

const WEEKDAY_LABELS = ["S", "M", "T", "W", "T", "F", "S"];

function colorFor(value: number, min: number, max: number): string {
  if (max === min) return RAMP[0];
  const t = (value - min) / (max - min);
  const idx = Math.min(RAMP.length - 1, Math.floor(t * RAMP.length));
  return RAMP[idx];
}

export function ForecastCalendar({ predictions }: { predictions: ForecastPrediction[] }) {
  if (predictions.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Forecast calendar</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No forecast data.</p>
        </CardContent>
      </Card>
    );
  }

  const values = predictions.map((p) => p.predicted_occupancy);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const leadingBlanks = parseLocalDate(predictions[0].date).getDay();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Forecast calendar</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="mb-1 grid grid-cols-7 gap-1 text-center text-xs text-muted-foreground">
          {WEEKDAY_LABELS.map((label, i) => (
            <div key={i}>{label}</div>
          ))}
        </div>
        <div className="grid grid-cols-7 gap-1">
          {Array.from({ length: leadingBlanks }).map((_, i) => (
            <div key={`blank-${i}`} />
          ))}
          {predictions.map((p) => {
            const isHighDemand = p.predicted_occupancy > HIGH_DEMAND_THRESHOLD;
            return (
              <div
                key={p.date}
                title={`${p.date}: ${p.predicted_occupancy.toFixed(1)}% predicted (range ${p.lower_bound.toFixed(1)}-${p.upper_bound.toFixed(1)}%)`}
                className="flex aspect-square items-center justify-center rounded-md text-[11px] text-foreground/70"
                style={{
                  backgroundColor: colorFor(p.predicted_occupancy, min, max),
                  boxShadow: isHighDemand ? "inset 0 0 0 2px var(--status-warning)" : undefined,
                }}
              >
                {parseLocalDate(p.date).getDate()}
              </div>
            );
          })}
        </div>
        <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
          <span>{min.toFixed(1)}%</span>
          <div className="flex h-2 flex-1 overflow-hidden rounded-full">
            {RAMP.map((c) => (
              <div key={c} style={{ backgroundColor: c }} className="flex-1" />
            ))}
          </div>
          <span>{max.toFixed(1)}%</span>
        </div>
      </CardContent>
    </Card>
  );
}

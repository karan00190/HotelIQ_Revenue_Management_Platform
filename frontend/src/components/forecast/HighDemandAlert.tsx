import { TriangleAlertIcon } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ForecastPrediction } from "@/lib/api";
import { formatDateShort } from "@/lib/date";
import { HIGH_DEMAND_THRESHOLD } from "@/lib/forecastThresholds";

export function HighDemandAlert({ predictions }: { predictions: ForecastPrediction[] }) {
  const highDemandDays = predictions.filter((p) => p.predicted_occupancy > HIGH_DEMAND_THRESHOLD);

  return (
    <Card>
      <CardHeader>
        <CardTitle>High demand alerts</CardTitle>
      </CardHeader>
      <CardContent>
        {highDemandDays.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No dates in this forecast window are predicted above {HIGH_DEMAND_THRESHOLD}% occupancy.
          </p>
        ) : (
          <ul className="flex flex-col gap-2">
            {highDemandDays.map((p) => (
              <li key={p.date} className="flex items-center gap-2 text-sm">
                <TriangleAlertIcon className="h-4 w-4" style={{ color: "var(--status-warning)" }} />
                <span className="font-medium text-foreground">{formatDateShort(p.date)}</span>
                <span className="text-muted-foreground">{p.predicted_occupancy.toFixed(1)}% predicted occupancy</span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

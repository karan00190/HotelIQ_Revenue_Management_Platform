import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { ForecastComparisonResult, ModelMetrics } from "@/lib/api";

type ModelKey = keyof ForecastComparisonResult["models"];

const ROWS: { key: ModelKey; label: string }[] = [
  { key: "naive", label: "Naive baseline" },
  { key: "prophet", label: "Prophet" },
  { key: "xgboost", label: "XGBoost (challenger)" },
];

export function ModelAccuracyTable({ models }: { models: Record<ModelKey, ModelMetrics> }) {
  const bestKey = ROWS.reduce((best, row) => (models[row.key].mae < models[best].mae ? row.key : best), ROWS[0].key);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Forecast accuracy on the held-out window</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Model</TableHead>
              <TableHead className="text-right">MAE (pp)</TableHead>
              <TableHead className="text-right">RMSE (pp)</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {ROWS.map(({ key, label }) => (
              <TableRow key={key}>
                <TableCell className="text-foreground">
                  {label}
                  {key === bestKey && <span className="ml-2 text-xs text-status-good">lowest error</span>}
                </TableCell>
                <TableCell className="text-right" style={{ fontVariantNumeric: "tabular-nums" }}>
                  {models[key].mae.toFixed(2)}
                </TableCell>
                <TableCell className="text-right" style={{ fontVariantNumeric: "tabular-nums" }}>
                  {models[key].rmse.toFixed(2)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <p className="text-xs text-muted-foreground">
          MAE/RMSE in percentage points of occupancy - lower is better. {models.naive.description}.
        </p>
      </CardContent>
    </Card>
  );
}

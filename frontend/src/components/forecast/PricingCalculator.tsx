"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { forecastApi } from "@/lib/api";

const currency = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

export function PricingCalculator({
  hotelId,
  defaultTargetDate,
}: {
  hotelId: number;
  defaultTargetDate: string;
}) {
  // Deliberately NOT derived from the system clock (new Date() + N days):
  // the seeded demo data's date range is fixed from when it was generated,
  // while real time keeps advancing. A clock-based default can drift past
  // the training data's cutoff and 400 immediately on page load with zero
  // user interaction. Deriving it from the forecast's own predictions (a
  // date guaranteed to be in the forecastable window) avoids that entirely.
  const [targetDate, setTargetDate] = useState(defaultTargetDate);
  const [basePrice, setBasePrice] = useState("5000");

  const mutation = useMutation({
    mutationFn: () => forecastApi.pricingRecommendation(hotelId, targetDate, Number(basePrice)),
  });

  const result = mutation.data;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Pricing recommendation calculator</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 text-sm">
            <span className="text-muted-foreground">Target date</span>
            <input
              type="date"
              value={targetDate}
              onChange={(e) => setTargetDate(e.target.value)}
              className="rounded-md border border-input bg-background px-2 py-1.5 text-sm text-foreground"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="text-muted-foreground">Base price (INR)</span>
            <input
              type="number"
              value={basePrice}
              onChange={(e) => setBasePrice(e.target.value)}
              min={1}
              className="w-32 rounded-md border border-input bg-background px-2 py-1.5 text-sm text-foreground"
            />
          </label>
          <Button onClick={() => mutation.mutate()} disabled={mutation.isPending}>
            {mutation.isPending ? "Calculating..." : "Get recommendation"}
          </Button>
        </div>

        {mutation.isError && (
          <p className="text-sm text-status-critical">
            {mutation.error instanceof Error ? mutation.error.message : "Could not calculate a recommendation."}
          </p>
        )}

        {result && (
          <div className="flex flex-col gap-3 rounded-lg bg-muted/40 p-4">
            <div className="flex flex-wrap items-baseline gap-3">
              <span className="text-sm text-muted-foreground">Recommended price</span>
              <span className="text-2xl font-semibold text-foreground">
                {currency.format(result.recommended_price)}
              </span>
              <span
                className="text-sm font-medium"
                style={{ color: result.price_change_percent >= 0 ? "var(--status-good)" : "var(--status-critical)" }}
              >
                {result.price_change_percent >= 0 ? "+" : ""}
                {result.price_change_percent.toFixed(1)}%
              </span>
              <span className="text-sm text-muted-foreground">vs base {currency.format(result.base_price)}</span>
            </div>
            <p className="text-sm font-medium text-foreground">Strategy: {result.strategy}</p>
            <ul className="list-disc pl-5 text-sm text-muted-foreground">
              {result.factors.map((f, i) => (
                <li key={i}>{f}</li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

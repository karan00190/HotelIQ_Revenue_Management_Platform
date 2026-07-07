"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { mlApi, type ForecastComparisonResult, type Hotel, type RevenueBacktestResult } from "@/lib/api";
import { HotelSelector } from "@/components/dashboard/HotelSelector";
import { ForecastComparisonChart } from "./ForecastComparisonChart";
import { ModelAccuracyTable } from "./ModelAccuracyTable";
import { RevenueBacktestSummary } from "./RevenueBacktestSummary";

export function BacktestPageClient({
  hotels,
  initialHotelId,
  initialComparison,
  initialBacktest,
}: {
  hotels: Hotel[];
  initialHotelId: number;
  initialComparison: ForecastComparisonResult;
  initialBacktest: RevenueBacktestResult;
}) {
  const [hotelId, setHotelId] = useState(initialHotelId);
  const isInitial = hotelId === initialHotelId;

  const comparisonQuery = useQuery({
    queryKey: ["mlCompare", hotelId],
    queryFn: () => mlApi.compare(hotelId),
    initialData: isInitial ? initialComparison : undefined,
  });

  const backtestQuery = useQuery({
    queryKey: ["mlBacktest", hotelId],
    queryFn: () => mlApi.backtest(hotelId),
    initialData: isInitial ? initialBacktest : undefined,
  });

  return (
    <div className="flex w-full flex-col gap-6 p-6 md:p-10">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">ML Challenger</h1>
          <p className="text-sm text-muted-foreground">
            XGBoost vs. Prophet forecast accuracy, and a revenue backtest replaying real bookings through the
            pricing engine
          </p>
        </div>
        <HotelSelector hotels={hotels} selectedHotelId={hotelId} onChange={setHotelId} />
      </div>

      {(comparisonQuery.isLoading || backtestQuery.isLoading) && (
        <p className="text-sm text-muted-foreground">
          Training both models and evaluating on the held-out window - this retrains fresh, so it can take a few
          seconds...
        </p>
      )}
      {comparisonQuery.isError && (
        <p className="text-sm text-status-critical">
          {comparisonQuery.error instanceof Error ? comparisonQuery.error.message : "Could not load model comparison."}
        </p>
      )}
      {backtestQuery.isError && (
        <p className="text-sm text-status-critical">
          {backtestQuery.error instanceof Error ? backtestQuery.error.message : "Could not load revenue backtest."}
        </p>
      )}

      {comparisonQuery.data && (
        <>
          <ForecastComparisonChart data={comparisonQuery.data.daily_comparison} />
          <ModelAccuracyTable models={comparisonQuery.data.models} />
        </>
      )}

      {backtestQuery.data && <RevenueBacktestSummary data={backtestQuery.data} />}
    </div>
  );
}

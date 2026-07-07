"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { forecastApi, type ForecastResult, type Hotel } from "@/lib/api";
import { HotelSelector } from "@/components/dashboard/HotelSelector";
import { ForecastCalendar } from "./ForecastCalendar";
import { ForecastChart } from "./ForecastChart";
import { HighDemandAlert } from "./HighDemandAlert";
import { PricingCalculator } from "./PricingCalculator";

export function ForecastPageClient({
  hotels,
  initialHotelId,
  initialForecast,
}: {
  hotels: Hotel[];
  initialHotelId: number;
  initialForecast: ForecastResult;
}) {
  const [hotelId, setHotelId] = useState(initialHotelId);
  const isInitial = hotelId === initialHotelId;

  const forecastQuery = useQuery({
    queryKey: ["forecast", hotelId],
    queryFn: () => forecastApi.predict(hotelId, { days_ahead: 30 }),
    initialData: isInitial ? initialForecast : undefined,
  });

  const predictions = forecastQuery.data?.predictions ?? [];
  // A date guaranteed to be inside the forecastable window - see the
  // comment in PricingCalculator for why this isn't computed from the
  // system clock.
  const defaultTargetDate = predictions[7]?.date ?? predictions[0]?.date ?? "";

  return (
    <div className="flex w-full flex-col gap-6 p-6 md:p-10">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Forecast</h1>
          <p className="text-sm text-muted-foreground">Demand prediction and pricing insights</p>
        </div>
        <HotelSelector hotels={hotels} selectedHotelId={hotelId} onChange={setHotelId} />
      </div>

      {forecastQuery.isLoading && (
        <p className="text-sm text-muted-foreground">Training forecasting model...</p>
      )}
      {forecastQuery.isError && (
        <p className="text-sm text-status-critical">
          {forecastQuery.error instanceof Error ? forecastQuery.error.message : "Could not load forecast."}
        </p>
      )}

      <ForecastChart predictions={predictions} />

      <div className="grid gap-4 lg:grid-cols-2">
        <ForecastCalendar predictions={predictions} />
        <HighDemandAlert predictions={predictions} />
      </div>

      {defaultTargetDate && (
        <PricingCalculator key={hotelId} hotelId={hotelId} defaultTargetDate={defaultTargetDate} />
      )}
    </div>
  );
}

"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import {
  analyticsApi,
  smartQueriesApi,
  type BookingSourceDistribution,
  type Hotel,
  type TrendPoint,
  type WeekendVsWeekday,
} from "@/lib/api";
import { HotelSelector } from "@/components/dashboard/HotelSelector";
import { RevenueTrendChart } from "@/components/dashboard/RevenueTrendChart";
import { computeRange, PRESETS, type PresetKey } from "@/lib/dateRangePresets";
import { AdrRevparTrendChart } from "./AdrRevparTrendChart";
import { BookingSourceBreakdown } from "./BookingSourceBreakdown";
import { OccupancyByWeekdayChart } from "./OccupancyByWeekdayChart";
import { WeekendVsWeekdayComparison } from "./WeekendVsWeekdayComparison";

export interface AnalyticsInitialData {
  trend: TrendPoint[];
  bookingSources: BookingSourceDistribution;
  weekendVsWeekday: WeekendVsWeekday;
}

const DEFAULT_PRESET: PresetKey = "30d";

export function AnalyticsPageClient({
  hotels,
  initialHotelId,
  initial,
}: {
  hotels: Hotel[];
  initialHotelId: number;
  initial: AnalyticsInitialData;
}) {
  const [hotelId, setHotelId] = useState(initialHotelId);
  const [preset, setPreset] = useState<PresetKey>(DEFAULT_PRESET);
  const { startDate, endDate } = computeRange(preset);
  const isInitial = hotelId === initialHotelId && preset === DEFAULT_PRESET;

  const trend = useQuery({
    queryKey: ["analyticsTrend", hotelId, startDate, endDate],
    queryFn: () => analyticsApi.trend(hotelId, { start_date: startDate, end_date: endDate }),
    initialData: isInitial ? initial.trend : undefined,
  });

  const bookingSources = useQuery({
    queryKey: ["bookingSources", hotelId, startDate, endDate],
    queryFn: () => smartQueriesApi.bookingSources({ hotel_id: hotelId, start_date: startDate, end_date: endDate }),
    initialData: isInitial ? initial.bookingSources : undefined,
  });

  const weekendVsWeekday = useQuery({
    queryKey: ["weekendVsWeekday", hotelId, startDate, endDate],
    queryFn: () => smartQueriesApi.weekendVsWeekday(hotelId, { start_date: startDate, end_date: endDate }),
    initialData: isInitial ? initial.weekendVsWeekday : undefined,
  });

  const presetLabel = PRESETS.find((p) => p.key === preset)?.label ?? "";

  return (
    <div className="flex w-full flex-col gap-6 p-6 md:p-10">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Analytics</h1>
          <p className="text-sm text-muted-foreground">Detailed performance breakdowns</p>
        </div>
        <HotelSelector hotels={hotels} selectedHotelId={hotelId} onChange={setHotelId} />
      </div>

      <div className="flex w-fit gap-1 rounded-lg bg-muted/40 p-1">
        {PRESETS.map((p) => (
          <button
            key={p.key}
            onClick={() => setPreset(p.key)}
            className={`rounded-md px-3 py-1.5 text-sm transition-colors ${
              preset === p.key
                ? "bg-card text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>

      <RevenueTrendChart
        data={trend.data ?? []}
        title={`Revenue over time (${presetLabel.toLowerCase()})`}
      />

      <div className="grid gap-4 lg:grid-cols-2">
        <OccupancyByWeekdayChart data={trend.data ?? []} />
        {bookingSources.data && <BookingSourceBreakdown data={bookingSources.data} />}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {weekendVsWeekday.data && <WeekendVsWeekdayComparison data={weekendVsWeekday.data} />}
        <AdrRevparTrendChart data={trend.data ?? []} />
      </div>
    </div>
  );
}

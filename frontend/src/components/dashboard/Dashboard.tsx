"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import {
  analyticsApi,
  bookingsApi,
  smartQueriesApi,
  type Booking,
  type CancellationAnalysis,
  type DailyStatistics,
  type Hotel,
  type RevenueMetrics,
  type TrendPoint,
} from "@/lib/api";
import { HotelSelector } from "./HotelSelector";
import { KpiCard } from "./KpiCard";
import { OccupancyHeatmap } from "./OccupancyHeatmap";
import { RecentBookingsTable } from "./RecentBookingsTable";
import { RevenueTrendChart } from "./RevenueTrendChart";

export interface DashboardInitialData {
  hotelId: number;
  daily: DailyStatistics;
  revenue: RevenueMetrics;
  trend30d: TrendPoint[];
  trendMonth: TrendPoint[];
  bookings: Booking[];
  cancellations: CancellationAnalysis;
}

const currency = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

function monthStartAndToday() {
  const now = new Date();
  const monthStart = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-01`;
  const today = new Date(now.getTime() - now.getTimezoneOffset() * 60_000).toISOString().slice(0, 10);
  return { monthStart, today, monthLabel: now.toLocaleDateString("en-IN", { month: "long", year: "numeric" }) };
}

export function Dashboard({ hotels, initial }: { hotels: Hotel[]; initial: DashboardInitialData }) {
  const [hotelId, setHotelId] = useState(initial.hotelId);
  const isInitial = hotelId === initial.hotelId;
  const { monthStart, today, monthLabel } = monthStartAndToday();

  const daily = useQuery({
    queryKey: ["daily", hotelId],
    queryFn: () => analyticsApi.daily(hotelId),
    initialData: isInitial ? initial.daily : undefined,
  });

  const revenue = useQuery({
    queryKey: ["revenue", hotelId],
    queryFn: () => analyticsApi.revenue({ hotel_id: hotelId }),
    initialData: isInitial ? initial.revenue : undefined,
  });

  const trend30d = useQuery({
    queryKey: ["trend30d", hotelId],
    queryFn: () => analyticsApi.trend(hotelId),
    initialData: isInitial ? initial.trend30d : undefined,
  });

  const trendMonth = useQuery({
    queryKey: ["trendMonth", hotelId, monthStart],
    queryFn: () => analyticsApi.trend(hotelId, { start_date: monthStart, end_date: today }),
    initialData: isInitial ? initial.trendMonth : undefined,
  });

  const recentBookings = useQuery({
    queryKey: ["recentBookings", hotelId],
    queryFn: () => bookingsApi.list({ hotel_id: hotelId, limit: 8 }),
    initialData: isInitial ? initial.bookings : undefined,
  });

  const cancellations = useQuery({
    queryKey: ["cancellations", hotelId],
    queryFn: () => smartQueriesApi.cancellations({ hotel_id: hotelId }),
    initialData: isInitial ? initial.cancellations : undefined,
  });

  const activeBookings = cancellations.data
    ? cancellations.data.total_bookings - cancellations.data.cancelled_bookings
    : undefined;

  return (
    <div className="flex w-full flex-col gap-6 p-6 md:p-10">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">HotelIQ Dashboard</h1>
          <p className="text-sm text-muted-foreground">Revenue management overview</p>
        </div>
        <HotelSelector hotels={hotels} selectedHotelId={hotelId} onChange={setHotelId} />
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <KpiCard
          label="Today's occupancy"
          value={daily.data ? `${daily.data.occupancy_rate.toFixed(1)}%` : "—"}
        />
        <KpiCard
          label="Last 30 days revenue"
          value={revenue.data ? currency.format(revenue.data.total_revenue) : "—"}
        />
        <KpiCard
          label="Today's ADR"
          value={daily.data ? currency.format(daily.data.average_daily_rate) : "—"}
        />
        <KpiCard
          label="Today's RevPAR"
          value={daily.data ? currency.format(daily.data.revenue_per_available_room) : "—"}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <KpiCard
          label="Active bookings"
          value={activeBookings !== undefined ? String(activeBookings) : "—"}
          hint="confirmed + completed"
        />
        <KpiCard
          label="Cancelled bookings"
          value={cancellations.data ? String(cancellations.data.cancelled_bookings) : "—"}
          hint={
            cancellations.data
              ? `${cancellations.data.cancellation_rate.toFixed(1)}% cancellation rate`
              : undefined
          }
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <RevenueTrendChart data={trend30d.data ?? []} />
        <OccupancyHeatmap data={trendMonth.data ?? []} monthLabel={monthLabel} />
      </div>

      <RecentBookingsTable bookings={recentBookings.data ?? []} />
    </div>
  );
}

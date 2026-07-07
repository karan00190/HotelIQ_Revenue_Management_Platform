import { AnalyticsPageClient } from "@/components/analytics/AnalyticsPageClient";
import { analyticsApi, hotelsApi, smartQueriesApi } from "@/lib/api";
import { computeRange } from "@/lib/dateRangePresets";

export default async function AnalyticsPage() {
  const hotels = await hotelsApi.list();

  if (hotels.length === 0) {
    return (
      <div className="flex min-h-screen items-center justify-center p-10 text-center text-muted-foreground">
        No hotels yet. Seed the database to see analytics.
      </div>
    );
  }

  const hotelId = hotels[0].id;
  const { startDate, endDate } = computeRange("30d");

  const [trend, bookingSources, weekendVsWeekday] = await Promise.all([
    analyticsApi.trend(hotelId, { start_date: startDate, end_date: endDate }),
    smartQueriesApi.bookingSources({ hotel_id: hotelId, start_date: startDate, end_date: endDate }),
    smartQueriesApi.weekendVsWeekday(hotelId, { start_date: startDate, end_date: endDate }),
  ]);

  return (
    <AnalyticsPageClient
      hotels={hotels}
      initialHotelId={hotelId}
      initial={{ trend, bookingSources, weekendVsWeekday }}
    />
  );
}

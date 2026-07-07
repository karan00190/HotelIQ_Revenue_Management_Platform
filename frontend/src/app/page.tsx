import { Dashboard } from "@/components/dashboard/Dashboard";
import { analyticsApi, bookingsApi, hotelsApi, smartQueriesApi } from "@/lib/api";

export default async function Home() {
  const hotels = await hotelsApi.list();

  if (hotels.length === 0) {
    return (
      <div className="flex min-h-screen items-center justify-center p-10 text-center text-muted-foreground">
        No hotels yet. Seed the database to see the dashboard.
      </div>
    );
  }

  const defaultHotelId = hotels[0].id;
  const now = new Date();
  const monthStart = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-01`;
  const today = now.toISOString().slice(0, 10);

  const [daily, revenue, trend30d, trendMonth, bookings, cancellations] = await Promise.all([
    analyticsApi.daily(defaultHotelId),
    analyticsApi.revenue({ hotel_id: defaultHotelId }),
    analyticsApi.trend(defaultHotelId),
    analyticsApi.trend(defaultHotelId, { start_date: monthStart, end_date: today }),
    bookingsApi.list({ hotel_id: defaultHotelId, limit: 8 }),
    smartQueriesApi.cancellations({ hotel_id: defaultHotelId }),
  ]);

  return (
    <Dashboard
      hotels={hotels}
      initial={{
        hotelId: defaultHotelId,
        daily,
        revenue,
        trend30d,
        trendMonth,
        bookings,
        cancellations,
      }}
    />
  );
}

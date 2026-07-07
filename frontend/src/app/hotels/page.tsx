import { HotelsPageClient } from "@/components/hotels/HotelsPageClient";
import { analyticsApi, hotelsApi, roomsApi, type RevenueMetrics } from "@/lib/api";

export default async function HotelsPage() {
  const hotels = await hotelsApi.list();

  if (hotels.length === 0) {
    return (
      <div className="flex min-h-screen items-center justify-center p-10 text-center text-muted-foreground">
        No hotels yet.
      </div>
    );
  }

  const revenueEntries = await Promise.all(
    hotels.map(async (hotel) => [hotel.id, await analyticsApi.revenue({ hotel_id: hotel.id })] as const),
  );
  const revenueByHotel: Record<number, RevenueMetrics> = Object.fromEntries(revenueEntries);

  const selectedHotelId = hotels[0].id;
  const rooms = await roomsApi.list({ hotel_id: selectedHotelId });

  return (
    <HotelsPageClient initial={{ hotels, revenueByHotel, selectedHotelId, rooms }} />
  );
}

import { BookingsPageClient } from "@/components/bookings/BookingsPageClient";
import { bookingsApi, hotelsApi } from "@/lib/api";

export default async function BookingsPage() {
  const hotels = await hotelsApi.list();

  if (hotels.length === 0) {
    return (
      <div className="flex min-h-screen items-center justify-center p-10 text-center text-muted-foreground">
        No hotels yet. Seed the database to see bookings.
      </div>
    );
  }

  const hotelId = hotels[0].id;
  const bookings = await bookingsApi.list({
    hotel_id: hotelId,
    sort_by: "check_in_date",
    sort_order: "desc",
    skip: 0,
    limit: 20,
  });

  return <BookingsPageClient hotels={hotels} initialHotelId={hotelId} initialBookings={bookings} />;
}

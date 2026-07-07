import { ForecastPageClient } from "@/components/forecast/ForecastPageClient";
import { forecastApi, hotelsApi } from "@/lib/api";

export default async function ForecastPage() {
  const hotels = await hotelsApi.list();

  if (hotels.length === 0) {
    return (
      <div className="flex min-h-screen items-center justify-center p-10 text-center text-muted-foreground">
        No hotels yet. Seed the database to see forecasts.
      </div>
    );
  }

  const hotelId = hotels[0].id;
  const forecast = await forecastApi.predict(hotelId, { days_ahead: 30 });

  return <ForecastPageClient hotels={hotels} initialHotelId={hotelId} initialForecast={forecast} />;
}

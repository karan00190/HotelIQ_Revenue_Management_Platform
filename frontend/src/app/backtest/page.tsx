import { BacktestPageClient } from "@/components/backtest/BacktestPageClient";
import { hotelsApi, mlApi } from "@/lib/api";

export default async function BacktestPage() {
  const hotels = await hotelsApi.list();

  if (hotels.length === 0) {
    return (
      <div className="flex min-h-screen items-center justify-center p-10 text-center text-muted-foreground">
        No hotels yet. Seed the database to see the ML challenger backtest.
      </div>
    );
  }

  const hotelId = hotels[0].id;
  const [comparison, backtest] = await Promise.all([mlApi.compare(hotelId), mlApi.backtest(hotelId)]);

  return (
    <BacktestPageClient
      hotels={hotels}
      initialHotelId={hotelId}
      initialComparison={comparison}
      initialBacktest={backtest}
    />
  );
}

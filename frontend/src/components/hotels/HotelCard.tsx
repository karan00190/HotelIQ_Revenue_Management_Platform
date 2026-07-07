import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Hotel, RevenueMetrics } from "@/lib/api";

const currency = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

interface HotelCardProps {
  hotel: Hotel;
  revenue?: RevenueMetrics;
  isSelected: boolean;
  onSelect: () => void;
}

export function HotelCard({ hotel, revenue, isSelected, onSelect }: HotelCardProps) {
  return (
    <Card
      onClick={onSelect}
      className={`cursor-pointer transition-all duration-200 ease-out hover:-translate-y-1 hover:shadow-lg ${
        isSelected ? "ring-2 ring-primary" : "hover:bg-muted/40"
      }`}
    >
      <CardHeader>
        <CardTitle>{hotel.name}</CardTitle>
        <p className="text-sm text-muted-foreground">{hotel.location}</p>
      </CardHeader>
      <CardContent className="flex flex-col gap-2 text-sm">
        <div className="flex justify-between">
          <span className="text-muted-foreground">Star rating</span>
          <span className="font-medium text-foreground">
            {hotel.star_rating.toFixed(1)} <span className="text-brand-gold">★</span>
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Total rooms</span>
          <span className="font-medium text-foreground">{hotel.total_rooms}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Revenue (30d)</span>
          <span className="font-medium text-foreground">
            {revenue ? currency.format(revenue.total_revenue) : "—"}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Occupancy (30d)</span>
          <span className="font-medium text-foreground">
            {revenue ? `${revenue.occupancy_rate.toFixed(1)}%` : "—"}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

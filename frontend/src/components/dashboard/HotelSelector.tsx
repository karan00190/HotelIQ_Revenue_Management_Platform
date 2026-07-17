"use client";

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { Hotel } from "@/lib/api";

interface HotelSelectorProps {
  hotels: Hotel[];
  selectedHotelId: number;
  onChange: (hotelId: number) => void;
}

export function HotelSelector({ hotels, selectedHotelId, onChange }: HotelSelectorProps) {
  return (
    <Select value={String(selectedHotelId)} onValueChange={(value) => onChange(Number(value))}>
      <SelectTrigger className="w-full sm:w-64">
        <SelectValue placeholder="Select a hotel" />
      </SelectTrigger>
      <SelectContent>
        {hotels.map((hotel) => (
          <SelectItem key={hotel.id} value={String(hotel.id)}>
            {hotel.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

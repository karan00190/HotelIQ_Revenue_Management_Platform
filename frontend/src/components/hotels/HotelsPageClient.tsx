"use client";

import { useState } from "react";
import { PlusIcon } from "lucide-react";
import { useQueries, useQuery } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { analyticsApi, hotelsApi, roomsApi, type Hotel, type RevenueMetrics, type Room } from "@/lib/api";
import { AddHotelDialog } from "./AddHotelDialog";
import { HotelCard } from "./HotelCard";
import { RoomsPanel } from "./RoomsPanel";

export interface HotelsInitialData {
  hotels: Hotel[];
  revenueByHotel: Record<number, RevenueMetrics>;
  selectedHotelId: number;
  rooms: Room[];
}

export function HotelsPageClient({ initial }: { initial: HotelsInitialData }) {
  const [selectedHotelId, setSelectedHotelId] = useState(initial.selectedHotelId);
  const [addHotelOpen, setAddHotelOpen] = useState(false);

  const hotelsQuery = useQuery({
    queryKey: ["hotels"],
    queryFn: () => hotelsApi.list(),
    initialData: initial.hotels,
  });
  const hotels = hotelsQuery.data;

  // One query per hotel (only ever a handful) for its own 30-day revenue -
  // useQueries is the documented pattern for a dynamic-length list of
  // independent queries, where a plain loop of useQuery calls would break
  // the rules of hooks.
  const revenueQueries = useQueries({
    queries: hotels.map((hotel) => ({
      queryKey: ["hotelRevenue", hotel.id],
      queryFn: () => analyticsApi.revenue({ hotel_id: hotel.id }),
      initialData: initial.revenueByHotel[hotel.id],
    })),
  });

  const roomsQuery = useQuery({
    queryKey: ["rooms", selectedHotelId],
    queryFn: () => roomsApi.list({ hotel_id: selectedHotelId }),
    initialData: selectedHotelId === initial.selectedHotelId ? initial.rooms : undefined,
  });

  const selectedHotel = hotels.find((h) => h.id === selectedHotelId) ?? null;

  return (
    <div className="flex w-full flex-col gap-6 p-6 md:p-10">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Hotels</h1>
          <p className="text-sm text-muted-foreground">Property and room inventory management</p>
        </div>
        <Button onClick={() => setAddHotelOpen(true)}>
          <PlusIcon />
          Add hotel
        </Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {hotels.map((hotel, i) => (
          <HotelCard
            key={hotel.id}
            hotel={hotel}
            revenue={revenueQueries[i]?.data}
            isSelected={hotel.id === selectedHotelId}
            onSelect={() => setSelectedHotelId(hotel.id)}
          />
        ))}
      </div>

      <RoomsPanel hotel={selectedHotel} rooms={roomsQuery.data ?? []} />

      <AddHotelDialog open={addHotelOpen} onOpenChange={setAddHotelOpen} />
    </div>
  );
}

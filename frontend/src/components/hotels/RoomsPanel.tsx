"use client";

import { useState } from "react";
import { PlusIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { Hotel, Room } from "@/lib/api";
import { AddRoomDialog } from "./AddRoomDialog";

const currency = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

export function RoomsPanel({ hotel, rooms }: { hotel: Hotel | null; rooms: Room[] }) {
  const [addRoomOpen, setAddRoomOpen] = useState(false);

  if (!hotel) return null;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Rooms — {hotel.name}</CardTitle>
        <Button size="sm" onClick={() => setAddRoomOpen(true)}>
          <PlusIcon />
          Add room
        </Button>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Room #</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Max occupancy</TableHead>
              <TableHead>Available</TableHead>
              <TableHead className="text-right">Base price</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rooms.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-muted-foreground">
                  No rooms yet for this hotel.
                </TableCell>
              </TableRow>
            )}
            {rooms.map((r) => (
              <TableRow key={r.id}>
                <TableCell>{r.room_number}</TableCell>
                <TableCell>{r.room_type}</TableCell>
                <TableCell>{r.max_occupancy}</TableCell>
                <TableCell>{r.is_available ? "Yes" : "No"}</TableCell>
                <TableCell className="text-right" style={{ fontVariantNumeric: "tabular-nums" }}>
                  {currency.format(r.base_price)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>

      <AddRoomDialog hotelId={hotel.id} open={addRoomOpen} onOpenChange={setAddRoomOpen} />
    </Card>
  );
}

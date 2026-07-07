"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { roomsApi } from "@/lib/api";

const ROOM_TYPES = ["Standard", "Deluxe", "Executive", "Suite"];

interface AddRoomDialogProps {
  hotelId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AddRoomDialog({ hotelId, open, onOpenChange }: AddRoomDialogProps) {
  const [roomNumber, setRoomNumber] = useState("");
  const [roomType, setRoomType] = useState("Standard");
  const [basePrice, setBasePrice] = useState("3000");
  const [maxOccupancy, setMaxOccupancy] = useState("2");
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () =>
      roomsApi.create({
        hotel_id: hotelId,
        room_number: roomNumber,
        room_type: roomType,
        base_price: Number(basePrice),
        max_occupancy: Number(maxOccupancy),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rooms", hotelId] });
      handleOpenChange(false);
    },
  });

  function resetForm() {
    setRoomNumber("");
    setRoomType("Standard");
    setBasePrice("3000");
    setMaxOccupancy("2");
    mutation.reset();
  }

  function handleOpenChange(next: boolean) {
    if (!next) resetForm();
    onOpenChange(next);
  }

  const isValid = roomNumber.trim().length > 0 && Number(basePrice) > 0 && Number(maxOccupancy) > 0;

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add a room</DialogTitle>
        </DialogHeader>

        <div className="flex flex-col gap-3">
          <label className="flex flex-col gap-1 text-sm">
            <span className="text-muted-foreground">Room number</span>
            <input
              value={roomNumber}
              onChange={(e) => setRoomNumber(e.target.value)}
              className="rounded-md border border-input bg-background px-2 py-1.5 text-sm text-foreground"
              placeholder="101"
            />
          </label>

          <label className="flex flex-col gap-1 text-sm">
            <span className="text-muted-foreground">Room type</span>
            <Select value={roomType} onValueChange={(v) => v && setRoomType(v)}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ROOM_TYPES.map((t) => (
                  <SelectItem key={t} value={t}>
                    {t}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </label>

          <div className="flex gap-3">
            <label className="flex flex-1 flex-col gap-1 text-sm">
              <span className="text-muted-foreground">Base price (INR)</span>
              <input
                type="number"
                min={1}
                value={basePrice}
                onChange={(e) => setBasePrice(e.target.value)}
                className="rounded-md border border-input bg-background px-2 py-1.5 text-sm text-foreground"
              />
            </label>
            <label className="flex flex-1 flex-col gap-1 text-sm">
              <span className="text-muted-foreground">Max occupancy</span>
              <input
                type="number"
                min={1}
                value={maxOccupancy}
                onChange={(e) => setMaxOccupancy(e.target.value)}
                className="rounded-md border border-input bg-background px-2 py-1.5 text-sm text-foreground"
              />
            </label>
          </div>
        </div>

        {mutation.isError && (
          <p className="text-sm text-status-critical">
            {mutation.error instanceof Error ? mutation.error.message : "Could not create room."}
          </p>
        )}

        <DialogFooter>
          <Button onClick={() => mutation.mutate()} disabled={!isValid || mutation.isPending}>
            {mutation.isPending ? "Creating..." : "Add room"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

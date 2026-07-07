"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { hotelsApi } from "@/lib/api";

interface AddHotelDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AddHotelDialog({ open, onOpenChange }: AddHotelDialogProps) {
  const [name, setName] = useState("");
  const [location, setLocation] = useState("");
  const [totalRooms, setTotalRooms] = useState("50");
  const [starRating, setStarRating] = useState("4");
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () =>
      hotelsApi.create({
        name,
        location,
        total_rooms: Number(totalRooms),
        star_rating: Number(starRating),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hotels"] });
      handleOpenChange(false);
    },
  });

  function resetForm() {
    setName("");
    setLocation("");
    setTotalRooms("50");
    setStarRating("4");
    mutation.reset();
  }

  function handleOpenChange(next: boolean) {
    if (!next) resetForm();
    onOpenChange(next);
  }

  const isValid =
    name.trim().length > 0 &&
    location.trim().length > 0 &&
    Number(totalRooms) > 0 &&
    Number(starRating) >= 1 &&
    Number(starRating) <= 5;

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add a new hotel</DialogTitle>
        </DialogHeader>

        <div className="flex flex-col gap-3">
          <label className="flex flex-col gap-1 text-sm">
            <span className="text-muted-foreground">Name</span>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="rounded-md border border-input bg-background px-2 py-1.5 text-sm text-foreground"
              placeholder="Grand Plaza Mumbai"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="text-muted-foreground">Location</span>
            <input
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="rounded-md border border-input bg-background px-2 py-1.5 text-sm text-foreground"
              placeholder="Mumbai, MH"
            />
          </label>
          <div className="flex gap-3">
            <label className="flex flex-1 flex-col gap-1 text-sm">
              <span className="text-muted-foreground">Total rooms</span>
              <input
                type="number"
                min={1}
                value={totalRooms}
                onChange={(e) => setTotalRooms(e.target.value)}
                className="rounded-md border border-input bg-background px-2 py-1.5 text-sm text-foreground"
              />
            </label>
            <label className="flex flex-1 flex-col gap-1 text-sm">
              <span className="text-muted-foreground">Star rating (1-5)</span>
              <input
                type="number"
                min={1}
                max={5}
                step={0.5}
                value={starRating}
                onChange={(e) => setStarRating(e.target.value)}
                className="rounded-md border border-input bg-background px-2 py-1.5 text-sm text-foreground"
              />
            </label>
          </div>
        </div>

        {mutation.isError && (
          <p className="text-sm text-status-critical">
            {mutation.error instanceof Error ? mutation.error.message : "Could not create hotel."}
          </p>
        )}

        <DialogFooter>
          <Button onClick={() => mutation.mutate()} disabled={!isValid || mutation.isPending}>
            {mutation.isPending ? "Creating..." : "Create hotel"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

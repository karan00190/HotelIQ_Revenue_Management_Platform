"use client";

import type { ReactNode } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { StatusDot } from "@/components/shared/StatusDot";
import { bookingsApi, type Booking } from "@/lib/api";
import { formatDateShort } from "@/lib/date";

const currency = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

function Field({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex justify-between gap-4 py-1.5 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-right font-medium text-foreground">{value}</span>
    </div>
  );
}

interface BookingDetailsDialogProps {
  booking: Booking | null;
  onOpenChange: (open: boolean) => void;
}

export function BookingDetailsDialog({ booking, onOpenChange }: BookingDetailsDialogProps) {
  const queryClient = useQueryClient();

  const cancelMutation = useMutation({
    mutationFn: (id: number) => bookingsApi.cancel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
      onOpenChange(false);
    },
  });

  if (!booking) return null;

  const nights = Math.round(
    (new Date(booking.check_out_date).getTime() - new Date(booking.check_in_date).getTime()) / 86_400_000,
  );
  const discountPct =
    booking.base_price > 0 ? ((booking.base_price - booking.booking_price) / booking.base_price) * 100 : 0;

  return (
    <Dialog open={!!booking} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Booking #{booking.id}</DialogTitle>
        </DialogHeader>

        <div className="flex flex-col divide-y divide-border">
          <Field label="Guest" value={booking.guest_name} />
          <Field label="Email" value={booking.guest_email ?? "—"} />
          <Field label="Guests" value={booking.num_guests} />
          <Field label="Check-in" value={formatDateShort(booking.check_in_date.slice(0, 10))} />
          <Field label="Check-out" value={formatDateShort(booking.check_out_date.slice(0, 10))} />
          <Field label="Nights" value={nights} />
          <Field label="Source" value={<span className="capitalize">{booking.booking_source}</span>} />
          <Field label="Status" value={<StatusDot status={booking.status} />} />
          <Field label="Base price" value={currency.format(booking.base_price)} />
          <Field label="Booking price" value={currency.format(booking.booking_price)} />
          <Field
            label={discountPct >= 0 ? "Discount" : "Premium"}
            value={`${Math.abs(discountPct).toFixed(1)}%`}
          />
          <Field label="Booked on" value={formatDateShort(booking.booking_date.slice(0, 10))} />
        </div>

        {cancelMutation.isError && (
          <p className="text-sm text-status-critical">
            {cancelMutation.error instanceof Error ? cancelMutation.error.message : "Failed to cancel booking."}
          </p>
        )}

        <DialogFooter>
          {booking.status === "confirmed" && (
            <Button
              variant="destructive"
              onClick={() => cancelMutation.mutate(booking.id)}
              disabled={cancelMutation.isPending}
            >
              {cancelMutation.isPending ? "Cancelling..." : "Cancel booking"}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

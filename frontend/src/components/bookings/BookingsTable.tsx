"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { StatusDot } from "@/components/shared/StatusDot";
import type { Booking } from "@/lib/api";
import { formatDateShort } from "@/lib/date";

const currency = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

interface BookingsTableProps {
  bookings: Booking[];
  isLoading: boolean;
  onRowClick: (booking: Booking) => void;
  page: number;
  onPageChange: (page: number) => void;
  hasNextPage: boolean;
}

export function BookingsTable({
  bookings,
  isLoading,
  onRowClick,
  page,
  onPageChange,
  hasNextPage,
}: BookingsTableProps) {
  return (
    <Card>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Guest</TableHead>
              <TableHead>Check-in</TableHead>
              <TableHead>Check-out</TableHead>
              <TableHead>Source</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Price</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {!isLoading && bookings.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-muted-foreground">
                  No bookings match these filters.
                </TableCell>
              </TableRow>
            )}
            {bookings.map((b) => (
              <TableRow key={b.id} onClick={() => onRowClick(b)} className="cursor-pointer">
                <TableCell>{b.guest_name}</TableCell>
                <TableCell>{formatDateShort(b.check_in_date.slice(0, 10))}</TableCell>
                <TableCell>{formatDateShort(b.check_out_date.slice(0, 10))}</TableCell>
                <TableCell className="capitalize">{b.booking_source}</TableCell>
                <TableCell>
                  <StatusDot status={b.status} />
                </TableCell>
                <TableCell className="text-right" style={{ fontVariantNumeric: "tabular-nums" }}>
                  {currency.format(b.booking_price)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        <div className="mt-4 flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Page {page + 1}</span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled={page === 0} onClick={() => onPageChange(page - 1)}>
              Previous
            </Button>
            <Button variant="outline" size="sm" disabled={!hasNextPage} onClick={() => onPageChange(page + 1)}>
              Next
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

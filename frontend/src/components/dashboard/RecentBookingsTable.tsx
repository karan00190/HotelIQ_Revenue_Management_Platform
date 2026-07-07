import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { StatusDot } from "@/components/shared/StatusDot";
import type { Booking } from "@/lib/api";
import { formatDateShort } from "@/lib/date";

const currency = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

export function RecentBookingsTable({ bookings }: { bookings: Booking[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent bookings</CardTitle>
      </CardHeader>
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
            {bookings.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-muted-foreground">
                  No bookings yet.
                </TableCell>
              </TableRow>
            )}
            {bookings.map((b) => (
              <TableRow key={b.id}>
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
      </CardContent>
    </Card>
  );
}

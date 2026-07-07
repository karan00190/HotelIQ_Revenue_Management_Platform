"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { bookingsApi, type Booking, type Hotel } from "@/lib/api";
import { BookingsFilterBar, type BookingsSortBy, type DateRangeFilter } from "./BookingsFilterBar";
import { BookingsTable } from "./BookingsTable";
import { BookingDetailsDialog } from "./BookingDetailsDialog";
import { CsvUploadDialog } from "./CsvUploadDialog";

const PAGE_SIZE = 20;

function dateRangeToDates(range: DateRangeFilter): { start_date?: string; end_date?: string } {
  if (range === "all") return {};
  const days = range === "7d" ? 7 : range === "30d" ? 30 : 90;
  const now = new Date();
  const start = new Date(now);
  start.setDate(start.getDate() - days);
  const pad = (n: number) => String(n).padStart(2, "0");
  const toIso = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  return { start_date: toIso(start), end_date: toIso(now) };
}

export function BookingsPageClient({
  hotels,
  initialHotelId,
  initialBookings,
}: {
  hotels: Hotel[];
  initialHotelId: number;
  initialBookings: Booking[];
}) {
  const [hotelId, setHotelId] = useState(initialHotelId);
  const [status, setStatus] = useState("all");
  const [dateRange, setDateRange] = useState<DateRangeFilter>("all");
  const [sortBy, setSortBy] = useState<BookingsSortBy>("check_in_date");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(0);
  const [selectedBooking, setSelectedBooking] = useState<Booking | null>(null);
  const [uploadOpen, setUploadOpen] = useState(false);

  const isInitial =
    hotelId === initialHotelId &&
    status === "all" &&
    dateRange === "all" &&
    sortBy === "check_in_date" &&
    sortOrder === "desc" &&
    page === 0;

  const { start_date, end_date } = dateRangeToDates(dateRange);

  const bookingsQuery = useQuery({
    queryKey: ["bookings", hotelId, status, dateRange, sortBy, sortOrder, page],
    queryFn: () =>
      bookingsApi.list({
        hotel_id: hotelId,
        status_filter: status === "all" ? undefined : status,
        start_date,
        end_date,
        sort_by: sortBy,
        sort_order: sortOrder,
        skip: page * PAGE_SIZE,
        limit: PAGE_SIZE,
      }),
    initialData: isInitial ? initialBookings : undefined,
  });

  const bookings = bookingsQuery.data ?? [];

  function resetToFirstPage() {
    setPage(0);
  }

  return (
    <div className="flex w-full flex-col gap-6 p-6 md:p-10">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Bookings</h1>
        <p className="text-sm text-muted-foreground">Search, filter, and manage reservations</p>
      </div>

      <BookingsFilterBar
        hotels={hotels}
        hotelId={hotelId}
        onHotelChange={(id) => {
          setHotelId(id);
          resetToFirstPage();
        }}
        status={status}
        onStatusChange={(s) => {
          setStatus(s);
          resetToFirstPage();
        }}
        dateRange={dateRange}
        onDateRangeChange={(r) => {
          setDateRange(r);
          resetToFirstPage();
        }}
        sortBy={sortBy}
        sortOrder={sortOrder}
        onSortByChange={(s) => {
          setSortBy(s);
          resetToFirstPage();
        }}
        onToggleSortOrder={() => setSortOrder((o) => (o === "asc" ? "desc" : "asc"))}
        onUploadClick={() => setUploadOpen(true)}
      />

      <BookingsTable
        bookings={bookings}
        isLoading={bookingsQuery.isLoading}
        onRowClick={setSelectedBooking}
        page={page}
        onPageChange={setPage}
        hasNextPage={bookings.length === PAGE_SIZE}
      />

      <BookingDetailsDialog
        booking={selectedBooking}
        onOpenChange={(open) => !open && setSelectedBooking(null)}
      />
      <CsvUploadDialog open={uploadOpen} onOpenChange={setUploadOpen} />
    </div>
  );
}

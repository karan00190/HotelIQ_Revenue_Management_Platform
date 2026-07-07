"use client";

import { ArrowDownIcon, ArrowUpIcon, UploadIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { HotelSelector } from "@/components/dashboard/HotelSelector";
import type { Hotel } from "@/lib/api";

export type BookingsSortBy = "check_in_date" | "booking_price" | "guest_name";
export type DateRangeFilter = "all" | "7d" | "30d" | "90d";

const STATUS_OPTIONS = [
  { value: "all", label: "All statuses" },
  { value: "confirmed", label: "Confirmed" },
  { value: "completed", label: "Completed" },
  { value: "cancelled", label: "Cancelled" },
];

const DATE_OPTIONS: { value: DateRangeFilter; label: string }[] = [
  { value: "all", label: "All time" },
  { value: "7d", label: "Last 7 days" },
  { value: "30d", label: "Last 30 days" },
  { value: "90d", label: "Last 90 days" },
];

const SORT_OPTIONS: { value: BookingsSortBy; label: string }[] = [
  { value: "check_in_date", label: "Check-in date" },
  { value: "booking_price", label: "Price" },
  { value: "guest_name", label: "Guest name" },
];

interface BookingsFilterBarProps {
  hotels: Hotel[];
  hotelId: number;
  onHotelChange: (id: number) => void;
  status: string;
  onStatusChange: (status: string) => void;
  dateRange: DateRangeFilter;
  onDateRangeChange: (range: DateRangeFilter) => void;
  sortBy: BookingsSortBy;
  sortOrder: "asc" | "desc";
  onSortByChange: (sortBy: BookingsSortBy) => void;
  onToggleSortOrder: () => void;
  onUploadClick: () => void;
}

export function BookingsFilterBar({
  hotels,
  hotelId,
  onHotelChange,
  status,
  onStatusChange,
  dateRange,
  onDateRangeChange,
  sortBy,
  sortOrder,
  onSortByChange,
  onToggleSortOrder,
  onUploadClick,
}: BookingsFilterBarProps) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <HotelSelector hotels={hotels} selectedHotelId={hotelId} onChange={onHotelChange} />

      <Select value={status} onValueChange={(v) => v && onStatusChange(v)}>
        <SelectTrigger className="w-40">
          <SelectValue placeholder="Status" />
        </SelectTrigger>
        <SelectContent>
          {STATUS_OPTIONS.map((opt) => (
            <SelectItem key={opt.value} value={opt.value}>
              {opt.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select value={dateRange} onValueChange={(v) => onDateRangeChange(v as DateRangeFilter)}>
        <SelectTrigger className="w-40">
          <SelectValue placeholder="Date range" />
        </SelectTrigger>
        <SelectContent>
          {DATE_OPTIONS.map((opt) => (
            <SelectItem key={opt.value} value={opt.value}>
              {opt.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select value={sortBy} onValueChange={(v) => onSortByChange(v as BookingsSortBy)}>
        <SelectTrigger className="w-40">
          <SelectValue placeholder="Sort by" />
        </SelectTrigger>
        <SelectContent>
          {SORT_OPTIONS.map((opt) => (
            <SelectItem key={opt.value} value={opt.value}>
              {opt.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Button variant="outline" size="icon" onClick={onToggleSortOrder} title="Toggle sort order">
        {sortOrder === "asc" ? <ArrowUpIcon /> : <ArrowDownIcon />}
      </Button>

      <div className="flex-1" />

      <Button onClick={onUploadClick}>
        <UploadIcon />
        Upload CSV
      </Button>
    </div>
  );
}

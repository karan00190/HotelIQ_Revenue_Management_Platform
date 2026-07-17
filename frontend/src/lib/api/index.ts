import { apiClient } from "./client";
import type {
  AnalyticsSummary,
  AssistantChatMessage,
  AssistantChatResult,
  AssistantStatus,
  Booking,
  BookingSourceDistribution,
  CancellationAnalysis,
  DailyStatistics,
  ForecastComparisonResult,
  ForecastResult,
  Hotel,
  OccupancyStats,
  PopularRoomTypes,
  PricingRecommendation,
  RevenueBacktestResult,
  RevenueMetrics,
  Room,
  TopBooking,
  TotalRevenueResult,
  TrainResult,
  TrendPoint,
  UploadResult,
  WeekendVsWeekday,
} from "./types";

export * from "./types";
export { ApiError } from "./client";

export const hotelsApi = {
  list: (params?: { skip?: number; limit?: number }) => apiClient.get<Hotel[]>("/hotels/", params),
  get: (id: number) => apiClient.get<Hotel>(`/hotels/${id}`),
  create: (data: { name: string; location: string; total_rooms: number; star_rating: number }) =>
    apiClient.post<Hotel>("/hotels/", data),
  remove: (id: number) => apiClient.delete<void>(`/hotels/${id}`),
};

export const roomsApi = {
  list: (params?: { hotel_id?: number }) => apiClient.get<Room[]>("/rooms/", params),
  get: (id: number) => apiClient.get<Room>(`/rooms/${id}`),
  create: (data: {
    hotel_id: number;
    room_number: string;
    room_type: string;
    base_price: number;
    max_occupancy: number;
    is_available?: boolean;
  }) => apiClient.post<Room>("/rooms/", data),
};

export const bookingsApi = {
  list: (params?: {
    hotel_id?: number;
    status_filter?: string;
    start_date?: string;
    end_date?: string;
    sort_by?: "check_in_date" | "booking_price" | "guest_name";
    sort_order?: "asc" | "desc";
    skip?: number;
    limit?: number;
  }) => apiClient.get<Booking[]>("/bookings/", params),
  get: (id: number) => apiClient.get<Booking>(`/bookings/${id}`),
  cancel: (id: number) => apiClient.patch<Booking>(`/bookings/${id}/cancel`),
};

export const analyticsApi = {
  revenue: (params?: { hotel_id?: number; start_date?: string; end_date?: string }) =>
    apiClient.get<RevenueMetrics>("/analytics/revenue", params),
  daily: (hotelId: number, targetDate?: string) =>
    apiClient.get<DailyStatistics>(`/analytics/daily/${hotelId}`, { target_date: targetDate }),
  summary: () => apiClient.get<AnalyticsSummary>("/analytics/summary"),
  trend: (hotelId: number, params?: { start_date?: string; end_date?: string }) =>
    apiClient.get<TrendPoint[]>(`/analytics/trend/${hotelId}`, params),
};

export const smartQueriesApi = {
  totalRevenue: (params?: { hotel_id?: number; start_date?: string; end_date?: string }) =>
    apiClient.get<TotalRevenueResult>("/smart-queries/total-revenue", params),
  occupancyStats: (hotelId: number, params?: { start_date?: string; end_date?: string }) =>
    apiClient.get<OccupancyStats>(`/smart-queries/occupancy-stats/${hotelId}`, params),
  topBookings: (params?: { hotel_id?: number; sort_by?: "price" | "recent"; limit?: number }) =>
    apiClient.get<TopBooking[]>("/smart-queries/top-bookings", params),
  bookingSources: (params?: { hotel_id?: number; start_date?: string; end_date?: string }) =>
    apiClient.get<BookingSourceDistribution>("/smart-queries/booking-sources", params),
  weekendVsWeekday: (hotelId: number, params?: { start_date?: string; end_date?: string }) =>
    apiClient.get<WeekendVsWeekday>(`/smart-queries/weekend-vs-weekday/${hotelId}`, params),
  cancellations: (params?: { hotel_id?: number; start_date?: string; end_date?: string }) =>
    apiClient.get<CancellationAnalysis>("/smart-queries/cancellations", params),
  popularRooms: (hotelId: number, limit?: number) =>
    apiClient.get<PopularRoomTypes>(`/smart-queries/popular-rooms/${hotelId}`, { limit }),
};

export const forecastApi = {
  train: (hotelId: number, daysBack?: number) =>
    apiClient.post<TrainResult>(`/forecast/train/${hotelId}`, undefined, { days_back: daysBack }),
  predict: (hotelId: number, params?: { days_ahead?: number; days_back?: number }) =>
    apiClient.get<ForecastResult>(`/forecast/predict/${hotelId}`, params),
  pricingRecommendation: (hotelId: number, targetDate: string, basePrice: number) =>
    apiClient.get<PricingRecommendation>(`/forecast/pricing-recommendation/${hotelId}`, {
      target_date: targetDate,
      base_price: basePrice,
    }),
};

export const mlApi = {
  predict: (hotelId: number, params?: { days_ahead?: number }) =>
    apiClient.get<ForecastResult>(`/ml/predict/${hotelId}`, params),
  compare: (hotelId: number) => apiClient.get<ForecastComparisonResult>(`/ml/compare/${hotelId}`),
  backtest: (hotelId: number) => apiClient.get<RevenueBacktestResult>(`/ml/backtest/${hotelId}`),
};

export const assistantApi = {
  status: () => apiClient.get<AssistantStatus>("/assistant/status"),
  chat: (message: string, history: AssistantChatMessage[]) =>
    apiClient.post<AssistantChatResult>("/assistant/chat", { message, history }),
};

export const ingestionApi = {
  uploadCsv: async (file: File): Promise<UploadResult> => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000"}/ingestion/upload-csv`,
      { method: "POST", body: form },
    );
    if (!res.ok) {
      const body = await res.json().catch(() => undefined);
      throw new Error(body?.detail ?? `Upload failed with status ${res.status}`);
    }
    return res.json();
  },
};

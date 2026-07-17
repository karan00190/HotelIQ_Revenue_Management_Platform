// Mirrors the Pydantic/dict response shapes from the FastAPI backend
// (backend/app/models/schemas.py and the various service return dicts).

export interface Hotel {
  id: number;
  name: string;
  location: string;
  total_rooms: number;
  star_rating: number;
  created_at: string;
}

export interface Room {
  id: number;
  hotel_id: number;
  room_number: string;
  room_type: string;
  base_price: number;
  max_occupancy: number;
  is_available: boolean;
}

export interface Booking {
  id: number;
  hotel_id: number;
  room_id: number;
  check_in_date: string;
  check_out_date: string;
  guest_name: string;
  guest_email: string | null;
  num_guests: number;
  booking_price: number;
  base_price: number;
  booking_date: string;
  booking_source: string;
  status: "confirmed" | "cancelled" | "completed";
}

export interface DailyMetrics {
  id: number;
  hotel_id: number;
  date: string;
  occupancy_rate: number;
  rooms_occupied: number;
  rooms_available: number;
  total_revenue: number;
  average_daily_rate: number;
  revenue_per_available_room: number;
  booking_count: number;
  cancellation_count: number;
  calculated_at: string;
}

// ---------- Analytics ----------

export interface RevenueMetrics {
  hotel_id: number | null;
  start_date: string;
  end_date: string;
  total_revenue: number;
  total_bookings: number;
  total_room_nights: number;
  average_daily_rate: number;
  occupancy_rate: number;
}

export interface DailyStatistics {
  hotel_id: number;
  date: string;
  rooms_occupied: number;
  rooms_available: number;
  occupancy_rate: number;
  total_revenue: number;
  average_daily_rate: number;
  revenue_per_available_room: number;
}

export interface TrendPoint {
  date: string;
  total_revenue: number;
  occupancy_rate: number;
  average_daily_rate: number;
  revenue_per_available_room: number;
}

export interface AnalyticsSummary {
  total_hotels: number;
  total_rooms: number;
  total_bookings: number;
  active_confirmed_bookings: number;
  current_month_revenue: number;
  current_month_occupancy_rate: number;
}

// ---------- Smart Queries ----------

export interface TotalRevenueResult {
  hotel_id: number | null;
  start_date: string | null;
  end_date: string | null;
  total_revenue: number;
  total_bookings: number;
}

export interface OccupancyStats {
  hotel_id: number;
  start_date: string | null;
  end_date: string | null;
  days_with_data: number;
  average_occupancy_rate: number;
  max_occupancy_rate: number;
  min_occupancy_rate: number;
  message?: string;
}

export interface TopBooking {
  id: number;
  hotel_id: number;
  room_id: number;
  guest_name: string;
  check_in_date: string;
  check_out_date: string;
  booking_price: number;
  booking_source: string;
}

export interface BookingSourceBreakdown {
  booking_source: string;
  booking_count: number;
  total_revenue: number;
  percent_of_bookings: number;
}

export interface BookingSourceDistribution {
  hotel_id: number | null;
  total_bookings: number;
  sources: BookingSourceBreakdown[];
}

export interface WeekdayStats {
  count: number;
  total_revenue: number;
  average_price: number;
}

export interface WeekendVsWeekday {
  hotel_id: number;
  start_date: string | null;
  end_date: string | null;
  weekend: WeekdayStats;
  weekday: WeekdayStats;
  weekend_premium_percent: number;
}

export interface CancellationAnalysis {
  hotel_id: number | null;
  total_bookings: number;
  cancelled_bookings: number;
  cancellation_rate: number;
  lost_revenue: number;
}

export interface PopularRoomType {
  room_type: string;
  booking_count: number;
  average_price: number;
}

export interface PopularRoomTypes {
  hotel_id: number;
  room_types: PopularRoomType[];
}

// ---------- Ingestion ----------

export interface DataQualityReport {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  info: string[];
  stats: Record<string, unknown>;
}

export interface FeatureSummary {
  total_features_created: number;
  total_columns: number;
  features_by_category: Record<string, number>;
  feature_names: Record<string, string[]>;
  sample_rows?: Record<string, unknown>[];
}

export interface UploadResult {
  success: boolean;
  duration_seconds: number;
  source: string;
  records_extracted: number;
  validation: DataQualityReport;
  load: { loaded: number; skipped: number; errors: number; error_messages: string[] } | null;
  feature_summary: FeatureSummary | null;
  filename?: string;
  saved_as?: string;
}

// ---------- Forecasting ----------

export interface TrainResult {
  hotel_id: number;
  status: string;
  training_days: number;
  date_range: { start: string; end: string };
  occupancy_stats: { mean: number; min: number; max: number };
}

export interface ForecastPrediction {
  date: string;
  predicted_occupancy: number;
  lower_bound: number;
  upper_bound: number;
}

export interface ForecastResult {
  hotel_id: number;
  summary: {
    mean_occupancy: number;
    min_occupancy: number;
    max_occupancy: number;
    median_occupancy: number;
    days_forecasted: number;
  };
  predictions: ForecastPrediction[];
}

export interface PricingRecommendation {
  hotel_id: number;
  target_date: string;
  base_price: number;
  recommended_price: number;
  price_multiplier: number;
  price_change_percent: number;
  strategy: string;
  factors: string[];
  inputs: {
    predicted_occupancy: number;
    current_occupancy: number;
    is_weekend: boolean;
    is_peak_season: boolean;
    lead_time_days: number;
  };
}

// ---------- ML Challenger ----------

export interface ModelMetrics {
  mae: number;
  rmse: number;
  description?: string;
}

export interface DailyComparisonPoint {
  date: string;
  actual: number;
  naive: number;
  prophet: number;
  xgboost: number;
}

export interface ForecastComparisonResult {
  hotel_id: number;
  train_days: number;
  test_days: number;
  test_date_range: { start: string; end: string };
  models: {
    naive: ModelMetrics;
    prophet: ModelMetrics;
    xgboost: ModelMetrics;
  };
  daily_comparison: DailyComparisonPoint[];
}

export interface BootstrapDelta {
  point_estimate: number;
  p5: number;
  p95: number;
}

export interface PerBookingDetail {
  booking_id: number;
  check_in_date: string;
  base_price: number;
  actual_price: number;
  simulated_price_prophet: number;
  simulated_price_ml: number;
}

export interface RevenueBacktestResult {
  hotel_id: number;
  test_date_range: { start: string; end: string };
  booking_count: number;
  actual_revenue: number;
  simulated_revenue_prophet: number;
  simulated_revenue_ml: number;
  deltas: {
    ml_vs_prophet: BootstrapDelta;
    ml_vs_actual: BootstrapDelta;
    prophet_vs_actual: BootstrapDelta;
  };
  assumptions: string[];
  per_booking_detail: PerBookingDetail[];
}

// ---------- Assistant ----------

export interface AssistantChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface AssistantToolCall {
  tool: string;
  args: Record<string, unknown>;
  ok: boolean;
  summary: unknown;
}

export interface AssistantChatResult {
  reply: string;
  tool_calls: AssistantToolCall[];
  model: string;
  elapsed_ms: number;
}

export interface AssistantStatus {
  configured: boolean;
  model: string;
  knowledge_available: boolean;
  knowledge_chunks: number;
}

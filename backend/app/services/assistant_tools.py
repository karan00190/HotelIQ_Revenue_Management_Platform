"""The assistant's tools: thin, read-only wrappers around the SAME service
functions the dashboard and REST API already use (QueryBuilder, analytics_service,
MLDemandForecaster, DynamicPricingEngine, knowledge_service). This is the whole
anti-hallucination design in one file - the agent never answers a data question
from its own recall, only by calling one of these and relaying what comes back.

build_tools(db) is a factory, not a module of standalone functions, because
each tool needs to close over the current request's SQLAlchemy session - the
same session cannot be shared across requests, so a fresh set of tool closures
is built per chat request. Every tool catches its own exceptions and returns
{"error": ...} rather than raising, so a bad hotel_id or a malformed date from
the LLM becomes a plain, relayable message instead of a crashed request.

The two forecasting/pricing tools deliberately use the XGBoost challenger
(MLDemandForecaster), never Prophet - Prophet's 30-60s+ training time per call
is a timeout risk inside a chat turn. See app/knowledge/forecasting-methodology.md.
"""

from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.hotel import DailyMetrics, Hotel
from app.services import analytics_service, knowledge_service
from app.services.ml_forecasting_service import MLDemandForecaster
from app.services.pricing_engine import PEAK_MONTHS, DynamicPricingEngine
from app.services.query_builder import QueryBuilder

MAX_LIST_LIMIT = 5
MAX_FORECAST_DAYS = 30
MAX_PRICING_DAYS_AHEAD = 90


def _parse_date(value: Optional[str], field_name: str) -> Optional[date]:
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{field_name} must be an ISO date string (YYYY-MM-DD), got: {value!r}")


def build_tools(db: Session) -> list:
    """Build a fresh list of LangChain tools closing over this request's db session."""
    from langchain_core.tools import tool

    qb = QueryBuilder(db)

    @tool
    def list_hotels() -> dict:
        """List every hotel in the system with its numeric id, name, location,
        total_rooms, and star_rating. Call this first whenever the user refers
        to a hotel by name, to resolve the name to the hotel_id every other
        tool requires."""
        try:
            hotels = db.query(Hotel).all()
            return {
                "hotels": [
                    {
                        "hotel_id": h.id,
                        "name": h.name,
                        "location": h.location,
                        "total_rooms": h.total_rooms,
                        "star_rating": h.star_rating,
                    }
                    for h in hotels
                ]
            }
        except Exception as exc:
            return {"error": str(exc)}

    @tool
    def get_total_revenue(
        hotel_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        """Total revenue and booking count for a hotel (or all hotels if
        hotel_id is omitted) over a date range, filtered to check-in date.
        start_date/end_date are inclusive ISO dates (YYYY-MM-DD); omit either
        to leave that bound open."""
        try:
            start = _parse_date(start_date, "start_date")
            end = _parse_date(end_date, "end_date")
            return qb.get_total_revenue(hotel_id=hotel_id, start_date=start, end_date=end)
        except Exception as exc:
            return {"error": str(exc)}

    @tool
    def get_occupancy_stats(
        hotel_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        """Average/max/min daily occupancy rate for one hotel over a date
        range, from pre-calculated daily metrics. start_date/end_date are
        inclusive ISO dates (YYYY-MM-DD); omit either to leave that bound
        open."""
        try:
            start = _parse_date(start_date, "start_date")
            end = _parse_date(end_date, "end_date")
            result = qb.get_occupancy_stats(hotel_id=hotel_id, start_date=start, end_date=end)
            if result is None:
                return {"error": f"Hotel {hotel_id} not found"}
            return result
        except Exception as exc:
            return {"error": str(exc)}

    @tool
    def get_top_bookings(
        hotel_id: Optional[int] = None,
        sort_by: str = "price",
        limit: int = 5,
    ) -> dict:
        """The highest-priced or most recent bookings for a hotel (or all
        hotels if hotel_id is omitted). sort_by is "price" (default, highest
        first) or "recent" (most recent check-in first). limit is capped at 5
        to keep the response small."""
        try:
            capped_limit = max(1, min(limit, MAX_LIST_LIMIT))
            bookings = qb.get_top_bookings(hotel_id=hotel_id, sort_by=sort_by, limit=capped_limit)
            return {"bookings": bookings}
        except Exception as exc:
            return {"error": str(exc)}

    @tool
    def get_booking_source_distribution(
        hotel_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        """Booking count, revenue, and share of bookings per booking source
        (e.g. direct, OTA channels) for a hotel (or all hotels if hotel_id is
        omitted). start_date/end_date are inclusive ISO dates (YYYY-MM-DD);
        omit either to leave that bound open."""
        try:
            start = _parse_date(start_date, "start_date")
            end = _parse_date(end_date, "end_date")
            return qb.get_booking_source_distribution(hotel_id=hotel_id, start_date=start, end_date=end)
        except Exception as exc:
            return {"error": str(exc)}

    @tool
    def get_weekend_vs_weekday_comparison(
        hotel_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        """Compares weekend (Friday/Saturday check-in) vs weekday booking
        count, revenue, and average price for one hotel. start_date/end_date
        are inclusive ISO dates (YYYY-MM-DD); omit either to leave that bound
        open."""
        try:
            start = _parse_date(start_date, "start_date")
            end = _parse_date(end_date, "end_date")
            result = qb.get_weekend_vs_weekday_comparison(hotel_id=hotel_id, start_date=start, end_date=end)
            if result is None:
                return {"error": f"Hotel {hotel_id} not found"}
            return result
        except Exception as exc:
            return {"error": str(exc)}

    @tool
    def get_cancellation_analysis(
        hotel_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        """Cancellation rate and revenue lost to cancellations for a hotel (or
        all hotels if hotel_id is omitted). start_date/end_date are inclusive
        ISO dates (YYYY-MM-DD); omit either to leave that bound open."""
        try:
            start = _parse_date(start_date, "start_date")
            end = _parse_date(end_date, "end_date")
            return qb.get_cancellation_analysis(hotel_id=hotel_id, start_date=start, end_date=end)
        except Exception as exc:
            return {"error": str(exc)}

    @tool
    def get_popular_room_types(hotel_id: int, limit: int = 5) -> dict:
        """The most-booked room types at one hotel and their average price.
        limit is capped at 5 to keep the response small."""
        try:
            capped_limit = max(1, min(limit, MAX_LIST_LIMIT))
            result = qb.get_popular_room_types(hotel_id=hotel_id, limit=capped_limit)
            if result is None:
                return {"error": f"Hotel {hotel_id} not found"}
            return result
        except Exception as exc:
            return {"error": str(exc)}

    @tool
    def get_daily_snapshot(hotel_id: int, target_date: Optional[str] = None) -> dict:
        """A live snapshot of one hotel on one specific day: rooms occupied,
        rooms available, occupancy rate, revenue, ADR, and RevPAR.
        target_date is an ISO date (YYYY-MM-DD); omit it to use today."""
        try:
            parsed = _parse_date(target_date, "target_date")
            result = analytics_service.get_daily_statistics(db, hotel_id=hotel_id, target_date=parsed)
            if result is None:
                return {"error": f"Hotel {hotel_id} not found"}
            return result
        except Exception as exc:
            return {"error": str(exc)}

    @tool
    def get_revenue_kpis(
        hotel_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        """Aggregate revenue KPIs (total revenue, bookings, room nights, ADR,
        occupancy rate) for a hotel (or all hotels if hotel_id is omitted)
        over a date range. start_date/end_date are inclusive ISO dates
        (YYYY-MM-DD); if both are omitted, defaults to the last 30 days."""
        try:
            start = _parse_date(start_date, "start_date")
            end = _parse_date(end_date, "end_date")
            return analytics_service.calculate_revenue_metrics(db, hotel_id=hotel_id, start_date=start, end_date=end)
        except Exception as exc:
            return {"error": str(exc)}

    @tool
    def forecast_occupancy(hotel_id: int, days_ahead: int = 14) -> dict:
        """Forecasts daily occupancy rate for one hotel for the next
        days_ahead days (capped at 30), using the XGBoost demand model.
        Returns a summary (mean/min/max/median occupancy) plus the first 7
        days of daily predictions."""
        try:
            capped_days = max(1, min(days_ahead, MAX_FORECAST_DAYS))
            hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
            if not hotel:
                return {"error": f"Hotel {hotel_id} not found"}

            forecaster = MLDemandForecaster(db)
            full_df = forecaster.build_feature_frame()
            forecaster.train(full_df)
            forecast_df = forecaster.forecast_future(hotel_id, days_ahead=capped_days)
            summary = forecaster.get_forecast_summary(forecast_df)

            truncated = summary["predictions"][:7]
            return {
                "hotel_id": hotel_id,
                "forecast_engine": "xgboost_pooled",
                "summary": summary["summary"],
                "predictions": truncated,
                "note": (
                    f"Showing the first {len(truncated)} of {len(summary['predictions'])} "
                    "forecasted days. Use the summary for the full period."
                    if len(summary["predictions"]) > len(truncated)
                    else None
                ),
            }
        except Exception as exc:
            return {"error": str(exc)}

    @tool
    def get_pricing_recommendation(hotel_id: int, target_date: str, base_price: float) -> dict:
        """Recommends a price for one hotel on one future check-in date,
        given a base_price. Forecasts occupancy with the XGBoost model, then
        runs the same rule-based pricing engine used by the rest of the app
        (weekend/peak-season/lead-time/occupancy factors). target_date is an
        ISO date (YYYY-MM-DD) and must be after the last date with data."""
        try:
            if base_price <= 0:
                return {"error": "base_price must be positive"}
            target = _parse_date(target_date, "target_date")

            hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
            if not hotel:
                return {"error": f"Hotel {hotel_id} not found"}

            last_metric_dt = (
                db.query(DailyMetrics.date)
                .filter(DailyMetrics.hotel_id == hotel_id)
                .order_by(DailyMetrics.date.desc())
                .first()
            )
            if last_metric_dt is None:
                return {"error": f"No daily metrics found for hotel {hotel_id}"}
            last_metric_date = last_metric_dt[0].date()

            days_ahead = (target - last_metric_date).days
            if days_ahead <= 0:
                return {"error": f"target_date must be after {last_metric_date.isoformat()} (the last date with data)"}
            if days_ahead > MAX_PRICING_DAYS_AHEAD:
                return {
                    "error": (
                        f"target_date is too far ahead (max {MAX_PRICING_DAYS_AHEAD} days "
                        f"past {last_metric_date.isoformat()})"
                    )
                }

            forecaster = MLDemandForecaster(db)
            full_df = forecaster.build_feature_frame()
            forecaster.train(full_df)
            forecast_df = forecaster.forecast_future(hotel_id, days_ahead=days_ahead)

            target_row = forecast_df[forecast_df["ds"].dt.date == target]
            if target_row.empty:
                return {"error": "Forecast did not include target_date"}
            predicted_occupancy = float(target_row.iloc[0]["yhat"])

            is_weekend = target.weekday() in (4, 5)
            is_peak_season = target.month in PEAK_MONTHS
            lead_time_days = (target - date.today()).days

            latest_metric = (
                db.query(DailyMetrics)
                .filter(DailyMetrics.hotel_id == hotel_id)
                .order_by(DailyMetrics.date.desc())
                .first()
            )
            current_occupancy = latest_metric.occupancy_rate if latest_metric else 0.0

            engine = DynamicPricingEngine()
            recommendation = engine.get_pricing_recommendation(
                base_price=base_price,
                predicted_occupancy=predicted_occupancy,
                current_occupancy=current_occupancy,
                is_weekend=is_weekend,
                is_peak_season=is_peak_season,
                lead_time_days=lead_time_days,
            )
            recommendation["hotel_id"] = hotel_id
            recommendation["target_date"] = target.isoformat()
            recommendation["forecast_engine"] = "xgboost_pooled"
            return recommendation
        except Exception as exc:
            return {"error": str(exc)}

    @tool
    def search_knowledge(query: str) -> dict:
        """Searches HotelIQ's knowledge base for explanations of how the
        platform works, what a metric means, or methodology questions - e.g.
        "what is RevPAR", "how does the pricing engine decide on a price",
        "why doesn't this system predict price elasticity". Do NOT use this
        for real numbers like revenue, occupancy, or forecasts - use the data
        tools for those."""
        try:
            hits = knowledge_service.search(query, k=4)
            return {
                "results": [
                    {"source": h["source"], "heading": h["heading"], "text": h["text"]}
                    for h in hits
                ]
            }
        except Exception as exc:
            return {"error": str(exc)}

    return [
        list_hotels,
        get_total_revenue,
        get_occupancy_stats,
        get_top_bookings,
        get_booking_source_distribution,
        get_weekend_vs_weekday_comparison,
        get_cancellation_analysis,
        get_popular_room_types,
        get_daily_snapshot,
        get_revenue_kpis,
        forecast_occupancy,
        get_pricing_recommendation,
        search_knowledge,
    ]

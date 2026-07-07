"""Pre-built analytical queries answering the questions hotel managers ask
most often, without needing SQL access or a paid LLM.

Status-filter rule used throughout: a cancelled booking never earned revenue
and never occupied a room, so every "how am I performing" query excludes it
via ACTIVE_STATUSES (reused from analytics_service). The one deliberate
exception is get_cancellation_analysis, which needs ALL bookings — it is the
query whose entire job is to measure cancellations.
"""

from datetime import date
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.hotel import Booking, DailyMetrics, Hotel, Room
from app.services.analytics_service import ACTIVE_STATUSES


class QueryBuilder:
    def __init__(self, db: Session):
        self.db = db

    def get_total_revenue(
        self,
        hotel_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        query = self.db.query(
            func.sum(Booking.booking_price),
            func.count(Booking.id),
        ).filter(Booking.status.in_(ACTIVE_STATUSES))
        if hotel_id is not None:
            query = query.filter(Booking.hotel_id == hotel_id)
        if start_date is not None:
            query = query.filter(func.date(Booking.check_in_date) >= start_date.isoformat())
        if end_date is not None:
            query = query.filter(func.date(Booking.check_in_date) <= end_date.isoformat())

        total_revenue, total_bookings = query.one()
        return {
            "hotel_id": hotel_id,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "total_revenue": round(total_revenue or 0.0, 2),
            "total_bookings": total_bookings or 0,
        }

    def get_occupancy_stats(
        self,
        hotel_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Optional[dict]:
        hotel = self.db.query(Hotel).filter(Hotel.id == hotel_id).first()
        if not hotel:
            return None

        query = self.db.query(
            func.avg(DailyMetrics.occupancy_rate),
            func.max(DailyMetrics.occupancy_rate),
            func.min(DailyMetrics.occupancy_rate),
            func.count(DailyMetrics.id),
        ).filter(DailyMetrics.hotel_id == hotel_id)
        if start_date is not None:
            query = query.filter(func.date(DailyMetrics.date) >= start_date.isoformat())
        if end_date is not None:
            query = query.filter(func.date(DailyMetrics.date) <= end_date.isoformat())

        avg_occ, max_occ, min_occ, days_with_data = query.one()
        result = {
            "hotel_id": hotel_id,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "days_with_data": days_with_data or 0,
            "average_occupancy_rate": round(avg_occ, 2) if avg_occ is not None else 0.0,
            "max_occupancy_rate": round(max_occ, 2) if max_occ is not None else 0.0,
            "min_occupancy_rate": round(min_occ, 2) if min_occ is not None else 0.0,
        }
        # daily_metrics is only populated by /ingestion/calculate-metrics; a hotel
        # that exists but was never processed would otherwise look identical to a
        # genuinely zero-occupancy hotel, so make the distinction explicit.
        if not days_with_data:
            result["message"] = (
                "No daily metrics found for this hotel/date range. "
                "Run POST /ingestion/calculate-metrics first."
            )
        return result

    def get_top_bookings(
        self,
        hotel_id: Optional[int] = None,
        sort_by: str = "price",
        limit: int = 10,
    ) -> list[dict]:
        query = self.db.query(Booking).filter(Booking.status.in_(ACTIVE_STATUSES))
        if hotel_id is not None:
            query = query.filter(Booking.hotel_id == hotel_id)

        if sort_by == "recent":
            query = query.order_by(Booking.check_in_date.desc())
        else:
            query = query.order_by(Booking.booking_price.desc())

        bookings = query.limit(limit).all()
        return [
            {
                "id": b.id,
                "hotel_id": b.hotel_id,
                "room_id": b.room_id,
                "guest_name": b.guest_name,
                "check_in_date": b.check_in_date.isoformat(),
                "check_out_date": b.check_out_date.isoformat(),
                "booking_price": b.booking_price,
                "booking_source": b.booking_source,
            }
            for b in bookings
        ]

    def get_booking_source_distribution(
        self,
        hotel_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        query = self.db.query(
            Booking.booking_source,
            func.count(Booking.id),
            func.sum(Booking.booking_price),
        ).filter(Booking.status.in_(ACTIVE_STATUSES))
        if hotel_id is not None:
            query = query.filter(Booking.hotel_id == hotel_id)
        if start_date is not None:
            query = query.filter(func.date(Booking.check_in_date) >= start_date.isoformat())
        if end_date is not None:
            query = query.filter(func.date(Booking.check_in_date) <= end_date.isoformat())

        rows = query.group_by(Booking.booking_source).all()
        total_bookings = sum(count for _, count, _ in rows)

        sources = []
        for source, count, revenue in rows:
            pct = (count / total_bookings * 100) if total_bookings > 0 else 0.0
            sources.append({
                "booking_source": source,
                "booking_count": count,
                "total_revenue": round(revenue or 0.0, 2),
                "percent_of_bookings": round(pct, 2),
            })
        sources.sort(key=lambda s: s["booking_count"], reverse=True)

        return {"hotel_id": hotel_id, "total_bookings": total_bookings, "sources": sources}

    def get_weekend_vs_weekday_comparison(
        self,
        hotel_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Optional[dict]:
        hotel = self.db.query(Hotel).filter(Hotel.id == hotel_id).first()
        if not hotel:
            return None

        query = self.db.query(Booking).filter(
            Booking.hotel_id == hotel_id, Booking.status.in_(ACTIVE_STATUSES)
        )
        if start_date is not None:
            query = query.filter(func.date(Booking.check_in_date) >= start_date.isoformat())
        if end_date is not None:
            query = query.filter(func.date(Booking.check_in_date) <= end_date.isoformat())
        bookings = query.all()

        # Friday(4)/Saturday(5) check-ins = "weekend", same convention used by
        # the feature engineering and data generator modules.
        groups: dict[str, list[float]] = {"weekend": [], "weekday": []}
        for b in bookings:
            key = "weekend" if b.check_in_date.weekday() in (4, 5) else "weekday"
            groups[key].append(b.booking_price)

        def summarize(prices: list[float]) -> dict:
            count = len(prices)
            total = sum(prices)
            average = (total / count) if count > 0 else 0.0
            return {"count": count, "total_revenue": round(total, 2), "average_price": round(average, 2)}

        weekend = summarize(groups["weekend"])
        weekday = summarize(groups["weekday"])
        weekend_premium_percent = (
            (weekend["average_price"] - weekday["average_price"]) / weekday["average_price"] * 100
            if weekday["average_price"] > 0
            else 0.0
        )

        return {
            "hotel_id": hotel_id,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "weekend": weekend,
            "weekday": weekday,
            "weekend_premium_percent": round(weekend_premium_percent, 2),
        }

    def get_cancellation_analysis(
        self,
        hotel_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        # Deliberately no ACTIVE_STATUSES filter: this query's entire purpose
        # is to measure cancellations against the full population of bookings.
        base = self.db.query(Booking)
        if hotel_id is not None:
            base = base.filter(Booking.hotel_id == hotel_id)
        if start_date is not None:
            base = base.filter(func.date(Booking.check_in_date) >= start_date.isoformat())
        if end_date is not None:
            base = base.filter(func.date(Booking.check_in_date) <= end_date.isoformat())

        total_bookings = base.count()
        cancelled_count, lost_revenue = (
            base.filter(Booking.status == "cancelled")
            .with_entities(func.count(Booking.id), func.sum(Booking.booking_price))
            .one()
        )
        cancelled_count = cancelled_count or 0
        lost_revenue = lost_revenue or 0.0
        cancellation_rate = (cancelled_count / total_bookings * 100) if total_bookings > 0 else 0.0

        return {
            "hotel_id": hotel_id,
            "total_bookings": total_bookings,
            "cancelled_bookings": cancelled_count,
            "cancellation_rate": round(cancellation_rate, 2),
            "lost_revenue": round(lost_revenue, 2),
        }

    def get_popular_room_types(self, hotel_id: int, limit: int = 5) -> Optional[dict]:
        hotel = self.db.query(Hotel).filter(Hotel.id == hotel_id).first()
        if not hotel:
            return None

        rows = (
            self.db.query(
                Room.room_type,
                func.count(Booking.id),
                func.avg(Booking.booking_price),
            )
            .join(Booking, Booking.room_id == Room.id)
            .filter(Room.hotel_id == hotel_id, Booking.status.in_(ACTIVE_STATUSES))
            .group_by(Room.room_type)
            .order_by(func.count(Booking.id).desc())
            .limit(limit)
            .all()
        )

        return {
            "hotel_id": hotel_id,
            "room_types": [
                {
                    "room_type": room_type,
                    "booking_count": count,
                    "average_price": round(avg_price or 0.0, 2),
                }
                for room_type, count, avg_price in rows
            ],
        }

    def get_available_queries(self) -> dict:
        return {
            "queries": [
                {
                    "name": "total-revenue",
                    "endpoint": "/smart-queries/total-revenue",
                    "description": "Total revenue and booking count for a period.",
                    "parameters": ["hotel_id (optional)", "start_date (optional)", "end_date (optional)"],
                },
                {
                    "name": "occupancy-stats",
                    "endpoint": "/smart-queries/occupancy-stats/{hotel_id}",
                    "description": "Average/max/min occupancy rate from pre-calculated daily metrics.",
                    "parameters": ["hotel_id (required, path)", "start_date (optional)", "end_date (optional)"],
                },
                {
                    "name": "top-bookings",
                    "endpoint": "/smart-queries/top-bookings",
                    "description": "Highest-priced or most recent bookings.",
                    "parameters": ["hotel_id (optional)", "sort_by: price|recent (default price)", "limit (default 10)"],
                },
                {
                    "name": "booking-sources",
                    "endpoint": "/smart-queries/booking-sources",
                    "description": "Booking count, revenue, and share of bookings per channel.",
                    "parameters": ["hotel_id (optional)", "start_date (optional)", "end_date (optional)"],
                },
                {
                    "name": "weekend-vs-weekday",
                    "endpoint": "/smart-queries/weekend-vs-weekday/{hotel_id}",
                    "description": "Compares weekend vs weekday booking count, revenue, and average price.",
                    "parameters": ["hotel_id (required, path)"],
                },
                {
                    "name": "cancellations",
                    "endpoint": "/smart-queries/cancellations",
                    "description": "Cancellation rate and revenue lost to cancellations.",
                    "parameters": ["hotel_id (optional)", "start_date (optional)", "end_date (optional)"],
                },
                {
                    "name": "popular-rooms",
                    "endpoint": "/smart-queries/popular-rooms/{hotel_id}",
                    "description": "Most-booked room types and their average price.",
                    "parameters": ["hotel_id (required, path)", "limit (default 5)"],
                },
            ]
        }

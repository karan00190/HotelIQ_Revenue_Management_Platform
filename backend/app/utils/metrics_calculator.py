"""Pre-aggregation: compute daily KPIs once and persist them to daily_metrics.

This is what makes dashboard reads fast — instead of recalculating from raw
bookings on every request, this module writes the computed values into a row
that future reads simply select. calculate_daily_metrics is upsert-shaped:
update the existing row for a hotel+date if present, otherwise create one.
"""

from datetime import date, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.hotel import Booking, DailyMetrics, Hotel

ACTIVE_STATUSES = ("confirmed", "completed")


def calculate_daily_metrics(db: Session, hotel_id: int, target_date: date) -> DailyMetrics:
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise ValueError(f"Hotel {hotel_id} does not exist")

    target_str = target_date.isoformat()

    overlapping = (
        db.query(Booking)
        .filter(
            Booking.hotel_id == hotel_id,
            Booking.status.in_(ACTIVE_STATUSES),
            func.date(Booking.check_in_date) <= target_str,
            func.date(Booking.check_out_date) > target_str,
        )
        .all()
    )

    rooms_occupied = len(overlapping)
    rooms_available = hotel.total_rooms
    # Same per-night revenue allocation as analytics_service.get_daily_statistics
    # — a multi-night booking contributes only its nightly share to this date.
    total_revenue = sum(
        b.booking_price / max((b.check_out_date - b.check_in_date).days, 1)
        for b in overlapping
    )
    occupancy_rate = (rooms_occupied / rooms_available * 100) if rooms_available > 0 else 0.0
    average_daily_rate = (total_revenue / rooms_occupied) if rooms_occupied > 0 else 0.0
    revpar = (total_revenue / rooms_available) if rooms_available > 0 else 0.0

    # booking_count/cancellation_count track NEW bookings starting that day,
    # a different question from occupancy (which counts overlapping stays).
    checkins_today = (
        db.query(Booking)
        .filter(Booking.hotel_id == hotel_id, func.date(Booking.check_in_date) == target_str)
        .all()
    )
    booking_count = len(checkins_today)
    cancellation_count = sum(1 for b in checkins_today if b.status == "cancelled")

    existing = (
        db.query(DailyMetrics)
        .filter(DailyMetrics.hotel_id == hotel_id, func.date(DailyMetrics.date) == target_str)
        .first()
    )
    metric = existing if existing else DailyMetrics(hotel_id=hotel_id, date=target_date)

    metric.occupancy_rate = round(occupancy_rate, 2)
    metric.rooms_occupied = rooms_occupied
    metric.rooms_available = rooms_available
    metric.total_revenue = round(total_revenue, 2)
    metric.average_daily_rate = round(average_daily_rate, 2)
    metric.revenue_per_available_room = round(revpar, 2)
    metric.booking_count = booking_count
    metric.cancellation_count = cancellation_count
    metric.calculated_at = datetime.utcnow()

    if not existing:
        db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


def calculate_date_range_metrics(
    db: Session, hotel_id: int, start_date: date, end_date: date
) -> list[DailyMetrics]:
    results = []
    current = start_date
    while current <= end_date:
        results.append(calculate_daily_metrics(db, hotel_id, current))
        current += timedelta(days=1)
    return results


def recalculate_all_metrics(db: Session) -> dict:
    """Recompute daily_metrics for every hotel across the full booking history."""
    earliest = db.query(func.min(Booking.check_in_date)).scalar()
    latest = db.query(func.max(Booking.check_out_date)).scalar()
    if earliest is None or latest is None:
        return {"hotels_processed": 0, "days_processed": 0, "metrics_calculated": 0}

    start = earliest.date()
    end = latest.date()

    hotels = db.query(Hotel).all()
    total = 0
    for hotel in hotels:
        metrics = calculate_date_range_metrics(db, hotel.id, start, end)
        total += len(metrics)

    return {
        "hotels_processed": len(hotels),
        "date_range": {"start": start.isoformat(), "end": end.isoformat()},
        "metrics_calculated": total,
    }

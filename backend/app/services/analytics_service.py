"""Revenue management KPI calculations, read directly from raw bookings.

Two entry points, both read-only (never write to the database):
- calculate_revenue_metrics: aggregate KPIs over a period (ADR, occupancy, ...)
- get_daily_statistics: a live snapshot for one hotel on one specific date

Neither of these persists anything. The metrics_calculator module (Module 8's
other half, in app/utils/) reuses the same overlap logic but writes the
result into the daily_metrics table for fast repeated reads.
"""

from datetime import date, timedelta
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.hotel import Booking, Hotel

# A cancelled booking never occupied a room and never earned revenue, so it is
# excluded from every KPI calculation in this module.
ACTIVE_STATUSES = ("confirmed", "completed")


def calculate_revenue_metrics(
    db: Session,
    hotel_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> dict:
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=30)

    query = db.query(Booking).filter(
        Booking.status.in_(ACTIVE_STATUSES),
        func.date(Booking.check_in_date) >= start_date.isoformat(),
        func.date(Booking.check_in_date) <= end_date.isoformat(),
    )
    if hotel_id is not None:
        query = query.filter(Booking.hotel_id == hotel_id)
    bookings = query.all()

    total_revenue = sum(b.booking_price for b in bookings)
    total_room_nights = sum((b.check_out_date - b.check_in_date).days for b in bookings)
    total_bookings = len(bookings)

    average_daily_rate = (total_revenue / total_room_nights) if total_room_nights > 0 else 0.0

    if hotel_id is not None:
        hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
        total_rooms = hotel.total_rooms if hotel else 0
    else:
        total_rooms = db.query(func.sum(Hotel.total_rooms)).scalar() or 0

    days_in_period = (end_date - start_date).days + 1
    available_room_nights = total_rooms * days_in_period
    occupancy_rate = (
        (total_room_nights / available_room_nights * 100) if available_room_nights > 0 else 0.0
    )

    return {
        "hotel_id": hotel_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_revenue": round(total_revenue, 2),
        "total_bookings": total_bookings,
        "total_room_nights": total_room_nights,
        "average_daily_rate": round(average_daily_rate, 2),
        "occupancy_rate": round(occupancy_rate, 2),
    }


def get_daily_statistics(db: Session, hotel_id: int, target_date: Optional[date] = None) -> Optional[dict]:
    if target_date is None:
        target_date = date.today()
    target_str = target_date.isoformat()

    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        return None

    # A stay "occupies" target_date if it checked in on or before it and
    # checks out after it (checkout day itself is not an occupied night).
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

    # A multi-night booking's total price is spread evenly across its nights
    # so a 5-night stay doesn't count its full price on every night it spans.
    total_revenue = sum(
        b.booking_price / max((b.check_out_date - b.check_in_date).days, 1)
        for b in overlapping
    )

    occupancy_rate = (rooms_occupied / rooms_available * 100) if rooms_available > 0 else 0.0
    average_daily_rate = (total_revenue / rooms_occupied) if rooms_occupied > 0 else 0.0
    revenue_per_available_room = (total_revenue / rooms_available) if rooms_available > 0 else 0.0

    return {
        "hotel_id": hotel_id,
        "date": target_str,
        "rooms_occupied": rooms_occupied,
        "rooms_available": rooms_available,
        "occupancy_rate": round(occupancy_rate, 2),
        "total_revenue": round(total_revenue, 2),
        "average_daily_rate": round(average_daily_rate, 2),
        "revenue_per_available_room": round(revenue_per_available_room, 2),
    }

from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.query_builder import QueryBuilder

router = APIRouter(prefix="/smart-queries", tags=["Smart Queries"])


@router.get("/available")
def available_queries(db: Session = Depends(get_db)):
    """Lists every pre-built query this API can answer, with parameter docs."""
    return QueryBuilder(db).get_available_queries()


@router.get("/total-revenue")
def total_revenue(
    hotel_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """Total revenue and booking count for confirmed/completed bookings."""
    return QueryBuilder(db).get_total_revenue(hotel_id=hotel_id, start_date=start_date, end_date=end_date)


@router.get("/occupancy-stats/{hotel_id}")
def occupancy_stats(
    hotel_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """Average/max/min occupancy for one hotel, from pre-computed daily_metrics."""
    stats = QueryBuilder(db).get_occupancy_stats(hotel_id=hotel_id, start_date=start_date, end_date=end_date)
    if stats is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hotel not found")
    return stats


@router.get("/top-bookings")
def top_bookings(
    hotel_id: Optional[int] = None,
    sort_by: Literal["price", "recent"] = "price",
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Highest-priced (sort_by=price) or most recent (sort_by=recent) bookings."""
    return QueryBuilder(db).get_top_bookings(hotel_id=hotel_id, sort_by=sort_by, limit=limit)


@router.get("/booking-sources")
def booking_sources(
    hotel_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """Booking count, revenue, and share of total per booking_source channel."""
    return QueryBuilder(db).get_booking_source_distribution(
        hotel_id=hotel_id, start_date=start_date, end_date=end_date
    )


@router.get("/weekend-vs-weekday/{hotel_id}")
def weekend_vs_weekday(
    hotel_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """Friday/Saturday check-ins vs the rest of the week: count, revenue, avg price, premium %."""
    result = QueryBuilder(db).get_weekend_vs_weekday_comparison(
        hotel_id=hotel_id, start_date=start_date, end_date=end_date
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hotel not found")
    return result


@router.get("/cancellations")
def cancellations(
    hotel_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """Cancellation rate and total lost revenue, across ALL booking statuses."""
    return QueryBuilder(db).get_cancellation_analysis(hotel_id=hotel_id, start_date=start_date, end_date=end_date)


@router.get("/popular-rooms/{hotel_id}")
def popular_rooms(hotel_id: int, limit: int = 5, db: Session = Depends(get_db)):
    """Most-booked room types for one hotel, with average booking price."""
    result = QueryBuilder(db).get_popular_room_types(hotel_id=hotel_id, limit=limit)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hotel not found")
    return result

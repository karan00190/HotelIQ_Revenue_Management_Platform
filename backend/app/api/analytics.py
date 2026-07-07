from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.hotel import Booking, DailyMetrics, Hotel
from app.services.analytics_service import calculate_revenue_metrics, get_daily_statistics

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/revenue")
def revenue(
    hotel_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """Revenue KPIs for a period. Defaults to the last 30 days if no dates given."""
    return calculate_revenue_metrics(db, hotel_id=hotel_id, start_date=start_date, end_date=end_date)


@router.get("/daily/{hotel_id}")
def daily(hotel_id: int, target_date: Optional[date] = None, db: Session = Depends(get_db)):
    """Live KPI snapshot for one hotel on one date. Defaults to today."""
    stats = get_daily_statistics(db, hotel_id=hotel_id, target_date=target_date)
    if stats is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hotel not found")
    return stats


@router.get("/trend/{hotel_id}")
def trend(
    hotel_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """Date-ordered daily_metrics rows for one hotel — the series a chart needs.

    Every other analytics endpoint returns a single aggregate or a single day;
    dashboard charts (revenue trend, occupancy heatmap) need a day-by-day list,
    which is exactly what the daily_metrics pre-aggregation table holds. Reads
    straight from it rather than recomputing anything.
    """
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hotel not found")

    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=30)

    rows = (
        db.query(DailyMetrics)
        .filter(
            DailyMetrics.hotel_id == hotel_id,
            func.date(DailyMetrics.date) >= start_date.isoformat(),
            func.date(DailyMetrics.date) <= end_date.isoformat(),
        )
        .order_by(DailyMetrics.date.asc())
        .all()
    )

    return [
        {
            "date": r.date.date().isoformat(),
            "total_revenue": r.total_revenue,
            "occupancy_rate": r.occupancy_rate,
            "average_daily_rate": r.average_daily_rate,
            "revenue_per_available_room": r.revenue_per_available_room,
        }
        for r in rows
    ]


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    """System-wide snapshot across all hotels."""
    total_hotels = db.query(Hotel).count()
    total_rooms = db.query(func.sum(Hotel.total_rooms)).scalar() or 0
    total_bookings = db.query(Booking).count()
    active_confirmed_bookings = db.query(Booking).filter(Booking.status == "confirmed").count()

    today = date.today()
    month_start = today.replace(day=1)
    month_metrics = calculate_revenue_metrics(db, hotel_id=None, start_date=month_start, end_date=today)

    return {
        "total_hotels": total_hotels,
        "total_rooms": total_rooms,
        "total_bookings": total_bookings,
        "active_confirmed_bookings": active_confirmed_bookings,
        "current_month_revenue": month_metrics["total_revenue"],
        "current_month_occupancy_rate": month_metrics["occupancy_rate"],
    }

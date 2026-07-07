from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.hotel import Booking, Hotel, Room
from app.models.schemas import BookingCreate, BookingResponse

router = APIRouter(prefix="/bookings", tags=["Bookings"])

SORTABLE_COLUMNS = {
    "check_in_date": Booking.check_in_date,
    "booking_price": Booking.booking_price,
    "guest_name": Booking.guest_name,
}


@router.get("/", response_model=list[BookingResponse])
def list_bookings(
    hotel_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    sort_by: Literal["check_in_date", "booking_price", "guest_name"] = "check_in_date",
    sort_order: Literal["asc", "desc"] = "desc",
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    query = db.query(Booking)
    if hotel_id is not None:
        query = query.filter(Booking.hotel_id == hotel_id)
    if status_filter is not None:
        query = query.filter(Booking.status == status_filter)
    if start_date is not None:
        query = query.filter(Booking.check_in_date >= start_date)
    if end_date is not None:
        query = query.filter(Booking.check_in_date <= end_date)

    column = SORTABLE_COLUMNS[sort_by]
    order_clause = column.asc() if sort_order == "asc" else column.desc()

    return query.order_by(order_clause).offset(skip).limit(limit).all()


@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return booking


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(booking_in: BookingCreate, db: Session = Depends(get_db)):
    hotel = db.query(Hotel).filter(Hotel.id == booking_in.hotel_id).first()
    if not hotel:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="hotel_id does not reference an existing hotel",
        )
    room = db.query(Room).filter(Room.id == booking_in.room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="room_id does not reference an existing room",
        )
    if room.hotel_id != booking_in.hotel_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="room does not belong to the specified hotel",
        )
    booking = Booking(**booking_in.model_dump())
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@router.patch("/{booking_id}/cancel", response_model=BookingResponse)
def cancel_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    booking.status = "cancelled"
    db.commit()
    db.refresh(booking)
    return booking

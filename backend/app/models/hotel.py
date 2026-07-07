from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Hotel(Base):
    __tablename__ = "hotels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    location = Column(String, nullable=False)
    total_rooms = Column(Integer, nullable=False)
    star_rating = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    rooms = relationship("Room", back_populates="hotel", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="hotel", cascade="all, delete-orphan")
    daily_metrics = relationship("DailyMetrics", back_populates="hotel", cascade="all, delete-orphan")


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False, index=True)
    room_number = Column(String, nullable=False)
    room_type = Column(String, nullable=False)
    base_price = Column(Float, nullable=False)
    max_occupancy = Column(Integer, nullable=False)
    is_available = Column(Boolean, default=True)

    hotel = relationship("Hotel", back_populates="rooms")
    bookings = relationship("Booking", back_populates="room")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False, index=True)
    check_in_date = Column(DateTime, nullable=False, index=True)
    check_out_date = Column(DateTime, nullable=False)
    guest_name = Column(String, nullable=False)
    guest_email = Column(String, nullable=True)
    num_guests = Column(Integer, nullable=False)
    booking_price = Column(Float, nullable=False)
    base_price = Column(Float, nullable=False)
    booking_date = Column(DateTime, default=datetime.utcnow)
    booking_source = Column(String, default="direct")
    status = Column(String, default="confirmed")

    hotel = relationship("Hotel", back_populates="bookings")
    room = relationship("Room", back_populates="bookings")


class DailyMetrics(Base):
    __tablename__ = "daily_metrics"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    occupancy_rate = Column(Float, default=0.0)
    rooms_occupied = Column(Integer, default=0)
    rooms_available = Column(Integer, default=0)
    total_revenue = Column(Float, default=0.0)
    average_daily_rate = Column(Float, default=0.0)
    revenue_per_available_room = Column(Float, default=0.0)
    booking_count = Column(Integer, default=0)
    cancellation_count = Column(Integer, default=0)
    calculated_at = Column(DateTime, default=datetime.utcnow)

    hotel = relationship("Hotel", back_populates="daily_metrics")

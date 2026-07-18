"""Shared pytest fixtures.

The `db` fixture builds a fresh, isolated in-memory SQLite database per test,
seeds it with a small, hand-countable dataset, and yields a session. Every
expected value in the DB-backed tests is derived by hand from the seed below,
so a failing assertion points at a real logic change, not at mystery data.
"""

import os

# Point the app's global engine at a throwaway in-memory DB *before* anything
# under app/ is imported (app.database.connection builds its engine at import
# time from DATABASE_URL). The DB-backed tests use their own StaticPool engine
# below; this just guarantees importing the app never touches the real dev file.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from datetime import datetime  # noqa: E402

import pytest  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database.connection import Base  # noqa: E402
from app.models.hotel import Booking, DailyMetrics, Hotel, Room  # noqa: E402


def _seed(session):
    """Two hotels, a handful of rooms/bookings/metrics with round numbers.

    Hotel 1 (Grand Plaza, 10 rooms) active revenue = 10000 + 5000 + 12000 =
    27000 over 3 bookings; one cancelled 8000 booking is excluded from revenue
    but counts toward the cancellation rate (1 of 4 = 25%).
    Hotel 2 (Coastal Inn, 5 rooms) has one 3000 booking, so all-hotels revenue
    is 30000 over 4 active bookings.
    """
    h1 = Hotel(id=1, name="Grand Plaza", location="Mumbai", total_rooms=10, star_rating=5.0)
    h2 = Hotel(id=2, name="Coastal Inn", location="Goa", total_rooms=5, star_rating=4.0)
    session.add_all([h1, h2])

    session.add_all([
        Room(id=1, hotel_id=1, room_number="101", room_type="Deluxe", base_price=5000, max_occupancy=2),
        Room(id=2, hotel_id=1, room_number="102", room_type="Deluxe", base_price=5000, max_occupancy=2),
        Room(id=3, hotel_id=1, room_number="103", room_type="Suite", base_price=8000, max_occupancy=3),
        Room(id=4, hotel_id=2, room_number="201", room_type="Standard", base_price=3000, max_occupancy=2),
    ])

    session.add_all([
        # Hotel 1 - three active bookings + one cancelled.
        Booking(id=1, hotel_id=1, room_id=1, check_in_date=datetime(2025, 12, 1),
                check_out_date=datetime(2025, 12, 3), guest_name="Alice", num_guests=2,
                booking_price=10000, base_price=10000, booking_date=datetime(2025, 11, 20),
                booking_source="direct", status="confirmed"),
        Booking(id=2, hotel_id=1, room_id=2, check_in_date=datetime(2025, 12, 1),
                check_out_date=datetime(2025, 12, 2), guest_name="Bob", num_guests=1,
                booking_price=5000, base_price=5000, booking_date=datetime(2025, 11, 28),
                booking_source="booking.com", status="completed"),
        Booking(id=3, hotel_id=1, room_id=3, check_in_date=datetime(2025, 12, 5),
                check_out_date=datetime(2025, 12, 6), guest_name="Carol", num_guests=2,
                booking_price=8000, base_price=8000, booking_date=datetime(2025, 11, 30),
                booking_source="direct", status="cancelled"),
        Booking(id=4, hotel_id=1, room_id=1, check_in_date=datetime(2025, 12, 10),
                check_out_date=datetime(2025, 12, 12), guest_name="Dan", num_guests=2,
                booking_price=12000, base_price=12000, booking_date=datetime(2025, 12, 1),
                booking_source="direct", status="confirmed"),
        # Hotel 2 - one active booking.
        Booking(id=5, hotel_id=2, room_id=4, check_in_date=datetime(2025, 12, 1),
                check_out_date=datetime(2025, 12, 2), guest_name="Eve", num_guests=2,
                booking_price=3000, base_price=3000, booking_date=datetime(2025, 11, 25),
                booking_source="direct", status="confirmed"),
    ])

    # daily_metrics for hotel 1: avg occupancy = (20 + 10 + 30) / 3 = 20.0.
    session.add_all([
        DailyMetrics(hotel_id=1, date=datetime(2025, 12, 1), occupancy_rate=20.0,
                     rooms_occupied=2, rooms_available=10, booking_count=2, cancellation_count=0),
        DailyMetrics(hotel_id=1, date=datetime(2025, 12, 2), occupancy_rate=10.0,
                     rooms_occupied=1, rooms_available=10, booking_count=1, cancellation_count=0),
        DailyMetrics(hotel_id=1, date=datetime(2025, 12, 10), occupancy_rate=30.0,
                     rooms_occupied=3, rooms_available=10, booking_count=1, cancellation_count=0),
    ])
    session.commit()


@pytest.fixture
def db():
    # A single shared connection (StaticPool) so the in-memory DB survives across
    # the multiple connections a session may open within one test.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        _seed(session)
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()

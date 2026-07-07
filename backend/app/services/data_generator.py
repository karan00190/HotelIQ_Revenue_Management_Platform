"""Synthetic data generator for HotelIQ.

Creates a realistic 2-year booking history so the analytics, forecasting, and
ML-challenger modules have real demand signal to learn from, not noise. Two
things distinguish this from a naive "N random bookings" approach:

1. Booking ARRIVAL RATE (not just price) responds to weekend/season, via a
   per-room, sequential-in-time simulation. Earlier versions of this file
   only let weekend/season affect price, leaving check-in dates uniformly
   random — which meant Prophet's weekly/yearly seasonality had nothing real
   to fit, and the pricing engine's premium-demand tiers could never fire in
   a backtest, since occupancy never varied with the calendar.
2. Each room's stays are generated as a non-overlapping sequence (walk
   forward in time, only ever starting a new stay after the previous one's
   checkout). A naive "assign a uniformly random room to every booking"
   approach has no such guarantee, and at high enough volume will silently
   double-book rooms — which would let daily_metrics' occupancy_rate exceed
   100%, since it counts overlapping bookings, not unique rooms.

Idempotent: if the database already has hotels, generation is skipped
entirely. Safe to call on every startup or re-run by hand.
"""

import random
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.hotel import Booking, Hotel, Room

# Deterministic runs make debugging and verification sane. Remove the seed if
# you want a fresh random dataset each time.
random.seed(42)

# --- Static definitions -------------------------------------------------------

HOTELS = [
    {"name": "Grand Plaza Mumbai", "location": "Mumbai, MH", "total_rooms": 150, "star_rating": 5.0},
    {"name": "Coastal Inn Goa", "location": "Panaji, GA", "total_rooms": 80, "star_rating": 4.0},
    {"name": "Heritage Stay Jaipur", "location": "Jaipur, RJ", "total_rooms": 60, "star_rating": 4.5},
]

# room_type -> (share of hotel's rooms, nightly base price range in INR)
ROOM_MIX = [
    ("Standard", 0.40, (2000, 3500)),
    ("Deluxe", 0.30, (3500, 6000)),
    ("Executive", 0.20, (6000, 9000)),
    ("Suite", 0.10, (9000, 15000)),
]

BOOKING_SOURCES = ["website", "booking.com", "direct", "expedia", "makemytrip"]

FIRST_NAMES = ["Asha", "Rohan", "Priya", "Vikram", "Neha", "Arjun", "Kavya",
               "Sanjay", "Meera", "Aditya", "Isha", "Rahul", "Sneha", "Karan", "Divya"]
LAST_NAMES = ["Rao", "Sharma", "Iyer", "Patel", "Nair", "Gupta", "Reddy",
              "Mehta", "Singh", "Kulkarni", "Bose", "Kapoor", "Menon", "Joshi"]

HISTORY_DAYS = 730  # 2 years back - long enough for yearly seasonality to mean something
FUTURE_DAYS = 15    # a little future data too
BATCH_SIZE = 100    # commit in batches, same pattern as etl_pipeline.load_to_database

MAX_STAY_NIGHTS = 7
AVG_STAY_NIGHTS = 4.0  # matches random.randint(1, MAX_STAY_NIGHTS)'s mean

# Targeting ~65-70% mean ACTIVE occupancy after the ~10% cancellation rate
# below thins it out, with real day-to-day swing (not just noise) driven by
# the arrival multipliers - tuned empirically against the actual generated
# data (0.72 initially overshot to ~81% mean; 0.60 measured ~68% mean with
# weekday~64-67%/weekend~72-75%, monsoon~52%/peak~79%). If you change this,
# regenerate and check real mean/min/max occupancy via SQL rather than
# trusting the algebra.
TARGET_SLOT_FILL_RATE = 0.60


# --- Generation steps ---------------------------------------------------------


def _star_factor(star_rating: float) -> float:
    """Higher-rated hotels charge more. 4-star = 1.0 baseline."""
    return star_rating / 4.0


def create_hotels(db: Session) -> list[Hotel]:
    hotels = []
    for spec in HOTELS:
        hotel = Hotel(**spec)
        db.add(hotel)
        hotels.append(hotel)
    db.commit()
    for hotel in hotels:
        db.refresh(hotel)
    return hotels


def create_rooms(db: Session, hotels: list[Hotel]) -> list[Room]:
    rooms = []
    for hotel in hotels:
        factor = _star_factor(hotel.star_rating)
        room_seq = 1
        for room_type, share, (low, high) in ROOM_MIX:
            count = round(hotel.total_rooms * share)
            for _ in range(count):
                base_price = round(random.uniform(low, high) * factor, -1)  # round to nearest 10
                room = Room(
                    hotel_id=hotel.id,
                    room_number=str(100 * (room_seq // 100 + 1) + room_seq),
                    room_type=room_type,
                    base_price=base_price,
                    max_occupancy=2 if room_type in ("Standard", "Deluxe") else 4,
                    is_available=True,
                )
                db.add(room)
                rooms.append(room)
                room_seq += 1
    db.commit()
    for room in rooms:
        db.refresh(room)
    return rooms


def _seasonal_price_factor(month: int) -> float:
    """Peak Oct-Feb = premium, monsoon Jun-Aug = discount, else neutral."""
    if month in (10, 11, 12, 1, 2):
        return random.uniform(1.10, 1.30)
    if month in (6, 7, 8):
        return random.uniform(0.70, 0.90)
    return 1.0


def _weekend_price_factor(check_in: datetime) -> float:
    """Friday(4) / Saturday(5) check-ins carry a price premium."""
    if check_in.weekday() in (4, 5):
        return random.uniform(1.20, 1.50)
    return 1.0


def _seasonal_arrival_multiplier(month: int) -> float:
    """Same shape as the price factor, applied to DEMAND instead of price:
    more check-ins actually arrive in peak season, fewer during monsoon."""
    if month in (10, 11, 12, 1, 2):
        return 1.5
    if month in (6, 7, 8):
        return 0.6
    return 1.0


def _weekend_arrival_multiplier(day: datetime) -> float:
    """Friday/Saturday see more check-ins arrive, not just higher prices."""
    if day.weekday() in (4, 5):
        return 1.5
    return 1.0


def _base_arrival_probability(target_slot_fill: float, avg_nights: float) -> float:
    """Daily 'a new stay starts today' probability that gives a room an
    average slot-fill rate of target_slot_fill, given stays averaging
    avg_nights and a geometric gap between them (occupancy = L / (L + 1/p),
    solved for p)."""
    return target_slot_fill / (avg_nights * (1 - target_slot_fill))


def _daily_arrival_probability(day: datetime, base_p: float) -> float:
    p = base_p * _seasonal_arrival_multiplier(day.month) * _weekend_arrival_multiplier(day)
    return min(p, 0.95)


def create_bookings(db: Session, hotels: list[Hotel], rooms: list[Room]) -> int:
    rooms_by_hotel: dict[int, list[Room]] = {h.id: [] for h in hotels}
    for room in rooms:
        rooms_by_hotel[room.hotel_id].append(room)

    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    window_start = today - timedelta(days=HISTORY_DAYS)
    window_end = today + timedelta(days=FUTURE_DAYS)
    base_p = _base_arrival_probability(TARGET_SLOT_FILL_RATE, AVG_STAY_NIGHTS)

    buffer: list[Booking] = []
    total_created = 0

    for hotel in hotels:
        for room in rooms_by_hotel[hotel.id]:
            # Walk this room's calendar forward in time. A new stay can only
            # start once the previous one has checked out, so two bookings
            # for the same room can never overlap - the room-collision
            # problem is avoided by construction, not by checking afterward.
            day = window_start
            while day < window_end:
                remaining_days = (window_end - day).days
                if remaining_days < 1:
                    break

                p_day = _daily_arrival_probability(day, base_p)
                if random.random() >= p_day:
                    day += timedelta(days=1)
                    continue

                nights = random.randint(1, min(MAX_STAY_NIGHTS, remaining_days))
                check_in = day
                check_out = check_in + timedelta(days=nights)

                nightly = room.base_price
                base_total = round(nightly * nights, 2)
                adjusted = (
                    nightly * nights * _weekend_price_factor(check_in) * _seasonal_price_factor(check_in.month)
                )
                booking_total = round(adjusted, 2)

                lead_days = random.randint(1, 60)
                booking_date = check_in - timedelta(days=lead_days)

                # 90% confirmed / 10% cancelled; past-checkout confirmed -> completed
                if random.random() < 0.10:
                    status = "cancelled"
                elif check_out < today:
                    status = "completed"
                else:
                    status = "confirmed"

                guest = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
                booking = Booking(
                    hotel_id=hotel.id,
                    room_id=room.id,
                    check_in_date=check_in,
                    check_out_date=check_out,
                    guest_name=guest,
                    guest_email=f"{guest.lower().replace(' ', '.')}@example.com",
                    num_guests=random.randint(1, room.max_occupancy),
                    booking_price=booking_total,
                    base_price=base_total,
                    booking_date=booking_date,
                    booking_source=random.choice(BOOKING_SOURCES),
                    status=status,
                )
                buffer.append(booking)
                total_created += 1

                if len(buffer) >= BATCH_SIZE:
                    db.add_all(buffer)
                    db.commit()
                    buffer = []

                day = check_out

    if buffer:
        db.add_all(buffer)
        db.commit()

    return total_created


def generate_all(db: Session) -> dict:
    """Populate the database if empty. Returns a summary of what happened."""
    if db.query(Hotel).count() > 0:
        return {
            "created": False,
            "reason": "database already contains hotels; skipping generation",
            "hotels": db.query(Hotel).count(),
            "rooms": db.query(Room).count(),
            "bookings": db.query(Booking).count(),
        }

    hotels = create_hotels(db)
    rooms = create_rooms(db, hotels)
    booking_count = create_bookings(db, hotels, rooms)

    return {
        "created": True,
        "hotels": len(hotels),
        "rooms": len(rooms),
        "bookings": booking_count,
    }


if __name__ == "__main__":
    from app.database.connection import SessionLocal
    from app.database.init_db import init_db

    init_db()
    session = SessionLocal()
    try:
        result = generate_all(session)
        print("Data generation result:")
        for key, value in result.items():
            print(f"  {key}: {value}")
    finally:
        session.close()

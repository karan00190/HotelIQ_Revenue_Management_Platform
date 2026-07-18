"""Tests for analytics_service (app/services/analytics_service.py) against the
hand-seeded in-memory database from conftest.py.

Hotel 1 active December bookings: 10000 (2 nights) + 5000 (1) + 12000 (2) =
27000 over 5 room-nights; a cancelled 8000 booking is excluded.
"""

from datetime import date

from app.services import analytics_service


class TestRevenueMetrics:
    def test_aggregate_metrics_for_december(self, db):
        result = analytics_service.calculate_revenue_metrics(
            db, hotel_id=1, start_date=date(2025, 12, 1), end_date=date(2025, 12, 31),
        )
        assert result["total_revenue"] == 27000
        assert result["total_bookings"] == 3          # cancelled excluded
        assert result["total_room_nights"] == 5        # 2 + 1 + 2
        assert result["average_daily_rate"] == 5400    # 27000 / 5
        # 5 room-nights of 10 rooms * 31 days = 5/310 = 1.61%
        assert result["occupancy_rate"] == 1.61


class TestDailyStatistics:
    def test_snapshot_on_dec_1(self, db):
        result = analytics_service.get_daily_statistics(
            db, hotel_id=1, target_date=date(2025, 12, 1),
        )
        assert result["rooms_occupied"] == 2           # B1 and B2 overlap Dec 1
        assert result["rooms_available"] == 10
        assert result["occupancy_rate"] == 20.0
        # B1 10000/2 nights + B2 5000/1 night = 10000 spread onto Dec 1
        assert result["total_revenue"] == 10000
        assert result["average_daily_rate"] == 5000    # 10000 / 2 occupied
        assert result["revenue_per_available_room"] == 1000   # 10000 / 10

    def test_unknown_hotel_returns_none(self, db):
        assert analytics_service.get_daily_statistics(db, hotel_id=999) is None

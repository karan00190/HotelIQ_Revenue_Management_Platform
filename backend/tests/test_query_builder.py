"""Tests for QueryBuilder (app/services/query_builder.py) against the seeded
in-memory database. Confirms the ACTIVE_STATUSES filter, hotel scoping, and
the cancellation math.
"""

from app.services.query_builder import QueryBuilder


class TestTotalRevenue:
    def test_single_hotel_excludes_cancelled(self, db):
        result = QueryBuilder(db).get_total_revenue(hotel_id=1)
        assert result["total_revenue"] == 27000   # cancelled 8000 not counted
        assert result["total_bookings"] == 3

    def test_all_hotels(self, db):
        result = QueryBuilder(db).get_total_revenue()
        assert result["total_revenue"] == 30000    # 27000 + hotel 2's 3000
        assert result["total_bookings"] == 4

    def test_other_hotel_scoped(self, db):
        result = QueryBuilder(db).get_total_revenue(hotel_id=2)
        assert result["total_revenue"] == 3000
        assert result["total_bookings"] == 1


class TestOccupancyStats:
    def test_average_from_daily_metrics(self, db):
        result = QueryBuilder(db).get_occupancy_stats(hotel_id=1)
        assert result["average_occupancy_rate"] == 20.0   # (20 + 10 + 30) / 3
        assert result["max_occupancy_rate"] == 30.0
        assert result["min_occupancy_rate"] == 10.0
        assert result["days_with_data"] == 3

    def test_unknown_hotel_returns_none(self, db):
        assert QueryBuilder(db).get_occupancy_stats(hotel_id=999) is None


class TestCancellationAnalysis:
    def test_rate_and_lost_revenue(self, db):
        result = QueryBuilder(db).get_cancellation_analysis(hotel_id=1)
        assert result["total_bookings"] == 4          # all statuses counted here
        assert result["cancelled_bookings"] == 1
        assert result["cancellation_rate"] == 25.0     # 1 of 4
        assert result["lost_revenue"] == 8000

"""Tests for the assistant's tool layer (app/services/assistant_tools.py).

The tools are thin, read-only wrappers over the same services tested elsewhere;
what matters here is their contract: correct date parsing, and that every tool
returns a plain dict (an {"error": ...} dict on bad input) rather than raising.
"""

import pytest

from app.services.assistant_tools import _parse_date, build_tools


class TestParseDate:
    def test_valid_iso_date(self):
        from datetime import date
        assert _parse_date("2025-12-01", "target_date") == date(2025, 12, 1)

    def test_none_passes_through(self):
        assert _parse_date(None, "start_date") is None

    def test_bad_date_raises_value_error(self):
        with pytest.raises(ValueError):
            _parse_date("31-12-2025", "target_date")


class TestTools:
    def _tools(self, db):
        return {t.name: t for t in build_tools(db)}

    def test_list_hotels(self, db):
        result = self._tools(db)["list_hotels"].invoke({})
        assert len(result["hotels"]) == 2
        names = {h["name"] for h in result["hotels"]}
        assert names == {"Grand Plaza", "Coastal Inn"}

    def test_get_total_revenue_tool(self, db):
        result = self._tools(db)["get_total_revenue"].invoke({"hotel_id": 1})
        assert result["total_revenue"] == 27000
        assert result["total_bookings"] == 3

    def test_bad_hotel_returns_error_dict_not_exception(self, db):
        # get_occupancy_stats on an unknown hotel must degrade to {"error": ...},
        # never raise - the agent relies on this to relay failures honestly.
        result = self._tools(db)["get_occupancy_stats"].invoke({"hotel_id": 999})
        assert "error" in result

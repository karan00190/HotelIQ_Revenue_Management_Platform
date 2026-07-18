"""Tests for the data-quality gate (app/services/data_validator.py).

Covers all nine validation checks plus the non-destructive clean_dataframe.
"""

import pandas as pd
import pytest

from app.services.data_validator import BookingDataValidator

validator = BookingDataValidator()


def valid_frame():
    """A minimal frame that passes every check with zero errors/warnings."""
    return pd.DataFrame({
        "hotel_id": [1, 1],
        "room_id": [1, 2],
        "check_in_date": ["2025-12-01", "2025-12-05"],
        "check_out_date": ["2025-12-03", "2025-12-06"],
        "guest_name": ["Alice", "Bob"],
        "num_guests": [2, 1],
        "booking_price": [10000, 5000],
        "base_price": [10000, 5000],
    })


class TestValidateDataframe:
    def test_valid_frame_passes(self):
        report = validator.validate_dataframe(valid_frame())
        assert report.is_valid()
        assert report.errors == []
        assert report.stats["total_records"] == 2

    def test_missing_required_column(self):
        df = valid_frame().drop(columns=["booking_price"])
        report = validator.validate_dataframe(df)
        assert not report.is_valid()
        assert any("Missing required columns" in e for e in report.errors)

    def test_empty_frame(self):
        df = valid_frame().iloc[0:0]
        report = validator.validate_dataframe(df)
        assert not report.is_valid()
        assert any("empty" in e.lower() for e in report.errors)

    def test_null_in_required_column(self):
        df = valid_frame()
        df.loc[0, "guest_name"] = None
        report = validator.validate_dataframe(df)
        assert not report.is_valid()
        assert any("null" in e.lower() for e in report.errors)

    def test_unparseable_dates(self):
        df = valid_frame()
        df.loc[0, "check_in_date"] = "not-a-date"
        report = validator.validate_dataframe(df)
        assert not report.is_valid()
        assert any("date" in e.lower() for e in report.errors)

    def test_checkout_not_after_checkin(self):
        df = valid_frame()
        df.loc[0, "check_out_date"] = "2025-12-01"  # same as check-in
        report = validator.validate_dataframe(df)
        assert not report.is_valid()
        assert any("check_out_date" in e for e in report.errors)

    def test_non_positive_prices(self):
        df = valid_frame()
        df.loc[0, "booking_price"] = 0
        df.loc[1, "base_price"] = -100
        report = validator.validate_dataframe(df)
        assert not report.is_valid()
        assert any("booking_price <= 0" in e for e in report.errors)
        assert any("base_price <= 0" in e for e in report.errors)

    def test_non_positive_guests(self):
        df = valid_frame()
        df.loc[0, "num_guests"] = 0
        report = validator.validate_dataframe(df)
        assert not report.is_valid()
        assert any("num_guests <= 0" in e for e in report.errors)

    def test_duplicates_are_warning_not_error(self):
        df = valid_frame()
        # Make row 2 duplicate row 1's hotel/room/check-in.
        df.loc[1, ["hotel_id", "room_id", "check_in_date"]] = [1, 1, "2025-12-01"]
        report = validator.validate_dataframe(df)
        assert report.is_valid()  # duplicates never block ingestion
        assert any("duplicate" in w.lower() for w in report.warnings)

    def test_price_outlier_is_warning(self):
        # 20 normal prices + one extreme. A single outlier in a tiny sample
        # inflates the std enough to hide itself (mean + 3*std), so enough
        # normal points are needed for the outlier to genuinely stand out.
        n = 20
        prices = [5000] * n + [100000]
        df = pd.DataFrame({
            "hotel_id": [1] * (n + 1),
            "room_id": list(range(1, n + 2)),
            "check_in_date": ["2025-12-01"] * (n + 1),
            "check_out_date": ["2025-12-02"] * (n + 1),
            "guest_name": ["G"] * (n + 1),
            "num_guests": [1] * (n + 1),
            "booking_price": prices,
            "base_price": prices,
        })
        report = validator.validate_dataframe(df)
        assert any("outlier" in w.lower() for w in report.warnings)


class TestCleanDataframe:
    def test_is_non_destructive(self):
        df = valid_frame()
        before = df.copy()
        validator.clean_dataframe(df)
        pd.testing.assert_frame_equal(df, before)  # input untouched

    def test_applies_optional_defaults(self):
        cleaned = validator.clean_dataframe(valid_frame())
        assert (cleaned["booking_source"] == "direct").all()
        assert (cleaned["status"] == "confirmed").all()

    def test_strips_whitespace(self):
        df = valid_frame()
        df.loc[0, "guest_name"] = "  Alice  "
        cleaned = validator.clean_dataframe(df)
        assert cleaned.loc[0, "guest_name"] == "Alice"

    def test_removes_duplicates(self):
        df = valid_frame()
        df.loc[1, ["hotel_id", "room_id", "check_in_date"]] = [1, 1, "2025-12-01"]
        cleaned = validator.clean_dataframe(df)
        assert len(cleaned) == 1

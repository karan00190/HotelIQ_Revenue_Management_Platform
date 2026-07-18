"""Tests for feature engineering (app/services/feature_engineering.py).

The FeatureEngineer methods are pure, DB-agnostic static methods, so they can
be driven with a tiny hand-built frame and checked column by column.
"""

import pandas as pd

from app.services.feature_engineering import FeatureEngineer


def base_frame():
    return pd.DataFrame({
        "hotel_id": [1, 1],
        "room_id": [1, 2],
        # 2025-12-05 is a Friday (weekend, peak season); 2025-06-10 is a Tue
        # (weekday, monsoon low season).
        "check_in_date": ["2025-12-05", "2025-06-10"],
        "check_out_date": ["2025-12-08", "2025-06-11"],
        "booking_date": ["2025-12-03", "2025-05-01"],
        "booking_price": [9000, 5000],
        "base_price": [10000, 5000],
    })


class TestTimeFeatures:
    def test_weekend_flag_only_fri_sat(self):
        out = FeatureEngineer.create_time_features(base_frame())
        assert out.loc[0, "is_weekend"] == 1   # Friday
        assert out.loc[1, "is_weekend"] == 0   # Tuesday

    def test_peak_season_only_oct_to_feb(self):
        out = FeatureEngineer.create_time_features(base_frame())
        assert out.loc[0, "is_peak_season"] == 1   # December
        assert out.loc[1, "is_peak_season"] == 0   # June

    def test_season_map(self):
        out = FeatureEngineer.create_time_features(base_frame())
        assert out.loc[0, "season"] == "winter"    # December
        assert out.loc[1, "season"] == "monsoon"   # June

    def test_month_extracted(self):
        out = FeatureEngineer.create_time_features(base_frame())
        assert out.loc[0, "month"] == 12
        assert out.loc[1, "month"] == 6


class TestStayFeatures:
    def test_length_of_stay(self):
        out = FeatureEngineer.create_stay_features(base_frame())
        assert out.loc[0, "length_of_stay"] == 3   # Dec 5 -> Dec 8
        assert out.loc[1, "length_of_stay"] == 1   # Jun 10 -> Jun 11

    def test_lead_time_and_last_minute(self):
        out = FeatureEngineer.create_stay_features(base_frame())
        assert out.loc[0, "lead_time_days"] == 2    # Dec 3 -> Dec 5
        assert out.loc[0, "is_last_minute"] == 1    # <= 3 days
        assert out.loc[1, "lead_time_days"] == 40   # May 1 -> Jun 10
        assert out.loc[1, "is_last_minute"] == 0


class TestPricingFeatures:
    def test_price_per_night_and_discount(self):
        df = FeatureEngineer.create_stay_features(base_frame())
        out = FeatureEngineer.create_pricing_features(df)
        assert out.loc[0, "price_per_night"] == 3000    # 9000 / 3 nights
        assert out.loc[0, "discount_pct"] == 10.0       # (10000-9000)/10000*100
        assert out.loc[1, "discount_pct"] == 0.0        # paid full base price

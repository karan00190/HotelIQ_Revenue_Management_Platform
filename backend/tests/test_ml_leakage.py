"""The flagship correctness test: no target leakage in the XGBoost features.

MLDemandForecaster._add_lagged_features (app/services/ml_forecasting_service.py)
computes lag/rolling occupancy features by shifting the series by one day
BEFORE rolling, so a row's features only ever see days strictly before it.
Get that shift wrong and every test-set row would leak its own occupancy into
its "recent average" feature - a subtle, accuracy-inflating bug. These tests
assert the shift is exactly right on a hand-built series.
"""

import pandas as pd

from app.services.ml_forecasting_service import MLDemandForecaster


def series_frame(n=14):
    """occupancy_rate[i] == i * 10, on n consecutive days - distinct values so
    every lag/rolling result is unambiguous."""
    return pd.DataFrame({
        "date": pd.date_range("2025-01-01", periods=n, freq="D"),
        "occupancy_rate": [i * 10 for i in range(n)],
        "booking_count": [i for i in range(n)],
        "cancellation_count": [0] * n,
    })


def test_lag_1_is_previous_day():
    out = MLDemandForecaster._add_lagged_features(series_frame()).reset_index(drop=True)
    # lag_1 at row 5 must be occupancy of row 4 (== 40), never row 5's own value.
    assert out.loc[5, "lag_1"] == 40
    assert pd.isna(out.loc[0, "lag_1"])  # nothing before the first day


def test_rolling_mean_7_excludes_current_day():
    out = MLDemandForecaster._add_lagged_features(series_frame()).reset_index(drop=True)
    # At row 7, the trailing-7 window is occupancy[0..6] = 0,10,...,60 -> mean 30.
    # If the shift(1) were missing it would be mean(occupancy[1..7]) = 40. The
    # assertion of 30 (not 40) is what makes this a real leakage detector.
    assert out.loc[7, "rolling_mean_7"] == 30.0
    assert out.loc[13, "rolling_mean_7"] == 90.0  # occupancy[6..12] mean


def test_rolling_mean_matches_hand_computed_window():
    frame = series_frame()
    occ = frame["occupancy_rate"].tolist()
    out = MLDemandForecaster._add_lagged_features(frame).reset_index(drop=True)
    for i in range(7, len(occ)):
        expected = sum(occ[i - 7:i]) / 7  # the 7 days strictly before i
        assert out.loc[i, "rolling_mean_7"] == expected


def test_lag_7_and_lag_14():
    out = MLDemandForecaster._add_lagged_features(series_frame(20)).reset_index(drop=True)
    assert out.loc[10, "lag_7"] == 30    # occupancy[3]
    assert out.loc[15, "lag_14"] == 10   # occupancy[1]

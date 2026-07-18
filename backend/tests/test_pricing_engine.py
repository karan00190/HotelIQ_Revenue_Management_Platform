"""Tests for the rule-based pricing engine (app/services/pricing_engine.py).

Every expected multiplier below is computed by hand from the documented tier
table, so these tests double as executable documentation of the pricing rules.
"""

import pytest

from app.services.pricing_engine import MAX_MULTIPLIER, MIN_MULTIPLIER, DynamicPricingEngine

engine = DynamicPricingEngine()


def mult(**kwargs):
    base = dict(
        predicted_occupancy=50,   # 40-69 -> neutral
        current_occupancy=50,     # 30-85 -> neutral
        is_weekend=False,
        is_peak_season=False,
        lead_time_days=10,        # 4-29 -> neutral
    )
    base.update(kwargs)
    return engine.calculate_price_multiplier(**base)


class TestPredictedOccupancyTier:
    def test_neutral_band_no_change(self):
        assert mult(predicted_occupancy=50) == pytest.approx(1.0)

    def test_very_high_demand_premium(self):
        assert mult(predicted_occupancy=95) == pytest.approx(1.40)

    def test_boundary_90_is_premium(self):
        assert mult(predicted_occupancy=90) == pytest.approx(1.40)

    def test_above_average_demand(self):
        assert mult(predicted_occupancy=75) == pytest.approx(1.15)

    def test_boundary_70_is_moderate(self):
        assert mult(predicted_occupancy=70) == pytest.approx(1.15)

    def test_boundary_40_is_neutral(self):
        # 40 is NOT below 40, so no discount.
        assert mult(predicted_occupancy=40) == pytest.approx(1.0)

    def test_low_demand_discount(self):
        assert mult(predicted_occupancy=30) == pytest.approx(0.80)


class TestCurrentOccupancyTier:
    def test_scarcity_premium_above_85(self):
        assert mult(current_occupancy=90) == pytest.approx(1.10)

    def test_boundary_85_no_scarcity(self):
        # >85 required; exactly 85 does nothing.
        assert mult(current_occupancy=85) == pytest.approx(1.0)

    def test_under_occupied_discount(self):
        assert mult(current_occupancy=20) == pytest.approx(0.95)


class TestFlatFactors:
    def test_weekend_premium(self):
        assert mult(is_weekend=True) == pytest.approx(1.15)

    def test_peak_season_premium(self):
        assert mult(is_peak_season=True) == pytest.approx(1.10)

    def test_last_minute_premium(self):
        assert mult(lead_time_days=2) == pytest.approx(1.20)

    def test_advance_discount(self):
        assert mult(lead_time_days=45) == pytest.approx(0.95)


class TestCombinationAndClipping:
    def test_anchor_value_pricing_case(self):
        # 0.80 (low demand) * 0.95 (empty) * 1.15 (weekend) = 0.874
        m = mult(predicted_occupancy=26, current_occupancy=0, is_weekend=True, lead_time_days=15)
        assert m == pytest.approx(0.874)

    def test_clipped_to_ceiling(self):
        # Everything stacked: 1.40*1.10*1.15*1.10*1.20 = 2.338 -> clipped to 1.5
        m = mult(predicted_occupancy=95, current_occupancy=95, is_weekend=True,
                 is_peak_season=True, lead_time_days=1)
        assert m == pytest.approx(MAX_MULTIPLIER)

    def test_lowest_reachable_stays_above_floor(self):
        # The floor is 0.7, but the engine's own factors only bottom out at
        # 0.80*0.95*0.95 = 0.722 (nothing pushes below), so the floor clip is
        # never actually triggered by real inputs. This documents that.
        m = mult(predicted_occupancy=20, current_occupancy=10, lead_time_days=40)
        assert m == pytest.approx(0.722)
        assert m >= MIN_MULTIPLIER


class TestRecommendation:
    def test_price_and_strategy_for_anchor_case(self):
        rec = engine.get_pricing_recommendation(
            base_price=5000, predicted_occupancy=26, current_occupancy=0,
            is_weekend=True, is_peak_season=False, lead_time_days=15,
        )
        assert rec["recommended_price"] == pytest.approx(4370.0)  # 5000 * 0.874
        assert rec["price_multiplier"] == pytest.approx(0.874)
        assert rec["price_change_percent"] == pytest.approx(-12.6)
        assert rec["strategy"] == "Value Pricing"

    def test_premium_strategy_label(self):
        rec = engine.get_pricing_recommendation(
            base_price=5000, predicted_occupancy=95, current_occupancy=50,
            is_weekend=False, is_peak_season=False, lead_time_days=10,
        )
        assert rec["recommended_price"] == pytest.approx(7000.0)  # 5000 * 1.40
        assert rec["strategy"] == "Premium Pricing"

    def test_factors_are_explained(self):
        rec = engine.get_pricing_recommendation(
            base_price=5000, predicted_occupancy=95, current_occupancy=90,
            is_weekend=True, is_peak_season=True, lead_time_days=1,
        )
        # Each fired factor should contribute a human-readable line.
        joined = " ".join(rec["factors"]).lower()
        assert "premium" in joined
        assert "weekend" in joined
        assert "peak season" in joined

    def test_no_signals_maintains_base_price(self):
        rec = engine.get_pricing_recommendation(
            base_price=5000, predicted_occupancy=50, current_occupancy=50,
            is_weekend=False, is_peak_season=False, lead_time_days=10,
        )
        assert rec["recommended_price"] == pytest.approx(5000.0)
        assert rec["strategy"] == "Maintain Base Price"
        assert rec["factors"] == ["No strong demand signals - base price maintained"]

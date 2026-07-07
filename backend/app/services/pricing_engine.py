"""Rule-based dynamic pricing. Not a machine learning model - a set of
multiplicative factors encoding standard revenue-management principles.
Takes a demand forecast (from forecasting_service) plus contextual signals
and turns them into one concrete recommended price with a plain explanation.

architecture.md specifies the two extremes of the "predicted occupancy"
factor precisely (90%+ -> +40%, <40% -> a discount) but leaves the exact
discount size, the 40-90% middle band, and the exact strategy-label
boundaries unspecified. Concrete choices made here (flagged inline) fill
those gaps; they're easy to retune later since they're all in one place.
"""

MIN_MULTIPLIER = 0.7
MAX_MULTIPLIER = 1.5

# Oct-Feb: the Indian hospitality peak season. Canonical definition - other
# modules (feature_engineering, the forecasting API, the ML challenger) all
# import this rather than redefining the same month set.
PEAK_MONTHS = (10, 11, 12, 1, 2)


class DynamicPricingEngine:
    def calculate_price_multiplier(
        self,
        predicted_occupancy: float,
        current_occupancy: float,
        is_weekend: bool,
        is_peak_season: bool,
        lead_time_days: int,
    ) -> float:
        multiplier = 1.0

        # Predicted occupancy factor (strongest signal). Doc specifies both
        # extremes exactly; the 70-89% tier and the exact "low demand"
        # discount size are judgment calls, not in the spec.
        if predicted_occupancy >= 90:
            multiplier *= 1.40
        elif predicted_occupancy >= 70:
            multiplier *= 1.15
        elif predicted_occupancy < 40:
            multiplier *= 0.80
        # 40-69%: normal demand, no adjustment.

        # Current occupancy factor (scarcity premium / stimulate discount).
        if current_occupancy > 85:
            multiplier *= 1.10
        elif current_occupancy < 30:
            multiplier *= 0.95

        # Weekend factor: flat premium for Friday/Saturday check-in.
        if is_weekend:
            multiplier *= 1.15

        # Peak season factor: flat premium for Oct-Feb check-in.
        if is_peak_season:
            multiplier *= 1.10

        # Lead time factor: last-minute premium, advance-booking discount.
        if lead_time_days <= 3:
            multiplier *= 1.20
        elif lead_time_days >= 30:
            multiplier *= 0.95

        return max(MIN_MULTIPLIER, min(MAX_MULTIPLIER, multiplier))

    def get_pricing_recommendation(
        self,
        base_price: float,
        predicted_occupancy: float,
        current_occupancy: float,
        is_weekend: bool,
        is_peak_season: bool,
        lead_time_days: int,
    ) -> dict:
        multiplier = self.calculate_price_multiplier(
            predicted_occupancy=predicted_occupancy,
            current_occupancy=current_occupancy,
            is_weekend=is_weekend,
            is_peak_season=is_peak_season,
            lead_time_days=lead_time_days,
        )
        recommended_price = round(base_price * multiplier, 2)
        price_change_percent = round((multiplier - 1) * 100, 2)

        factors = []
        if predicted_occupancy >= 90:
            factors.append(f"Very high predicted demand ({predicted_occupancy:.0f}%) supports a premium price")
        elif predicted_occupancy >= 70:
            factors.append(f"Above-average predicted demand ({predicted_occupancy:.0f}%) supports a moderate increase")
        elif predicted_occupancy < 40:
            factors.append(f"Low predicted demand ({predicted_occupancy:.0f}%) - discount to stimulate bookings")

        if current_occupancy > 85:
            factors.append(f"Hotel is nearly full today ({current_occupancy:.0f}%) - scarcity premium applied")
        elif current_occupancy < 30:
            factors.append(f"Hotel is under-occupied today ({current_occupancy:.0f}%) - discount applied")

        if is_weekend:
            factors.append("Weekend check-in (Friday/Saturday) - weekend premium applied")
        if is_peak_season:
            factors.append("Peak season (October-February) - seasonal premium applied")

        if lead_time_days <= 3:
            factors.append(f"Last-minute booking ({lead_time_days} day(s) out) - premium applied")
        elif lead_time_days >= 30:
            factors.append(f"Advance booking ({lead_time_days} days out) - early-bird discount applied")

        if not factors:
            factors.append("No strong demand signals - base price maintained")

        # Strategy label boundaries: another judgment call, spanning the
        # [0.7, 1.5] multiplier range into 5 roughly even bands.
        if multiplier >= 1.30:
            strategy = "Premium Pricing"
        elif multiplier >= 1.10:
            strategy = "Moderate Increase"
        elif multiplier >= 0.95:
            strategy = "Maintain Base Price"
        elif multiplier >= 0.85:
            strategy = "Value Pricing"
        else:
            strategy = "Aggressive Discounting"

        return {
            "base_price": base_price,
            "recommended_price": recommended_price,
            "price_multiplier": round(multiplier, 3),
            "price_change_percent": price_change_percent,
            "strategy": strategy,
            "factors": factors,
            "inputs": {
                "predicted_occupancy": round(predicted_occupancy, 2),
                "current_occupancy": round(current_occupancy, 2),
                "is_weekend": is_weekend,
                "is_peak_season": is_peak_season,
                "lead_time_days": lead_time_days,
            },
        }

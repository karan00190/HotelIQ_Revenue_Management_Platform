"""Head-to-head evaluation of the Prophet forecaster vs. the XGBoost
challenger, plus a "what-if" revenue simulation that replays real historical
bookings through the existing pricing engine using each model's forecast.

Both entry points share one time-based split (_fit_and_evaluate): the last
TEST_FRACTION of the shared calendar range is held out, both models are
trained only on data strictly before it, and every comparison happens on
that identical held-out window. This is what makes "Prophet vs XGBoost" and
"actual vs simulated pricing" fair comparisons rather than cherry-picked
ones.

Metrics are hand-rolled rather than pulled from scikit-learn - both formulas
are one line, and avoiding the dependency was a deliberate choice (see
ml_forecasting_service.py's docstring for the matching reasoning about
XGBRegressor vs the native Booster API).
"""

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.models.hotel import Booking, DailyMetrics
from app.services.forecasting_service import DemandForecaster
from app.services.ml_forecasting_service import MLDemandForecaster
from app.services.pricing_engine import PEAK_MONTHS, DynamicPricingEngine
from app.utils.metrics_calculator import ACTIVE_STATUSES

TEST_FRACTION = 0.20
MIN_TEST_DAYS = 30
BOOTSTRAP_ITERATIONS = 1000
BOOTSTRAP_SEED = 42


def _mae(actual: pd.Series, predicted) -> float:
    return float((actual - pd.Series(predicted, index=actual.index)).abs().mean())


def _rmse(actual: pd.Series, predicted) -> float:
    return float(((actual - pd.Series(predicted, index=actual.index)) ** 2).mean() ** 0.5)


def _train_prophet_up_to(db: Session, hotel_id: int, cutoff_date: pd.Timestamp) -> DemandForecaster:
    """Mirrors DemandForecaster.prepare_training_data's ds/y shape, but
    constrained to end strictly before cutoff_date - prepare_training_data
    itself only supports "last N days ending today", which can't express a
    historical holdout, so this builds the same shape by hand instead of
    modifying forecasting_service.py."""
    rows = (
        db.query(DailyMetrics.date, DailyMetrics.occupancy_rate)
        .filter(DailyMetrics.hotel_id == hotel_id, DailyMetrics.date < cutoff_date)
        .order_by(DailyMetrics.date)
        .all()
    )
    training_df = pd.DataFrame(rows, columns=["ds", "y"])
    forecaster = DemandForecaster(db)
    forecaster.last_training_date = training_df["ds"].max()
    forecaster.train(training_df)
    return forecaster


def _fit_and_evaluate(db: Session, hotel_id: int) -> dict:
    """Fits both challenger models on one identical time-based split and
    returns everything both run_forecast_comparison and run_revenue_backtest
    need, so the split/training logic lives in exactly one place."""
    ml_forecaster = MLDemandForecaster(db)
    full_df = ml_forecaster.build_feature_frame()

    unique_dates = sorted(full_df["date"].unique())
    cutoff_idx = int(len(unique_dates) * (1 - TEST_FRACTION))
    cutoff_date = pd.Timestamp(unique_dates[cutoff_idx])

    train_df = full_df[full_df["date"] < cutoff_date]
    test_df = full_df[full_df["date"] >= cutoff_date]

    hotel_train_df = train_df[train_df["hotel_id"] == hotel_id].sort_values("date").reset_index(drop=True)
    hotel_test_df = test_df[test_df["hotel_id"] == hotel_id].sort_values("date").reset_index(drop=True)

    if len(hotel_test_df) < MIN_TEST_DAYS:
        raise ValueError(
            f"Only {len(hotel_test_df)} held-out test day(s) for hotel {hotel_id}; need at least {MIN_TEST_DAYS}."
        )

    # ML model trains pooled across every hotel's training-window rows.
    ml_forecaster.train(train_df)
    ml_preds = ml_forecaster.predict(hotel_test_df)

    # Naive baseline: a single constant, the training window's own mean -
    # deliberately dumb, so it calibrates how much the other two are
    # actually adding over "assume tomorrow looks like history's average".
    naive_pred = float(hotel_train_df["occupancy_rate"].mean())

    # Prophet trains on ONLY this hotel's rows up to the same cutoff, then
    # forecasts forward exactly as many days as the test window is long.
    prophet_forecaster = _train_prophet_up_to(db, hotel_id, cutoff_date)
    prophet_df = prophet_forecaster.forecast(days_ahead=len(hotel_test_df))
    prophet_by_date = dict(zip(prophet_df["ds"].dt.normalize(), prophet_df["yhat"]))

    hotel_test_df = hotel_test_df.assign(
        naive_pred=naive_pred,
        ml_pred=ml_preds.values,
        prophet_pred=[prophet_by_date.get(pd.Timestamp(d).normalize()) for d in hotel_test_df["date"]],
    )
    if hotel_test_df["prophet_pred"].isna().any():
        raise ValueError(
            "Prophet's forecast dates did not fully cover the test window - "
            "check for gaps between the training cutoff and the test dates."
        )

    return {
        "hotel_id": hotel_id,
        "cutoff_date": cutoff_date,
        "hotel_train_df": hotel_train_df,
        "hotel_test_df": hotel_test_df,
    }


def run_forecast_comparison(db: Session, hotel_id: int) -> dict:
    fit = _fit_and_evaluate(db, hotel_id)
    test_df = fit["hotel_test_df"]
    actual = test_df["occupancy_rate"]

    def _metrics(pred_col: str) -> dict:
        return {"mae": round(_mae(actual, test_df[pred_col]), 3), "rmse": round(_rmse(actual, test_df[pred_col]), 3)}

    return {
        "hotel_id": hotel_id,
        "train_days": len(fit["hotel_train_df"]),
        "test_days": len(test_df),
        "test_date_range": {
            "start": test_df["date"].min().date().isoformat(),
            "end": test_df["date"].max().date().isoformat(),
        },
        "models": {
            "naive": {
                **_metrics("naive_pred"),
                "description": "Constant prediction: mean occupancy over the training window",
            },
            "prophet": _metrics("prophet_pred"),
            "xgboost": _metrics("ml_pred"),
        },
        "daily_comparison": [
            {
                "date": row.date.date().isoformat(),
                "actual": round(row.occupancy_rate, 2),
                "naive": round(row.naive_pred, 2),
                "prophet": round(row.prophet_pred, 2),
                "xgboost": round(row.ml_pred, 2),
            }
            for row in test_df.itertuples()
        ],
    }


def _bootstrap_total(deltas: np.ndarray) -> dict:
    """Resamples the per-booking deltas with replacement to put a 5th-95th
    percentile band around the point estimate, rather than reporting one
    falsely-precise headline number from what is still a fairly small
    per-hotel sample."""
    total = float(deltas.sum())
    if len(deltas) == 0:
        return {"point_estimate": 0.0, "p5": 0.0, "p95": 0.0}
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    idx = rng.integers(0, len(deltas), size=(BOOTSTRAP_ITERATIONS, len(deltas)))
    totals = deltas[idx].sum(axis=1)
    return {
        "point_estimate": round(total, 2),
        "p5": round(float(np.percentile(totals, 5)), 2),
        "p95": round(float(np.percentile(totals, 95)), 2),
    }


def run_revenue_backtest(db: Session, hotel_id: int) -> dict:
    fit = _fit_and_evaluate(db, hotel_id)
    test_df = fit["hotel_test_df"]
    cutoff_date = fit["cutoff_date"]

    prophet_by_date = dict(zip(test_df["date"], test_df["prophet_pred"]))
    ml_by_date = dict(zip(test_df["date"], test_df["ml_pred"]))

    # Full history (not just the test window) - a test-window booking's
    # booking_date can sit well before the cutoff once its lead time is
    # subtracted, so "current_occupancy as of booking_date - 1" needs
    # access to training-window days too.
    occ_rows = (
        db.query(DailyMetrics.date, DailyMetrics.occupancy_rate).filter(DailyMetrics.hotel_id == hotel_id).all()
    )
    occ_lookup = {pd.Timestamp(d).normalize(): occ for d, occ in occ_rows}

    bookings = (
        db.query(Booking)
        .filter(
            Booking.hotel_id == hotel_id,
            Booking.status.in_(ACTIVE_STATUSES),
            Booking.check_in_date >= cutoff_date,
        )
        .all()
    )

    pricing_engine = DynamicPricingEngine()
    detail = []
    for b in bookings:
        check_in = pd.Timestamp(b.check_in_date).normalize()
        if check_in not in prophet_by_date:
            continue  # outside the forecasted window (shouldn't happen given the filter above)

        is_weekend = bool(check_in.dayofweek in (4, 5))
        is_peak_season = bool(check_in.month in PEAK_MONTHS)
        lead_time_days = (b.check_in_date - b.booking_date).days

        prior_day = pd.Timestamp(b.booking_date).normalize() - pd.Timedelta(days=1)
        if prior_day not in occ_lookup:
            raise ValueError(
                f"No daily_metrics row for hotel {hotel_id} on {prior_day.date()} "
                f"(booking {b.id}'s booking_date - 1); recalculate-all-metrics may be needed."
            )
        current_occupancy = occ_lookup[prior_day]

        prophet_rec = pricing_engine.get_pricing_recommendation(
            base_price=b.base_price,
            predicted_occupancy=prophet_by_date[check_in],
            current_occupancy=current_occupancy,
            is_weekend=is_weekend,
            is_peak_season=is_peak_season,
            lead_time_days=lead_time_days,
        )
        ml_rec = pricing_engine.get_pricing_recommendation(
            base_price=b.base_price,
            predicted_occupancy=ml_by_date[check_in],
            current_occupancy=current_occupancy,
            is_weekend=is_weekend,
            is_peak_season=is_peak_season,
            lead_time_days=lead_time_days,
        )

        detail.append({
            "booking_id": b.id,
            "check_in_date": check_in.date().isoformat(),
            "base_price": b.base_price,
            "actual_price": b.booking_price,
            "simulated_price_prophet": prophet_rec["recommended_price"],
            "simulated_price_ml": ml_rec["recommended_price"],
        })

    actual_total = sum(d["actual_price"] for d in detail)
    prophet_total = sum(d["simulated_price_prophet"] for d in detail)
    ml_total = sum(d["simulated_price_ml"] for d in detail)

    delta_ml_vs_prophet = np.array([d["simulated_price_ml"] - d["simulated_price_prophet"] for d in detail])
    delta_ml_vs_actual = np.array([d["simulated_price_ml"] - d["actual_price"] for d in detail])
    delta_prophet_vs_actual = np.array([d["simulated_price_prophet"] - d["actual_price"] for d in detail])

    return {
        "hotel_id": hotel_id,
        "test_date_range": {
            "start": test_df["date"].min().date().isoformat(),
            "end": test_df["date"].max().date().isoformat(),
        },
        "booking_count": len(detail),
        "actual_revenue": round(actual_total, 2),
        "simulated_revenue_prophet": round(prophet_total, 2),
        "simulated_revenue_ml": round(ml_total, 2),
        "deltas": {
            "ml_vs_prophet": _bootstrap_total(delta_ml_vs_prophet),
            "ml_vs_actual": _bootstrap_total(delta_ml_vs_actual),
            "prophet_vs_actual": _bootstrap_total(delta_prophet_vs_actual),
        },
        "assumptions": [
            "actual_revenue is what the synthetic generator's own ad hoc weekend/season pricing produced - not a no-pricing-strategy baseline.",
            "simulated_revenue_* assumes demand would be unchanged by the recommended price. Neither model estimates real price elasticity - the booking data has no record of declined or counterfactual prices to learn one from, so that effect is deliberately not claimed.",
            "predicted_occupancy for every simulated price comes from a model trained only on data strictly before this test window, and current_occupancy uses only the day before each booking was made - never information unavailable at the time of that pricing decision.",
            "ml_vs_prophet is the most reliable of these three comparisons: identical pricing formula, identical real bookings, only the forecaster differs.",
        ],
        "per_booking_detail": detail,
    }

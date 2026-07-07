"""XGBoost challenger to the Prophet forecaster in forecasting_service.py.

Same target as Prophet (daily occupancy_rate) so the two are directly
comparable - see backtest_service.py for the head-to-head evaluation. The
architectural difference is deliberate: this model is trained ONCE, POOLED
across every hotel's history (not one model per hotel like Prophet), because
after the 2-year reseed each hotel only has ~600 training days - pooling
gives the tree model more rows to find weekday/seasonal structure in, and
lets it share patterns across hotels. It's still evaluated per-hotel for a
fair comparison against Prophet.

Uses XGBoost's native Booster/DMatrix API rather than the sklearn-compatible
XGBRegressor wrapper - the wrapper imports scikit-learn at construction time
even though it never calls into it for anything this project needs, and
pulling in a whole extra dependency for that felt worse than the extra few
lines of native-API code.

Unlike Prophet, this model uses lag/rolling occupancy features, which means
forecasting N days into the genuine future is a recursive process: day 2's
lag_1 feature is day 1's PREDICTED occupancy, since day 1's real occupancy
doesn't exist yet. forecast_future() walks forward one day at a time and
feeds each prediction back in as if it were the newest known day.
"""

from datetime import date

import holidays
import pandas as pd
import xgboost as xgb
from sqlalchemy.orm import Session

from app.models.hotel import DailyMetrics, Hotel
from app.services.pricing_engine import PEAK_MONTHS

HOLIDAY_MONTHS = {12, 4, 10}
MIN_HISTORY_DAYS = 14  # longest lookback used by any lag/rolling feature
RECENT_WINDOW_FOR_FORECAST = 30  # trailing days pulled to seed a live forecast

XGB_PARAMS = {
    "max_depth": 4,
    "eta": 0.1,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "objective": "reg:squarederror",
    "seed": 42,  # subsample/colsample_bytree are both randomized internally;
    # without a fixed seed, re-running the same backtest would silently
    # produce different numbers each time.
}
NUM_BOOST_ROUND = 200
# Deliberately not tuned against any held-out set: with ~600 days per hotel,
# carving out a third validation split (or using the test set for early
# stopping - which is the same mistake in disguise) would shrink an already
# small dataset into noise. These are plain, literature-typical values.


def _calendar_features(dates: pd.Series, india_holidays: holidays.HolidayBase) -> pd.DataFrame:
    dow = dates.dt.dayofweek
    month = dates.dt.month
    return pd.DataFrame({
        "day_of_week": dow,
        "is_weekend": dow.isin([4, 5]).astype(int),
        "month": month,
        "is_peak_season": month.isin(PEAK_MONTHS).astype(int),
        "is_holiday_season": month.isin(HOLIDAY_MONTHS).astype(int),
        "is_public_holiday": dates.dt.date.isin(india_holidays).astype(int),
    })


class MLDemandForecaster:
    def __init__(self, db: Session):
        self.db = db
        self.booster: xgb.Booster | None = None
        self.feature_columns: list[str] | None = None
        self.hotel_ids: list[int] | None = None
        # Wide static range so both the 2-year history and any future
        # forecast window fall safely inside it without recomputing.
        self.india_holidays = holidays.India(years=range(2023, 2031))

    def build_feature_frame(self) -> pd.DataFrame:
        """Pooled, fully-engineered feature frame across every hotel's
        complete daily_metrics history. Lag/rolling features are computed
        per-hotel on the FULL chronological series here, before any
        train/test split - backtest_service.py splits this frame by date
        afterward, so the split never influences how these features were
        computed in the first place."""
        rows = (
            self.db.query(
                DailyMetrics.hotel_id,
                DailyMetrics.date,
                DailyMetrics.occupancy_rate,
                DailyMetrics.booking_count,
                DailyMetrics.cancellation_count,
            )
            .order_by(DailyMetrics.hotel_id, DailyMetrics.date)
            .all()
        )
        df = pd.DataFrame(
            rows, columns=["hotel_id", "date", "occupancy_rate", "booking_count", "cancellation_count"]
        )
        df["date"] = pd.to_datetime(df["date"])

        hotels = self.db.query(Hotel.id, Hotel.total_rooms, Hotel.star_rating).all()
        hotel_df = pd.DataFrame(hotels, columns=["hotel_id", "total_rooms", "star_rating"])
        df = df.merge(hotel_df, on="hotel_id", how="left")

        df = df.sort_values(["hotel_id", "date"]).reset_index(drop=True)
        df = pd.concat([df, _calendar_features(df["date"], self.india_holidays)], axis=1)

        lagged = df.groupby("hotel_id", group_keys=False)[
            ["date", "occupancy_rate", "booking_count", "cancellation_count"]
        ].apply(self._add_lagged_features)
        df = df.join(lagged[[c for c in lagged.columns if c not in df.columns]])

        self.hotel_ids = sorted(df["hotel_id"].unique().tolist())
        for hid in self.hotel_ids:
            df[f"hotel_{hid}"] = (df["hotel_id"] == hid).astype(int)

        required = ["lag_1", "lag_7", "lag_14", "rolling_mean_7", "rolling_mean_14", "rolling_std_7"]
        df = df.dropna(subset=required).reset_index(drop=True)
        return df

    @staticmethod
    def _add_lagged_features(group: pd.DataFrame) -> pd.DataFrame:
        group = group.sort_values("date").copy()
        occ = group["occupancy_rate"]
        # shift(1) BEFORE rolling(): "today"'s features must only ever see
        # days strictly before "today". shifted[T] = occupancy[T-1], so
        # shifted.rolling(7) at T averages occupancy[T-7 .. T-1] - the
        # trailing 7 days, excluding T itself.
        shifted = occ.shift(1)
        group["lag_1"] = shifted
        group["lag_7"] = occ.shift(7)
        group["lag_14"] = occ.shift(14)
        group["rolling_mean_7"] = shifted.rolling(7).mean()
        group["rolling_mean_14"] = shifted.rolling(14).mean()
        group["rolling_std_7"] = shifted.rolling(7).std()
        group["booking_count_lag_1"] = group["booking_count"].shift(1)
        group["cancellation_count_lag_1"] = group["cancellation_count"].shift(1)
        return group

    def _feature_columns_for(self, df: pd.DataFrame) -> list[str]:
        base = [
            "day_of_week", "is_weekend", "month", "is_peak_season", "is_holiday_season", "is_public_holiday",
            "lag_1", "lag_7", "lag_14", "rolling_mean_7", "rolling_mean_14", "rolling_std_7",
            "booking_count_lag_1", "cancellation_count_lag_1",
            "total_rooms", "star_rating",
        ]
        # Match the one-hot "hotel_<id>" columns specifically - a plain
        # startswith("hotel_") also matches the raw "hotel_id" column itself,
        # which would silently feed an unordered categorical into the model
        # as if it were a meaningful number.
        hotel_cols = [c for c in df.columns if c.startswith("hotel_") and c.split("_", 1)[1].isdigit()]
        return base + sorted(hotel_cols)

    def train(self, train_df: pd.DataFrame) -> xgb.Booster:
        self.feature_columns = self._feature_columns_for(train_df)
        dtrain = xgb.DMatrix(train_df[self.feature_columns], label=train_df["occupancy_rate"])
        self.booster = xgb.train(XGB_PARAMS, dtrain, num_boost_round=NUM_BOOST_ROUND)
        return self.booster

    def predict(self, feature_df: pd.DataFrame) -> pd.Series:
        """Predict for rows that already carry real, precomputed features
        (e.g. a historical held-out test set)."""
        if self.booster is None or self.feature_columns is None:
            raise ValueError("Model has not been trained yet - call train() first.")
        dmat = xgb.DMatrix(feature_df[self.feature_columns])
        preds = self.booster.predict(dmat)
        return pd.Series(preds, index=feature_df.index).clip(0, 100)

    def forecast_future(self, hotel_id: int, days_ahead: int = 30) -> pd.DataFrame:
        """Recursive multi-day-ahead forecast for genuinely unseen future
        dates, for the live /ml/predict endpoint. Mirrors the response shape
        callers get from DemandForecaster.forecast() (a ds/yhat/yhat_lower/
        yhat_upper-shaped frame), even though this model has no native
        uncertainty interval - see get_forecast_summary for how bounds are
        approximated."""
        if self.booster is None or self.feature_columns is None:
            raise ValueError("Model has not been trained yet - call train() first.")

        hotel = self.db.query(Hotel).filter(Hotel.id == hotel_id).first()
        if not hotel:
            raise ValueError(f"Hotel {hotel_id} does not exist")

        recent = (
            self.db.query(
                DailyMetrics.date, DailyMetrics.occupancy_rate,
                DailyMetrics.booking_count, DailyMetrics.cancellation_count,
            )
            .filter(DailyMetrics.hotel_id == hotel_id)
            .order_by(DailyMetrics.date.desc())
            .limit(RECENT_WINDOW_FOR_FORECAST)
            .all()
        )
        if len(recent) < MIN_HISTORY_DAYS:
            raise ValueError(
                f"Only {len(recent)} day(s) of daily_metrics found for hotel {hotel_id}; "
                f"need at least {MIN_HISTORY_DAYS}."
            )

        working = pd.DataFrame(recent, columns=["date", "occupancy_rate", "booking_count", "cancellation_count"])
        working["date"] = pd.to_datetime(working["date"]).dt.tz_localize(None)
        working = working.sort_values("date").reset_index(drop=True)
        last_date = working["date"].max()

        predictions = []
        for step in range(1, days_ahead + 1):
            target_date = last_date + pd.Timedelta(days=step)
            row = self._build_future_row(hotel, target_date, working)
            pred = float(self.booster.predict(xgb.DMatrix(row[self.feature_columns]))[0])
            pred = max(0.0, min(100.0, pred))
            predictions.append({"ds": target_date, "yhat": pred})

            # Recent booking/cancellation counts aren't knowable this far
            # ahead, so future steps hold them at their trailing average
            # rather than pretending to forecast them separately.
            working = pd.concat([working, pd.DataFrame([{
                "date": target_date,
                "occupancy_rate": pred,
                "booking_count": working["booking_count"].tail(7).mean(),
                "cancellation_count": working["cancellation_count"].tail(7).mean(),
            }])], ignore_index=True)

        result = pd.DataFrame(predictions)
        # No native prediction interval (unlike Prophet's Bayesian yhat_lower/
        # upper) - approximate a band from the recent occupancy volatility so
        # the frontend's ForecastChart, which expects both bounds, still has
        # something honest to plot. Widening with sqrt(step) reflects
        # compounding uncertainty the further out the recursive forecast goes.
        recent_std = working["occupancy_rate"].tail(30).std() or 0.0
        steps = pd.Series(range(1, len(result) + 1), index=result.index)
        spread = recent_std * steps.pow(0.5)
        result["yhat_lower"] = (result["yhat"] - spread).clip(lower=0)
        result["yhat_upper"] = (result["yhat"] + spread).clip(upper=100)
        return result

    def _build_future_row(self, hotel: Hotel, target_date: pd.Timestamp, working: pd.DataFrame) -> pd.DataFrame:
        occ = working["occupancy_rate"]
        bk = working["booking_count"]
        cc = working["cancellation_count"]

        cal = _calendar_features(pd.Series([target_date]), self.india_holidays).iloc[0]
        row = {
            **cal.to_dict(),
            "lag_1": occ.iloc[-1],
            "lag_7": occ.iloc[-7] if len(occ) >= 7 else occ.iloc[0],
            "lag_14": occ.iloc[-14] if len(occ) >= 14 else occ.iloc[0],
            "rolling_mean_7": occ.tail(7).mean(),
            "rolling_mean_14": occ.tail(14).mean(),
            "rolling_std_7": occ.tail(7).std() if len(occ) >= 2 else 0.0,
            "booking_count_lag_1": bk.iloc[-1],
            "cancellation_count_lag_1": cc.iloc[-1],
            "total_rooms": hotel.total_rooms,
            "star_rating": hotel.star_rating,
        }
        for hid in self.hotel_ids or []:
            row[f"hotel_{hid}"] = 1 if hotel.id == hid else 0
        return pd.DataFrame([row])

    def get_forecast_summary(self, forecast_df: pd.DataFrame) -> dict:
        """Same shape as DemandForecaster.get_forecast_summary, so the
        frontend's existing ForecastChart can render this model's output
        unmodified."""
        predictions = [
            {
                "date": row.ds.date().isoformat(),
                "predicted_occupancy": round(row.yhat, 2),
                "lower_bound": round(row.yhat_lower, 2),
                "upper_bound": round(row.yhat_upper, 2),
            }
            for row in forecast_df.itertuples()
        ]
        return {
            "summary": {
                "mean_occupancy": round(forecast_df["yhat"].mean(), 2),
                "min_occupancy": round(forecast_df["yhat"].min(), 2),
                "max_occupancy": round(forecast_df["yhat"].max(), 2),
                "median_occupancy": round(forecast_df["yhat"].median(), 2),
                "days_forecasted": len(forecast_df),
            },
            "predictions": predictions,
        }

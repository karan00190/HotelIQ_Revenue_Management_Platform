"""Prophet wrapper for hotel occupancy demand forecasting.

DemandForecaster is used per-request, not persisted between calls: every API
endpoint that needs a forecast calls prepare_training_data -> train ->
forecast in sequence and throws the fitted model away afterward. This
matches architecture.md's endpoint descriptions (both /predict and
/pricing-recommendation "train the model" as part of serving the request)
and avoids the complexity of pickling/caching a model across requests.
"""

from datetime import date

import pandas as pd
from prophet import Prophet
from sqlalchemy.orm import Session

from app.models.hotel import DailyMetrics

MIN_TRAINING_DAYS = 30
DEFAULT_HISTORY_DAYS = 180


class DemandForecaster:
    def __init__(self, db: Session):
        self.db = db
        self.model: Prophet | None = None
        self.last_training_date: pd.Timestamp | None = None

    def prepare_training_data(self, hotel_id: int, days_back: int = DEFAULT_HISTORY_DAYS) -> pd.DataFrame:
        rows = (
            self.db.query(DailyMetrics.date, DailyMetrics.occupancy_rate)
            .filter(DailyMetrics.hotel_id == hotel_id)
            .order_by(DailyMetrics.date.desc())
            .limit(days_back)
            .all()
        )
        if len(rows) < MIN_TRAINING_DAYS:
            raise ValueError(
                f"Only {len(rows)} day(s) of daily_metrics found for hotel {hotel_id}; "
                f"need at least {MIN_TRAINING_DAYS}. Run POST /ingestion/calculate-metrics first."
            )

        df = pd.DataFrame(rows, columns=["ds", "y"]).sort_values("ds").reset_index(drop=True)
        self.last_training_date = df["ds"].max()
        return df

    def train(self, training_df: pd.DataFrame) -> Prophet:
        # daily_seasonality is deliberately off: it models intra-day patterns,
        # which need sub-day timestamps we don't have (one row per calendar
        # day). The "daily (weekday/weekend)" pattern architecture.md refers
        # to is actually a day-of-week effect, which weekly_seasonality plus
        # the custom "weekend" seasonality below both capture.
        model = Prophet(
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=True,
            changepoint_prior_scale=0.05,
        )
        model.add_seasonality(name="weekend", period=7, fourier_order=3)
        model.fit(training_df)
        self.model = model
        return model

    def forecast(self, days_ahead: int = 30) -> pd.DataFrame:
        if self.model is None or self.last_training_date is None:
            raise ValueError("Model has not been trained yet — call train() first.")

        future = self.model.make_future_dataframe(periods=days_ahead)
        prediction = self.model.predict(future)

        for col in ("yhat", "yhat_lower", "yhat_upper"):
            prediction[col] = prediction[col].clip(0, 100)

        future_only = prediction[prediction["ds"] > self.last_training_date]
        return future_only[["ds", "yhat", "yhat_lower", "yhat_upper"]].reset_index(drop=True)

    def get_forecast_summary(self, forecast_df: pd.DataFrame) -> dict:
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

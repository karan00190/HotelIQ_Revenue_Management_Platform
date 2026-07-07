from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.hotel import DailyMetrics, Hotel
from app.services.forecasting_service import DemandForecaster
from app.services.pricing_engine import PEAK_MONTHS, DynamicPricingEngine

router = APIRouter(prefix="/forecast", tags=["Forecasting"])

MAX_DAYS_AHEAD = 90


@router.post("/train/{hotel_id}")
def train_model(hotel_id: int, days_back: int = 180, db: Session = Depends(get_db)):
    """Trains a Prophet model on a hotel's occupancy history and reports data stats.

    This does not persist the model — /predict and /pricing-recommendation
    each train their own model fresh. This endpoint exists to validate that
    a hotel has enough history and to report what the training data looks
    like, before committing to a full forecast call.
    """
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hotel not found")

    forecaster = DemandForecaster(db)
    try:
        training_df = forecaster.prepare_training_data(hotel_id, days_back=days_back)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    forecaster.train(training_df)

    return {
        "hotel_id": hotel_id,
        "status": "trained",
        "training_days": len(training_df),
        "date_range": {
            "start": training_df["ds"].min().date().isoformat(),
            "end": training_df["ds"].max().date().isoformat(),
        },
        "occupancy_stats": {
            "mean": round(training_df["y"].mean(), 2),
            "min": round(training_df["y"].min(), 2),
            "max": round(training_df["y"].max(), 2),
        },
    }


@router.get("/predict/{hotel_id}")
def predict(
    hotel_id: int,
    days_ahead: int = 30,
    days_back: int = 180,
    db: Session = Depends(get_db),
):
    """Trains fresh and returns a days_ahead forecast with confidence intervals."""
    if days_ahead < 1 or days_ahead > MAX_DAYS_AHEAD:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"days_ahead must be between 1 and {MAX_DAYS_AHEAD}",
        )
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hotel not found")

    forecaster = DemandForecaster(db)
    try:
        training_df = forecaster.prepare_training_data(hotel_id, days_back=days_back)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    forecaster.train(training_df)
    forecast_df = forecaster.forecast(days_ahead=days_ahead)

    result = forecaster.get_forecast_summary(forecast_df)
    result["hotel_id"] = hotel_id
    return result


@router.get("/pricing-recommendation/{hotel_id}")
def pricing_recommendation(
    hotel_id: int,
    target_date: date,
    base_price: float,
    db: Session = Depends(get_db),
):
    """The full pipeline: forecast demand for target_date, then recommend a price."""
    if base_price <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="base_price must be positive")

    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hotel not found")

    forecaster = DemandForecaster(db)
    try:
        training_df = forecaster.prepare_training_data(hotel_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    last_training_date = training_df["ds"].max().date()
    days_ahead = (target_date - last_training_date).days
    if days_ahead <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"target_date must be after {last_training_date.isoformat()} (the last date with data)",
        )
    if days_ahead > MAX_DAYS_AHEAD:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"target_date is too far ahead (max {MAX_DAYS_AHEAD} days past {last_training_date.isoformat()})",
        )

    forecaster.train(training_df)
    forecast_df = forecaster.forecast(days_ahead=days_ahead)

    target_row = forecast_df[forecast_df["ds"].dt.date == target_date]
    if target_row.empty:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Forecast did not include the target_date",
        )
    predicted_occupancy = float(target_row.iloc[0]["yhat"])

    is_weekend = target_date.weekday() in (4, 5)
    is_peak_season = target_date.month in PEAK_MONTHS
    lead_time_days = (target_date - date.today()).days

    latest_metric = (
        db.query(DailyMetrics)
        .filter(DailyMetrics.hotel_id == hotel_id)
        .order_by(DailyMetrics.date.desc())
        .first()
    )
    current_occupancy = latest_metric.occupancy_rate if latest_metric else 0.0

    engine = DynamicPricingEngine()
    recommendation = engine.get_pricing_recommendation(
        base_price=base_price,
        predicted_occupancy=predicted_occupancy,
        current_occupancy=current_occupancy,
        is_weekend=is_weekend,
        is_peak_season=is_peak_season,
        lead_time_days=lead_time_days,
    )
    recommendation["hotel_id"] = hotel_id
    recommendation["target_date"] = target_date.isoformat()
    return recommendation

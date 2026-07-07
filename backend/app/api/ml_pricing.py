from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.hotel import Hotel
from app.services.backtest_service import run_forecast_comparison, run_revenue_backtest
from app.services.ml_forecasting_service import MLDemandForecaster

router = APIRouter(prefix="/ml", tags=["ML Challenger"])

MAX_DAYS_AHEAD = 90


def _get_hotel_or_404(db: Session, hotel_id: int) -> Hotel:
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hotel not found")
    return hotel


@router.get("/predict/{hotel_id}")
def predict(hotel_id: int, days_ahead: int = 30, db: Session = Depends(get_db)):
    """XGBoost's live forecast - same response shape as GET /forecast/predict,
    so the frontend can plot both on the same chart component. Trains on the
    full available pooled history (not a train/test split - that's only for
    /compare's accuracy evaluation, not for getting the best real forecast)."""
    if days_ahead < 1 or days_ahead > MAX_DAYS_AHEAD:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"days_ahead must be between 1 and {MAX_DAYS_AHEAD}",
        )
    _get_hotel_or_404(db, hotel_id)

    forecaster = MLDemandForecaster(db)
    full_df = forecaster.build_feature_frame()
    forecaster.train(full_df)
    forecast_df = forecaster.forecast_future(hotel_id, days_ahead=days_ahead)

    result = forecaster.get_forecast_summary(forecast_df)
    result["hotel_id"] = hotel_id
    return result


@router.get("/compare/{hotel_id}")
def compare(hotel_id: int, db: Session = Depends(get_db)):
    """Naive/Prophet/XGBoost forecast accuracy, evaluated on one identical
    held-out window per hotel."""
    _get_hotel_or_404(db, hotel_id)
    try:
        return run_forecast_comparison(db, hotel_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/backtest/{hotel_id}")
def backtest(hotel_id: int, db: Session = Depends(get_db)):
    """The revenue what-if simulation: real held-out bookings, repriced by
    the existing pricing engine using each model's forecast instead of the
    generator's own historical pricing."""
    _get_hotel_or_404(db, hotel_id)
    try:
        return run_revenue_backtest(db, hotel_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

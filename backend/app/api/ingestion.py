import io
import os
from datetime import date, datetime
from typing import Optional

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal, get_db
from app.services.etl_pipeline import ETLPipeline
from app.utils.metrics_calculator import calculate_date_range_metrics, recalculate_all_metrics

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])

UPLOAD_DIR = os.path.join("data", "uploads")


@router.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Accept a CSV, run the full ETL pipeline, and return the complete result."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .csv files are accepted",
        )

    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not parse CSV: {exc}",
        )

    # Save a timestamped copy for debugging/audit before processing.
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    saved_path = os.path.join(UPLOAD_DIR, f"{timestamp}_{file.filename}")
    with open(saved_path, "wb") as f:
        f.write(contents)

    pipeline = ETLPipeline(db)
    result = pipeline.run_full_pipeline(source="csv", file_path=saved_path)
    result["filename"] = file.filename
    result["saved_as"] = saved_path
    return result


@router.post("/process-existing-data")
def process_existing_data(
    hotel_id: Optional[int] = None,
    start_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """Re-run existing DB records through the pipeline (validation + features).

    Because inserts are idempotent, already-present rows are skipped; this is
    mainly a way to re-validate history and regenerate the feature summary.
    """
    pipeline = ETLPipeline(db)
    result = pipeline.run_full_pipeline(
        source="database", hotel_id=hotel_id, start_date=start_date
    )
    return result


@router.get("/data-quality-check")
def data_quality_check(db: Session = Depends(get_db)):
    """Validate all bookings currently in the database. Read-only."""
    pipeline = ETLPipeline(db)
    df = pipeline.extract_from_database()
    if df.empty:
        return {"message": "No bookings in database", "is_valid": True}
    report = pipeline.validator.validate_dataframe(df)
    return report.to_dict()


@router.get("/feature-summary")
def feature_summary(sample_size: int = 50, db: Session = Depends(get_db)):
    """Run feature engineering on a sample and report the features created."""
    pipeline = ETLPipeline(db)
    df = pipeline.extract_from_database(limit=sample_size)
    if df.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No bookings available to summarize",
        )
    from app.models.hotel import Hotel

    hotel_rooms = {h.id: h.total_rooms for h in db.query(Hotel).all()}
    cleaned = pipeline.validator.clean_dataframe(df)
    featured = pipeline.feature_engineer.create_all_features(cleaned, hotel_rooms)
    summary = pipeline.feature_engineer.get_feature_summary(featured)

    # Attach a couple of sample rows (feature columns only) for illustration.
    feature_cols = [
        c for cols in summary["feature_names"].values() for c in cols
    ]
    sample_rows = featured[feature_cols].head(3).to_dict(orient="records")
    summary["sample_rows"] = _jsonsafe(sample_rows)
    return summary


@router.post("/calculate-metrics")
def calculate_metrics(
    hotel_id: int,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
):
    """Populate daily_metrics for one hotel over a date range."""
    metrics = calculate_date_range_metrics(db, hotel_id=hotel_id, start_date=start_date, end_date=end_date)
    return {
        "hotel_id": hotel_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "metrics_calculated": len(metrics),
    }


def _run_recalculate_all_metrics():
    # Background tasks run after the response is sent, and the request's own
    # `db` session may already be torn down by then — open a fresh session
    # scoped to just this task instead of reusing the request's session.
    session = SessionLocal()
    try:
        recalculate_all_metrics(session)
    finally:
        session.close()


@router.post("/recalculate-all-metrics")
def recalculate_all_metrics_endpoint(background_tasks: BackgroundTasks):
    """Schedule a full metrics recalculation across all hotels and history."""
    background_tasks.add_task(_run_recalculate_all_metrics)
    return {"status": "started", "message": "Full metrics recalculation running in the background"}


def _jsonsafe(rows):
    """Make sample rows JSON-serializable (NaN/NaT -> None, Timestamp -> str)."""
    safe = []
    for row in rows:
        clean = {}
        for k, v in row.items():
            if isinstance(v, pd.Timestamp):
                clean[k] = str(v)
            elif pd.isna(v):
                clean[k] = None
            else:
                clean[k] = v
        safe.append(clean)
    return safe

"""ETL pipeline: orchestrates Extract -> Transform -> Load.

The pipeline is the single coordinator that ties together the validator
(Module 5) and the feature engineer (Module 6). It is deliberately safe:
- validation failures stop the run before any write happens
- loads happen in batches, each committed independently
- inserts are idempotent, so re-running the same data creates no duplicates
"""

import time
from datetime import date, datetime
from typing import Optional

import pandas as pd
from sqlalchemy.orm import Session

from app.models.hotel import Booking, Hotel
from app.services.data_validator import BookingDataValidator
from app.services.feature_engineering import FeatureEngineer

# The bookings table's own columns (id/booking_date are auto-populated). The
# transform step produces ~24 extra feature columns; those are used for
# validation/ML but are NOT persisted — only these land in the table.
BOOKING_COLUMNS = [
    "hotel_id", "room_id", "check_in_date", "check_out_date", "guest_name",
    "guest_email", "num_guests", "booking_price", "base_price",
    "booking_date", "booking_source", "status",
]

BATCH_SIZE = 100


def _clean_value(value):
    """Convert pandas NaN/NaT to None and Timestamps to python datetime."""
    if value is None or (not isinstance(value, (list, dict)) and pd.isna(value)):
        return None
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    return value


class ETLPipeline:
    def __init__(self, db: Session):
        self.db = db
        self.validator = BookingDataValidator()
        self.feature_engineer = FeatureEngineer()

    # ---- Extract ----

    def extract_from_csv(self, file_path: str) -> pd.DataFrame:
        df = pd.read_csv(file_path)
        return df

    def extract_from_database(
        self,
        hotel_id: Optional[int] = None,
        start_date: Optional[date] = None,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        query = self.db.query(Booking)
        if hotel_id is not None:
            query = query.filter(Booking.hotel_id == hotel_id)
        if start_date is not None:
            query = query.filter(Booking.check_in_date >= start_date)
        if limit is not None:
            query = query.limit(limit)

        rows = query.all()
        records = [
            {
                "hotel_id": b.hotel_id, "room_id": b.room_id,
                "check_in_date": b.check_in_date, "check_out_date": b.check_out_date,
                "guest_name": b.guest_name, "guest_email": b.guest_email,
                "num_guests": b.num_guests, "booking_price": b.booking_price,
                "base_price": b.base_price, "booking_date": b.booking_date,
                "booking_source": b.booking_source, "status": b.status,
            }
            for b in rows
        ]
        return pd.DataFrame(records)

    # ---- Transform ----

    def transform(self, df: pd.DataFrame):
        """Validate, then clean + feature-engineer. Returns (report, df)."""
        report = self.validator.validate_dataframe(df)
        if not report.is_valid():
            return report, df  # unmodified; caller must stop

        cleaned = self.validator.clean_dataframe(df)
        hotel_rooms = {h.id: h.total_rooms for h in self.db.query(Hotel).all()}
        featured = self.feature_engineer.create_all_features(cleaned, hotel_rooms)
        return report, featured

    # ---- Load ----

    def load_to_database(self, df: pd.DataFrame) -> dict:
        cols = [c for c in BOOKING_COLUMNS if c in df.columns]
        loaded = skipped = errors = 0
        error_messages: list[str] = []

        records = df[cols].to_dict(orient="records")
        for batch_start in range(0, len(records), BATCH_SIZE):
            batch = records[batch_start:batch_start + BATCH_SIZE]
            try:
                for raw in batch:
                    row = {k: _clean_value(v) for k, v in raw.items()}

                    exists = (
                        self.db.query(Booking)
                        .filter(
                            Booking.hotel_id == row.get("hotel_id"),
                            Booking.room_id == row.get("room_id"),
                            Booking.check_in_date == row.get("check_in_date"),
                        )
                        .first()
                    )
                    if exists:
                        skipped += 1
                        continue

                    self.db.add(Booking(**row))
                    loaded += 1
                self.db.commit()
            except Exception as exc:  # noqa: BLE001 - report, don't crash the run
                self.db.rollback()
                errors += len(batch)
                loaded -= len(batch)  # this batch did not actually land
                error_messages.append(str(exc))

        return {
            "loaded": max(loaded, 0),
            "skipped": skipped,
            "errors": errors,
            "error_messages": error_messages,
        }

    # ---- Orchestration ----

    def run_full_pipeline(
        self,
        source: str = "csv",
        file_path: Optional[str] = None,
        hotel_id: Optional[int] = None,
        start_date: Optional[date] = None,
    ) -> dict:
        started = time.time()

        if source == "csv":
            if not file_path:
                raise ValueError("file_path is required when source='csv'")
            df = self.extract_from_csv(file_path)
        elif source == "database":
            df = self.extract_from_database(hotel_id=hotel_id, start_date=start_date)
        else:
            raise ValueError(f"Unknown source: {source}")

        report, transformed = self.transform(df)
        if not report.is_valid():
            return {
                "success": False,
                "duration_seconds": round(time.time() - started, 3),
                "source": source,
                "records_extracted": int(len(df)),
                "validation": report.to_dict(),
                "load": None,
                "feature_summary": None,
            }

        load_stats = self.load_to_database(transformed)
        feature_summary = self.feature_engineer.get_feature_summary(transformed)

        return {
            "success": True,
            "duration_seconds": round(time.time() - started, 3),
            "source": source,
            "records_extracted": int(len(df)),
            "validation": report.to_dict(),
            "load": load_stats,
            "feature_summary": feature_summary,
        }

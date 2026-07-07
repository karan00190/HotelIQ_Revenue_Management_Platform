"""Data quality gate for incoming booking data.

Nothing enters the database without passing through BookingDataValidator.
The validator never mutates the input; it inspects a DataFrame and returns a
DataQualityReport. Cleaning is a separate, explicit step (clean_dataframe).
"""

import pandas as pd

REQUIRED_COLUMNS = [
    "hotel_id",
    "room_id",
    "check_in_date",
    "check_out_date",
    "guest_name",
    "num_guests",
    "booking_price",
    "base_price",
]

OPTIONAL_DEFAULTS = {
    "guest_email": None,
    "booking_source": "direct",
    "status": "confirmed",
}


class DataQualityReport:
    """Accumulates validation results. Valid only when there are zero errors."""

    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []
        self.stats: dict = {}

    def add_error(self, message: str):
        self.errors.append(message)

    def add_warning(self, message: str):
        self.warnings.append(message)

    def add_info(self, message: str):
        self.info.append(message)

    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid(),
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "stats": self.stats,
        }


class BookingDataValidator:
    """Runs nine quality checks against a bookings DataFrame."""

    def validate_dataframe(self, df: pd.DataFrame) -> DataQualityReport:
        report = DataQualityReport()

        # Check 1 - Required columns. Bail out early: every later check assumes
        # these columns exist.
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            report.add_error(f"Missing required columns: {missing}")
            return report
        report.add_info("All required columns present.")

        # Check 2 - Empty DataFrame.
        if len(df) == 0:
            report.add_error("DataFrame is empty; no records to process.")
            return report
        report.add_info(f"Received {len(df)} records.")

        # Check 3 - Null values.
        for col in REQUIRED_COLUMNS:
            null_count = int(df[col].isnull().sum())
            if null_count > 0:
                report.add_error(f"Column '{col}' has {null_count} null value(s).")
        for col, _ in OPTIONAL_DEFAULTS.items():
            if col in df.columns:
                null_count = int(df[col].isnull().sum())
                if null_count > 0:
                    report.add_warning(
                        f"Optional column '{col}' has {null_count} null value(s); "
                        "defaults will be applied during cleaning."
                    )

        # Check 4 - Date type conversion. Work on copies so the input is untouched.
        try:
            check_in = pd.to_datetime(df["check_in_date"], errors="raise")
            check_out = pd.to_datetime(df["check_out_date"], errors="raise")
        except (ValueError, TypeError) as exc:
            report.add_error(f"Date columns could not be parsed: {exc}")
            return report
        report.add_info("Date columns parsed successfully.")

        # Check 5 - Logical date validation.
        bad_dates = int((check_out <= check_in).sum())
        if bad_dates > 0:
            report.add_error(
                f"{bad_dates} row(s) have check_out_date on or before check_in_date."
            )

        # Check 6 - Price validation.
        bad_booking_price = int((df["booking_price"] <= 0).sum())
        bad_base_price = int((df["base_price"] <= 0).sum())
        if bad_booking_price > 0:
            report.add_error(f"{bad_booking_price} row(s) have booking_price <= 0.")
        if bad_base_price > 0:
            report.add_error(f"{bad_base_price} row(s) have base_price <= 0.")

        # Check 7 - Guest count validation.
        bad_guests = int((df["num_guests"] <= 0).sum())
        if bad_guests > 0:
            report.add_error(f"{bad_guests} row(s) have num_guests <= 0.")

        # Check 8 - Duplicate detection (warning only).
        dup_mask = df.duplicated(
            subset=["hotel_id", "room_id", "check_in_date"], keep=False
        )
        dup_count = int(dup_mask.sum())
        if dup_count > 0:
            report.add_warning(
                f"{dup_count} row(s) share a hotel_id/room_id/check_in_date "
                "combination; possible duplicate bookings."
            )

        # Check 9 - Outlier detection (warning only).
        mean = df["booking_price"].mean()
        std = df["booking_price"].std()
        if pd.notna(std) and std > 0:
            threshold = mean + 3 * std
            outliers = int((df["booking_price"] > threshold).sum())
            if outliers > 0:
                report.add_warning(
                    f"{outliers} row(s) have booking_price above 3 standard "
                    f"deviations (> {threshold:.2f}); possible outliers."
                )

        # Dataset statistics (only meaningful once dates parsed).
        report.stats = {
            "total_records": int(len(df)),
            "date_range": {
                "earliest_check_in": str(check_in.min()),
                "latest_check_in": str(check_in.max()),
            },
            "price_range": {
                "min_booking_price": float(df["booking_price"].min()),
                "max_booking_price": float(df["booking_price"].max()),
            },
            "unique_hotels": int(df["hotel_id"].nunique()),
            "unique_rooms": int(df["room_id"].nunique()),
        }

        return report

    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Non-destructive repairs on a copy: types, defaults, whitespace, dups."""
        cleaned = df.copy()

        # Standardize date types.
        cleaned["check_in_date"] = pd.to_datetime(cleaned["check_in_date"])
        cleaned["check_out_date"] = pd.to_datetime(cleaned["check_out_date"])
        if "booking_date" in cleaned.columns:
            cleaned["booking_date"] = pd.to_datetime(
                cleaned["booking_date"], errors="coerce"
            )

        # Fill optional columns with sensible defaults. A None default (e.g.
        # guest_email) means "leave nulls as-is" — pandas fillna(None) is an
        # error, so only fill when there is an actual value to fill with.
        for col, default in OPTIONAL_DEFAULTS.items():
            if col not in cleaned.columns:
                cleaned[col] = default
            elif default is not None:
                cleaned[col] = cleaned[col].fillna(default)

        # Strip whitespace from string columns. Use the .str accessor directly
        # (not astype(str)) so that NaN/None stays null instead of becoming the
        # literal string "nan".
        for col in cleaned.select_dtypes(include="object").columns:
            cleaned[col] = cleaned[col].str.strip()

        # Remove verified duplicates, keeping the first occurrence.
        before = len(cleaned)
        cleaned = cleaned.drop_duplicates(
            subset=["hotel_id", "room_id", "check_in_date"], keep="first"
        ).reset_index(drop=True)
        removed = before - len(cleaned)
        if removed > 0:
            cleaned.attrs["duplicates_removed"] = removed

        return cleaned

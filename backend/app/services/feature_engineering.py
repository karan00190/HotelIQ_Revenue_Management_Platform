"""Feature engineering: turn raw booking rows into ML-ready features.

Every method is a @staticmethod that takes a DataFrame and returns a new
DataFrame with extra columns. All calculations are vectorized Pandas
operations (no per-row Python loops) — see architecture.md section 10 for why
this matters (roughly 15x faster than a loop-based approach).

The class does not touch the database. create_occupancy_features needs to know
each hotel's total room count; the caller (the ETL pipeline) passes that in as
a {hotel_id: total_rooms} mapping so this module stays DB-agnostic.
"""

import pandas as pd

from app.services.pricing_engine import PEAK_MONTHS

# month -> season, encoding the Indian hospitality calendar.
SEASON_MAP = {
    12: "winter", 1: "winter", 2: "winter",
    3: "spring", 4: "spring", 5: "spring",
    6: "monsoon", 7: "monsoon", 8: "monsoon",
    9: "autumn", 10: "autumn", 11: "autumn",
}
HOLIDAY_MONTHS = {12, 4, 10}

# Feature columns grouped by the method that produces them. Used by
# get_feature_summary to report what was created.
FEATURE_COLUMNS = {
    "time": [
        "day_of_week", "day_of_month", "month", "quarter", "year",
        "week_of_year", "is_weekend", "season", "is_peak_season",
        "is_holiday_season",
    ],
    "stay": ["length_of_stay", "stay_category", "lead_time_days", "is_last_minute"],
    "pricing": ["price_per_night", "discount_pct", "price_category"],
    "aggregated": [
        "avg_price_7d", "avg_price_30d", "booking_count_7d",
        "booking_count_30d", "prev_booking_price",
    ],
    "occupancy": ["hotel_total_rooms", "occupancy_rate"],
}


class FeatureEngineer:

    @staticmethod
    def create_time_features(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        check_in = pd.to_datetime(df["check_in_date"])

        df["day_of_week"] = check_in.dt.dayofweek           # Mon=0 .. Sun=6
        df["day_of_month"] = check_in.dt.day
        df["month"] = check_in.dt.month
        df["quarter"] = check_in.dt.quarter
        df["year"] = check_in.dt.year
        df["week_of_year"] = check_in.dt.isocalendar().week.astype(int)
        df["is_weekend"] = check_in.dt.dayofweek.isin([4, 5]).astype(int)  # Fri/Sat
        df["season"] = df["month"].map(SEASON_MAP)
        df["is_peak_season"] = df["month"].isin(PEAK_MONTHS).astype(int)
        df["is_holiday_season"] = df["month"].isin(HOLIDAY_MONTHS).astype(int)
        return df

    @staticmethod
    def create_stay_features(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        check_in = pd.to_datetime(df["check_in_date"])
        check_out = pd.to_datetime(df["check_out_date"])

        df["length_of_stay"] = (check_out - check_in).dt.days
        df["stay_category"] = pd.cut(
            df["length_of_stay"],
            bins=[0, 1, 3, 7, float("inf")],
            labels=["short", "medium", "long", "extended"],
        )

        # lead_time needs booking_date; if it's absent, leave the features null
        # rather than fabricating a value.
        if "booking_date" in df.columns:
            booking_date = pd.to_datetime(df["booking_date"], errors="coerce")
            df["lead_time_days"] = (check_in - booking_date).dt.days
            df["is_last_minute"] = (df["lead_time_days"] <= 3).astype("Int64")
        else:
            df["lead_time_days"] = pd.NA
            df["is_last_minute"] = pd.NA
        return df

    @staticmethod
    def create_pricing_features(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        # Depends on length_of_stay, so create_stay_features must run first.
        los = df["length_of_stay"].replace(0, pd.NA)
        df["price_per_night"] = df["booking_price"] / los
        df["discount_pct"] = (
            (df["base_price"] - df["booking_price"]) / df["base_price"] * 100
        )
        df["price_category"] = pd.cut(
            df["price_per_night"],
            bins=[0, 3000, 6000, 10000, float("inf")],
            labels=["budget", "mid_range", "premium", "luxury"],
        )
        return df

    @staticmethod
    def create_aggregated_features(df: pd.DataFrame) -> pd.DataFrame:
        # Rolling windows are time-based ('7D'/'30D') and computed WITHIN each
        # hotel so one hotel's history never bleeds into another's. Time-based
        # rolling needs a real datetime column, so convert first.
        df = df.copy()
        df["check_in_date"] = pd.to_datetime(df["check_in_date"])
        df = df.sort_values("check_in_date")

        df["avg_price_7d"] = pd.NA
        df["avg_price_30d"] = pd.NA
        df["booking_count_7d"] = pd.NA
        df["booking_count_30d"] = pd.NA

        # Iterate hotels (a handful) and assign back by index — index alignment
        # keeps this correct regardless of row order, and avoids the
        # groupby.apply-on-grouping-columns warning.
        for _, idx in df.groupby("hotel_id").groups.items():
            sub = df.loc[idx].sort_values("check_in_date")
            r7 = sub.rolling("7D", on="check_in_date")["booking_price"]
            r30 = sub.rolling("30D", on="check_in_date")["booking_price"]
            df.loc[sub.index, "avg_price_7d"] = r7.mean()
            df.loc[sub.index, "avg_price_30d"] = r30.mean()
            df.loc[sub.index, "booking_count_7d"] = r7.count()
            df.loc[sub.index, "booking_count_30d"] = r30.count()

        # Lag feature: previous booking price for the same room, in date order.
        df["prev_booking_price"] = df.groupby("room_id")["booking_price"].shift(1)
        return df

    @staticmethod
    def create_occupancy_features(df: pd.DataFrame, hotel_rooms: dict | None = None) -> pd.DataFrame:
        df = df.copy()
        if hotel_rooms:
            df["hotel_total_rooms"] = df["hotel_id"].map(hotel_rooms)
        else:
            df["hotel_total_rooms"] = pd.NA

        # Bookings sharing a hotel_id + check_in_date represent rooms occupied
        # on that date. Divide by the hotel's capacity for an occupancy signal.
        bookings_on_date = df.groupby(["hotel_id", "check_in_date"])["booking_price"].transform("count")
        df["occupancy_rate"] = bookings_on_date / df["hotel_total_rooms"] * 100
        return df

    @staticmethod
    def create_all_features(df: pd.DataFrame, hotel_rooms: dict | None = None) -> pd.DataFrame:
        df = FeatureEngineer.create_time_features(df)
        df = FeatureEngineer.create_stay_features(df)
        df = FeatureEngineer.create_pricing_features(df)
        df = FeatureEngineer.create_aggregated_features(df)
        df = FeatureEngineer.create_occupancy_features(df, hotel_rooms)
        return df

    @staticmethod
    def get_feature_summary(df: pd.DataFrame) -> dict:
        by_category = {
            category: [c for c in cols if c in df.columns]
            for category, cols in FEATURE_COLUMNS.items()
        }
        total = sum(len(cols) for cols in by_category.values())
        return {
            "total_features_created": total,
            "total_columns": len(df.columns),
            "features_by_category": {k: len(v) for k, v in by_category.items()},
            "feature_names": by_category,
        }

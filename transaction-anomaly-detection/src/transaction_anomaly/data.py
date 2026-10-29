"""Strict record contracts, deterministic fixtures, and temporal partitions."""

from pathlib import Path

import numpy as np
import pandas as pd

FEATURES = ["log_amount", "hour", "international", "card_present", "account_age_days"]
RAW_FEATURES = ["amount", "international", "card_present", "account_age_days"]
SCHEMA_VERSION = 1


def validate(frame: pd.DataFrame, labelled: bool = True) -> pd.DataFrame:
    required = ["transaction_id", "timestamp", *RAW_FEATURES]
    if labelled:
        required.append("is_anomaly")
    missing = set(required) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if frame.empty:
        raise ValueError("Dataset must contain records")
    result = frame.copy()
    if result[required].isna().any().any():
        raise ValueError("Required fields cannot be missing")
    ids = result.transaction_id.astype(str)
    if ids.str.strip().eq("").any() or ids.duplicated().any():
        raise ValueError("Transaction IDs must be nonempty and unique")
    result["transaction_id"] = ids
    result["timestamp"] = pd.to_datetime(result.timestamp, utc=True, errors="raise")
    if result.timestamp.isna().any():
        raise ValueError("Timestamps cannot be missing")
    for name in [*RAW_FEATURES, *(["is_anomaly"] if labelled else [])]:
        result[name] = pd.to_numeric(result[name], errors="raise")
        if not np.isfinite(result[name].to_numpy(dtype=float)).all():
            raise ValueError(f"Nonfinite values in {name}")
    for name in ["international", "card_present", *(["is_anomaly"] if labelled else [])]:
        if not result[name].isin([0, 1]).all():
            raise ValueError(f"{name} must be binary")
    if (result.amount <= 0).any() or (result.account_age_days < 0).any():
        raise ValueError("Amount must be positive and account age nonnegative")
    return result


def read_records(path: str | Path, labelled: bool = True) -> pd.DataFrame:
    return validate(pd.read_csv(path, dtype={"transaction_id": str}), labelled)


def features(frame: pd.DataFrame) -> pd.DataFrame:
    """Only allowlisted, decision-time attributes enter models; never IDs/labels."""
    return pd.DataFrame({
        "log_amount": np.log1p(frame.amount),
        "hour": frame.timestamp.dt.hour.astype(float),
        "international": frame.international.astype(float),
        "card_present": frame.card_present.astype(float),
        "account_age_days": frame.account_age_days.astype(float),
    }, index=frame.index)[FEATURES]


def temporal_split(frame: pd.DataFrame, train_end: str, validation_end: str):
    start = pd.to_datetime(train_end, utc=True)
    end = pd.to_datetime(validation_end, utc=True)
    if pd.isna(start) or pd.isna(end) or start >= end:
        raise ValueError("Require finite train_end < validation_end")
    ordered = frame.sort_values(["timestamp", "transaction_id"]).reset_index(drop=True)
    parts = (
        ordered[ordered.timestamp < start].copy(),
        ordered[(ordered.timestamp >= start) & (ordered.timestamp < end)].copy(),
        ordered[ordered.timestamp >= end].copy(),
    )
    for name, part in zip(["train", "validation", "test"], parts):
        if part.empty or part.is_anomaly.nunique() != 2:
            raise ValueError(f"{name} must be nonempty with both outcome classes")
    if not (parts[0].timestamp.max() < parts[1].timestamp.min()
            and parts[1].timestamp.max() < parts[2].timestamp.min()):
        raise ValueError("Temporal overlap detected")
    return parts


def synthetic_records(rows: int = 12000, seed: int = 42) -> pd.DataFrame:
    if rows < 100:
        raise ValueError("Generate at least 100 records")
    rng = np.random.default_rng(seed)
    # Fixed 90-day horizon makes the documented cutoffs independent of row count.
    seconds = np.sort(rng.integers(0, 90 * 86400, rows))
    timestamp = pd.Timestamp("2025-01-01", tz="UTC") + pd.to_timedelta(seconds, unit="s")
    international = rng.binomial(1, 0.13, rows)
    present = rng.binomial(1, 0.72, rows)
    age = rng.exponential(400, rows).round()
    late = seconds >= 72 * 86400
    amount = np.exp(rng.normal(3.5 + late * 0.3, 1.1, rows)).round(2).clip(0.01)
    log_odds = (-6.0 + 0.65 * (np.log1p(amount) - 3.5) + 1.9 * international
                + 1.1 * (1 - present) + 1.1 * (age < 30)
                + 0.7 * (timestamp.hour < 5) + late * 0.4)
    labels = rng.binomial(1, 1 / (1 + np.exp(-log_odds)))
    return pd.DataFrame({
        "transaction_id": [f"syn-{i:08d}" for i in range(rows)],
        "timestamp": timestamp, "amount": amount, "international": international,
        "card_present": present, "account_age_days": age, "is_anomaly": labels,
    })

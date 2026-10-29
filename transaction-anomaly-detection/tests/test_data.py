import numpy as np
import pandas as pd
import pytest

from transaction_anomaly.data import features, synthetic_records, temporal_split, validate


def fixture_records():
    return pd.DataFrame({
        "transaction_id": [f"t{i}" for i in range(12)],
        "timestamp": pd.date_range("2025-01-01", periods=12, tz="UTC"),
        "amount": np.arange(1, 13) * 10.0,
        "international": [0, 1] * 6, "card_present": [1, 0] * 6,
        "account_age_days": [100] * 12, "is_anomaly": [0, 1] * 6,
    })


@pytest.mark.parametrize("column,value", [
    ("amount", -1), ("amount", np.inf), ("international", 2),
    ("account_age_days", -1), ("is_anomaly", None), ("timestamp", "bad"),
])
def test_bad_records_rejected(column, value):
    frame = fixture_records()
    frame[column] = frame[column].astype(object)
    frame.loc[0, column] = value
    with pytest.raises((ValueError, TypeError)):
        validate(frame)


def test_duplicate_ids_rejected():
    frame = fixture_records()
    frame.loc[1, "transaction_id"] = frame.loc[0, "transaction_id"]
    with pytest.raises(ValueError, match="unique"):
        validate(frame)


def test_exact_boundaries_and_order():
    frame = validate(fixture_records().sample(frac=1, random_state=1))
    train, validation, test = temporal_split(frame, "2025-01-05", "2025-01-09")
    assert [len(part) for part in (train, validation, test)] == [4, 4, 4]
    assert validation.timestamp.min() == pd.Timestamp("2025-01-05", tz="UTC")
    assert test.timestamp.min() == pd.Timestamp("2025-01-09", tz="UTC")
    assert set(train.transaction_id).isdisjoint(test.transaction_id)


def test_label_and_unknown_columns_cannot_enter_features():
    frame = validate(fixture_records())
    expected = features(frame)
    frame["is_anomaly"] = 1 - frame.is_anomaly
    frame["future_chargeback"] = 999
    pd.testing.assert_frame_equal(expected, features(frame))


def test_class_degenerate_split_rejected():
    frame = validate(fixture_records())
    frame.loc[:3, "is_anomaly"] = 0
    with pytest.raises(ValueError, match="both outcome"):
        temporal_split(frame, "2025-01-05", "2025-01-09")


def test_synthetic_reproducibility():
    pd.testing.assert_frame_equal(synthetic_records(200, 7), synthetic_records(200, 7))

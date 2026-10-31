"""Contract checks for the original credit-card schema and chronological study."""

import numpy as np
import pandas as pd
import pytest

from transaction_anomaly.creditcard import FEATURES, split_creditcard, validate_creditcard


def records():
    frame = pd.DataFrame({name: np.arange(8, dtype=float) for name in FEATURES})
    frame["Time"] = [0, 1, 10, 10, 11, 20, 21, 22]
    frame["Class"] = [0, 1, 0, 1, 1, 0, 1, 0]
    return frame


def test_time_ties_never_cross_partitions():
    parts = split_creditcard(records(), 10, 20)
    assert parts["train"].Time.max() < parts["validation"].Time.min()
    assert parts["validation"].Time.max() < parts["test"].Time.min()
    assert len(parts["validation"]) == 3


def test_later_predictor_repeat_is_removed_without_using_its_label():
    frame = records()
    frame.loc[7, FEATURES] = frame.loc[0, FEATURES].to_numpy()
    frame.loc[7, "Class"] = 1
    parts = split_creditcard(frame, 10, 20)
    assert len(parts["test"]) == 2
    assert 7 not in parts["test"].index


@pytest.mark.parametrize("column,value", [("Time", -1), ("Amount", -1), ("V2", np.inf), ("Class", 2)])
def test_invalid_original_fields_fail(column, value):
    frame = records()
    frame.loc[0, column] = value
    with pytest.raises(ValueError):
        validate_creditcard(frame)


def test_time_and_label_are_excluded_from_predictors():
    assert "Time" not in FEATURES and "Class" not in FEATURES
    assert len(FEATURES) == 29


def test_invalid_cutoffs_fail():
    with pytest.raises(ValueError, match="finite"):
        split_creditcard(records(), 20, 10)


def test_cli_rejects_checksum_mismatch_before_training(tmp_path):
    from transaction_anomaly.creditcard import main
    data = tmp_path / "input.parquet"
    data.write_bytes(b"not the source")
    output = tmp_path / "results.json"
    with pytest.raises(SystemExit) as exc:
        main(["--data", str(data), "--output", str(output), "--sha256", "0" * 64])
    assert exc.value.code == 2
    assert not output.exists()

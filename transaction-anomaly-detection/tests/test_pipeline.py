import json

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import f1_score

from transaction_anomaly.data import features, validate
from transaction_anomaly.evaluation import drift_report, report, select_threshold
from transaction_anomaly.pipeline import make_model, run_experiment, score_batch
from test_data import fixture_records


def test_threshold_matches_validation_f1_optimum():
    y = np.array([0, 1, 0, 1, 0])
    scores = np.array([0.1, 0.7, 0.4, 0.8, 0.9])
    threshold = select_threshold(y, scores)
    assert f1_score(y, scores >= threshold) == max(f1_score(y, scores >= t) for t in scores)


def test_scaler_fitted_only_on_training_records():
    frame = validate(fixture_records())
    x = features(frame)
    model = make_model(list(x.columns), 42).fit(x.iloc[:8], frame.is_anomaly.iloc[:8])
    before = model.named_steps["features"].named_transformers_["numeric"].mean_.copy()
    x.loc[8:, "log_amount"] = 1e9
    model.predict_proba(x.iloc[8:])
    np.testing.assert_allclose(before, features(frame).iloc[:8].mean())
    np.testing.assert_array_equal(before, model.named_steps["features"].named_transformers_["numeric"].mean_)


def test_reporting_probability_endpoints_and_single_class():
    result = report([0, 1], [0.0, 1.0], 0.5)
    assert result["brier_score"] == 0
    assert sum(b["count"] for b in result["calibration_bins"]) == 2
    assert report([0, 0], [0.1, 0.2], 0.5)["roc_auc"] is None


def test_drift_identical_and_shifted():
    reference = pd.DataFrame({"amount": np.arange(100, dtype=float)})
    assert drift_report(reference, reference)["amount"]["psi"] == 0
    assert drift_report(reference, reference + 1000)["amount"]["review"]


def test_training_scoring_and_no_test_influence(tmp_path):
    frame = fixture_records()
    data = tmp_path / "data.csv"
    frame.to_csv(data, index=False)
    run = tmp_path / "run"
    metrics = run_experiment(data, run, "2025-01-05", "2025-01-09")
    changed = frame.copy()
    changed.loc[8:, "is_anomaly"] = 1 - changed.loc[8:, "is_anomaly"]
    changed.loc[8:, "amount"] *= 1000
    changed.to_csv(data, index=False)
    other = run_experiment(data, tmp_path / "other", "2025-01-05", "2025-01-09")
    assert metrics["selected_model"] == other["selected_model"]
    assert metrics["validation"] == other["validation"]
    batch = tmp_path / "batch.csv"
    frame.drop(columns="is_anomaly").iloc[8:].to_csv(batch, index=False)
    output = tmp_path / "scores.csv"
    score_batch(run / "model.pkl", batch, output)
    scored = pd.read_csv(output)
    selected = metrics["selected_model"]
    assert scored.alert.mean() == metrics["test"][selected]["alert_rate"]
    assert scored.transaction_id.tolist() == frame.transaction_id.iloc[8:].tolist()
    assert json.loads((run / "manifest.json").read_text())["status"] == "complete"
    with pytest.raises(FileExistsError):
        run_experiment(data, run, "2025-01-05", "2025-01-09")
    (run / "model.pkl").write_bytes(b"corrupted")
    with pytest.raises(ValueError, match="checksum"):
        score_batch(run / "model.pkl", batch, tmp_path / "bad.csv")

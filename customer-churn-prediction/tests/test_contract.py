"""Contract tests: real data only, no fake-data fallback."""
from pathlib import Path

import numpy as np
import pytest

from churn.download import DATA_URL
from churn.train import choose_threshold, load_real_data, metrics


def test_download_source_is_pinned():
    assert "d646177d0c23e7dd7cde532ee7a5162c768fe963" in DATA_URL


def test_missing_real_data_fails_closed(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="No synthetic"):
        load_real_data(tmp_path / "missing.csv")


def test_tiny_csv_is_rejected(tmp_path: Path):
    csv = tmp_path / "cell2celltrain.csv"
    csv.write_text("Churn,Usage\nYes,42\nNo,4\n", encoding="utf-8")
    with pytest.raises(ValueError, match="40k"):
        load_real_data(csv)


def test_threshold_selection_uses_validation_scores():
    labels = np.array([0, 1, 0, 1])
    scores = np.array([0.1, 0.9, 0.2, 0.8])
    assert 0.05 <= choose_threshold(labels, scores) <= 0.95


def test_metrics_perfect_ranking():
    result = metrics([0, 1, 0, 1], [0.1, 0.9, 0.2, 0.8], threshold=0.5)
    assert result["f1"] == 1
    assert result["roc_auc"] == 1
    assert result["confusion_matrix"] == [[2, 0], [0, 2]]

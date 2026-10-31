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
    with pytest.raises(ValueError, match="checksum mismatch"):
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


def test_threshold_accepts_lists_and_preserves_tie_rule():
    assert choose_threshold([0, 1], [0.1, 0.9]) == pytest.approx(0.11)


def test_cached_download_rejects_wrong_bytes(tmp_path):
    from churn.download import download
    path = tmp_path / "cached.csv"
    path.write_bytes(b"Churn," + b"x" * 100_000)
    with pytest.raises(ValueError, match="checksum mismatch"):
        download(path)


def test_failed_download_does_not_save_response(tmp_path, monkeypatch):
    import io
    import churn.download as downloader
    monkeypatch.setattr(downloader, "urlopen", lambda *a, **kw: io.BytesIO(b"error page"))
    path = tmp_path / "raw" / "data.csv"
    with pytest.raises(ValueError, match="checksum mismatch"):
        downloader.download(path)
    assert not path.exists()


def test_valid_download_and_cache_share_checksum_check(tmp_path, monkeypatch):
    import hashlib
    import io
    import churn.download as downloader
    content = b"Churn,Usage\nYes,42\nNo,4\n"
    expected = hashlib.sha256(content).hexdigest()
    monkeypatch.setattr(downloader, "DATA_SHA256", expected)
    monkeypatch.setattr(downloader, "urlopen", lambda *a, **kw: io.BytesIO(content))
    path = tmp_path / "raw" / "data.csv"
    assert downloader.download(path) == expected
    assert path.read_bytes() == content
    monkeypatch.setattr(downloader, "urlopen", lambda *a, **kw: pytest.fail("Unexpected download"))
    assert downloader.download(path) == expected


def test_preprocessing_handles_unseen_categories_without_refitting():
    import pandas as pd
    from churn.train import make_preprocessor
    train = pd.DataFrame({"usage": [1., 3., np.nan], "plan": ["a", "b", "a"]})
    validation = pd.DataFrame({"usage": [1000., np.nan], "plan": ["new", "a"]})
    processor = make_preprocessor().fit(train)
    imputer = processor.named_transformers_["num"].named_steps["impute"]
    before = imputer.statistics_.copy()
    transformed = processor.transform(validation)
    assert transformed.shape[0] == 2
    np.testing.assert_array_equal(imputer.statistics_, before)
    assert before[0] == 2.

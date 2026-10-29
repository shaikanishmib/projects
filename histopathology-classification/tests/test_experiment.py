import json

import numpy as np
import pytest
import torch

from histopathology.experiment import run, validate_config
from histopathology.fixtures import create_fixture
from histopathology.models import SmallCNN


@pytest.mark.parametrize("config", [{"epochs": 0}, {"seed": -1}, {"seed": 2**32},
                                    {"learning_rate": float("nan")}, {"image_size": 8},
                                    {"validation_fraction": .6, "test_fraction": .5}, {"typo": 1}])
def test_invalid_config(config):
    with pytest.raises(ValueError):
        validate_config(config)


def test_cnn_outputs_one_logit_per_image():
    torch.manual_seed(0)
    model = SmallCNN()
    logits = model(torch.zeros(2, 3, 32, 32))
    assert logits.shape == (2,)
    assert torch.isfinite(logits).all()
    logits.sum().backward()
    assert model.layers[0].weight.grad is not None


def test_baseline_run_writes_auditable_artifacts_and_safe_coefficients(tmp_path):
    root = tmp_path / "fixture"
    create_fixture(root)
    output = tmp_path / "run"
    run(root / "manifest.csv", root, root / "provenance.json", output,
        {"bootstrap_replicates": 10, "image_size": 32}, "baseline")
    assert json.loads((output / "status.json").read_text())["status"] == "completed"
    splits = json.loads((output / "splits.json").read_text())
    assert len(splits["test"]) == 8
    report = json.loads((output / "metrics.json").read_text())
    assert report["test"]["patient"]["n"] == 4
    assert set(report["test_brightness_stress"]) == {"0.8", "1.2"}
    predictions = json.loads((output / "test_predictions.json").read_text())
    # Check persisted numerical model against actual reported probabilities.
    from histopathology.data import read_manifest
    from histopathology.features import color_features
    samples, _ = read_manifest(root / "manifest.csv", root, root / "provenance.json")
    by_id = {s.image_id: s for s in samples}
    features = color_features(root, [by_id[p["image_id"]] for p in predictions], 32)
    with np.load(output / "baseline.npz", allow_pickle=False) as state:
        logits = ((features - state["mean"]) / state["scale"]) @ state["coef"].T + state["intercept"]
        np.testing.assert_allclose(1 / (1 + np.exp(-logits.ravel())), [p["probability"] for p in predictions])
    with pytest.raises(FileExistsError):
        run(root / "manifest.csv", root, root / "provenance.json", output, {}, "baseline")


def test_cnn_training_checkpoint_and_report_contract(tmp_path):
    root = tmp_path / "fixture"
    create_fixture(root)
    output = tmp_path / "cnn-run"
    run(root / "manifest.csv", root, root / "provenance.json", output,
        {"epochs": 1, "image_size": 16, "batch_size": 16, "bootstrap_replicates": 5}, "cnn")
    history = json.loads((output / "history.json").read_text())
    assert len(history) == 1
    assert np.isfinite(history[0]["validation_patient_log_loss"])
    restored = SmallCNN()
    restored.load_state_dict(torch.load(output / "cnn.pt", map_location="cpu", weights_only=True))
    assert json.loads((output / "status.json").read_text())["status"] == "completed"
    assert json.loads((output / "metrics.json").read_text())["test"]["patient"]["n"] == 4

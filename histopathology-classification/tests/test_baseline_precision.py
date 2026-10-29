"""Persisted baseline parameters must reproduce every reported probability."""

import json

import numpy as np

from histopathology.data import read_manifest
from histopathology.experiment import run
from histopathology.features import color_features
from histopathology.fixtures import create_fixture


def test_saved_baseline_reproduces_validation_and_test_probabilities(tmp_path):
    root = tmp_path / "fixture"
    create_fixture(root)
    output = tmp_path / "run"
    run(root / "manifest.csv", root, root / "provenance.json", output,
        {"bootstrap_replicates": 2, "image_size": 32}, "baseline")
    samples, _ = read_manifest(root / "manifest.csv", root, root / "provenance.json")
    by_id = {sample.image_id: sample for sample in samples}

    with np.load(output / "baseline.npz", allow_pickle=False) as state:
        for partition in ("validation", "test"):
            predictions = json.loads((output / f"{partition}_predictions.json").read_text())
            features = color_features(root, [by_id[p["image_id"]] for p in predictions], 32)
            logits = ((features - state["mean"]) / state["scale"]) @ state["coef"].T + state["intercept"]
            restored = 1 / (1 + np.exp(-logits.ravel()))
            np.testing.assert_allclose(
                restored, [p["probability"] for p in predictions], rtol=1e-12, atol=1e-15,
            )

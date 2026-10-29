"""Local experiment orchestration and auditable, per-run artifacts."""

from __future__ import annotations

import hashlib
import importlib.metadata
import logging
import math
import platform
import random
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .data import read_manifest, split_patients, split_record, write_json
from .evaluation import evaluate
from .features import color_features

LOG = logging.getLogger(__name__)

DEFAULTS = {"seed": 42, "validation_fraction": .2, "test_fraction": .2,
            "image_size": 96, "epochs": 10, "batch_size": 16,
            "learning_rate": .001, "threads": 1, "bootstrap_replicates": 1000}


def validate_config(values: dict) -> dict:
    if set(values) - set(DEFAULTS):
        raise ValueError(f"Unknown configuration keys: {sorted(set(values) - set(DEFAULTS))}")
    config = DEFAULTS | values
    for key in ("seed", "image_size", "epochs", "batch_size", "threads", "bootstrap_replicates"):
        if type(config[key]) is not int or config[key] < (0 if key == "seed" else 1):
            raise ValueError(f"{key} must be an integer in range")
    if not 0 <= config["seed"] < 2**32:
        raise ValueError("seed must fit an unsigned 32-bit integer")
    if config["image_size"] < 16:
        raise ValueError("image_size must be at least 16")
    for key in ("learning_rate", "validation_fraction", "test_fraction"):
        if type(config[key]) not in (int, float) or not math.isfinite(config[key]) or not 0 < config[key] < 1:
            raise ValueError(f"{key} must be finite and between 0 and 1")
    if config["validation_fraction"] + config["test_fraction"] >= 1:
        raise ValueError("Split fractions must sum to less than one")
    return config


def run(manifest: Path, root: Path, provenance: Path, output: Path, values: dict, model_kind: str) -> None:
    if model_kind not in {"baseline", "cnn"}:
        raise ValueError("Unknown model kind")
    config = validate_config(values)
    random.seed(config["seed"])
    np.random.seed(config["seed"])
    samples, info = read_manifest(manifest, root, provenance)
    splits = split_patients(samples, config["seed"], config["validation_fraction"], config["test_fraction"])
    output.mkdir(parents=True, exist_ok=False)
    # A failed run retains its inputs and failure status for diagnosis.
    write_json(output / "status.json", {"status": "running"})
    try:
        write_json(output / "config.json", config | {"model": model_kind, "threshold": .5})
        write_json(output / "provenance.json", info)
        write_json(output / "splits.json", split_record(splits))
        package_root = Path(__file__).parent
        code_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(package_root.glob("*.py"))}
        write_json(output / "environment.json", {
            "created_at": datetime.now(timezone.utc).isoformat(), "python": sys.version,
            "platform": platform.platform(), "source_sha256": code_hashes,
            "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
            "packages": {name: importlib.metadata.version(name) for name in ("numpy", "Pillow", "scikit-learn", "torch")},
        })
        train = splits["train"]
        LOG.info("Validated %d images; split patient counts: %s", len(samples),
                 {k: len({s.patient_id for s in v}) for k, v in splits.items()})
        if model_kind == "baseline":
            model = make_pipeline(StandardScaler(), LogisticRegression(C=1., max_iter=2000, random_state=config["seed"]))
            counts = Counter(s.patient_id for s in train)
            weights = np.array([1 / counts[s.patient_id] for s in train])
            weights *= len(weights) / weights.sum()
            # Scale in float64 so inference matches reconstruction from the saved
            # parameters without float32 rounding between subtraction and division.
            features = color_features(root, train, config["image_size"]).astype(np.float64)
            model.fit(features, [s.label for s in train],
                      standardscaler__sample_weight=weights, logisticregression__sample_weight=weights)
            scaler, classifier = model.steps[0][1], model.steps[1][1]
            if classifier.n_iter_.max() >= classifier.max_iter:
                raise ValueError("Baseline did not converge; inspect data before interpreting results")
            # Numeric arrays avoid pickle-based baseline serialization.
            np.savez(output / "baseline.npz", mean=scaler.mean_, scale=scaler.scale_,
                     coef=classifier.coef_, intercept=classifier.intercept_, classes=classifier.classes_)

            def probabilities(partition, brightness=1.):
                features = color_features(root, partition, config["image_size"], brightness).astype(np.float64)
                return model.predict_proba(features)[:, 1]

            history = []
        else:
            from .models import Images, predict, train_cnn
            model, history = train_cnn(root, splits, config, output)

            def probabilities(partition, brightness=1.):
                return predict(model, Images(root, partition, config["image_size"], brightness=brightness), config["batch_size"])

        write_json(output / "history.json", history)
        # Fixed protocol: no test-derived threshold, tuning, or model selection.
        results = {}
        for name in ("validation", "test"):
            partition = splits[name]
            p = probabilities(partition)
            results[name] = evaluate(partition, p, config["seed"], config["bootstrap_replicates"])
            write_json(output / f"{name}_predictions.json", [
                {"image_id": s.image_id, "patient_id": s.patient_id, "label": s.label, "probability": float(value)}
                for s, value in zip(partition, p)
            ])
        # Predeclared brightness stress test after freezing model, not a stain-shift simulation.
        results["test_brightness_stress"] = {
            str(factor): evaluate(splits["test"], probabilities(splits["test"], factor),
                                 config["seed"], config["bootstrap_replicates"])
            for factor in (.8, 1.2)
        }
        labels = {s.patient_id: s.label for s in train}
        prior = float(np.mean(list(labels.values())))
        results["test_constant_patient_prior"] = evaluate(
            splits["test"], np.full(len(splits["test"]), prior), config["seed"], config["bootstrap_replicates"])
        write_json(output / "metrics.json", results)
        write_json(output / "status.json", {"status": "completed"})
        LOG.info("Completed %s experiment in %s", model_kind, output)
    except Exception as exc:
        write_json(output / "status.json", {"status": "failed", "error_type": type(exc).__name__, "message": str(exc)})
        raise

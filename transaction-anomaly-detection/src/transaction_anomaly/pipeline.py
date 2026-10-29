"""Train-only model fitting and auditable local experiment artifacts."""

import hashlib
import json
import logging
import pickle
import platform
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from . import __version__
from .data import FEATURES, SCHEMA_VERSION, features, read_records, temporal_split
from .evaluation import drift_report, report, select_threshold

LOGGER = logging.getLogger(__name__)


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def make_model(columns: list[str], seed: int) -> Pipeline:
    return Pipeline([
        ("features", ColumnTransformer([("numeric", StandardScaler(), columns)], remainder="drop")),
        ("classifier", LogisticRegression(max_iter=2000, random_state=seed)),
    ])


def run_experiment(data: Path, output: Path, train_end: str, validation_end: str,
                   seed: int = 42) -> dict:
    records = read_records(data)
    train, validation, test = temporal_split(records, train_end, validation_end)
    x_train, x_validation, x_test = map(features, (train, validation, test))
    # Never overwrite prior runs; a complete manifest is written only after success.
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "status.json", {"status": "running"})
    models = {
        "prior": DummyClassifier(strategy="prior"),
        "amount_logistic": make_model(["log_amount"], seed),
        "logistic": make_model(FEATURES, seed),
    }
    validation_reports, thresholds = {}, {}
    for name, model in models.items():
        model.fit(x_train, train.is_anomaly)
        if name != "prior" and model.named_steps["classifier"].n_iter_.max() >= 2000:
            raise RuntimeError(f"{name} failed to converge; inspect data and scaling")
        probabilities = model.predict_proba(x_validation)[:, 1]
        thresholds[name] = select_threshold(validation.is_anomaly, probabilities)
        validation_reports[name] = report(validation.is_anomaly, probabilities, thresholds[name])
    # Fixed insertion order resolves exact ties in favor of the simpler baseline.
    selected = max(models, key=lambda name: validation_reports[name]["average_precision"])
    LOGGER.info("Selected %s using validation average precision", selected)
    test_reports = {}
    for name, model in models.items():
        probabilities = model.predict_proba(x_test)[:, 1]
        test_reports[name] = report(test.is_anomaly, probabilities, thresholds[name])
    probabilities = models[selected].predict_proba(x_test)[:, 1]
    alerts = probabilities >= thresholds[selected]
    errors = test[["transaction_id", "timestamp", "is_anomaly", "international", "card_present"]].copy()
    errors["score"] = probabilities
    errors["alert"] = alerts
    errors["error_type"] = np.where(alerts, "false_positive", "false_negative")
    errors.loc[alerts != test.is_anomaly.to_numpy().astype(bool)].to_csv(output / "test_errors.csv", index=False)
    slices = {}
    for column in ["international", "card_present"]:
        for value in [0, 1]:
            mask = test[column].to_numpy() == value
            if mask.any():
                slices[f"{column}={value}"] = report(test.is_anomaly.to_numpy()[mask],
                                                     probabilities[mask], thresholds[selected])
    interpretations = {}
    for name in ["amount_logistic", "logistic"]:
        model = models[name]
        names = model.named_steps["features"].transformers_[0][2]
        classifier = model.named_steps["classifier"]
        interpretations[name] = {
            "standardized_log_odds_coefficients": dict(zip(names, classifier.coef_[0].tolist())),
            "intercept": float(classifier.intercept_[0]),
        }
    metrics = {"selected_model": selected, "validation": validation_reports,
               "test": test_reports, "test_slices": slices,
               "drift_train_to_validation": drift_report(x_train, x_validation),
               "drift_train_to_test": drift_report(x_train, x_test),
               "interpretation": interpretations}
    write_json(output / "metrics.json", metrics)
    artifact = {"schema_version": SCHEMA_VERSION, "package_version": __version__,
                "sklearn_version": version("scikit-learn"), "features": FEATURES,
                "model": models[selected], "model_name": selected,
                "threshold": thresholds[selected]}
    with (output / "model.pkl").open("wb") as stream:
        pickle.dump(artifact, stream, protocol=pickle.HIGHEST_PROTOCOL)
    manifest = {
        "status": "complete", "created_utc": datetime.now(timezone.utc).isoformat(),
        "package_version": __version__, "python": platform.python_version(),
        "dependencies": {name: version(name) for name in ["numpy", "pandas", "scikit-learn"]},
        "input_sha256": sha256(data), "input_file": data.name,
        "config": {"train_end": train_end, "validation_end": validation_end, "seed": seed,
                   "selection_metric": "validation_average_precision", "threshold_metric": "validation_f1"},
        "splits": {name: {"rows": len(part), "positives": int(part.is_anomaly.sum()),
                          "start": part.timestamp.min().isoformat(), "end": part.timestamp.max().isoformat()}
                   for name, part in zip(["train", "validation", "test"], [train, validation, test])},
        "source_sha256": {path.name: sha256(path) for path in Path(__file__).parent.glob("*.py")},
        "artifact_sha256": {name: sha256(output / name)
                            for name in ["model.pkl", "metrics.json", "test_errors.csv"]},
    }
    write_json(output / "manifest.json", manifest)
    write_json(output / "status.json", {"status": "complete"})
    return metrics


def score_batch(artifact_path: Path, data: Path, output: Path) -> None:
    """Load only artifacts produced locally and controlled by the operator."""
    if output.exists():
        raise ValueError(f"Output already exists: {output}")
    manifest = json.loads((artifact_path.parent / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "complete":
        raise ValueError("Incomplete experiment")
    if sha256(artifact_path) != manifest["artifact_sha256"]["model.pkl"]:
        raise ValueError("Artifact checksum mismatch")
    # A checksum detects accidental changes; it does not make untrusted pickle safe.
    with artifact_path.open("rb") as stream:
        artifact = pickle.load(stream)
    if (artifact["schema_version"] != SCHEMA_VERSION or artifact["features"] != FEATURES
            or artifact["package_version"] != __version__
            or artifact["sklearn_version"] != version("scikit-learn")):
        raise ValueError("Incompatible model artifact; recreate the original environment")
    records = read_records(data, labelled=False)
    probabilities = artifact["model"].predict_proba(features(records))[:, 1]
    scored = records[["transaction_id", "timestamp"]].copy()
    scored["anomaly_probability"] = probabilities
    scored["threshold"] = artifact["threshold"]
    scored["alert"] = probabilities >= artifact["threshold"]
    scored["model_name"] = artifact["model_name"]
    scored.to_csv(output, index=False)

"""Chronological evaluation of the original ULB/Worldline credit-card fields."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import arff
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from .evaluation import report, select_threshold

FEATURES = [*[f"V{i}" for i in range(1, 29)], "Amount"]
TRAIN_END = 103680
VALIDATION_END = 138240


def read_creditcard(path: Path) -> pd.DataFrame:
    """Read OpenML ARFF or Parquet with the original field contract."""
    if Path(path).suffix.lower() in {".pq", ".parquet"}:
        frame = pd.read_parquet(path)
    else:
        records, _ = arff.loadarff(path)
        frame = pd.DataFrame(records)
    required = ["Time", *FEATURES, "Class"]
    if set(frame) != set(required) or frame.empty:
        raise ValueError("Expected the original Time, V1..V28, Amount, Class schema")
    for column in required:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    validate_creditcard(frame)
    return frame.sort_values("Time", kind="stable").reset_index(drop=True)


def validate_creditcard(frame: pd.DataFrame) -> None:
    if not np.isfinite(frame[["Time", *FEATURES, "Class"]].to_numpy()).all():
        raise ValueError("Original numeric fields must be finite")
    if not frame.Class.isin([0, 1]).all() or (frame.Time < 0).any() or (frame.Amount < 0).any():
        raise ValueError("Invalid class, elapsed seconds, or amount")


def split_creditcard(frame: pd.DataFrame, train_end=TRAIN_END, validation_end=VALIDATION_END):
    """Keep time ties together and remove later exact predictor repeats."""
    if not np.isfinite([train_end, validation_end]).all() or not 0 < train_end < validation_end:
        raise ValueError("Require finite 0 < train_end < validation_end")
    validate_creditcard(frame)
    ordered = frame.sort_values("Time", kind="stable")
    # No identity fields exist. This catches exact repeats, not repeated people.
    ordered = ordered.drop_duplicates(FEATURES, keep="first")
    partitions = [ordered[ordered.Time < train_end].copy(),
                  ordered[(ordered.Time >= train_end) & (ordered.Time < validation_end)].copy(),
                  ordered[ordered.Time >= validation_end].copy()]
    for part in partitions:
        if part.empty or part.Class.nunique() != 2:
            raise ValueError("Each chronological partition needs both classes")
    return dict(zip(("train", "validation", "test"), partitions))


def model_candidates(seed=42):
    return {
        "prior": DummyClassifier(strategy="prior"),
        "logistic": make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, random_state=seed)),
        "balanced_logistic": make_pipeline(StandardScaler(), LogisticRegression(
            max_iter=2000, class_weight="balanced", random_state=seed)),
        "histogram_boosting": HistGradientBoostingClassifier(
            max_iter=150, max_leaf_nodes=15, learning_rate=.08,
            early_stopping=False, random_state=seed),
    }


def summarize(y, scores, threshold):
    result = report(y, scores, threshold)
    # Curves contain individual score thresholds; retain aggregate diagnostics only.
    result.pop("precision_recall_curve")
    return result


def experiment(frame: pd.DataFrame, seed=42):
    splits = split_creditcard(frame)
    train, validation, test = (splits[name] for name in ("train", "validation", "test"))
    models = model_candidates(seed)
    validation_results, thresholds = {}, {}
    for name, model in models.items():
        model.fit(train[FEATURES], train.Class)
        if name.endswith("logistic") and model[-1].n_iter_.max() >= model[-1].max_iter:
            raise RuntimeError(f"{name} did not converge")
        score = model.predict_proba(validation[FEATURES])[:, 1]
        thresholds[name] = select_threshold(validation.Class, score)
        validation_results[name] = summarize(validation.Class, score, thresholds[name])
    winner = max(models, key=lambda name: validation_results[name]["average_precision"])
    # All candidates and thresholds are frozen before this comparison on test.
    test_scores = {name: model.predict_proba(test[FEATURES])[:, 1] for name, model in models.items()}
    result = {"selected_model": winner, "validation": validation_results,
              "test": {name: summarize(test.Class, score, thresholds[name]) for name, score in test_scores.items()},
              "split_counts": {name: {"rows": len(part), "frauds": int(part.Class.sum()),
                                     "first_second": float(part.Time.min()), "last_second": float(part.Time.max())}
                               for name, part in splits.items()},
              "removed_exact_predictor_repeats": len(frame) - sum(map(len, splits.values())),
              "protocol": {"train_end_seconds": TRAIN_END, "validation_end_seconds": VALIDATION_END,
                           "seed": seed, "selection": "validation average precision", "threshold": "validation F1"}}
    return result, splits, models, test_scores


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sha256", required=True, help="Expected source-file SHA-256 from the retrieval record")
    args = parser.parse_args(argv)
    try:
        if args.output.exists():
            raise ValueError("Output already exists")
        actual_digest = hashlib.sha256(args.data.read_bytes()).hexdigest()
        if actual_digest != args.sha256:
            raise ValueError("Source checksum mismatch")
        with threadpool_limits(limits=4):
            result, _, _, _ = experiment(read_creditcard(args.data))
        result["input_sha256"] = actual_digest
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(2, f"Credit-card experiment failed: {exc}\n")


if __name__ == "__main__":
    main()

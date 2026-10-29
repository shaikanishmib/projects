"""Image and patient metrics with patient-resampled uncertainty."""

import numpy as np
from sklearn.metrics import (average_precision_score, balanced_accuracy_score,
                             brier_score_loss, confusion_matrix, f1_score,
                             log_loss, roc_auc_score)

from .data import Sample


def metrics(y: np.ndarray, probability: np.ndarray) -> dict:
    y = np.asarray(y)
    p = np.asarray(probability, dtype=float)
    if y.ndim != 1 or p.shape != y.shape or not len(y):
        raise ValueError("Expected aligned nonempty one-dimensional labels and probabilities")
    if not np.isin(y, [0, 1]).all() or not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError("Invalid labels or probabilities")
    predicted = p >= .5
    tn, fp, fn, tp = confusion_matrix(y, predicted, labels=[0, 1]).ravel()
    return {
        "n": len(y), "balanced_accuracy": float(balanced_accuracy_score(y, predicted)),
        "f1": float(f1_score(y, predicted, zero_division=0)),
        "sensitivity": float(tp / (tp + fn)) if tp + fn else None,
        "specificity": float(tn / (tn + fp)) if tn + fp else None,
        "roc_auc": float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else None,
        "average_precision": float(average_precision_score(y, p)) if len(np.unique(y)) == 2 else None,
        "brier": float(brier_score_loss(y, p)), "log_loss": float(log_loss(y, p, labels=[0, 1])),
        "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
    }


def evaluate(samples: list[Sample], probabilities: np.ndarray, seed: int, bootstrap: int = 1000) -> dict:
    image_metrics = metrics(np.array([s.label for s in samples]), probabilities)
    grouped = {}
    for sample, p in zip(samples, probabilities):
        entry = grouped.setdefault(sample.patient_id, {"label": sample.label, "probabilities": []})
        if entry["label"] != sample.label:
            raise ValueError("Inconsistent patient diagnosis")
        entry["probabilities"].append(float(p))
    y = np.array([entry["label"] for entry in grouped.values()])
    p = np.array([np.mean(entry["probabilities"]) for entry in grouped.values()])
    patient_metrics = metrics(y, p)
    rng = np.random.default_rng(seed)
    aucs = []
    for _ in range(bootstrap):
        index = rng.integers(0, len(y), len(y))
        if len(np.unique(y[index])) == 2:
            aucs.append(float(roc_auc_score(y[index], p[index])))
    patient_metrics["roc_auc_bootstrap_95_interval"] = np.quantile(aucs, [.025, .975]).tolist() if aucs else None
    patient_metrics["bootstrap_valid_replicates"] = len(aucs)
    errors = [{"image_id": s.image_id, "patient_id": s.patient_id, "label": s.label, "probability": float(p)}
              for s, p in zip(samples, probabilities) if int(p >= .5) != s.label]
    errors.sort(key=lambda row: abs(row["probability"] - .5), reverse=True)
    return {"image": image_metrics, "patient": patient_metrics, "errors": errors}

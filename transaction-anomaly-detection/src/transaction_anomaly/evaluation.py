"""Validation-only operating points, probability diagnostics, and drift checks."""

import numpy as np
from sklearn.metrics import (average_precision_score, brier_score_loss,
                             confusion_matrix, log_loss, precision_recall_curve,
                             roc_auc_score)


def select_threshold(y, scores) -> float:
    """Maximize validation F1; ties favor the higher, more conservative threshold."""
    precision, recall, thresholds = precision_recall_curve(y, scores)
    f1 = 2 * precision[:-1] * recall[:-1] / np.maximum(precision[:-1] + recall[:-1], 1e-15)
    candidates = np.flatnonzero(np.isclose(f1, f1.max(), rtol=0, atol=1e-12))
    return float(thresholds[candidates[-1]])


def report(y, scores, threshold: float) -> dict:
    y, scores = np.asarray(y), np.asarray(scores)
    predicted = scores >= threshold
    tn, fp, fn, tp = confusion_matrix(y, predicted, labels=[0, 1]).ravel()
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    bins = []
    for i in range(10):
        selected = (scores >= i / 10) & ((scores < (i + 1) / 10) if i < 9 else (scores <= 1))
        if selected.any():
            bins.append({"lower": i / 10, "upper": (i + 1) / 10,
                         "count": int(selected.sum()),
                         "mean_score": float(scores[selected].mean()),
                         "observed_rate": float(y[selected].mean())})
    p, r, t = precision_recall_curve(y, scores)
    return {
        "rows": len(y), "prevalence": float(y.mean()), "threshold": threshold,
        "average_precision": float(average_precision_score(y, scores)),
        "roc_auc": float(roc_auc_score(y, scores)) if len(np.unique(y)) == 2 else None,
        "brier_score": float(brier_score_loss(y, scores)),
        "log_loss": float(log_loss(y, scores, labels=[0, 1])),
        "precision": float(precision), "recall": float(recall),
        "f1": float(2 * precision * recall / max(precision + recall, 1e-15)),
        "alert_rate": float(predicted.mean()),
        "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "calibration_bins": bins,
        "expected_calibration_error": float(sum(
            b["count"] / len(y) * abs(b["mean_score"] - b["observed_rate"]) for b in bins)),
        "precision_recall_curve": {"precision": p.tolist(), "recall": r.tolist(),
                                   "thresholds": t.tolist()},
    }


def drift_report(reference, current) -> dict:
    output = {}
    for name in reference.columns:
        # Edges are derived exclusively from training data, including tail buckets.
        inner = np.unique(np.quantile(reference[name], np.arange(0.1, 1, 0.1)))
        edges = np.r_[-np.inf, inner, np.inf]
        ref = np.histogram(reference[name], bins=edges)[0].astype(float) + 0.5
        cur = np.histogram(current[name], bins=edges)[0].astype(float) + 0.5
        ref, cur = ref / ref.sum(), cur / cur.sum()
        psi = float(np.sum((cur - ref) * np.log(cur / ref)))
        output[name] = {"psi": psi, "review": psi >= 0.2,
                        "reference_mean": float(reference[name].mean()),
                        "current_mean": float(current[name].mean())}
    return output

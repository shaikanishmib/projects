"""Train, select, and evaluate churn models on real Cell2Cell records only."""
from __future__ import annotations
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer, make_column_selector
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score, balanced_accuracy_score, brier_score_loss,
    confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .download import RAW_PATH, validate_content

SEED = 42
MIN_ROWS = 40_000
DROP_COLUMNS = {"CustomerID", "CustomerId", "customer_id", "Churn"}


def load_real_data(path: Path = RAW_PATH) -> tuple[pd.DataFrame, pd.Series, str]:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(
            "Real Cell2Cell CSV missing. Run python -m churn.download first. "
            "No synthetic data will be used."
        )
    digest = validate_content(path.read_bytes())
    frame = pd.read_csv(path, low_memory=False)
    if len(frame) < MIN_ROWS or "Churn" not in frame:
        raise ValueError("Unexpected Cell2Cell file: needs >=40k rows and Churn column")
    mapped = frame["Churn"].astype("string").str.strip().str.lower().map(
        {"yes": 1, "no": 0, "1": 1, "0": 0}
    )
    valid = mapped.notna()
    if valid.sum() < MIN_ROWS or mapped[valid].nunique() != 2:
        raise ValueError("Invalid or insufficient churn labels")
    frame = frame.loc[valid].copy()
    y = mapped.loc[valid].astype(int)
    X = frame.drop(columns=[c for c in frame if c in DROP_COLUMNS])
    # Exclude target variants and identifiers from predictors.
    suspicious = [c for c in X if "churn" in c.lower() or c.lower().endswith("id")]
    X = X.drop(columns=suspicious)
    # Normalize categorical missing values before fold-local imputation.
    for col in X.select_dtypes(include=["object", "string"]).columns:
        X[col] = X[col].astype("object").where(X[col].notna(), np.nan)
    if X.empty or X.shape[1] < 10:
        raise ValueError("Too few usable predictors")
    return X, y, digest


def make_preprocessor() -> ColumnTransformer:
    num = Pipeline([
        ("impute", SimpleImputer(strategy="median", add_indicator=True)),
        ("scale", StandardScaler()),
    ])
    cat = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=20)),
    ])
    return ColumnTransformer([
        ("num", num, make_column_selector(dtype_include=np.number)),
        ("cat", cat, make_column_selector(dtype_exclude=np.number)),
    ])


def metrics(y_true, scores, threshold: float) -> dict:
    pred = (np.asarray(scores) >= threshold).astype(int)
    return {
        "average_precision": float(average_precision_score(y_true, scores)),
        "roc_auc": float(roc_auc_score(y_true, scores)),
        "brier_score": float(brier_score_loss(y_true, scores)),
        "precision": float(precision_score(y_true, pred, zero_division=0)),
        "recall": float(recall_score(y_true, pred, zero_division=0)),
        "f1": float(f1_score(y_true, pred, zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, pred)),
        "confusion_matrix": confusion_matrix(y_true, pred).tolist(),
    }


def choose_threshold(y_valid, scores) -> float:
    # Break F1 ties by choosing the lowest candidate threshold.
    scores = np.asarray(scores, dtype=float)
    candidates = np.unique(np.concatenate([np.linspace(0.05, 0.95, 91), [0.5]]))
    f1s = [f1_score(y_valid, scores >= t, zero_division=0) for t in candidates]
    return float(candidates[int(np.argmax(f1s))])


def run(dataset: Path = RAW_PATH, output: Path = Path("artifacts")) -> dict:
    X, y, digest = load_real_data(dataset)
    X_dev, X_test, y_dev, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=SEED
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_dev, y_dev, test_size=0.25, stratify=y_dev, random_state=SEED
    )
    candidates = {
        "majority": DummyClassifier(strategy="prior"),
        "logistic_regression": LogisticRegression(
            max_iter=1200, class_weight="balanced", solver="lbfgs"
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=150, max_depth=16, min_samples_leaf=6,
            class_weight="balanced_subsample", n_jobs=-1, random_state=SEED
        ),
    }
    selection = {}
    trained = {}
    for name, estimator in candidates.items():
        model = Pipeline([("preprocess", make_preprocessor()), ("model", estimator)])
        model.fit(X_train, y_train)
        score = model.predict_proba(X_val)[:, 1]
        threshold = choose_threshold(y_val, score)
        selection[name] = {"threshold": threshold, **metrics(y_val, score, threshold)}
        trained[name] = model

    winner = max(selection, key=lambda n: selection[n]["average_precision"])
    # The selected fitted model is frozen; do not use test information to tune it.
    best = trained[winner]
    threshold = selection[winner]["threshold"]
    test_scores = best.predict_proba(X_test)[:, 1]
    result = {
        "source": "historical Cell2Cell US telecom labeled training CSV",
        "dataset_sha256": digest,
        "rows": int(len(X)),
        "feature_count": int(X.shape[1]),
        "split_sizes": {"train": len(X_train), "validation": len(X_val), "test": len(X_test)},
        "selected_model": winner,
        "selection_metric": "validation average_precision",
        "threshold": threshold,
        "validation": selection,
        "test": metrics(y_test, test_scores, threshold),
        "limitations": "Random stratified holdout, not future-time or external deployment validation.",
    }
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    pd.DataFrame({
        "row_index": X_test.index, "actual_churn": y_test.to_numpy(),
        "churn_probability": test_scores, "predicted_churn": (test_scores >= threshold).astype(int),
    }).to_csv(output / "test_predictions.csv", index=False)
    joblib.dump({"pipeline": best, "threshold": threshold, "feature_columns": list(X.columns)}, output / "model.joblib")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))

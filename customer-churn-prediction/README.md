# Customer churn prediction with Cell2Cell data

This project uses the historical US Cell2Cell telecom dataset to predict customer churn. The aim is to compare a few reasonable classification approaches, choose a model and decision threshold without looking at the test data, and understand where the resulting predictions are useful or limited.

The dataset contains 51,047 labeled training records and roughly 58 columns. It was originally released for the Teradata Center for Customer Relationship Management churn tournament at Duke University. See [DATA.md](docs/DATA.md) for the source, checksum, and usage restrictions.

## Approach

The training pipeline compares a majority-class baseline, regularized logistic regression, and random forest. It uses stratified training, validation, and test partitions (seed 42). Preprocessing is fitted only on the appropriate training data to avoid leaking information into validation or test results.

The model is chosen using **validation average precision**. The classification cutoff is then selected on validation data to maximize F1. Only after both choices are fixed is the test set evaluated. The [benchmark report](docs/BENCHMARK.md) contains the measured results and error analysis; this README deliberately does not substitute example scores for executed results.

The completed research notebook analyzes the same 51,047 records. The command-line implementation follows the same data, split, preprocessing, candidate-model, and validation-selection rules.

## Run locally

From the `customer-churn-prediction` directory:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m churn.download
python -m churn.train
python -m pytest -q
```

On macOS or Linux, activate with `source .venv/bin/activate` and use `python3` if required.

The downloader retrieves the pinned Cell2Cell source and checks its SHA-256 hash. It stops if the source is unavailable or the bytes do not match. If you have obtained the authorized source yourself, place it at `data/raw/cell2celltrain.csv`. Downloaded data and generated artifacts are excluded from Git.

After a successful training run, the pipeline writes `artifacts/metrics.json`, `artifacts/model.joblib`, and `artifacts/test_predictions.csv`.

## What the results can and cannot show

The evaluation measures how these models perform on a held-out partition of the historical dataset. It is **not** a test of modern telecom customer behavior. There is no later-in-time or external holdout, and the study does not estimate whether a retention intervention would actually prevent churn.

The upstream dataset is pinned to a specific Git commit, and the downloader and loader verify its hash. Results record the dataset checksum. Dependency ranges allow compatible installations, but exact numerical reproduction also depends on the library versions and numerical environment used for the original run.

The source dataset is not redistributed here, and this repository does not grant permission to redistribute it.

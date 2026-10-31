# Customer churn prediction: US Cell2Cell telecom

Tabular classification using historical US telecommunications customer records, originally released for the Teradata Center for Customer Relationship Management churn tournament at Duke University.

Data: Cell2Cell, 51,047 original labeled training rows, approximately 58 columns. See [DATA.md](docs/DATA.md) for provenance and usage restrictions.

## What it does

- Retrieves the real Cell2Cell dataset from a pinned public source; aborts if unavailable.
- Validates target and dataset size; separates train, validation, and test with stratified sampling.
- Compares a majority-class baseline, regularized logistic regression, and a random forest.
- Fits preprocessing within each training fold to avoid validation/test leakage.
- Selects the model by validation average precision, chooses an F1-maximizing decision threshold on validation only, and evaluates the untouched test set once.
- Saves metrics, predictions, schema, and the trained pipeline locally. See [the executed benchmark](docs/BENCHMARK.md) for results and limitations.

## Quick start

```powershell
cd customer-churn-prediction
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m churn.download
python -m churn.train
python -m pytest -q
```

Mac/Linux: replace the activation command with `source .venv/bin/activate` and use `python3` if needed.

You can instead download the authorized source yourself and save it as `data/raw/cell2celltrain.csv`. All dataset downloads and generated outputs are gitignored.

## Reproducibility notes
Dataset download is pinned to an upstream Git commit; the original upstream file must remain reachable. The downloader and training loader verify the documented SHA-256 before accepting the CSV. Model results record the checksum. The dataset's historical age limits how well the model represents the current US telecom market. There is no external/temporal holdout and no causal retention-effect evaluation. Split seed is 42.

## Outputs

`artifacts/metrics.json`, `artifacts/model.joblib`, `artifacts/test_predictions.csv`. These appear only after successful training.

The completed research notebook reports the executed benchmark on 51,047 records. The engineering pipeline uses the same data, split seed, preprocessing, candidate models, and validation selection rules. Dependency ranges allow compatible releases; exact numerical replication also requires the original library versions and numerical environment.

This repository does not grant any license to redistribute the Cell2Cell dataset.

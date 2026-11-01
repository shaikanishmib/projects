# Fraud detection on chronological credit-card transactions

I compared several fraud-ranking models using the 284,807 genuine ULB/Worldline transactions available as OpenML dataset 1597. Because fraud cases are rare, the main question is not just overall classification accuracy: it is whether a model places the right transactions high enough in a review queue.

The [executed notebook](notebooks/01_real_data_workflow.ipynb) covers class imbalance, every original predictor, calibration, review capacity, errors, and uncertainty across time blocks.

IEEE-CIS was the preferred dataset, but competition access and Kaggle credentials were unavailable. The ULB dataset provided real labeled transactions instead. It spans only two days and most features are anonymized PCA components, so it cannot establish how a system would behave in a contemporary payment operation. [DATA.md](docs/DATA.md) records the source and checksums.

## Results on the held-out period

After excluding later exact repeats of predictor values, the chronological train, validation, and test partitions contain 150,174, 54,811, and 70,678 records respectively. Model and threshold choices were made on validation data.

| Model | Validation AP | Test AP | Test ROC-AUC | Test Brier loss |
| --- | ---: | ---: | ---: | ---: |
| Constant training prior | 0.000821 | 0.001372 | 0.500000 | 0.001371 |
| Logistic regression | 0.518610 | 0.640964 | 0.971417 | 0.000810 |
| Balanced logistic regression | **0.735804** | **0.760540** | **0.977691** | 0.036272 |
| Histogram boosting | 0.105091 | 0.109533 | 0.613035 | 0.001457 |

Balanced logistic regression had the highest validation average precision. At its validation-selected F1 cutoff, it flagged 69 test transactions: 66 genuine frauds and three false alerts. It missed 31 frauds. That gives precision of 0.956522 and recall of 0.680412.

This is a useful ranking result, but not a well-calibrated probability model. Its Brier loss is worse than the constant-prior baseline. A 200-resample bootstrap over 30-minute blocks gives a conditional test AP interval of 0.656239–0.860407. See [failure modes](docs/FAILURE_MODES.md) for the tradeoffs.

## Reproduce the study

Use Python 3.12. Run these commands from `transaction-anomaly-detection` in PowerShell:

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[research,test]"
New-Item -ItemType Directory -Force data
curl.exe --fail --location --output data/creditcard.parquet https://data.openml.org/datasets/0000/1597/dataset_1597.pq
$env:PYTHONPATH = "$PWD/src"
.venv/Scripts/python -m transaction_anomaly.creditcard --data data/creditcard.parquet --sha256 b7efcb35a428bbe22347a05d2437d9177bab07ce61e51214a17bec584ad9496d --output artifacts/creditcard-run.json
.venv/Scripts/python -m pytest tests
```

The CLI checks the supplied checksum before fitting, uses at most four threads for numerical fitting, and refuses to overwrite an existing result. The notebook also expects `data/manifest.json`, copied from the reviewed retrieval record at [reports/source.json](reports/source.json), and a kernel using this research environment. Run the notebook from a clean kernel in the project directory.

Executed package versions are listed in [reports/aggregate_results.json](reports/aggregate_results.json). Compatible dependency ranges alone do not guarantee identical measurements.

## Implementation and scope

`creditcard.py` reads the original ARFF or Parquet fields, validates numerical inputs, constructs chronological partitions, removes later exact predictor repeats without using labels, and compares the fixed model candidates. `evaluation.py` handles validation-only threshold selection and probability diagnostics. The tests check time boundaries, tied timestamps, nonfinite values, repeated predictors, excluded features, and checksum failures.

An earlier synthetic workflow remains in the repository as a software exercise. Its invented account and calendar fields do **not** appear in the real-data study; see [the synthetic workflow reference](docs/SYNTHETIC_WORKFLOW.md).

This is a historical supervised benchmark, not an estimate of avoided fraud, recovered money, investigator effectiveness, or performance on current transactions. Raw records and individual predictions are not published.

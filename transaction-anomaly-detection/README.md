# Transaction fraud ranking on real credit-card records

The [executed research notebook](notebooks/01_real_data_workflow.ipynb) studies 284,807 ULB/Worldline transactions from OpenML dataset 1597. It compares a constant prior, two logistic regressions, and histogram gradient boosting on chronological partitions. The report covers every original predictor, imbalance, calibration, review capacity, aggregate errors, and time-block uncertainty.

IEEE-CIS was preferred, but Kaggle credentials and competition access were unavailable. The fallback contains genuine transactions and fraud labels; its two-day horizon and anonymized PCA features limit what the study can establish. Source records and individual predictions are excluded from Git. [DATA.md](docs/DATA.md) records provenance, checksums, rights evidence, and the exact filtering protocol.

## Executed results

After removing later exact predictor repeats, the training / validation / test partitions contain 150,174 / 54,811 / 70,678 records. Model choice and thresholds use validation only.

| Model | Validation AP | Test AP | Test ROC-AUC | Test Brier loss |
| --- | ---: | ---: | ---: | ---: |
| Constant training prior | 0.000821 | 0.001372 | 0.500000 | 0.001371 |
| Logistic regression | 0.518610 | 0.640964 | 0.971417 | 0.000810 |
| Balanced logistic regression | 0.735804 | 0.760540 | 0.977691 | 0.036272 |
| Histogram boosting | 0.105091 | 0.109533 | 0.613035 | 0.001457 |

Balanced logistic regression wins on validation AP. Its validation F1 threshold flags 69 test transactions: 66 frauds and 3 false alerts, with 31 frauds missed. Precision is 0.956522 and recall is 0.680412. A 200-resample, 30-minute block bootstrap gives a conditional AP interval of 0.656239 to 0.860407. Its Brier loss is much worse than the constant prior, so the ranking result does not establish calibrated fraud probabilities. See [failure modes](docs/FAILURE_MODES.md).

## Reproduce the study

Use Python 3.12 and the research dependencies. From this directory:

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[research,test]"
New-Item -ItemType Directory -Force data
curl.exe --fail --location --output data/creditcard.parquet https://data.openml.org/datasets/0000/1597/dataset_1597.pq
$env:PYTHONPATH = "$PWD/src"
.venv/Scripts/python -m transaction_anomaly.creditcard --data data/creditcard.parquet --sha256 b7efcb35a428bbe22347a05d2437d9177bab07ce61e51214a17bec584ad9496d --output artifacts/creditcard-run.json
.venv/Scripts/python -m pytest tests
```

The CLI validates the caller-supplied checksum before fitting and rejects an existing output path. It limits numerical fitting to four threads and writes aggregate metrics. The notebook additionally needs `data/manifest.json`, copied from the reviewed retrieval record in [reports/source.json](reports/source.json), and an IPython kernel using the research environment. Execute all cells from a clean kernel with the project directory as the working directory. Exact package versions appear in [the aggregate results](reports/aggregate_results.json). Dependency ranges alone do not guarantee identical values across releases.

## Maintained components

`creditcard.py` reads original ARFF or Parquet fields, checks numeric contracts, partitions elapsed time, filters later exact predictor repeats without labels, and runs the frozen candidate comparison. `evaluation.py` supplies validation threshold selection and probability diagnostics. Tests check chronological boundaries, time ties, nonfinite fields, repeated predictors, feature exclusions, and checksum failure before fitting.

The earlier synthetic generator, generic CSV interface, and batch-scoring pipeline remain maintained for software exercises. Their invented account and calendar fields are absent from this research benchmark. Their contracts and commands are documented in [the synthetic workflow reference](docs/SYNTHETIC_WORKFLOW.md).

This is a historical supervised fraud benchmark. It does not estimate fraud prevention, recovered money, contemporary payment performance, or the effects of an investigator's actions.

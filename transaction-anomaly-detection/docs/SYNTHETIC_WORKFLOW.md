# Synthetic workflow reference

A local, reproducible transaction screening benchmark with temporal evaluation and batch scoring. The measurable objective is to rank labelled anomalies by average precision and choose an operating threshold by validation F1. Reports expose alert workload, missed anomalies, probability quality, and covariate shift. This is a portfolio engineering implementation, with no production deployment or external transaction validation claimed.

The legacy interface is maintained for software tests and synthetic workflow exercises. The real-data research benchmark uses the separate credit-card adapter described in the [project README](../README.md). The 16 legacy tests passed during the 2026-10-31 review; no standalone synthetic performance benchmark is published.

## Architecture

`CSV → schema checks → temporal partitions → train-only scaling/models → validation selection → frozen test evaluation → local artifacts → batch CSV`

- `data.py`: schema, explicit feature allowlist, deterministic synthetic generator, strict time partitions.
- `evaluation.py`: validation threshold selection, precision-recall curves, calibration diagnostics, and train-referenced population stability index (PSI).
- `pipeline.py`: baselines, experiment manifest, coefficients, error records, and artifact scoring.
- `cli.py`: local `generate`, `train`, and `score` commands with logging and nonzero exits on invalid input.

The legacy interface uses NumPy, pandas, and scikit-learn. No network calls, experiment service, deployment framework, or notebook is needed for the current scope.

## Environment and execution

Use Python 3.10+ with the dependencies in [pyproject.toml](pyproject.toml) already provisioned in an approved environment. Tests additionally require pytest. The commands below run directly from the source tree in PowerShell without an installation step. The integration tests execute the maintained interfaces on small authored inputs.

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m transaction_anomaly.cli generate --output data/synthetic.csv --rows 12000 --seed 42
python -m transaction_anomaly.cli train --data data/synthetic.csv --output runs/seed42 --train-end 2025-02-24T00:00:00Z --validation-end 2025-03-14T00:00:00Z --seed 42
python -m transaction_anomaly.cli score --model runs/seed42/model.pkl --data data/synthetic.csv --output runs/seed42/scored.csv
python -m pytest
```

The scoring example uses the generated file for interface verification; it includes training records and is **not** an additional evaluation. In normal use supply a separate, unlabelled batch. Output preserves batch row order. Existing data, run directories, and score files are rejected to avoid accidental replacement. Scoring output's parent directory must exist.

All configuration is explicit in command arguments. The defaults describe the synthetic horizon only. Supply appropriate cutoffs for other data. Thresholds and model choice are frozen after validation; scoring never retunes them. For sensitivity checks, repeat generation and training with seeds 7, 42, and 123 in separate directories, retaining every run. Do not choose a seed based on test performance.

## Data contract and provenance

See [the data card](DATA.md) for generation assumptions, licensing, and external-data requirements. The research notebook uses separately acquired ULB/Worldline data; the generator below remains synthetic. The generator creates an explicitly synthetic 90-day stream starting 2025-01-01 UTC and writes a provenance sidecar with seed, generator name, license, and content hash.

| Column | Contract | Model use |
| --- | --- | --- |
| `transaction_id` | Nonempty unique string within the file | Identity/output only |
| `timestamp` | Parseable timestamp; UTC normalization, naive input interpreted as UTC | UTC hour only; temporal partitions |
| `amount` | Finite, strictly positive, one consistent currency/unit | `log1p(amount)` |
| `international` | 0 or 1 | Numeric binary |
| `card_present` | 0 or 1 | Numeric binary |
| `account_age_days` | Finite, nonnegative age at transaction time | Numeric |
| `is_anomaly` | 0 or 1; required for training/evaluation | Outcome only |

Missing and nonfinite required fields fail ingestion. Extra columns are ignored by the feature allowlist. Labels, IDs, and arbitrary post-event fields cannot enter the model. Scoring needs every field except `is_anomaly`; if a label column is supplied it is ignored. Currency conversion, refunds, account joins, and historical aggregate calculation are out of scope. Resolve these upstream with a documented decision-time contract.

## Models and evaluation

The candidate set is fixed: a training prevalence predictor, amount-only logistic regression, and a multivariate logistic regression. The prior is the no-information baseline; amount-only measures the value of a simple amount signal. Standard scaling and logistic coefficients are fitted exclusively on training data. Class weighting and resampling are omitted to avoid deliberately distorting probability estimates.

Training uses timestamps strictly before `train-end`; validation includes `train-end` and excludes `validation-end`; test includes `validation-end` onward. Identical timestamps remain in the same partition. Each partition must contain both outcome classes. Records are sorted deterministically, and duplicate IDs are rejected globally before partitioning. Validation average precision selects the candidate; exact ties prefer the earlier, simpler candidate. Each candidate's validation F1 selects its threshold; tied thresholds favor the higher value. Predictions use `score >= threshold`. Models are not refitted after selection.

Test results include all prespecified baselines for comparison; they never influence selection. Average precision is the primary ranking metric for rare anomalies. ROC AUC is supplemental. Precision, recall, F1, alert rate, and confusion counts describe the operating point. Probability diagnostics include Brier score, log loss, and ten equal-width reliability bins with expected calibration error. These diagnose calibration; no separate probability calibrator is fitted. Single-class slices retain diagnostics but have null ROC AUC; their average precision can be uninformative and scikit-learn may warn for zero positives.

PSI compares validation and test features against training quantile bins, with infinite tail buckets and additive 0.5-count smoothing. A PSI of at least 0.2 flags manual review as a heuristic, not a statistical guarantee. Binary/discrete features may have fewer bins. This does not detect all conditional or label drift. Outcome prevalence is also reported by split.

## Artifacts and reproducibility

A successful run writes:

| Artifact | Contents |
| --- | --- |
| `manifest.json` | Input hash, explicit cutoffs/seed, split counts and ranges, source hashes, exact Python/dependency versions, artifact hashes |
| `metrics.json` | Validation/test metrics and PR curves, calibration bins, slice metrics, drift, standardized coefficients |
| `test_errors.csv` | False positives and negatives with IDs, scores, outcomes, and selected slice fields |
| `model.pkl` | Selected fitted pipeline, threshold, schema and compatibility metadata |
| `status.json` | `running` until all outputs are complete |

Runs are isolated directories, providing local experiment tracking without a service. A failed run may leave partial outputs with `running` status and no complete manifest; use a new output path after diagnosing the failure. Archive input, provenance sidecar, source, and the exact environment recorded in the manifest. Dependency ranges are compatibility bounds, not a lockfile or a promise of cross-version bitwise reproducibility. The real-data execution environment is recorded separately in the research outputs.

Pickle can execute code: load only trusted, locally controlled artifacts. Scoring checks the sibling manifest's model checksum and exact package/scikit-learn compatibility. Checksums detect corruption, not malicious artifacts or forged manifests. Treat input data, manifests, scores, and error records according to their sensitivity; no real private data is included here. External data provenance remains an operator responsibility.

## Tests and limitations

Tests cover schema violations, duplicate IDs, cutoff inclusion, degenerate partitions, reproducible synthetic generation, label exclusion, train-only preprocessing, validation threshold optimality, test perturbation isolation, calibration endpoints, drift, artifact corruption, and batch scoring integration. All 16 legacy tests passed during this review. Passing tests would establish only the tested software behavior, not operational readiness or real-world model utility.

See [failure modes and evaluation review](FAILURE_MODES.md). Synthetic labels are observable immediately, account identity is unavailable, and the generator is much simpler than actual payment behavior. The screening model learns synthetic label associations; it is a supervised anomaly baseline, not a novel unsupervised detector. The synthetic command has no external validation, confidence interval analysis, live drift monitoring, business cost tuning, or capacity enforcement. The separate real-data notebook includes conditional time-block intervals.

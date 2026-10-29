# Failure modes and review protocol

## Current evidence

No experiments or tests have been executed during implementation. There are no measured error patterns, improvements, or performance claims. The following are engineering hypotheses and review procedures, not observed findings.

## Expected limitations

| Failure mode | Consequence | Review or mitigation |
| --- | --- | --- |
| Synthetic-to-real mismatch | Strong simulation metrics may fail to transfer | Obtain licensed representative data and repeat a frozen temporal protocol |
| Delayed or incomplete anomaly labels | Leakage or distorted precision/recall | Establish outcome horizon and maturity embargo upstream |
| Related transactions across splits | Optimistic entity generalization | Add controlled entity IDs and evaluate new versus recurring entities |
| F1 threshold ignores queue capacity/cost | Unmanageable alerts or expensive misses | Define business costs and capacity, then implement a validation-only constrained policy |
| Logistic linearity and raw UTC hour | Missed interactions, circular time effects | Inspect coefficients and errors; preregister richer features for a new validation cycle |
| Probability miscalibration under shift | Scores cease to represent current event rates | Inspect reliability bins, Brier/log loss and delayed labels; fit any future calibrator on a separate chronological partition |
| PSI blind spots and small samples | Missed conditional drift or unstable review flags | Inspect prevalence, uncertainty, feature distributions and slice counts; do not automate retraining from PSI alone |
| Tiny or zero-positive slices | Noisy or undefined ranking diagnostics | Report counts and prevalence; collect more labelled observations |
| Strict ingestion | Partial upstream faults halt whole batches | Repair and quarantine upstream; this implementation deliberately has no partial acceptance path |
| In-memory CSV evaluation | Memory pressure on large datasets | Bound input sizes operationally; add partitioned ingestion before scaling |
| Repeated test-guided iteration | Benchmark overfitting | Reserve a new final holdout after exploratory test review |

## Reviewing an executed run

1. Confirm complete status, source/input hashes, environment versions, split chronology, and label maturity. Compare class prevalence across partitions.
2. Compare selected model against prior and amount-only baselines using average precision, operating-point confusion counts, and alert rate. Treat any difference as run-specific evidence.
3. Inspect calibration bins with counts, Brier score and log loss. ECE depends on binning and sample size; low ECE alone does not establish calibration.
4. Review `test_errors.csv` and international/card-presence slice reports. Quantify false positives and false negatives before attributing causes. Do not infer causal or demographic fairness conclusions from these synthetic indicators.
5. Relate drift flags to feature distributions and error changes. The generator's known late shift is a stress scenario, not proof that PSI detects arbitrary shift.
6. Repeat prespecified seeds and summarize all runs. For actual data, use several chronological windows and time-block uncertainty analysis; neither is implemented automatically here.

No alert should trigger a financial action from this benchmark. Deployment would require representative validation, operational ownership, privacy review, cost/capacity requirements, monitoring, and controlled integration beyond this repository's scope.

# Findings and limits of the chronological study

The executed benchmark selects balanced logistic regression by validation AP. Test AP is 0.760540, with 66 true alerts, 3 false alerts, and 31 missed frauds at the validation-selected threshold. These are outcomes in the retained historical test cohort. They do not measure fraud prevented or money recovered.

The clearest observed weakness is probability calibration. Balanced logistic regression has Brier loss 0.036272, compared with 0.001371 for the constant prior. Class weighting changes the fitting objective; its scores substantially overpredict the rare event frequency. A future probability calibrator would need its own chronological calibration interval. The test cohort cannot serve that purpose while retaining its evaluation role.

Histogram boosting performs poorly in the fixed configuration: validation AP is 0.105091 and test AP is 0.109533. The notebook compares training and validation ranking and reports feature sensitivity; this result does not establish that boosting is generally inferior. Any new tuning cycle needs a fresh final holdout after this test analysis.

The 200-resample uncertainty analysis resamples 30-minute blocks and excludes model-training and selection uncertainty. There are only 97 retained test frauds, and some error groups are smaller still. Unknown cardholder dependence, the upstream PCA fitting procedure, outcome delay, and the two-day observation period remain unresolved.

Removing later exact predictor repeats prevents identical feature vectors from entering later partitions, but also changes the population and can remove legitimate repeated purchases. Near-duplicates and shared customers remain possible. Results should not be compared directly with published random-split or full-cohort benchmarks.

F1 gives no financial loss function or queue constraint. Validation-derived capacity cutoffs illustrate workload transfer, without enforcing production capacity or establishing the cost of false alerts. Operational evaluation needs longer periods, matured labels, authorization-time inputs, representative external data, and a documented investigation policy.

The maintained synthetic workflow exercises engineering contracts only. Its invented calendar, account, and transaction fields provide no evidence for this real-data benchmark. [The synthetic reference](SYNTHETIC_WORKFLOW.md) documents that separate interface.

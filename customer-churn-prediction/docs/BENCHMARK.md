# Real-data benchmark: Cell2Cell

The complete notebook was executed on the real Cell2Cell CSV on 2026-10-31. Its recomputed model selection, threshold, and validation and test metrics match the existing benchmark within an absolute tolerance of `1e-8`. The original metric files, model artifact, training implementation, and data contracts are preserved.

- Dataset SHA-256: `3f6b8ff0b8e8f5975aa0de9f1f54967e6c8cb867a9bec6cbb64f4c8990f9a645`
- Rows: 51,047; model features: 56.
- Random stratified train/validation/test: 30,627 / 10,210 / 10,210.
- Model selection: validation average precision; selected random forest.
- Decision threshold: 0.44, selected using validation-set F1.
- Evaluation: the fixed random test split, with no cross-validation, temporal study, or external deployment evaluation.

| Metric | Held-out test |
| --- | ---: |
| Average precision | 0.425797 |
| ROC-AUC | 0.656335 |
| Brier score | 0.220860 |
| Precision | 0.359512 |
| Recall | 0.751530 |
| F1 | 0.486362 |
| Balanced accuracy | 0.604782 |

Confusion matrix (rows actual 0/1, columns predicted 0/1): `[[3329, 3939], [731, 2211]]`.

Validation average precision: majority 0.288149; logistic regression 0.378864; random forest 0.428300.

The model identifies about 75.2% of churners, but only 36.0% of flagged customers actually churned. The threshold flags 6,150 customers, including 3,939 who stayed. Observed true positives do not measure prevented churn. Campaign benefit requires evidence about intervention effects, contact costs, incentives, and customer value.

## Uncertainty and probability quality

The notebook computes 1,000 ordinary customer bootstrap resamples of the fixed test predictions with seed 2026. All resamples contain both classes. The pointwise 95% percentile intervals are:

| Metric | Estimate | Lower 95% | Upper 95% |
| --- | ---: | ---: | ---: |
| Average precision | 0.425797 | 0.410342 | 0.445092 |
| ROC-AUC | 0.656335 | 0.646235 | 0.667976 |
| Brier score | 0.220860 | 0.219066 | 0.222436 |
| Precision | 0.359512 | 0.346977 | 0.371112 |
| Recall | 0.751530 | 0.736077 | 0.767451 |
| F1 | 0.486362 | 0.472828 | 0.499158 |

These intervals condition on the fitted model, threshold, and historical cohort. They exclude retraining uncertainty, model-selection uncertainty, temporal drift, and customer dependence. They do not establish performance at another operator or in a later period.

The paired test Brier difference against a constant training-prevalence score is 0.015741, with a 95% interval of 0.012266 to 0.019440. Positive values mean the forest has greater squared probability error. Its mean test score is 0.455399, compared with observed prevalence of 0.288149; every displayed calibration decile overpredicts observed churn frequency.

## Execution and publication review

The notebook includes training-only EDA across all 34 numeric and 22 categorical predictors, common-capacity validation comparisons, calibration diagnostics, threshold workload, aggregate error profiles, and 500-resample subgroup error intervals. The fixed test cohort was exposed in earlier project analysis, which limits claims about independent confirmation.

The finalized notebook has 41 cells, including 14 code cells executed in order from a fresh kernel, with execution counts 1 through 14, no error outputs, and 24 saved figures. The project test suite passed: five tests, zero failures. Saved notebook outputs are produced by real-data execution, and the maintained benchmark is checked during that execution. The report contains aggregate tables and charts without individual customer records. The final Markdown and changed documentation were reviewed using the installed `blader/humanizer` skill.

The final publication audit covers all changed files, saved text and HTML outputs, notebook metadata, and all 24 figures. It found no customer records, customer identifiers, individual prediction tables, raw extracts, or serialized models in the proposed release. The publication contains original analysis and aggregate results; raw data, individual predictions, and trained models remain local. [The provenance record](DATA.md) distinguishes the exact mirrored CSV from Empulse's filtered cohort and the Kaggle distribution described as CC BY-SA 4.0 in the published literature. Source rights remain uncertain, and no permission to redistribute the CSV is asserted. No concrete blocker to this limited aggregate publication was identified in the reviewed material.

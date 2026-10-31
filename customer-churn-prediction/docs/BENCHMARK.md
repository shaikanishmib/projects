# Real-data benchmark — Cell2Cell

User-run training on 2026-10-31 using the real Cell2Cell CSV.

- Dataset SHA-256: `3f6b8ff0b8e8f5975aa0de9f1f54967e6c8cb867a9bec6cbb64f4c8990f9a645`
- Rows: **51,047**; model features: **56**
- Random stratified train/validation/test: **30,627 / 10,210 / 10,210**
- Model selection: validation **average precision**; selected **random forest**
- Decision threshold: **0.44**, selected using validation-set F1
- Results below are from the **held-out test split**, not cross-validation or an external deployment study.

| Metric | Held-out test |
| --- | ---: |
| Average precision | 0.425797 |
| ROC-AUC | 0.656335 |
| Brier score | 0.220860 |
| Precision | 0.359512 |
| Recall | 0.751530 |
| F1 | 0.486362 |
| Balanced accuracy | 0.604782 |

**Confusion matrix** (rows actual 0/1, columns predicted 0/1): `[[3329, 3939], [731, 2211]]`.

**Validation average precision:** majority 0.288149; logistic regression 0.378864; random forest 0.428300.

**Interpretation:** The model catches about 75.2% of churners, but among those flagged as likely churners only 36.0% actually churned in this held-out sample. A retention campaign would need a separate cost/benefit analysis. Accuracy is not used as the primary performance claim.

**Verification scope:** These numbers were supplied from the user's local `python -m churn.train` output; they have not been independently reproduced in this execution environment. The first local pytest attempt collected zero tests because the published test file was missing at that time. That file was subsequently added; tests still require local execution. These numbers must not be described as externally or temporally validated.

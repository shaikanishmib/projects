# Publication review: 2026-10-31

The real-data notebook executed from a fresh research kernel with 27 cells, 13 code cells numbered 1 through 13, no error outputs, and 14 saved figures. The final run completed in 22.9 seconds. Model and threshold choices were fixed before test comparisons. The notebook retains actual executed tables and figures; aggregate results and the source record are included in `reports/`.

All 25 tests passed. Eleven warnings come from the maintained legacy tests: ambiguous invalid-date parsing and precision-recall diagnostics on zero-positive slices. They are not errors in the real-data notebook. Added tests cover the original-field schema, chronological ties, exact-repeat exclusion independent of labels, feature allowlisting, and checksum rejection before fitting. Existing synthetic tests remain software checks only.

The engineering review added a separate original-field adapter and bounded-thread CLI without altering the legacy simulation pipeline. This keeps invented simulation attributes out of the research model. It also records the data filter's effect on counts and preserves a withheld chronological interval for the frozen comparison. The notebook exposes severe probability miscalibration despite strong ranking.

Humanizer was applied to changed Markdown, notebook narrative, docstrings, comments, CLI text, test messages, and the commit description. Every changed file and all saved notebook outputs were reviewed for unsupported claims and sensitive content. All 14 figures were inspected. Raw transactions, individual predictions, and model objects are excluded; the published reports contain aggregate metrics only. The source terms and limitations are recorded in [DATA.md](DATA.md). The original listing's license attribution was checked, while its authority and unknown upstream PCA fitting remain limitations.

This review does not establish operational readiness, external validation, or contemporary fraud performance.

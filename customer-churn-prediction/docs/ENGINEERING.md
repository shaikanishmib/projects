# Engineering review

The 2026-10-31 review preserves the completed research notebook and the maintained model configuration. The downloader and loader now reject bytes that do not match the documented Cell2Cell SHA-256. A pinned URL alone did not validate cached files. Network failures retain their original exception as the cause; unrelated programming errors propagate.

Threshold selection accepts Python lists as well as NumPy arrays. The candidate grid and lowest-threshold tie rule are unchanged. Tests cover corrupted cache entries, rejected network responses, successful acquisition and cache reuse, threshold ties, missing data, and fold-local preprocessing with unseen categories. Small authored inputs exercise contracts only; they provide no benchmark evidence. Pytest collection is limited to the tests directory so local experiment artifacts are excluded.

All 10 engineering tests passed. A full training rerun on the 51,047-row, 56-feature CSV reproduced model selection, split sizes, threshold, and validation and test metrics within absolute tolerance `1e-8`. The saved model independently reproduced the 10,210 held-out scores within `1e-14` and metrics within `1e-12`. Original metric and model files were preserved.

The regression environment used Python 3.12, NumPy 2.5.4, pandas 2.3.3, and scikit-learn 1.9.1. Dependency ranges remain compatible with the existing implementation; they do not promise identical results across releases. No algorithm or estimator settings changed. The random holdout and feature-timing limitations in the research report still apply.

Humanizer was applied to changed engineering prose, comments, docstrings, test messages, and the commit description. The diff contains no raw records, individual predictions, trained models, or notebook edits. Source rights remain uncertain as described in [DATA.md](DATA.md); this change publishes engineering source and documentation only.

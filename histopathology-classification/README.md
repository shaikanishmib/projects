# Histopathology Image Classification

A research-only binary image classification package for comparing a compact CNN with a color-feature logistic regression baseline on licensed pathology images. The objective is measurable patient-level benign/malignant discrimination under a patient-separated evaluation protocol. This project is not a diagnostic system and has no demonstrated clinical performance.

**Implementation status:** source, configuration, tests, and experiment reporting are provided. No real dataset is bundled or downloaded. No code, tests, or experiments were executed during implementation. No measured results or trained model are claimed.

## Architecture

`data.py` validates local manifests, provenance, content hashes, and patient identities, then creates diagnosis-stratified patient partitions. `features.py` implements common RGB resizing/cropping and fixed baseline features. `models.py` contains the CPU CNN and training loop. `evaluation.py` reports image and patient outcomes, uncertainty, and errors. `experiment.py` orchestrates immutable per-run outputs. `cli.py` exposes local validation and experiment commands.

Data stays local. The runtime does not download images or model weights, contact experiment services, or publish artifacts. Training uses only training patients; CNN checkpoint selection uses validation-patient log loss. Test data is reserved for the fixed final report and predeclared brightness stress checks.

## Setup

Requires Python 3.11+ and a user-provisioned environment with NumPy, Pillow, scikit-learn and PyTorch. Dependency ranges are in `pyproject.toml`; they have not been resolved or tested here. No package installation was performed. In an independently authorized environment, install from this project using your trusted package source:

```powershell
python -m pip install -e ".[dev]"
```

Alternatively, with dependencies already available, set `$env:PYTHONPATH = "$PWD/src"` and invoke `python -m histopathology` without installing the project. The commands below are future execution instructions, not operations performed during implementation.

## Data

Supply a CSV with `image_id,patient_id,path,label` and a provenance JSON documenting the original provider, exact license, acquisition date, and verified patient ID method. Labels are `0=benign`, `1=malignant`. All images for one patient must have a consistent diagnosis. At least three patients per class are needed to form nonempty partitions, though a credible study requires substantially more. See [the data contract](docs/DATA.md) for rights review, identity rules, supported formats, and limitations.

```powershell
python -m histopathology validate --manifest data/manifest.csv --data-root data --provenance data/provenance.json --config configs/default.toml
python -m histopathology run --model baseline --manifest data/manifest.csv --data-root data --provenance data/provenance.json --config configs/default.toml --output runs/baseline-001
python -m histopathology run --model cnn --manifest data/manifest.csv --data-root data --provenance data/provenance.json --config configs/default.toml --output runs/cnn-001
```

Use the same data, seed and split fractions for both models. Run directories must be new; existing results are never overwritten. Settings include image size, epochs, batch size, learning rate, seed, CPU threads and bootstrap count; unknown config keys and invalid values fail explicitly. Image decoding failures and validation errors stop the run. Whole-slide extraction and mixed-diagnosis patients require a separate protocol.

For a local pipeline check when no licensed images are available:

```powershell
python -m histopathology fixture --output data/synthetic
python -m histopathology run --model baseline --manifest data/synthetic/manifest.csv --data-root data/synthetic --provenance data/synthetic/provenance.json --output runs/synthetic-baseline
```

The fixture is artificial color noise, not pathology. Its scores cannot assess pathology accuracy.

## Evaluation and artifacts

The primary report is patient-level ROC-AUC; mean image probabilities form each patient prediction. Companion metrics include average precision, balanced accuracy, sensitivity, specificity, F1, Brier score and log loss. A fixed 0.5 threshold, patient bootstrap intervals, constant prevalence baseline, image error records and fixed brightness stress tests support comparison. See [the evaluation protocol](docs/EVALUATION.md) for precise selection rules and interpretation.

Each completed run writes:

- `config.json`, `provenance.json`, `splits.json`: effective settings, original data assertions and hashed split records.
- `environment.json`: runtime versions, platform, source hashes and manifest digest.
- `history.json`: CNN epoch training and validation losses; empty for the fixed baseline.
- `baseline.npz` or `cnn.pt`: numeric baseline state or CNN state dictionary.
- `validation_predictions.json`, `test_predictions.json`, `metrics.json`: probabilities, metrics, patient intervals and error lists.
- `status.json`: running, completed or failed status.

The baseline archive stores scaler mean/scale and logistic coefficients/intercept/classes and can be read with `numpy.load(..., allow_pickle=False)`. Its probability formula is `sigmoid(((features - mean) / scale) @ coef.T + intercept)`. CNN checkpoints contain a `SmallCNN` state dictionary; load only trusted local checkpoints with `torch.load(..., weights_only=True, map_location="cpu")`, instantiate the same architecture, and use the saved image size. There is no clinical serving endpoint.

## Tests

When validation is authorized and dependencies are available:

```powershell
python -m pytest
```

Tests cover patient separation and deterministic splits, duplicate bytes, path traversal, corrupt images, conflicting diagnoses, rights assertions, invalid configuration, known metric outcomes, patient aggregation, CNN output/gradient structure and an artificial end-to-end baseline run with artifact round-trip checks. They have not been run. Even a passing suite would establish software checks only, not clinical validity or production readiness.

## Limitations

Patient identity correctness and usage rights depend on operator verification. Exact hashes do not detect transformed duplicates. Patient separation does not remove institution, scanner, stain, subtype or magnification confounding. RGB center cropping may remove diagnostic tissue; the small CNN is an intentionally modest comparator and learns no pretrained pathology representation. Mean tile probability ignores tissue amount and tumor burden. No external cohort evaluation, stain normalization study, prospective validation, reader study, clinical calibration, fairness analysis, or deployment validation has been performed. Keep all claims tied to an actual frozen dataset and executed evaluation.

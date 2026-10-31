# Histopathology classification on original BreaKHis images

The [executed notebook](notebooks/01_patient_level_workflow.ipynb) compares a color-feature logistic baseline with a small CPU CNN on authentic BreaKHis images downloaded from the original university provider. It characterizes all 7,909 images and studies a predeclared 1,995-image 40X subset with conservative patient-disjoint grouping.

The archive has 82 source folders but 81 distinct year-and-slide identifiers. Two subtype folders sharing one identifier remain together to prevent possible patient leakage. This is a conservative source-group protocol, not independent verification of biological identities. [DATA.md](docs/DATA.md) records the discrepancy, original URL, archive checksum, observed counts, and noncommercial research terms.

## Completed comparison

The 40X train / validation / test partitions contain 1,269 / 377 / 349 images from 51 / 15 / 15 groups. Both methods use 96-pixel center crops and seed 42. The CNN trains for ten epochs on four CPU threads; validation patient log loss selects epoch 1. The 0.5 cutoff is fixed before test evaluation.

| Test patient-group metric | Color baseline | CNN |
| --- | ---: | ---: |
| ROC-AUC | 0.954545 | 0.977273 |
| Balanced accuracy | 0.750000 | 0.500000 |
| Malignant sensitivity | 1.000000 | 1.000000 |
| Benign specificity | 0.500000 | 0.000000 |
| Brier loss | 0.088731 | 0.169497 |

The CNN labels all 15 test groups malignant at the fixed cutoff. Its higher AUC does not establish an improvement: the paired CNN-minus-baseline AUC interval is -0.071429 to 0.162054. Only four benign test groups are available. Validation AUCs are much lower than test AUCs, and there is no external or clinical validation. See [the evaluation record](docs/EVALUATION.md) and [aggregate outputs](reports/aggregate_results.json).

## Reproduce locally

Use Python 3.12 with the research dependencies. From this directory:

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev,research]"
New-Item -ItemType Directory -Force data
curl.exe --fail --location --output data/BreaKHis_v1.tar.gz https://www.inf.ufpr.br/vri/databases/BreaKHis_v1.tar.gz
$env:PYTHONPATH = "$PWD/src"
.venv/Scripts/python -m histopathology.breakhis --archive data/BreaKHis_v1.tar.gz --output data/breakhis
.venv/Scripts/python -m pytest tests
```

Verify the archive SHA-256 against [reports/source.json](reports/source.json). Record the actual new retrieval date and checksum in `data/archive.json` and complete `data/breakhis/provenance.json` using the fields in [the data contract](docs/DATA.md). The published records describe this completed study; do not copy its retrieval date as a new acquisition date. Review the provider's terms before confirming rights.

Execute the notebook from a fresh kernel in the research environment. It derives the 40X manifest, checks groups and source hashes, runs missing baseline/CNN experiments, and verifies completed local runs before reuse. The exact configuration is [configs/breakhis40x.toml](configs/breakhis40x.toml). Completed runs remain in new local `artifacts/breakhis40x-baseline` and `artifacts/breakhis40x-cnn` directories. Remove or archive an invalid local run explicitly before rerunning; the program rejects existing output directories.

The maintained CLI also supports explicit runs:

```powershell
.venv/Scripts/python -m histopathology run --model baseline --manifest data/breakhis/manifest_40x.csv --data-root data/breakhis --provenance data/breakhis/provenance.json --config configs/breakhis40x.toml --output artifacts/another-baseline
```

Use the same manifest, group rule, seed, and split fractions for the CNN. Dependency ranges express compatibility; exact versions are recorded in the report. The completed study used Python 3.12.10, NumPy 2.5.4, Pillow 13.0.0, scikit-learn 1.9.1, and CPU PyTorch 2.15.0.

## Maintained framework

`breakhis.py` parses source identifiers, copies only recognized PNG members into a local collection, checks archive paths and gzip integrity, and writes a manifest with content hashes and magnification. `data.py` verifies image bytes, provenance assertions, identities, and patient splits. `features.py`, `models.py`, and `experiment.py` implement shared preprocessing and immutable experiment runs. `evaluation.py` keeps image and patient-group metrics separate.

All 31 tests pass, including archive corruption and source-group parsing checks. Existing artificial fixtures remain software tests and supply no pathology performance evidence. Original images, identifiers, per-image predictions, and model checkpoints are excluded from Git; the report includes aggregate outputs and a small cited panel of transformed illustrative crops. No diagnostic, screening, treatment, or clinical-performance claim is made.

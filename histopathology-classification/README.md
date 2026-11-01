# Classifying BreaKHis histopathology images

This study compares a simple color-feature logistic classifier with a small convolutional neural network (CNN) using original BreaKHis microscopy images. I wanted to see whether the CNN provided a meaningful improvement once the evaluation kept related images together instead of randomly splitting individual images across partitions.

The [executed notebook](notebooks/01_patient_level_workflow.ipynb) examines all 7,909 available images and evaluates both methods on a predeclared 1,995-image subset at 40× magnification.

## Dataset and grouping

The source archive has 82 folders but only 81 distinct year-and-slide identifiers. Two subtype folders share an identifier; I grouped them together rather than risk placing related images on both sides of a split. This is a conservative **source-group** protocol, not independent confirmation of biological patient identity. The source, checksum, group discrepancy, and noncommercial research terms are documented in [DATA.md](docs/DATA.md).

The 40× data was partitioned into 1,269 training, 377 validation, and 349 test images, representing 51, 15, and 15 groups. Both models use 96-pixel center crops and seed 42. The CNN ran for ten epochs on four CPU threads; validation group-level log loss selected epoch 1. The test cutoff of 0.5 was fixed in advance.

## What happened on the test set

| Patient-group metric | Color baseline | CNN |
| --- | ---: | ---: |
| ROC-AUC | 0.954545 | 0.977273 |
| Balanced accuracy | **0.750000** | 0.500000 |
| Malignant sensitivity | 1.000000 | 1.000000 |
| Benign specificity | **0.500000** | 0.000000 |
| Brier loss | **0.088731** | 0.169497 |

The CNN had the higher AUC, but at the fixed cutoff it labeled **all 15 test groups as malignant**. Its benign specificity was therefore zero. The paired CNN-minus-baseline AUC interval runs from -0.071429 to 0.162054, so the measured AUC difference does not establish a reliable improvement.

Only four benign groups were available in the test split. Validation AUCs were much lower than test AUCs, and the experiment has no independent external or clinical validation. These limitations matter more than the apparent headline AUC. See [EVALUATION.md](docs/EVALUATION.md) and [aggregate results](reports/aggregate_results.json).

## Reproduce locally

Use Python 3.12 and the research dependencies. From `histopathology-classification`:

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev,research]"
New-Item -ItemType Directory -Force data
curl.exe --fail --location --output data/BreaKHis_v1.tar.gz https://www.inf.ufpr.br/vri/databases/BreaKHis_v1.tar.gz
$env:PYTHONPATH = "$PWD/src"
.venv/Scripts/python -m histopathology.breakhis --archive data/BreaKHis_v1.tar.gz --output data/breakhis
.venv/Scripts/python -m pytest tests
```

Check the downloaded archive's SHA-256 against [reports/source.json](reports/source.json), then record your **actual** retrieval date and checksum in `data/archive.json`. Complete `data/breakhis/provenance.json` using the [data contract](docs/DATA.md), and review the provider's terms. The date from the published study must not be presented as the date of a new download.

Run the notebook in a fresh kernel. It builds the 40× manifest, checks the grouping and hashes, and either runs the baseline/CNN experiments or verifies valid completed local runs. The configuration is in [configs/breakhis40x.toml](configs/breakhis40x.toml). Outputs use separate local `artifacts/breakhis40x-baseline` and `artifacts/breakhis40x-cnn` directories; existing output directories are not silently overwritten.

For a separate baseline run:

```powershell
.venv/Scripts/python -m histopathology run --model baseline --manifest data/breakhis/manifest_40x.csv --data-root data/breakhis --provenance data/breakhis/provenance.json --config configs/breakhis40x.toml --output artifacts/another-baseline
```

Use the same manifest, split rule, seed, and fractions for a CNN comparison. The study ran on Python 3.12.10, NumPy 2.5.4, Pillow 13.0.0, scikit-learn 1.9.1, and CPU PyTorch 2.15.0.

## Code and limitations

`breakhis.py` extracts recognized PNGs, checks paths and archive integrity, and records hashes and magnification. `data.py` checks provenance, image bytes, and grouping. `features.py`, `models.py`, and `experiment.py` implement preprocessing and runs; `evaluation.py` separates image-level from group-level metrics.

All 31 reported tests pass, including corrupt-archive and group-parsing cases. Synthetic fixtures test software behavior, not medical performance. Original image files, identifiers, per-image predictions, and checkpoints are excluded from Git. This research makes no diagnostic, screening, treatment, or clinical-performance claim.

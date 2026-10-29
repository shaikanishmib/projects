# Evaluation protocol

The primary objective is patient-level malignant-versus-benign discrimination, measured by ROC-AUC on a fixed patient-held-out test partition. Compare the CNN with the fixed color-feature logistic baseline and constant training-patient prevalence predictor. No success threshold or measured performance is claimed before a licensed dataset and clinical-independent research acceptance criterion are specified.

## Partition and selection

For each binary patient diagnosis, sort IDs and shuffle with the configured seed. Allocate `max(1, floor(n * fraction))` patients to validation and test; assign the rest to training. Default requested proportions are 60/20/20, but actual proportions differ for small cohorts. All image records inherit their patient's split. Splits and content hashes are saved for comparison. Identical manifests, identity mappings, seed, and fractions produce the same patient membership for both models.

The baseline uses 16-bin RGB histograms plus channel means and standard deviations (54 features). Training-patient inverse tile-count weights are used for both scaling and logistic fitting, normalized to mean one. C=1 is fixed. A constant probability baseline is the malignant fraction of training patients. The CNN has three convolution stages and global average pooling, learns from scratch on CPU, and uses training-only flips and quarter turns. Inverse tile-count sampling gives each training patient equal expected exposure; replacement means not every image appears in every epoch. There are no pretrained weights or downloads.

The CNN checkpoint with the lowest validation **patient** log loss is selected from the configured fixed epoch budget. All epoch losses are recorded. Patient probability is the mean of its image probabilities. The decision threshold is fixed at 0.5 for every run. No threshold tuning, calibration fitting, or hyperparameter search is performed. If tuning is added later, use only training/validation data, retain the test cohort, and record every trial. Comparing many models against the same test set can itself overfit the test cohort.

## Reports

Validation and test reports contain image- and patient-level ROC-AUC, average precision, balanced accuracy, F1, sensitivity, specificity, Brier score, log loss, and a confusion matrix with true rows/predicted columns ordered `[0, 1]`. Sensitivity treats malignancy as positive. Patient metrics give each patient equal influence; tile metrics are descriptive and can be dominated by patients with many tiles. Brier and log loss diagnose probability quality but are not evidence of clinical calibration.

The percentile 95% ROC-AUC interval resamples patients with replacement using a fixed seed, skipping single-class replicates and reporting the valid count. It is a conditional uncertainty estimate for the frozen model and test cohort; it excludes model-training uncertainty and can be highly unstable with few patients. No image-independent confidence intervals are reported. Missing/undefined values become JSON null rather than fabricated zeroes.

Two predeclared stress evaluations multiply test-image brightness by 0.8 and 1.2 after selecting the checkpoint. Compare their patient metrics with clean test metrics. These perturbations are crude image stress checks, not a stain-variation, scanner, site-shift, or clinical robustness evaluation. They must not be used to tune the frozen model against test data.

Every report lists misclassified image IDs with patient ID, label, and probability, ordered by confidence. Inspect these alongside the source images locally. Before claiming a useful research result, review patient-level disagreements, tissue/background content, artifacts, magnification, subtype, and acquisition site; add audited subgroup metadata and report uncertainty where sample sizes permit. No automated subgroup claims are possible from the current minimal manifest.

## Execution and result status

No experiment, dataset acquisition, generated code, or test suite was executed during implementation, as requested. There are no measured performance results or trained artifacts in this repository. The integration test is designed to run an artificial baseline experiment in a temporary directory when validation is authorized; it asserts pipeline behavior rather than pathology performance. Package version ranges are compatibility declarations, not a tested lockfile. Freeze and retain the exact environment used for any subsequent experiment.

Keep runs in separate new directories. A failed run records failure status when failure occurs after its output directory is created. Runtime package versions, Python/platform, source hashes, manifest hash, effective config, provenance, image hashes and patient split assignments are persisted. These support audit and repeat execution, but deterministic CPU settings cannot guarantee bitwise equivalence across different hardware or library versions. Artifacts are local research records; review deidentification before sharing.

# Dataset provenance, rights, and limitations

## Source and file identity

The [pinned Cell2Cell README](https://github.com/janebunr/Cell2Cell/blob/d646177d0c23e7dd7cde532ee7a5162c768fe963/README.md) attributes the data to the Teradata Center for Customer Relationship Management at Duke University's Fuqua School of Business. [Empulse's dataset documentation](https://empulse.readthedocs.io/en/latest/guide/datasets/cell2cell.html) describes historical US wireless subscribers from the center's churn tournament. Liu, Wang, and Liu's [Scientific Reports article](https://doi.org/10.1038/s41598-025-22564-4) associates Cell2Cell with Duke's 2003 tournament. That tournament date does not establish when the observations in this particular CSV were collected.

The former [Duke distribution page](https://faculty.fuqua.duke.edu/teradatacenter/) could not be retrieved during this audit. Empulse reports that the center no longer distributes the data. The original distribution terms and the full chain from the original release to the mirrored CSV could not be verified. Sources were reviewed on 2026-10-31.

The downloader fixes the following source:

- Repository: `janebunr/Cell2Cell`.
- Commit: `d646177d0c23e7dd7cde532ee7a5162c768fe963`.
- File: `Data files/cell2celltrain.csv`.
- Local path: `data/raw/cell2celltrain.csv`.
- SHA-256: `3f6b8ff0b8e8f5975aa0de9f1f54967e6c8cb867a9bec6cbb64f4c8990f9a645`.
- Local file size: 13,365,153 bytes.
- Git blob SHA-1: `d0e16b8c6df11960fda20c9e8f2a806664699532`, matching the [file metadata at the pinned commit](https://api.github.com/repos/janebunr/Cell2Cell/contents/Data%20files?ref=d646177d0c23e7dd7cde532ee7a5162c768fe963).

The notebook verifies the local bytes against this checksum before analysis. A matching checksum identifies the file; it does not establish ownership, consent, or a license.

## Cohort and outcome

The file contains 51,047 labeled customer observations. `Churn` uses Yes/No labels, mapped to 1/0. The existing loader removes customer identifiers and target variants, leaving 56 predictors. It retains missing revenue observations.

Empulse's [`fetch_cell2cell` implementation](https://empulse.readthedocs.io/en/latest/_modules/empulse/datasets/_remote.html#fetch_cell2cell) uses the same mirror, commit, and CSV path. Its processing drops 156 customers without `MonthlyRevenue`, producing 50,891 observations. Empulse's software license does not establish the dataset's license. The notebook does not use Empulse's transformed cohort or its assumed campaign-cost parameters. Results from these cohorts require explicit qualification before comparison.

The raw CSV, individual predictions, and trained models remain local and are excluded from Git. The report contains original analysis, aggregate statistics, and charts. No synthetic observations substitute for missing source data.

## License evidence and remaining uncertainty

The pinned mirror's root listing and `Data files` directory were inspected. They contain the README, an R script, and two CSVs, with no license file in those listings. The README attributes the original source without stating reuse terms. This review therefore does not assign a license to the exact downloaded CSV or infer permission from its public availability.

A separate [Kaggle listing](https://www.kaggle.com/datasets/jpacse/datasets-for-churn-telecom), under account `jpacse`, is titled *telecom churn (cell2cell)*. Its page did not expose readable license metadata during this audit, and the attempted public API metadata requests returned HTTP 404. The listing's current license could not be independently confirmed. No Kaggle files were downloaded or compared with the local CSV.

Liu, Y.-w., Wang, J., and Liu, C. (2025), *Multimedia data-driven customer churn prediction using an enhanced extreme learning machine*, Scientific Reports 15, 38757, [DOI: 10.1038/s41598-025-22564-4](https://doi.org/10.1038/s41598-025-22564-4), explicitly attributes the Kaggle distribution to [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Its [data-availability statement](https://pmc.ncbi.nlm.nih.gov/articles/PMC12589437/#data-availability) is evidence of the authors' license attribution for that distribution. It is not a license grant from Duke, proof of the uploader's authority, or verification that the Kaggle files match this pinned CSV. The article's own publication license also must not be confused with a dataset license.

The remaining uncertainty concerns the original terms, the mirror's redistribution authority, and the applicability of the published Kaggle attribution to these exact bytes. This release makes no claim that the CSV is cleared for redistribution, commercial use, or model deployment. Anyone planning those uses should obtain authoritative terms or written permission and record the evidence before distributing customer-level material.

## Aggregate publication audit

The reviewed publication is limited to the notebook's original analysis, aggregate charts and tables, model metrics, and confidence intervals, together with these source notes. No source notice specifically prohibiting that limited publication was identified in the reviewed materials. This is a scoped audit finding, not a grant of dataset rights or a guarantee of legal clearance. The unresolved source terms remain documented above.

Every changed file, every saved text and HTML output, notebook metadata, and all 24 saved figures were checked. The figures contain the following aggregate views:

| Figures | Content |
| --- | --- |
| 1 to 2 | Outcome counts and feature missingness |
| 3 to 5 | Numeric histograms |
| 6 to 8 | Outcome-group boxplots with individual outlier markers disabled |
| 9 to 10 | Quantile-group churn rates and feature correlations |
| 11 to 14 | Categorical-group churn rates with intervals |
| 15 to 17 | Model metrics, validation curves, and test confusion matrix and curves |
| 18 to 19 | Binned calibration, score histograms, and threshold workload |
| 20 to 24 | Subgroup false-positive and false-negative rates with bootstrap intervals |

No customer records, customer identifiers, row-level feature extracts, individual prediction tables, or serialized models are embedded in the publication. Service-area labels name aggregate groups, not subscribers. Displayed categorical groups have at least 100 customers; displayed test error subgroups also require at least 20 observations in each outcome class. Histograms and cohort summaries can include rare bins and extrema, so this audit does not claim a formal anonymity guarantee. PNG metadata contains Matplotlib software and resolution information, with no customer metadata.

The final release is restricted to `notebooks/01_complete_ml_workflow.ipynb`, `docs/DATA.md`, and `docs/BENCHMARK.md`. Raw data, individual predictions, trained models, local audit evidence, and notebook checkpoints remain excluded. Engineering code, tests, existing metric artifacts, and data contracts are unchanged. The installed `blader/humanizer` skill was applied to the changed prose; the scientific results and saved outputs were preserved.

## Interpretation limits

These are historical observational records, not a randomized retention study. The file does not establish a prediction date, a usable temporal evaluation cohort, or compatibility with another operator. Retention-contact features require a timing audit before use in a prospective model. Fairness and privacy assessment remain incomplete. Historical benchmark performance does not establish contemporary accuracy, retention lift, commercial suitability, or permission to deploy.

# ULB/Worldline data provenance

## Source and rights evidence

The preferred [IEEE-CIS competition](https://www.kaggle.com/competitions/ieee-fraud-detection/data) requires Kaggle access and applicable competition rules. This environment had neither configured Kaggle credentials nor confirmed competition access. No competition rules were accepted automatically and no IEEE-CIS files were obtained.

The fallback is [OpenML dataset 1597, version 1](https://www.openml.org/api/v1/json/data/1597), uploaded on 2015-06-25. OpenML credits Andrea Dal Pozzolo, Olivier Caelen, and Gianluca Bontempi and describes a collaboration between Worldline and ULB. It records 284,807 European credit-card transactions over two days in September 2013, with 492 fraud labels. These counts were verified locally.

The [ULB Kaggle listing](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud) supplies more specific rights evidence than OpenML's `Public` label. Its [public API metadata](https://www.kaggle.com/api/v1/datasets/view/mlg-ulb/creditcardfraud), checked on 2026-10-31, reports `Database: Open Database, Contents: Database Contents`. These names refer to the [Open Database License](https://opendatacommons.org/licenses/odbl/1-0/) and [Database Contents License](https://opendatacommons.org/licenses/dbcl/1-0/). This records the original listing's attribution; it does not independently establish the uploader's authority or grant rights to other distributions.

Citation: Andrea Dal Pozzolo, Olivier Caelen, Reid A. Johnson, and Gianluca Bontempi. *Calibrating Probability with Undersampling for Unbalanced Classification*. IEEE Symposium on Computational Intelligence and Data Mining, 2015.

Raw data, individual scores, model objects, and sensitive records are excluded from Git. The publication contains original aggregate analysis. Further redistribution or operational use requires reviewing the applicable database and contents obligations. This repository's software license does not relicense the dataset.

## Exact downloaded distribution

- Source: `https://data.openml.org/datasets/0000/1597/dataset_1597.pq`.
- Local path: `data/creditcard.parquet`.
- Bytes: 73,231,184.
- SHA-256: `b7efcb35a428bbe22347a05d2437d9177bab07ce61e51214a17bec584ad9496d`.
- Retrieval: 2026-10-31; exact UTC timestamp is in [the source record](../reports/source.json).
- Shape: 284,807 rows and 31 columns; fraud count: 492.

Two ARFF transfer attempts stalled and were stopped. OpenML's advertised Parquet distribution was downloaded completely with curl. The original ARFF's published MD5, `178bcf9bb1f31a3dfe12d0e577884add`, was not verified and does not apply to the Parquet representation. The notebook checks the downloaded Parquet bytes, schema, and cohort counts. A checksum identifies the reviewed file; it does not prove license ownership.

## Original fields and exclusions

`V1` to `V28` are anonymized PCA components; `Amount` and `Time` retain their source meanings. `Class` is 1 for recorded fraud and 0 otherwise. `Time` is elapsed seconds from the first transaction, without a known calendar origin. No account age, international indicator, card-presence flag, invented transaction ID, or artificial label enters the real-data study. Zero amounts are permitted. Missing, nonfinite, negative time/amount, and nonbinary outcomes fail validation.

Models use the 28 components and original amount. `Time` is reserved for chronological partitioning and diagnostics. The PCA fitting cohort and feature availability are unknown, which limits leakage assurance. There are no cardholder identities or label-arrival dates.

## Filtering and partitions

After a stable time sort, exact duplicates of the 29 predictor values are removed, keeping the earliest record without using its label. This removes 9,144 later records, including 19 recorded frauds, and leaves 275,663 records with 473 frauds. Exact-repeat filtering can also remove genuine repeated purchases. It cannot identify transformed repeats or repeated people.

Training uses `Time < 103680`; validation uses `103680 <= Time < 138240`; test uses `Time >= 138240`. Tied seconds stay together. The partitions contain 150,174 / 54,811 / 70,678 records and 331 / 45 / 97 frauds. Each partition has both outcomes. Scaling and fitting use training only; model selection, F1 cutoffs, and capacity cutoffs use validation only. Test comparisons cover the predeclared candidates after selection. The model is not refitted on validation.

The dataset has only two days of transactions. The study cannot enforce a realistic chargeback-maturity embargo, infer customer separation, or establish performance across banks, countries, or later periods. See [the notebook](../notebooks/01_real_data_workflow.ipynb) for aggregate diagnostics and conditional uncertainty.

# Dataset provenance, rights, and limitations

**Dataset:** Cell2Cell customer churn, Teradata Center for Customer Relationship Management (Duke University) 2003 churn tournament, historical US wireless operator customer observations.

**Original source:** The Teradata/Duke tournament dataset (original distribution no longer active). Public pinned mirror: https://github.com/janebunr/Cell2Cell (file `Data files/cell2celltrain.csv`, commit `d646177d0c23e7dd7cde532ee7a5162c768fe963`).

**Research context:** https://empulse.readthedocs.io/en/latest/guide/datasets/cell2cell.html ; dataset copy at https://www.kaggle.com/datasets/jpacse/datasets-for-churn-telecom . A peer-reviewed article reports that the latter Kaggle dataset is released under CC BY-SA 4.0: https://pmc.ncbi.nlm.nih.gov/articles/PMC12589437/ . Licensing for the pinned GitHub mirror should **not** be inferred solely from another uploader's listing. Review the terms of the precise download before further distribution.

The raw data is **not committed to this repository**. No synthetic fallback exists. Expected original labeled training rows: 51,047 (other publications/loaders may filter missing revenue, resulting in 50,891). The supplied CSV determines actual row count.

Target: `Churn` with Yes/No labels. Historical observational data; not a randomized trial, and historical features may not be available at real-time prediction. Exclude customer identifiers, any split/target columns, and any potential future-information features before claiming production readiness. Fairness and privacy assessment is not complete.

**Limitations:** provenance is not proof of contemporary representativeness, anonymization quality, consent, or authorization for all commercial use cases. Verify original rights and usage context before deployment.

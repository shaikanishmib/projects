# Data card

## Included source

The repository contains source for an explicitly synthetic generator and small in-memory test fixtures. It contains no downloaded transactions, real account identifiers, generated dataset, or executed experiment outputs. The generator uses NumPy's seeded random number generator; it samples timestamps uniformly over 90 days, amounts from a lognormal distribution, two binary indicators, and account ages from an exponential distribution.

Labels are Bernoulli samples from a fixed logistic function of amount, international status, card presence, young account age, and early UTC hour. The final 18 days increase log amounts and label log odds to introduce a known distribution shift. Coefficients in the generator are simulation assumptions, not empirical estimates. Noise deliberately creates irreducible overlap between normal and anomalous examples.

Generator outputs and authored test fixtures are dedicated to the public domain under CC0-1.0, to the extent the authors hold rights in them. Source code is MIT licensed. No third-party dataset license or usage rights are asserted. The generated sidecar records synthetic status, seed, row count, content hash, and license. Retain it with the CSV; training hashes the input CSV but does not verify licensing or sidecar claims.

## Temporal protocol

The default boundaries are 2025-02-24 UTC (day 54) and 2025-03-14 UTC (day 72), corresponding to approximate 60/20/20 proportions under uniform timestamp generation. Exact counts vary with seed. Split by timestamp before fitting any scaler or model; no random train/test split is supported. Future data never determines training feature statistics, candidate selection, or thresholds.

All feature values must describe what was known at authorization time. Labels must represent a fixed, documented outcome horizon. Real chargebacks can mature weeks later: use an embargo or move training cutoffs back sufficiently so all training labels were known before validation decisions. The current synthetic dataset has immediate labels and does not implement delayed-label simulation or automatic embargo. Repeated customer identity and cross-file duplicates cannot be checked without additional identifiers and governance.

## Bringing another dataset

Before using the CSV contract, record the owner, original source URL or internal reference, version/date, license or explicit permission, permitted uses, content hash, timezone/currency conventions, consent/privacy controls, collection population, sampling, outcome definition, and feature availability times. Do not assume an internet-accessible file is openly licensed. Do not use private records in this repository.

Choose boundaries according to collection dates and label maturation. Freeze candidate models and validation selection criteria before inspecting test metrics. Retain raw and transformed data lineage. Investigate repeated transaction IDs and repeated entities, bot-like bursts, exclusions, refunds, missing values, inconsistent timezones, and label disagreements before evaluation. The strict schema rejects problems rather than silently imputing them.

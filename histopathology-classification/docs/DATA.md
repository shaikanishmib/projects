# Data contract and acquisition

## Original source and observed collection

The original [BreaKHis provider](https://web.inf.ufpr.br/vri/databases/breast-cancer-histopathological-database-breakhis/) was reviewed on 2026-10-31. Its access paragraph permits noncommercial research with citation; a CC BY 4.0 badge also appears on the page. This study follows the noncommercial restriction and does not infer broader commercial permission. The requested research analysis is noncommercial. Original images and model weights remain local and are excluded from Git. The software license does not relicense the images. The provider asks users to complete a post-download contact form; it was not submitted.

Required citation: Spanhol, F., Oliveira, L. S., Petitjean, C., and Heutte, L. *A Dataset for Breast Cancer Histopathological Image Classification*. IEEE Transactions on Biomedical Engineering, 63(7):1455-1462, 2016. [DOI: 10.1109/TBME.2015.2496264](https://doi.org/10.1109/TBME.2015.2496264).

The archive was retrieved directly from `https://www.inf.ufpr.br/vri/databases/BreaKHis_v1.tar.gz` on 2026-10-31. It contains 4,273,561,758 bytes with SHA-256 `d118014cf8a58f6d1fc4571e55efb523c932c85cfba2fb05627e455fc40bd640`. The complete HTTP length matched, gzip traversal checked its CRC, and all tar members were read. The experiment ingester verified all 7,909 images and their unique content hashes. All are RGB PNGs: 7,835 measure 700 by 460 pixels and 74 measure 700 by 456 pixels. No images were excluded for this small height difference. No provider checksum was available on the reviewed page; the SHA-256 is a local identity record, not independent authentication of the provider.

| Magnification | Benign images | Malignant images | Total |
| --- | ---: | ---: | ---: |
| 40X | 625 | 1,370 | 1,995 |
| 100X | 644 | 1,437 | 2,081 |
| 200X | 623 | 1,390 | 2,013 |
| 400X | 588 | 1,232 | 1,820 |
| All | 2,480 | 5,429 | 7,909 |

The provider introduction says 9,109 images, while its table and the cited paper describe 7,909. The webpage also gives a benign 40X entry of 652 that does not agree with its total. The counts above were measured from the downloaded original archive. Small transformed crops in the notebook illustrate the input under the cited research use; full original image files are not published.

## Source identities and splits

The provider's naming grammar is `SOB_CLASS_SUBTYPE-YEAR-SLIDE_ID-MAG-SEQUENCE.png`. Labels and magnifications are parsed from these source fields; subtype/class inconsistencies are rejected. The patient grouping retains the literal `YEAR-SLIDE_ID`, including any letter suffixes. Sequence numbers and random IDs never define patients.

There are 82 source subtype folders but 81 distinct year-and-slide identifiers: 24 benign and 57 malignant groups. One malignant identifier spans two subtype folders. The study merges those folders conservatively so a possible shared patient cannot cross splits. This does not independently establish 81 biological patients or resolve the paper's 82-patient description. The alias ambiguity is documented rather than repaired with invented identities.

The predeclared 40X subset contains 1,995 images. Seed-42 stratified group partitions give 1,269 / 377 / 349 images from 51 / 15 / 15 groups. Training has 16 benign and 35 malignant groups; validation and test each have 4 benign and 11 malignant groups. No group or exact image bytes cross splits. Both models use the same membership and preprocessing. Near-duplicates, undocumented aliases, and site confounding remain possible.

## Manifest

CSV in UTF-8 with a header:

```csv
image_id,patient_id,path,label
tile-001,subject-001,images/tile-001.png,0
tile-002,subject-001,images/tile-002.png,0
tile-003,subject-002,images/tile-003.png,1
```

The rows above illustrate the schema and are not bundled data. `0` means benign and `1` malignant for real pathology experiments. Both labels and at least three distinct patients per label are required. This minimum makes splits possible, not statistically adequate. Paths must resolve inside `--data-root`; absolute paths, escaping symlinks, repeated IDs, exact duplicate bytes, corrupt files, unsupported image formats, and multi-frame images are rejected. Supported images are single-frame PNG, JPEG, or TIFF at least 16 pixels per side. Whole-slide formats require an independently audited tile extraction step.

Use globally unique, pseudonymous patient IDs. All slides, tiles, lesions, acquisition sessions, and magnifications from the same patient must share that ID. Never infer a patient ID from a tile index or random row identifier. Confirm IDs against original dataset documentation. This protocol deliberately rejects patients with conflicting binary diagnoses; handle those cases through a separately specified labeling protocol rather than relabeling tiles to satisfy ingestion.

Exact hashes cannot catch transformed duplicates or aliases for the same patient. Review near-duplicates, cross-source subjects, and site identifiers upstream. This implementation provides patient separation, not site-disjoint external validation. Do not combine datasets without resolving these identity issues.

## Provenance JSON

Create an actual JSON file with the following fields populated from the selected source. This example is deliberately unapproved and must not be treated as evidence of a license:

```json
{
  "dataset_name": "REPLACE with dataset and release",
  "source_url": "REPLACE with original provider URL",
  "license": "REPLACE with exact license or permission reference",
  "license_url": "REPLACE with original terms URL",
  "acquired_at": "REPLACE with actual acquisition date",
  "patient_id_method": "REPLACE with verified identity extraction rule",
  "usage_rights_confirmed": false,
  "required_attribution": "REPLACE with required citation or attribution",
  "preprocessing": "REPLACE with extraction, filtering, and magnification details"
}
```

Set `usage_rights_confirmed` to true only after reviewing rights. Extra metadata is retained verbatim in run artifacts. Keep sensitive source records outside project artifacts; manifests should contain only deidentified IDs and local relative image paths. The project is scoped to public licensed data, not private clinical data.

## Synthetic fixtures

The fixture command generates colored noise with invented group IDs and fixed seed. It contains no tissue morphology or human data. Generated fixture images are dedicated to CC0-1.0 by this project. Their provenance explicitly marks them synthetic. They exercise I/O and partitioning; any measurements on them assess only the artificial task. They cannot establish pathology discrimination, generalization, clinical utility, or realistic robustness.

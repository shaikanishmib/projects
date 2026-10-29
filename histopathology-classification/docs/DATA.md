# Data contract and acquisition

No public images, patient identifiers, trained weights, or downloaded datasets are bundled. This repository does not acquire data. Use only locally supplied images whose license you have reviewed and whose use and redistribution terms you can meet. License fields are operator assertions; the program cannot verify legal rights or the authenticity of patient IDs.

A possible source to investigate is the [BreaKHis provider page](https://web.inf.ufpr.br/vri/databases/breast-cancer-histopathological-database-breakhis/). This is a discovery reference, not a claim that its current terms permit your intended use. No provider page was accessed during implementation. Review the provider's actual license/permission and attribution requirements before obtaining any images. Do not substitute a mirror's license for the original provider's terms. If terms do not authorize your use, select another licensed source. Record its exact release, original checksums, required citation, magnification/site coverage, and preprocessing in provenance metadata.

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

"""Strict local manifest ingestion and patient-disjoint partitioning."""

from __future__ import annotations

import csv
import hashlib
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image


@dataclass(frozen=True)
class Sample:
    image_id: str
    patient_id: str
    path: str
    label: int
    sha256: str


def read_manifest(manifest: Path, root: Path, provenance: Path) -> tuple[list[Sample], dict]:
    """Validate identities, binary diagnoses, image bytes, and license metadata.

    Metadata is an operator assertion, not an independent license verification.
    Identical bytes are rejected, even within a patient, to avoid overweighting.
    """
    info = json.loads(provenance.read_text(encoding="utf-8"))
    required = ("dataset_name", "source_url", "license", "license_url", "acquired_at", "patient_id_method")
    if not isinstance(info, dict) or any(not isinstance(info.get(k), str) or not info[k].strip() for k in required):
        raise ValueError(f"Provenance requires nonempty string fields: {required}")
    if info.get("usage_rights_confirmed") is not True:
        raise ValueError("Operator must confirm usage_rights_confirmed after reviewing the license")
    root = root.resolve(strict=True)
    samples, ids, hashes, diagnoses = [], set(), set(), {}
    with manifest.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not {"image_id", "patient_id", "path", "label"}.issubset(reader.fieldnames or []):
            raise ValueError("Manifest requires image_id,patient_id,path,label")
        for line, row in enumerate(reader, 2):
            if None in row or any(not isinstance(row.get(k), str) for k in ("image_id", "patient_id", "path", "label")):
                raise ValueError(f"Malformed CSV record at line {line}")
            image_id, patient_id, relative = (row[k].strip() for k in ("image_id", "patient_id", "path"))
            if not image_id or not patient_id or not relative or image_id in ids:
                raise ValueError(f"Invalid or duplicate identity at line {line}")
            if row["label"].strip() not in {"0", "1"}:
                raise ValueError(f"Label must be 0 or 1 at line {line}")
            label = int(row["label"])
            if patient_id in diagnoses and diagnoses[patient_id] != label:
                raise ValueError(f"Mixed diagnosis for patient {patient_id}; this protocol requires one diagnosis")
            if Path(relative).is_absolute():
                raise ValueError("Image paths must be relative to the data root")
            path = (root / relative).resolve(strict=True)
            if not path.is_relative_to(root) or not path.is_file():
                raise ValueError(f"Image escapes data root or is not a file: {relative}")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest in hashes:
                raise ValueError(f"Duplicate image bytes at line {line}")
            with Image.open(path) as image:
                if image.format not in {"PNG", "JPEG", "TIFF"} or min(image.size) < 16:
                    raise ValueError(f"Unsupported image or dimensions at line {line}")
                if getattr(image, "n_frames", 1) != 1:
                    raise ValueError("Multi-frame images require explicit preprocessing")
                image.verify()
            diagnoses[patient_id] = label
            ids.add(image_id)
            hashes.add(digest)
            samples.append(Sample(image_id, patient_id, relative, label, digest))
    if not samples:
        raise ValueError("Manifest is empty")
    return sorted(samples, key=lambda item: item.image_id), info


def split_patients(samples: list[Sample], seed: int, validation: float = .2, test: float = .2) -> dict[str, list[Sample]]:
    if not 0 < validation < 1 or not 0 < test < 1 or validation + test >= 1:
        raise ValueError("Split fractions must be positive and sum to less than one")
    labels = {}
    for sample in samples:
        if sample.patient_id in labels and labels[sample.patient_id] != sample.label:
            raise ValueError("Mixed patient labels")
        labels[sample.patient_id] = sample.label
    if set(labels.values()) != {0, 1}:
        raise ValueError("Both diagnoses are required")
    groups = {name: set() for name in ("train", "validation", "test")}
    rng = random.Random(seed)
    for label in (0, 1):
        patients = sorted(p for p, value in labels.items() if value == label)
        if len(patients) < 3:
            raise ValueError("At least three independent patients per diagnosis are required")
        rng.shuffle(patients)
        nv, nt = max(1, int(len(patients) * validation)), max(1, int(len(patients) * test))
        if nv + nt >= len(patients):
            raise ValueError("Fractions leave no training patients")
        groups["validation"].update(patients[:nv])
        groups["test"].update(patients[nv:nv + nt])
        groups["train"].update(patients[nv + nt:])
    return {name: [s for s in samples if s.patient_id in patients] for name, patients in groups.items()}


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def split_record(splits: dict[str, list[Sample]]) -> dict:
    return {name: [asdict(s) for s in samples] for name, samples in splits.items()}

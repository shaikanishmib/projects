"""Deterministic artificial RGB fixtures for pipeline checks, not pathology data."""

from pathlib import Path

import numpy as np
from PIL import Image

from .data import write_json


def create_fixture(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    images = destination / "images"
    images.mkdir()
    rng = np.random.default_rng(2026)
    rows = ["image_id,patient_id,path,label"]
    for label in (0, 1):
        for patient in range(10):
            patient_id = f"synthetic-{label}-{patient:02d}"
            tint = np.array([170, 95, 150] if label else [130, 110, 175])
            for tile in range(2):
                image_id = f"{patient_id}-{tile}"
                array = np.clip(rng.normal(tint, 30, (64, 64, 3)), 0, 255).astype(np.uint8)
                relative = f"images/{image_id}.png"
                Image.fromarray(array).save(destination / relative)
                rows.append(f"{image_id},{patient_id},{relative},{label}")
    (destination / "manifest.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    write_json(destination / "provenance.json", {
        "dataset_name": "Artificial color-noise fixtures; not tissue images",
        "source_url": "local:histopathology.fixtures", "license": "CC0-1.0",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "acquired_at": "generated locally with fixed seed 2026",
        "patient_id_method": "Artificial group identifiers; no human subjects",
        "usage_rights_confirmed": True, "synthetic": True,
    })

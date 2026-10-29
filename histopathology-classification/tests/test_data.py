import csv
import json

import pytest

from histopathology.data import read_manifest, split_patients
from histopathology.fixtures import create_fixture


@pytest.fixture
def data(tmp_path):
    root = tmp_path / "fixture"
    create_fixture(root)
    return root


def load(root):
    return read_manifest(root / "manifest.csv", root, root / "provenance.json")[0]


def rewrite(root, change):
    path = root / "manifest.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = reader.fieldnames
    change(rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_splits_are_patient_disjoint_and_reproducible(data):
    samples = load(data)
    first = split_patients(samples, 42)
    assert first == split_patients(samples, 42)
    groups = {k: {s.patient_id for s in v} for k, v in first.items()}
    assert not groups["train"] & groups["validation"]
    assert not groups["train"] & groups["test"]
    assert not groups["validation"] & groups["test"]
    assert sum(map(len, first.values())) == len(samples)
    for partition in first.values():
        assert {s.label for s in partition} == {0, 1}
    assert first != split_patients(samples, 43)


def test_duplicate_content_rejected_across_patients(data):
    rewrite(data, lambda rows: rows[2].update(path=rows[0]["path"]))
    with pytest.raises(ValueError, match="Duplicate image bytes"):
        load(data)


def test_path_traversal_rejected(data):
    # An existing file outside the supplied data root must still be rejected.
    outside = data.parent / "outside.png"
    outside.write_bytes(next((data / "images").glob("*.png")).read_bytes())
    rewrite(data, lambda rows: rows[0].update(path="../outside.png"))
    with pytest.raises(ValueError, match="escapes"):
        load(data)


def test_conflicting_patient_diagnoses_rejected(data):
    rewrite(data, lambda rows: rows[1].update(label="1"))
    with pytest.raises(ValueError, match="Mixed diagnosis"):
        load(data)


def test_missing_usage_rights_rejected(data):
    path = data / "provenance.json"
    info = json.loads(path.read_text())
    info["usage_rights_confirmed"] = False
    path.write_text(json.dumps(info))
    with pytest.raises(ValueError, match="usage_rights_confirmed"):
        load(data)


def test_insufficient_patients_rejected(data):
    samples = [s for s in load(data) if s.patient_id.endswith(("00", "01"))]
    with pytest.raises(ValueError, match="three independent"):
        split_patients(samples, 42)


def test_corrupt_image_rejected(data):
    image = next((data / "images").glob("*.png"))
    image.write_bytes(b"invalid image")
    with pytest.raises(OSError):
        load(data)

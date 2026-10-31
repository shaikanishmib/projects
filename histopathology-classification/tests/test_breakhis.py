"""Source-name and archive integrity contracts; no research measurements."""

import io
import tarfile

import pytest

from histopathology.breakhis import image_metadata, prepare


def test_preserves_identifier_across_magnification_and_subtype():
    first = image_metadata("SOB_M_DC-14-13412-40-001.png")
    second = image_metadata("SOB_M_LC-14-13412-400-002.png")
    assert first["patient_id"] == second["patient_id"] == "14-13412"
    assert first["label"] == 1 and second["magnification"] == 400


@pytest.mark.parametrize("name", ["random.png", "SOB_B_DC-14-13412-40-001.png",
                                 "SOB_M_DC-14-13412-80-001.png"])
def test_rejects_unknown_names_and_conflicting_labels(name):
    with pytest.raises(ValueError):
        image_metadata(name)


def test_extracts_only_named_file_bytes_without_following_archive_paths(tmp_path):
    archive = tmp_path / "images.tar.gz"
    with tarfile.open(archive, "w:gz") as bundle:
        member = tarfile.TarInfo("../../SOB_B_A-14-1-40-001.png")
        member.size = 3
        bundle.addfile(member, io.BytesIO(b"png"))
    output = tmp_path / "prepared"
    prepare(archive, output)
    assert (output / "images/SOB_B_A-14-1-40-001.png").read_bytes() == b"png"
    assert not (tmp_path / "SOB_B_A-14-1-40-001.png").exists()
    with pytest.raises(ValueError, match="already exists"):
        prepare(archive, output)


def test_gzip_crc_corruption_is_rejected(tmp_path):
    archive = tmp_path / "images.tar.gz"
    with tarfile.open(archive, "w:gz") as bundle:
        member = tarfile.TarInfo("SOB_B_A-14-1-40-001.png")
        member.size = 3
        bundle.addfile(member, io.BytesIO(b"png"))
    raw = bytearray(archive.read_bytes())
    raw[-8] ^= 1
    archive.write_bytes(raw)
    with pytest.raises((OSError, tarfile.TarError)):
        prepare(archive, tmp_path / "prepared")

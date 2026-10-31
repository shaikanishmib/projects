"""Build a local manifest from the original university BreaKHis archive."""

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re
import tarfile

SOURCE = "https://web.inf.ufpr.br/vri/databases/breast-cancer-histopathological-database-breakhis/"
PATTERN = re.compile(r"SOB_([BM])_(A|F|PT|TA|DC|LC|MC|PC)-(\d{2})-([A-Za-z0-9]+)-(40|100|200|400)-(\d+)\.png")


def image_metadata(filename: str) -> dict:
    """Preserve the provider's year and slide identifier as the patient group."""
    match = PATTERN.fullmatch(filename)
    if match is None:
        raise ValueError(f"Unrecognized BreaKHis image name: {filename}")
    diagnosis, subtype, year, slide, magnification, sequence = match.groups()
    if (diagnosis == "B") != (subtype in {"A", "F", "PT", "TA"}):
        raise ValueError("Filename diagnosis and subtype disagree")
    return {"image_id": filename, "patient_id": f"{year}-{slide}",
            "label": int(diagnosis == "M"), "subtype": subtype,
            "magnification": int(magnification), "sequence": int(sequence)}


def prepare(archive: Path, output: Path) -> None:
    """Read the entire gzip stream and copy only named PNG members locally."""
    if output.exists():
        raise ValueError("Output directory already exists")
    output.mkdir(parents=True)
    images = output / "images"
    images.mkdir()
    rows, seen = [], set()
    # Streaming decompression verifies gzip integrity without unpacking arbitrary paths.
    with gzip.open(archive, "rb") as decompressed:
        with tarfile.open(fileobj=decompressed, mode="r|") as bundle:
            for member in bundle:
                if not member.isfile() or not member.name.lower().endswith(".png"):
                    continue
                filename = Path(member.name).name
                info = image_metadata(filename)
                if filename in seen or member.size > 20_000_000:
                    raise ValueError("Duplicate image name or oversized image")
                seen.add(filename)
                stream = bundle.extractfile(member)
                if stream is None:
                    raise ValueError("Image member has no content")
                content = stream.read()
                if len(content) != member.size:
                    raise ValueError("Truncated image member")
                (images / filename).write_bytes(content)
                rows.append(info | {"path": f"images/{filename}", "sha256": hashlib.sha256(content).hexdigest()})
        while decompressed.read(1024 * 1024):
            pass
    if not rows:
        raise ValueError("Archive contains no BreaKHis PNG images")
    rows.sort(key=lambda row: row["image_id"])
    with (output / "manifest.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (output / "preparation.json").write_text(json.dumps({
        "images": len(rows), "patient_groups": len({r["patient_id"] for r in rows}),
        "source_url": SOURCE, "identity_rule": "Literal YEAR-SLIDE_ID from the original filename",
        "integrity": "Complete tar traversal; per-image SHA-256; validate image decoding separately"
    }, indent=2) + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        prepare(args.archive, args.output)
    except (OSError, ValueError, tarfile.TarError) as exc:
        parser.exit(2, f"BreaKHis preparation failed: {exc}\n")


if __name__ == "__main__":
    main()

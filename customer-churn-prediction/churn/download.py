"""Download the pinned historical US Cell2Cell CSV; never generate substitute data."""
from __future__ import annotations
import hashlib
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

DATA_URL = (
    "https://raw.githubusercontent.com/janebunr/Cell2Cell/"
    "d646177d0c23e7dd7cde532ee7a5162c768fe963/"
    "Data%20files/cell2celltrain.csv"
)
RAW_PATH = Path("data/raw/cell2celltrain.csv")
MAX_BYTES = 50_000_000
DATA_SHA256 = "3f6b8ff0b8e8f5975aa0de9f1f54967e6c8cb867a9bec6cbb64f4c8990f9a645"


def validate_content(content: bytes) -> str:
    """Verify the exact CSV used by the maintained benchmark."""
    digest = hashlib.sha256(content).hexdigest()
    if digest != DATA_SHA256:
        raise ValueError("Cell2Cell checksum mismatch; see docs/DATA.md for the pinned file")
    return digest


def download(destination: Path = RAW_PATH) -> str:
    destination = Path(destination)
    if destination.exists():
        content = destination.read_bytes()
        return validate_content(content)

    request = Request(DATA_URL, headers={"User-Agent": "cell2cell-churn-portfolio/1.0"})
    try:
        with urlopen(request, timeout=60) as response:
            content = response.read(MAX_BYTES + 1)
    except (OSError, URLError) as exc:
        raise RuntimeError(
            "Could not download the real Cell2Cell dataset. "
            "No synthetic fallback is permitted. See docs/DATA.md."
        ) from exc
    digest = validate_content(content)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    return digest


if __name__ == "__main__":
    digest = download()
    print(f"Cell2Cell CSV SHA256: {digest}")

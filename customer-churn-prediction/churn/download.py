"""Download the pinned historical US Cell2Cell CSV; never generate substitute data."""
from __future__ import annotations
import hashlib
from pathlib import Path
from urllib.request import Request, urlopen

DATA_URL = (
    "https://raw.githubusercontent.com/janebunr/Cell2Cell/"
    "d646177d0c23e7dd7cde532ee7a5162c768fe963/"
    "Data%20files/cell2celltrain.csv"
)
RAW_PATH = Path("data/raw/cell2celltrain.csv")
MAX_BYTES = 50_000_000


def download(destination: Path = RAW_PATH) -> str:
    destination = Path(destination)
    if destination.exists():
        content = destination.read_bytes()
        if len(content) < 100_000 or b"Churn" not in content[:16_384]:
            raise ValueError("Existing dataset is unexpectedly small or lacks Churn column")
        return hashlib.sha256(content).hexdigest()

    request = Request(DATA_URL, headers={"User-Agent": "cell2cell-churn-portfolio/1.0"})
    try:
        with urlopen(request, timeout=60) as response:
            content = response.read(MAX_BYTES + 1)
    except Exception as exc:
        raise RuntimeError(
            "Could not download the real Cell2Cell dataset. "
            "No synthetic fallback is permitted. See docs/DATA.md."
        ) from exc
    if not (100_000 <= len(content) <= MAX_BYTES) or b"Churn" not in content[:16_384]:
        raise ValueError("Unexpected dataset response: refusing to save or train")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    return hashlib.sha256(content).hexdigest()


if __name__ == "__main__":
    digest = download()
    print(f"Cell2Cell CSV SHA256: {digest}")

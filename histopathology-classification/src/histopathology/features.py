"""Fixed feature baseline and common image preprocessing."""

from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageOps

from .data import Sample


def pixels(root: Path, sample: Sample, size: int, brightness: float = 1.) -> np.ndarray:
    # Aspect ratio is retained with a center crop; no validation/test augmentation.
    with Image.open(root / sample.path) as source:
        image = ImageOps.fit(source.convert("RGB"), (size, size), method=Image.Resampling.BILINEAR)
        if brightness != 1.:
            image = ImageEnhance.Brightness(image).enhance(brightness)
        return np.asarray(image, dtype=np.float32) / 255.


def color_features(root: Path, samples: list[Sample], size: int, brightness: float = 1.) -> np.ndarray:
    rows = []
    for sample in samples:
        image = pixels(root, sample, size, brightness)
        channels = [image[..., channel].ravel() for channel in range(3)]
        rows.append(np.concatenate([
            np.histogram(c, bins=16, range=(0, 1))[0] / c.size for c in channels
        ] + [image.mean(axis=(0, 1)), image.std(axis=(0, 1))]))
    return np.asarray(rows, dtype=np.float32)

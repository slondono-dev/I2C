"""Fidelity check between the clean product image and a generated (model) image.

Cheap, local and deterministic: compares colour histograms (HSV) of the product region.
Good enough to flag obvious colour/pattern drift; a real similarity model can replace it later.
"""

from __future__ import annotations

from io import BytesIO

from PIL import Image

REVIEW_THRESHOLD = 0.70


def _hist(data: bytes) -> list[float]:
    img = Image.open(BytesIO(data)).convert("RGBA")
    img.thumbnail((256, 256))
    # keep opaque pixels only (transparent background on clean images)
    rgb = Image.new("RGB", img.size, (255, 255, 255))
    rgb.paste(img, mask=img.split()[3])
    hsv = rgb.convert("HSV")
    hist = hsv.histogram()  # 3 × 256
    h, s = _rebin(hist[:256], 24), _rebin(hist[256:512], 8)
    total = float(sum(h)) or 1.0
    return [v / total for v in h] + [v / total for v in s]


def _rebin(values: list[int], bins: int) -> list[int]:
    size = len(values) // bins
    return [sum(values[i * size : (i + 1) * size]) for i in range(bins)]


def fidelity_score(reference: bytes, generated: bytes) -> float:
    a, b = _hist(reference), _hist(generated)
    inter = sum(min(x, y) for x, y in zip(a, b, strict=True))
    return round(max(0.0, min(1.0, inter / 2)), 3)


def needs_review(score: float) -> bool:
    return score < REVIEW_THRESHOLD

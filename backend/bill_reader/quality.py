"""Image-quality check for bill photos, in plain code (runs alongside the AI read).

Sharpness = variance of the Laplacian on a grayscale copy scaled to 1000 px wide and auto-contrasted (so dim but
sharp photos aren't called blurry). Calibrated on eval/data/bills (2026-11-23): readable photos 450-820
(dim ones ~640); Pillow-blurred copies 105 (radius 3) and 48 (radius 7). Threshold 150 sits between.
"""

from __future__ import annotations

import io
from dataclasses import asdict, dataclass, field
from typing import Any

from PIL import Image, ImageFilter, ImageOps, ImageStat, UnidentifiedImageError

SHARPNESS_MIN = 150.0
MIN_SHORT_SIDE_PX = 500
DARK_MEAN_MAX = 40.0  # mean gray level (0-255) below this = too dark to read
MEASURE_WIDTH = 1000
_LAPLACIAN = ImageFilter.Kernel((3, 3), [0, 1, 0, 1, -4, 1, 0, 1, 0], scale=1, offset=128)

REASON_BLURRY = "blurry"
REASON_TOO_SMALL = "too_small"
REASON_DARK = "dark"


@dataclass(frozen=True)
class ImageQuality:
    ok: bool
    checked: bool
    reasons: tuple[str, ...] = field(default_factory=tuple)
    sharpness: float | None = None
    brightness: float | None = None
    width: int | None = None
    height: int | None = None

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["reasons"] = list(self.reasons)
        return out


NOT_CHECKED = ImageQuality(ok=True, checked=False)  # PDFs: nothing to measure


def sharpness(img: Image.Image) -> float:
    gray = ImageOps.exif_transpose(img).convert("L")
    gray = gray.resize((MEASURE_WIDTH, max(1, int(gray.height * MEASURE_WIDTH / gray.width))))
    gray = ImageOps.autocontrast(gray, cutoff=1)
    return float(ImageStat.Stat(gray.filter(_LAPLACIAN)).var[0])


def check_image(data: bytes) -> ImageQuality:
    try:
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(data)))
        img.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        return NOT_CHECKED  # the reader reports an unreadable file itself
    width, height = img.size
    sharp = round(sharpness(img), 1)
    bright = round(float(ImageStat.Stat(img.convert("L")).mean[0]), 1)
    reasons = []
    if sharp < SHARPNESS_MIN:
        reasons.append(REASON_BLURRY)
    if min(width, height) < MIN_SHORT_SIDE_PX:
        reasons.append(REASON_TOO_SMALL)
    if bright < DARK_MEAN_MAX:
        reasons.append(REASON_DARK)
    return ImageQuality(ok=not reasons, checked=True, reasons=tuple(reasons), sharpness=sharp, brightness=bright,
                        width=width, height=height)

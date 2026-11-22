"""Decode a bill photo in memory, fix EXIF rotation, shrink to <= 1600 px, re-encode as JPEG."""

from __future__ import annotations

import io

from PIL import Image, ImageOps, UnidentifiedImageError

from backend.policy_reader.llm_clients import ImagePart

MAX_LONG_EDGE = 1600
JPEG_QUALITY = 85
Image.MAX_IMAGE_PIXELS = 60_000_000  # refuse decompression bombs

try:  # HEIC from iPhones, if the optional wheel is installed
    from pillow_heif import register_heif_opener

    register_heif_opener()
    HEIC_SUPPORTED = True
except ImportError:  # pragma: no cover
    HEIC_SUPPORTED = False


class ImageError(ValueError):
    """Not a readable image. Message is safe to show users."""


def prepare_image(data: bytes) -> ImagePart:
    try:
        img = Image.open(io.BytesIO(data))
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ImageError("could not read that image; try a JPG or PNG photo") from exc
    img.thumbnail((MAX_LONG_EDGE, MAX_LONG_EDGE))
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=JPEG_QUALITY)
    return ImagePart(data=out.getvalue(), media_type="image/jpeg")

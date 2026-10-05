"""Upload validation: never trust filename; inspect bytes with Pillow."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import get_settings

ALLOWED_FORMATS = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}
MIME_BY_FORMAT = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}


class InvalidImage(ValueError):
    pass


@dataclass
class ValidatedImage:
    data: bytes
    format: str
    extension: str
    content_type: str
    width: int
    height: int


def validate_image(data: bytes, max_side: int | None = None) -> ValidatedImage:
    s = get_settings()
    if len(data) > s.max_upload_mb * 1024 * 1024:
        raise InvalidImage(f"image exceeds {s.max_upload_mb} MB")
    try:
        img = Image.open(BytesIO(data))
        img.verify()
        img = Image.open(BytesIO(data))
    except (UnidentifiedImageError, OSError) as exc:
        raise InvalidImage("file is not a supported image") from exc
    fmt = (img.format or "").upper()
    if fmt not in ALLOWED_FORMATS:
        raise InvalidImage("only JPEG, PNG and WEBP are supported")
    w, h = img.size
    if w < s.min_image_dimension or h < s.min_image_dimension:
        raise InvalidImage("image is too small")
    if w > s.max_image_dimension or h > s.max_image_dimension:
        raise InvalidImage("image is too large")

    # Normalize orientation (phone photos) and optionally downscale
    img = ImageOps.exif_transpose(img) or img  # type: ignore[assignment]
    limit = max_side or 2048
    if max(img.size) > limit:
        img.thumbnail((limit, limit))
    out = BytesIO()
    if fmt == "JPEG":
        img.convert("RGB").save(out, format="JPEG", quality=88, optimize=True)
    else:
        img.save(out, format=fmt)
    return ValidatedImage(
        data=out.getvalue(),
        format=fmt,
        extension=ALLOWED_FORMATS[fmt],
        content_type=MIME_BY_FORMAT[fmt],
        width=img.size[0],
        height=img.size[1],
    )


def make_thumbnail(data: bytes, size: int = 480) -> bytes:
    img = Image.open(BytesIO(data))
    img.thumbnail((size, size))
    out = BytesIO()
    if img.mode in ("RGBA", "LA", "P"):
        img.save(out, format="PNG", optimize=True)
    else:
        img.convert("RGB").save(out, format="JPEG", quality=82)
    return out.getvalue()

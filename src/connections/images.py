"""Bound, orient and sanitize screenshots before sending them to OpenAI."""

import base64
import io
import warnings
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageGrab, ImageOps, UnidentifiedImageError

MAX_FILE_BYTES = 12 * 1024 * 1024
MAX_PIXELS = 25_000_000


@dataclass(frozen=True)
class PreparedImage:
    data: bytes
    width: int
    height: int

    @property
    def data_url(self) -> str:
        return "data:image/png;base64," + base64.b64encode(self.data).decode("ascii")


def prepare_image(data: bytes) -> PreparedImage:
    if not data or len(data) > MAX_FILE_BYTES:
        raise ValueError("Use an image smaller than 12 MB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as source:
                if source.width * source.height > MAX_PIXELS:
                    raise ValueError(
                        "Image is too large. Crop it to the puzzle grid (25 MP limit)."
                    )
                if min(source.size) < 64:
                    raise ValueError("Image is too small. Capture a readable puzzle grid.")
                if source.format not in {"PNG", "JPEG", "WEBP", "BMP"}:
                    raise ValueError("Use a PNG, JPEG, WebP or BMP image.")
                oriented = ImageOps.exif_transpose(source).convert("RGBA")
                background = Image.new("RGBA", oriented.size, "white")
                background.alpha_composite(oriented)
                image = background.convert("RGB")
                image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
                # A fresh image prevents EXIF, paths or other metadata surviving the encoding.
                clean = Image.new("RGB", image.size)
                clean.paste(image)
                buffer = io.BytesIO()
                clean.save(buffer, format="PNG")
                return PreparedImage(buffer.getvalue(), *clean.size)
    except (
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as error:
        raise ValueError("Cannot read this image. Copy a new screenshot of the grid.") from error


def read_image(path: Path) -> PreparedImage:
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("Use an image smaller than 12 MB.")
    return prepare_image(path.read_bytes())


def clipboard_image() -> PreparedImage:
    try:
        image = ImageGrab.grabclipboard()
    except (OSError, NotImplementedError) as error:
        raise ValueError(
            "Clipboard images are unavailable here. Use --image PATH instead."
        ) from error
    if not isinstance(image, Image.Image):
        raise ValueError("No image in the clipboard. Copy a screenshot first, or use --image PATH.")
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    return prepare_image(buffer.getvalue())

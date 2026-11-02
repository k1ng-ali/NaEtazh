"""
Хранение загруженных фото на диске. nginx отдаёт их по MEDIA_URL.
"""

import uuid
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import settings

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
# Больше не нужно ни на одном экране, а лишние пиксели тормозят мобильный интернет
MAX_SIDE_PX = 1600
WEBP_QUALITY = 82
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}

# Защита от «бомб»: маленький файл с огромным разрешением
Image.MAX_IMAGE_PIXELS = 50_000_000


class InvalidImageError(ValueError):
    pass


def compress_image(content: bytes) -> bytes:
    """JPEG, PNG или WebP → WebP не больше MAX_SIDE_PX по длинной стороне."""
    try:
        image = Image.open(BytesIO(content))
        if image.format not in ALLOWED_FORMATS:
            raise InvalidImageError("Unsupported image format")
        image.load()
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError) as exc:
        raise InvalidImageError("File is not a valid image") from exc

    # Фото с телефона часто повёрнуты через EXIF
    image = ImageOps.exif_transpose(image)
    if image.mode in ("RGBA", "LA", "P"):
        image = image.convert("RGBA")
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.getchannel("A"))
        image = background
    else:
        image = image.convert("RGB")
    image.thumbnail((MAX_SIDE_PX, MAX_SIDE_PX))

    output = BytesIO()
    image.save(output, format="WEBP", quality=WEBP_QUALITY, method=6)
    return output.getvalue()


def save_media(content: bytes, folder: str, extension: str = "webp") -> str:
    """Сохраняет файл и возвращает его адрес для ссылок."""
    directory = Path(settings.MEDIA_ROOT) / folder
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{extension}"
    (directory / filename).write_bytes(content)
    return f"{settings.MEDIA_URL}/{folder}/{filename}"


def delete_media(url: str) -> None:
    """Удаляет свой файл. Чужие ссылки и пути за пределами MEDIA_ROOT не трогает."""
    prefix = f"{settings.MEDIA_URL}/"
    if not url.startswith(prefix):
        return
    root = Path(settings.MEDIA_ROOT).resolve()
    path = (root / url.removeprefix(prefix)).resolve()
    if path.is_relative_to(root) and path.is_file():
        path.unlink()

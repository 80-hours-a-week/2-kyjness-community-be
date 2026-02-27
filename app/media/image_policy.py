import uuid
from typing import List, Literal, Optional

from fastapi import UploadFile

from app.core.config import settings
from app.common import ApiCode, raise_http_error
from app.common.validators import normalize_image_content_type
from app.core.storage import storage_save

MAX_FILE_SIZE = settings.MAX_FILE_SIZE

ImagePurpose = Literal["profile", "post"]
IMAGE_PURPOSES: tuple[ImagePurpose, ...] = ("profile", "post")


async def _validate_image(file: Optional[UploadFile], allowed_types: List[str], max_size: int = MAX_FILE_SIZE) -> bytes:
    if not file:
        raise_http_error(400, ApiCode.MISSING_REQUIRED_FIELD)

    normalized = normalize_image_content_type(file.content_type)
    allowed_set = set(allowed_types)
    if "image/jpeg" in allowed_set:
        allowed_set |= {"image/jpg", "image/pjpeg"}
    if normalized not in allowed_set:
        raise_http_error(400, ApiCode.INVALID_FILE_TYPE)

    content = await file.read()
    if not content:
        raise_http_error(400, ApiCode.INVALID_IMAGE_FILE)

    if len(content) > max_size:
        raise_http_error(400, ApiCode.FILE_SIZE_EXCEEDED)

    return content


def _safe_extension(filename: Optional[str], content_type: str) -> str:
    if filename and "." in filename:
        ext = filename.lower().split(".")[-1].strip()
        if ext and len(ext) <= 5 and ext.isalnum():
            return ext
    if "png" in content_type:
        return "png"
    return "jpg"


def _generate_key(purpose: ImagePurpose, ext: str) -> str:
    filename = f"{uuid.uuid4().hex}.{ext}"
    return f"{purpose}/{filename}"


async def save_image_for_media(file: Optional[UploadFile], purpose: ImagePurpose = "post", allowed_types: Optional[List[str]] = None, max_size: int = MAX_FILE_SIZE) -> tuple[str, str, str, int]:
    if purpose not in IMAGE_PURPOSES:
        purpose = "post"
    types = allowed_types or settings.ALLOWED_IMAGE_TYPES
    content = await _validate_image(file, allowed_types=types, max_size=max_size)
    ct = normalize_image_content_type(file.content_type if file else None)
    ext = _safe_extension(file.filename if file else None, ct)
    key = _generate_key(purpose, ext)
    url = storage_save(key, content, ct)
    return key, url, ct, len(content)

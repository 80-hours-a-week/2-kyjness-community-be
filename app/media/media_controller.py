# app/media/media_controller.py
"""이미지 업로드 통합. POST /v1/media/images → imageId, url 반환. DELETE /images/:id → soft delete."""

from typing import Optional

from fastapi import UploadFile

from app.core.file_upload import save_image_for_media
from app.core.codes import ApiCode
from app.core.response import success_response, raise_http_error
from app.media.media_model import MediaModel


def delete_image(image_id: int, user_id: int) -> None:
    """이미지 삭제 (soft delete). 업로더 본인만 삭제 가능."""
    img = MediaModel.get_image_for_delete(image_id)
    if not img:
        raise_http_error(404, ApiCode.IMAGE_NOT_FOUND)
    uploader_id = img.get("uploader_id")
    if uploader_id is not None and int(uploader_id) != user_id:
        raise_http_error(403, ApiCode.FORBIDDEN)
    if not MediaModel.delete_image(image_id):
        raise_http_error(404, ApiCode.IMAGE_NOT_FOUND)


async def upload_image(
    file: Optional[UploadFile],
    user_id: Optional[int] = None,
    folder: str = "post",
) -> dict:
    """이미지 1건 업로드. folder: profile | post. 저장 후 images 테이블에 메타 저장, imageId·url 반환."""
    if not file:
        raise_http_error(400, ApiCode.MISSING_REQUIRED_FIELD)
    file_key, file_url, content_type, size = await save_image_for_media(file, folder=folder)
    row = MediaModel.create_image(
        file_key=file_key,
        file_url=file_url,
        content_type=content_type,
        size=size,
        uploader_id=user_id,
    )
    return success_response(ApiCode.OK, {"imageId": row["imageId"], "url": row["fileUrl"]})

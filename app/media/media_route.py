# app/media/media_route.py
"""공통 이미지 업로드/삭제. POST /v1/media/images, DELETE /images/:id soft delete."""

from typing import Literal, Optional

from fastapi import APIRouter, Depends, File, Path, UploadFile, Query

from app.media import media_controller
from app.core.dependencies import get_current_user, get_current_user_optional
from app.core.response import ApiResponse

router = APIRouter(prefix="/media", tags=["media"])


@router.delete("/images/{image_id}", status_code=204)
async def delete_image(
    image_id: int = Path(..., description="삭제할 이미지 ID"),
    user_id: int = Depends(get_current_user),
):
    """이미지 삭제 (soft delete: deleted_at 설정). 업로더 본인만 삭제 가능."""
    media_controller.delete_image(image_id=image_id, user_id=user_id)


@router.post("/images", status_code=201, response_model=ApiResponse)
async def upload_image(
    image: UploadFile = File(..., description="이미지 파일 (jpeg/png 등)"),
    image_type: Literal["profile", "post"] = Query("post", alias="type", description="profile=프로필 사진, post=게시글 이미지"),
    user_id: Optional[int] = Depends(get_current_user_optional),
):
    """
    이미지 1건 업로드. profile이면 upload/profile, post면 upload/post에 저장.
    로그인 시 uploader_id 저장, 비로그인(회원가입 전)은 None. 응답의 imageId로 회원가입(profileImageId),
    PATCH /users/me(profileImageId), 게시글(imageIds)에 연결.
    """
    return await media_controller.upload_image(file=image, user_id=user_id, folder=image_type)
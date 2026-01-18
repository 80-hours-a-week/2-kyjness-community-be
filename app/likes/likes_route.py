# app/likes/likes_route.py
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from app.likes.likes_controller import LikesController
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/posts/{post_id}/likes", tags=["likes"])

# 좋아요 추가
@router.post("", status_code=201)
async def create_like(
    post_id: int,
    user_id: int = Depends(get_current_user)
):
    """좋아요 추가 API"""
    return LikesController.create_like(
        post_id=post_id,
        user_id=user_id
    )

# 좋아요 취소
@router.delete("", status_code=204)
async def delete_like(
    post_id: int,
    user_id: int = Depends(get_current_user)
):
    """좋아요 취소 API"""
    LikesController.delete_like(
        post_id=post_id,
        user_id=user_id
    )
    
    # status code 204번(삭제 성공) - 응답 본문 없음
    return Response(status_code=204)

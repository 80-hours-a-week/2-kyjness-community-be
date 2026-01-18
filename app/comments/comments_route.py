# app/comments/comments_route.py
from fastapi import APIRouter, Query, Depends
from fastapi.responses import Response
from app.comments.comments_scheme import CommentCreateRequest, CommentUpdateRequest
from app.comments.comments_controller import CommentsController
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/posts/{post_id}/comments", tags=["comments"])

# 댓글 작성
@router.post("", status_code=201)
async def create_comment(
    post_id: int,
    comment_data: CommentCreateRequest,
    user_id: int = Depends(get_current_user)
):
    """댓글 작성 API"""
    return CommentsController.create_comment(
        post_id=post_id,
        user_id=user_id,
        content=comment_data.content
    )

# 댓글 목록 조회
@router.get("", status_code=200)
async def get_comments(
    post_id: int,
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, description="페이지 크기 (기본값: 20)")
):
    """댓글 목록 조회 API"""
    return CommentsController.get_comments(post_id=post_id, page=page, size=size)

# 댓글 수정
@router.patch("/{comment_id}", status_code=200)
async def update_comment(
    post_id: int,
    comment_id: int,
    comment_data: CommentUpdateRequest,
    user_id: int = Depends(get_current_user)
):
    """댓글 수정 API"""
    return CommentsController.update_comment(
        post_id=post_id,
        comment_id=comment_id,
        user_id=user_id,
        content=comment_data.content
    )

# 댓글 삭제
@router.delete("/{comment_id}", status_code=204)
async def delete_comment(
    post_id: int,
    comment_id: int,
    user_id: int = Depends(get_current_user)
):
    """댓글 삭제 API"""
    CommentsController.delete_comment(
        post_id=post_id,
        comment_id=comment_id,
        user_id=user_id
    )
    
    # status code 204번(삭제 성공) - 응답 본문 없음
    return Response(status_code=204)

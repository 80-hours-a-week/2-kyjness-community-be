# app/likes/likes_controller.py
from fastapi import HTTPException
from app.likes.likes_model import LikesModel
from app.posts.posts_model import PostsModel

"""좋아요 관련 비즈니스 로직 처리 (함수형 컨트롤러)."""


def create_like(post_id: int, user_id: int):
    """좋아요 추가 처리."""
    # 게시글 존재 확인
    post = PostsModel.find_post_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail={"code": "POST_NOT_FOUND", "data": None})

    # status code 400번
    # 중복 좋아요 체크
    if LikesModel.has_liked(post_id, user_id):
        raise HTTPException(status_code=400, detail={"code": "ALREADY_LIKED", "data": None})

    # 좋아요 생성
    like = LikesModel.create_like(post_id, user_id)
    if not like:
        raise HTTPException(status_code=400, detail={"code": "ALREADY_LIKED", "data": None})

    # 게시글의 좋아요 수 증가
    PostsModel.increment_like_count(post_id)

    # 업데이트된 좋아요 수 조회
    updated_post = PostsModel.find_post_by_id(post_id)
    like_count = updated_post["likeCount"] if updated_post else 0

    # status code 201번(좋아요 추가 성공)
    return {"code": "POSTLIKE_UPLOADED", "data": {"likeCount": like_count}}


def delete_like(post_id: int, user_id: int):
    """좋아요 취소 처리."""
    # 게시글 존재 확인
    post = PostsModel.find_post_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail={"code": "POST_NOT_FOUND", "data": None})

    # 좋아요 존재 확인
    if not LikesModel.has_liked(post_id, user_id):
        raise HTTPException(status_code=404, detail={"code": "LIKE_NOT_FOUND", "data": None})

    # 좋아요 삭제
    LikesModel.delete_like(post_id, user_id)

    # 게시글의 좋아요 수 감소
    PostsModel.decrement_like_count(post_id)

    # status code 204번(삭제 성공) - 응답 본문 없음
    return None

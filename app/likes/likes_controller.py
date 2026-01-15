# app/likes/likes_controller.py
from fastapi import HTTPException
from typing import Optional
from app.likes.likes_model import LikesModel
from app.posts.posts_model import PostsModel
from app.auth.auth_model import AuthModel

class LikesController:
    """Likes 비즈니스 로직 처리"""

    @staticmethod
    def create_like(post_id: int, session_id: Optional[str]):
        """좋아요 추가 처리"""
        # status code 401번
        # 인증 정보 없음
        if not session_id:
            raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "data": None})
        
        # 세션 ID 검증
        authenticated_user_id = AuthModel.verify_token(session_id)
        if not authenticated_user_id:
            raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "data": None})
        
        # status code 400번
        # post_id 형식 검증
        if not isinstance(post_id, int) or post_id <= 0:
            raise HTTPException(status_code=400, detail={"code": "INVALID_POSTID_FORMAT", "data": None})
        
        # 게시글 존재 확인
        post = PostsModel.find_post_by_id(post_id)
        if not post:
            raise HTTPException(status_code=404, detail={"code": "POST_NOT_FOUND", "data": None})
        
        # status code 400번
        # 중복 좋아요 체크
        if LikesModel.has_liked(post_id, authenticated_user_id):
            raise HTTPException(status_code=400, detail={"code": "ALREADY_LIKED", "data": None})

        # 좋아요 생성
        like = LikesModel.create_like(post_id, authenticated_user_id)
        if not like:
            raise HTTPException(status_code=400, detail={"code": "ALREADY_LIKED", "data": None})

        # 게시글의 좋아요 수 증가
        PostsModel.increment_like_count(post_id)

        # status code 201번(좋아요 추가 성공)
        return {"code": "LIKE_CREATED", "data": None}

    @staticmethod
    def delete_like(post_id: int, session_id: Optional[str]):
        """좋아요 취소 처리"""
        # status code 401번
        # 인증 정보 없음
        if not session_id:
            raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "data": None})
        
        # 세션 ID 검증
        authenticated_user_id = AuthModel.verify_token(session_id)
        if not authenticated_user_id:
            raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "data": None})
        
        # status code 400번
        # post_id 형식 검증
        if not isinstance(post_id, int) or post_id <= 0:
            raise HTTPException(status_code=400, detail={"code": "INVALID_POSTID_FORMAT", "data": None})
        
        # 게시글 존재 확인
        post = PostsModel.find_post_by_id(post_id)
        if not post:
            raise HTTPException(status_code=404, detail={"code": "POST_NOT_FOUND", "data": None})
        
        # 좋아요 존재 확인
        if not LikesModel.has_liked(post_id, authenticated_user_id):
            raise HTTPException(status_code=404, detail={"code": "LIKE_NOT_FOUND", "data": None})

        # 좋아요 삭제
        LikesModel.delete_like(post_id, authenticated_user_id)

        # 게시글의 좋아요 수 감소
        PostsModel.decrement_like_count(post_id)

        # status code 204번(삭제 성공) - 응답 본문 없음
        return None

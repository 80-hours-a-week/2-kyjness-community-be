# app/likes/likes_model.py
from typing import Optional, Dict
from datetime import datetime
import threading

class LikesModel:
    """인메모리 JSON 저장소를 사용한 Likes 모델"""

    # 인메모리 데이터 저장소
    # 구조: {(post_id, user_id): {postId, userId, createdAt}}
    # 중복 좋아요 방지를 위해 (post_id, user_id) 튜플을 키로 사용
    _likes: Dict[tuple, dict] = {}
    _likes_lock = threading.Lock()  # 동시성 제어용 락

    #좋아요 생성
    @classmethod
    def create_like(cls, post_id: int, user_id: int) -> dict:
        """좋아요 생성 (중복 체크 포함)"""
        key = (post_id, user_id)
        
        # 동시성 제어: 좋아요 생성 시 락 사용
        with cls._likes_lock:
            # 중복 체크
            if key in cls._likes:
                return None  # 이미 좋아요가 존재함
            
            like = {
                "postId": post_id,
                "userId": user_id,
                "createdAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            cls._likes[key] = like
            return like

    #좋아요 조회 (특정 게시글, 특정 사용자)
    @classmethod
    def find_like(cls, post_id: int, user_id: int) -> Optional[dict]:
        """특정 게시글에 대한 특정 사용자의 좋아요 조회"""
        key = (post_id, user_id)
        return cls._likes.get(key)

    #좋아요 존재 여부 확인
    @classmethod
    def has_liked(cls, post_id: int, user_id: int) -> bool:
        """특정 게시글에 대한 특정 사용자의 좋아요 존재 여부"""
        key = (post_id, user_id)
        return key in cls._likes

    #좋아요 삭제
    @classmethod
    def delete_like(cls, post_id: int, user_id: int) -> bool:
        """좋아요 삭제"""
        key = (post_id, user_id)
        if key in cls._likes:
            del cls._likes[key]
            return True
        return False

    #특정 게시글의 좋아요 수 조회
    @classmethod
    def get_like_count_by_post_id(cls, post_id: int) -> int:
        """특정 게시글의 좋아요 수 조회"""
        count = sum(1 for (p_id, _) in cls._likes.keys() if p_id == post_id)
        return count

    #특정 사용자가 좋아요한 게시글 목록 조회
    @classmethod
    def get_liked_posts_by_user_id(cls, user_id: int) -> list:
        """특정 사용자가 좋아요한 게시글 ID 목록 조회"""
        post_ids = [post_id for (post_id, u_id) in cls._likes.keys() if u_id == user_id]
        return post_ids

    #모든 데이터 초기화(테스트용)
    @classmethod
    def clear_all_data(cls):
        cls._likes.clear()

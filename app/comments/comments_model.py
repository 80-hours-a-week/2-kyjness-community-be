# app/comments/comments_model.py
from typing import Optional, Dict, List
from datetime import datetime
import threading

class CommentsModel:
    """인메모리 JSON 저장소를 사용한 Comments 모델"""

    # 인메모리 데이터 저장소
    # 구조: {comment_id: {commentId, postId, content, authorId, createdAt}}
    _comments: Dict[int, dict] = {}
    _comment_id_counter: int = 1
    _comment_id_lock = threading.Lock()  # 동시성 제어용 락

    #댓글 생성, 자동으로 commentId 할당
    @classmethod
    def create_comment(cls, post_id: int, user_id: int, content: str) -> dict:
        # 동시성 제어: comment_id 할당 시 락 사용
        with cls._comment_id_lock:
            comment_id = cls._comment_id_counter
            cls._comment_id_counter += 1

        comment = {
            "commentId": comment_id,
            "postId": post_id,
            "content": content,
            "authorId": user_id,
            "createdAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        cls._comments[comment_id] = comment
        return comment

    #댓글 조회
    @classmethod
    def find_comment_by_id(cls, comment_id: int) -> Optional[dict]:
        return cls._comments.get(comment_id)

    #특정 게시글의 댓글 목록 조회 (페이징 지원)
    @classmethod
    def get_comments_by_post_id(cls, post_id: int, page: int = 1, size: int = 20) -> List[dict]:
        # 해당 게시글의 댓글만 필터링
        post_comments = [c for c in cls._comments.values() if c["postId"] == post_id]
        
        # 최신순 정렬 (commentId 내림차순)
        sorted_comments = sorted(post_comments, key=lambda x: x["commentId"], reverse=True)

        # 페이징 처리
        start_idx = (page - 1) * size
        end_idx = start_idx + size

        return sorted_comments[start_idx:end_idx]

    #댓글 수정
    @classmethod
    def update_comment(cls, comment_id: int, content: str) -> bool:
        comment = cls._comments.get(comment_id)
        if not comment:
            return False

        comment["content"] = content
        return True

    #댓글 삭제
    @classmethod
    def delete_comment(cls, comment_id: int) -> bool:
        if comment_id in cls._comments:
            del cls._comments[comment_id]
            return True
        return False

    #댓글 작성자 ID 조회
    @classmethod
    def get_comment_author_id(cls, comment_id: int) -> Optional[int]:
        comment = cls._comments.get(comment_id)
        return comment["authorId"] if comment else None

    #댓글의 게시글 ID 조회
    @classmethod
    def get_comment_post_id(cls, comment_id: int) -> Optional[int]:
        comment = cls._comments.get(comment_id)
        return comment["postId"] if comment else None

    #모든 데이터 초기화(테스트용)
    @classmethod
    def clear_all_data(cls):
        cls._comments.clear()
        with cls._comment_id_lock:
            cls._comment_id_counter = 1

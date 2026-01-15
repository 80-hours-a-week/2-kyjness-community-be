# app/comments/comments_controller.py
from fastapi import HTTPException
from typing import Optional
from app.comments.comments_model import CommentsModel
from app.posts.posts_model import PostsModel
from app.auth.auth_model import AuthModel

class CommentsController:
    """Comments 비즈니스 로직 처리"""

    @staticmethod
    def create_comment(post_id: int, session_id: Optional[str], content: str):
        """댓글 작성 처리"""
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
        # 필수 필드 검증
        if not content or not isinstance(content, str) or not content.strip():
            raise HTTPException(status_code=400, detail={"code": "MISSING_REQUIRED_FIELD", "data": None})

        # 댓글 생성
        comment = CommentsModel.create_comment(post_id, authenticated_user_id, content)

        # 게시글의 댓글 수 증가
        PostsModel.increment_comment_count(post_id)

        # status code 201번(작성 성공)
        return {"code": "COMMENT_CREATED", "data": {"commentId": comment["commentId"]}}

    @staticmethod
    def get_comments(post_id: int, page: int = 1, size: int = 20):
        """댓글 목록 조회 처리"""
        # status code 400번
        # post_id 형식 검증
        if not isinstance(post_id, int) or post_id <= 0:
            raise HTTPException(status_code=400, detail={"code": "INVALID_POSTID_FORMAT", "data": None})
        
        # 게시글 존재 확인
        post = PostsModel.find_post_by_id(post_id)
        if not post:
            raise HTTPException(status_code=404, detail={"code": "POST_NOT_FOUND", "data": None})
        
        # status code 400번
        # 페이지 검증
        if not isinstance(page, int) or page < 1:
            raise HTTPException(status_code=400, detail={"code": "INVALID_PAGE_VALUE", "data": None})
        if not isinstance(size, int) or size < 1:
            raise HTTPException(status_code=400, detail={"code": "INVALID_SIZE_VALUE", "data": None})

        comments = CommentsModel.get_comments_by_post_id(post_id, page, size)

        # 작성자 정보 추가
        result = []
        for comment in comments:
            author = AuthModel.find_user_by_id(comment["authorId"])
            if author:
                result.append({
                    "commentId": comment["commentId"],
                    "content": comment["content"],
                    "author": {
                        "userId": author["userId"],
                        "nickname": author["nickname"],
                        "profileImageUrl": author.get("profileImageUrl", author.get("profileImage", ""))
                    },
                    "createdAt": comment["createdAt"]
                })

        # status code 200번(조회 성공)
        return {"code": "COMMENTS_RETRIEVED", "data": result}

    @staticmethod
    def update_comment(post_id: int, comment_id: int, session_id: Optional[str], content: str):
        """댓글 수정 처리"""
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
        
        # status code 400번
        # comment_id 형식 검증
        if not isinstance(comment_id, int) or comment_id <= 0:
            raise HTTPException(status_code=400, detail={"code": "INVALID_COMMENTID_FORMAT", "data": None})
        
        # 게시글 존재 확인
        post = PostsModel.find_post_by_id(post_id)
        if not post:
            raise HTTPException(status_code=404, detail={"code": "POST_NOT_FOUND", "data": None})
        
        # 댓글 존재 확인
        comment = CommentsModel.find_comment_by_id(comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail={"code": "COMMENT_NOT_FOUND", "data": None})
        
        # status code 400번
        # 댓글이 해당 게시글에 속하는지 확인
        if comment["postId"] != post_id:
            raise HTTPException(status_code=400, detail={"code": "INVALID_POSTID_FORMAT", "data": None})
        
        # status code 403번
        # 작성자 확인
        if comment["authorId"] != authenticated_user_id:
            raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "data": None})
        
        # status code 400번
        # 필수 필드 검증
        if not content or not isinstance(content, str) or not content.strip():
            raise HTTPException(status_code=400, detail={"code": "INVALID_CONTENT_FORMAT", "data": None})

        # 댓글 수정
        CommentsModel.update_comment(comment_id, content)

        # status code 200번(수정 성공)
        return {"code": "COMMENT_UPDATED", "data": None}

    @staticmethod
    def delete_comment(post_id: int, comment_id: int, session_id: Optional[str]):
        """댓글 삭제 처리"""
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
        
        # status code 400번
        # comment_id 형식 검증
        if not isinstance(comment_id, int) or comment_id <= 0:
            raise HTTPException(status_code=400, detail={"code": "INVALID_COMMENTID_FORMAT", "data": None})
        
        # 게시글 존재 확인
        post = PostsModel.find_post_by_id(post_id)
        if not post:
            raise HTTPException(status_code=404, detail={"code": "POST_NOT_FOUND", "data": None})
        
        # 댓글 존재 확인
        comment = CommentsModel.find_comment_by_id(comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail={"code": "COMMENT_NOT_FOUND", "data": None})
        
        # status code 400번
        # 댓글이 해당 게시글에 속하는지 확인
        if comment["postId"] != post_id:
            raise HTTPException(status_code=400, detail={"code": "INVALID_POSTID_FORMAT", "data": None})
        
        # status code 403번
        # 작성자 확인
        if comment["authorId"] != authenticated_user_id:
            raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "data": None})

        # 댓글 삭제
        CommentsModel.delete_comment(comment_id)

        # 게시글의 댓글 수 감소
        PostsModel.decrement_comment_count(post_id)

        # status code 204번(삭제 성공) - 응답 본문 없음
        return None

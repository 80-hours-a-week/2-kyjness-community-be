# app/comments/comments_schema.py
from pydantic import BaseModel, Field
from typing import Optional

# 댓글 작성 요청
class CommentCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, description="댓글 내용 (길이 제한 없음)")

# 댓글 수정 요청
class CommentUpdateRequest(BaseModel):
    content: str = Field(..., min_length=1, description="댓글 내용 (길이 제한 없음)")

# 작성자 정보
class CommentAuthorInfo(BaseModel):
    userId: int
    nickname: str
    profileImageUrl: str

# 댓글 목록조회/상세조회 성공 응답 (data 항목용)
class CommentResponse(BaseModel):
    commentId: int
    content: str
    author: CommentAuthorInfo
    createdAt: str
    postId: Optional[int] = None  # 목록 조회 시 포함

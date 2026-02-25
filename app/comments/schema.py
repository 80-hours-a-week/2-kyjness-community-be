from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CommentUpsertRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=500, description="댓글 내용 (1~500자)")


class CommentAuthorInfo(BaseModel):
    id: int = Field(serialization_alias="userId")
    nickname: str
    profile_image_url: Optional[str] = Field(default=None, serialization_alias="profileImageUrl")


class CommentResponse(BaseModel):
    id: int = Field(serialization_alias="commentId")
    content: str
    author: CommentAuthorInfo
    created_at: datetime = Field(serialization_alias="createdAt")
    post_id: Optional[int] = Field(default=None, serialization_alias="postId")

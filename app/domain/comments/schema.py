# 댓글 요청/응답 DTO. CommentCreateRequest, CommentResponse, 목록 스키마.
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.common import UtcDatetime


class CommentUpsertRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=500, description="댓글 내용 (1~500자)")


class CommentAuthorInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(serialization_alias="userId")
    nickname: str
    profile_image_id: Optional[int] = Field(default=None, serialization_alias="profileImageId")
    profile_image_url: Optional[str] = Field(default=None, serialization_alias="profileImageUrl")

    @model_validator(mode="wrap")
    @classmethod
    def anonymize_inactive_user(cls, data, handler):
        if hasattr(data, "is_active") and data.is_active is False:
            return handler({
                "id": data.id,
                "nickname": "알수없음",
                "profile_image_id": None,
                "profile_image_url": None,
            })
        return handler(data)


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(serialization_alias="commentId")
    content: str
    author: CommentAuthorInfo
    created_at: UtcDatetime = Field(serialization_alias="createdAt")
    post_id: Optional[int] = Field(default=None, serialization_alias="postId")

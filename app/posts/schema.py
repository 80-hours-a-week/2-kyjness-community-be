from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class PostCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=26)
    content: str = Field(..., min_length=1)
    image_ids: Optional[List[int]] = Field(default=None, max_length=5, validation_alias="imageIds", serialization_alias="imageIds")

    @field_validator("image_ids")
    @classmethod
    def image_ids_max_five_create(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        if v is not None and len(v) > 5:
            raise ValueError("POST_FILE_LIMIT_EXCEEDED")
        return v


class PostUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=26)
    content: Optional[str] = Field(default=None, min_length=1)
    image_ids: Optional[List[int]] = Field(default=None, validation_alias="imageIds", serialization_alias="imageIds")

    @field_validator("image_ids")
    @classmethod
    def image_ids_max_five_update(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        if v is not None and len(v) > 5:
            raise ValueError("POST_FILE_LIMIT_EXCEEDED")
        return v


class AuthorInfo(BaseModel):
    id: int = Field(serialization_alias="userId")
    nickname: str
    profile_image_url: str = Field(serialization_alias="profileImageUrl", default="")

    @field_validator("profile_image_url", mode="before")
    @classmethod
    def empty_str_if_none(cls, v):
        return (v or "").strip() or ""


class FileInfo(BaseModel):
    id: int = Field(serialization_alias="fileId")
    file_url: str = Field(serialization_alias="fileUrl", default="")
    image_id: Optional[int] = Field(default=None, serialization_alias="imageId")

    @field_validator("file_url", mode="before")
    @classmethod
    def empty_str_if_none(cls, v):
        return (v or "").strip() or ""


class PostListQuery(BaseModel):
    page: int = Field(1, ge=1, description="페이지 번호")
    size: int = Field(10, ge=1, le=100, description="페이지 크기 (기본 10, 최대 100)")


class PostListResponse(BaseModel):
    id: int = Field(serialization_alias="postId")
    title: str
    content_preview: str = Field(serialization_alias="contentPreview")
    view_count: int = Field(serialization_alias="hits", default=0)
    like_count: int = Field(serialization_alias="likeCount", default=0)
    comment_count: int = Field(serialization_alias="commentCount", default=0)
    author: AuthorInfo
    files: List[FileInfo] = Field(default_factory=list)
    created_at: datetime = Field(serialization_alias="createdAt")

    @classmethod
    def from_rows(cls, post_row: dict, file_rows: List[dict], author_row: dict, preview_length: int = 100) -> "PostListResponse":
        content = (post_row.get("content") or "").strip()
        content_preview = content[:preview_length] if len(content) > preview_length else content
        data = {
            **post_row,
            "content_preview": content_preview,
            "author": author_row,
            "files": (file_rows or [])[:1],
        }
        return cls.model_validate(data)


class PostResponse(BaseModel):
    id: int = Field(serialization_alias="postId")
    title: str
    content: str
    view_count: int = Field(serialization_alias="hits", default=0)
    like_count: int = Field(serialization_alias="likeCount", default=0)
    comment_count: int = Field(serialization_alias="commentCount", default=0)
    author: AuthorInfo
    files: List[FileInfo] = Field(default_factory=list)
    created_at: datetime = Field(serialization_alias="createdAt")

    @classmethod
    def from_rows(cls, post_row: dict, file_rows: List[dict], author_row: dict) -> "PostResponse":
        data = {
            **post_row,
            "author": author_row,
            "files": (file_rows or [])[:5],
        }
        return cls.model_validate(data)

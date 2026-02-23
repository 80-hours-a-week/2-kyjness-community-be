# app/core/dependencies.py
"""인증·권한 공통 로직 (Route에서 Depends로 사용). DB 세션은 Depends(get_db)로 주입."""

from datetime import datetime
from typing import NamedTuple, Optional

from fastapi import Cookie, Depends, Path, Query
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session

from app.auth.model import AuthModel
from app.core.codes import ApiCode
from app.core.database import get_db
from app.core.response import raise_http_error
from app.users.model import UsersModel
from app.users.schema import UserAvailabilityQuery


# -----------------------------------------------------------------------------
# Auth: 현재 사용자 타입·세션
# -----------------------------------------------------------------------------


class CurrentUser(BaseModel):
    """Depends(get_current_user)로 주입되는 로그인 사용자. user.id, user.email 등으로 사용."""

    id: int = Field(..., description="사용자 ID")
    email: str = ""
    nickname: str = ""
    profile_image_url: str = ""
    created_at: datetime = Field(default_factory=datetime.now)

    model_config = {"from_attributes": True}


def get_current_user(session_id: Optional[str] = Cookie(None), db: Session = Depends(get_db)) -> CurrentUser:
    """Cookie의 session_id로 세션 조회 후 CurrentUser 반환. 없거나 무효면 401."""
    if not session_id:
        raise_http_error(401, ApiCode.UNAUTHORIZED)
    user_id = AuthModel.get_user_id_by_session(session_id, db=db)
    if not user_id:
        raise_http_error(401, ApiCode.UNAUTHORIZED)
    user = UsersModel.find_user_by_id(user_id, db=db)
    if not user:
        raise_http_error(401, ApiCode.UNAUTHORIZED)
    return CurrentUser.model_validate(user)


def get_current_user_optional(session_id: Optional[str] = Cookie(None), db: Session = Depends(get_db)) -> Optional[CurrentUser]:
    """세션 있으면 CurrentUser 반환, 없거나 무효면 None."""
    if not session_id:
        return None
    user_id = AuthModel.get_user_id_by_session(session_id, db=db)
    if not user_id:
        return None
    user = UsersModel.find_user_by_id(user_id, db=db)
    return CurrentUser.model_validate(user) if user else None


# -----------------------------------------------------------------------------
# Users: 가용성 조회 쿼리
# -----------------------------------------------------------------------------


def parse_availability_query(email: Optional[str] = Query(None, description="이메일"), nickname: Optional[str] = Query(None, description="닉네임")) -> UserAvailabilityQuery:
    """이메일·닉네임 가용 여부 쿼리 파싱. 최소 하나 필수."""
    try:
        return UserAvailabilityQuery(email=email, nickname=nickname)
    except ValidationError:
        raise_http_error(400, ApiCode.INVALID_REQUEST)


# -----------------------------------------------------------------------------
# Posts: 게시글 작성자 권한
# -----------------------------------------------------------------------------


def require_post_author(post_id: int = Path(..., description="게시글 ID"), user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)) -> int:
    """게시글 작성자만 통과. 없으면 404, 타인이면 403."""
    from app.posts.model import PostsModel

    found = PostsModel.find_post_by_id(post_id, db=db)
    if not found:
        raise_http_error(404, ApiCode.POST_NOT_FOUND)
    post_row = found[0]
    if post_row["user_id"] != user.id:
        raise_http_error(403, ApiCode.FORBIDDEN)
    return post_id


# -----------------------------------------------------------------------------
# Comments: 댓글 작성자 권한
# -----------------------------------------------------------------------------


class CommentAuthorContext(NamedTuple):
    """require_comment_author 통과 시 반환."""
    post_id: int
    user_id: int
    comment_id: int


def require_comment_author(post_id: int = Path(..., description="게시글 ID"), comment_id: int = Path(..., description="댓글 ID"), user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)) -> CommentAuthorContext:
    """댓글 작성자만 통과."""
    from app.comments.model import CommentsModel
    from app.posts.model import PostsModel

    post = PostsModel.find_post_by_id(post_id, db=db)
    if not post:
        raise_http_error(404, ApiCode.POST_NOT_FOUND)
    comment = CommentsModel.find_comment_by_id(comment_id, db=db)
    if not comment:
        raise_http_error(404, ApiCode.COMMENT_NOT_FOUND)
    if comment["post_id"] != post_id:
        raise_http_error(400, ApiCode.INVALID_POSTID_FORMAT)
    if comment["author_id"] != user.id:
        raise_http_error(403, ApiCode.FORBIDDEN)
    return CommentAuthorContext(post_id=post_id, user_id=user.id, comment_id=comment_id)

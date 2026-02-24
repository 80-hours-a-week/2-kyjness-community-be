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


class CurrentUser(BaseModel):
    id: int = Field(..., description="사용자 ID")
    email: str = ""
    nickname: str = ""
    profile_image_url: str = ""
    created_at: datetime = Field(default_factory=datetime.now)

    model_config = {"from_attributes": True}


def get_current_user(session_id: Optional[str] = Cookie(None), db: Session = Depends(get_db)) -> CurrentUser:
    if not session_id:
        raise_http_error(401, ApiCode.UNAUTHORIZED)
    user_id = AuthModel.get_user_id_by_session(session_id, db=db)
    if not user_id:
        raise_http_error(401, ApiCode.UNAUTHORIZED)
    user = UsersModel.find_user_by_id(user_id, db=db)
    if not user:
        raise_http_error(401, ApiCode.UNAUTHORIZED)
    return CurrentUser.model_validate(user)


def parse_availability_query(email: Optional[str] = Query(None, description="이메일"), nickname: Optional[str] = Query(None, description="닉네임")) -> UserAvailabilityQuery:
    try:
        return UserAvailabilityQuery(email=email, nickname=nickname)
    except ValidationError:
        raise_http_error(400, ApiCode.INVALID_REQUEST)


def require_post_author(post_id: int = Path(..., ge=1, description="게시글 ID"), user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)) -> int:
    from app.posts.model import PostsModel

    author_id = PostsModel.get_post_author_id(post_id, db=db)
    if author_id is None:
        raise_http_error(404, ApiCode.POST_NOT_FOUND)
    if author_id != user.id:
        raise_http_error(403, ApiCode.FORBIDDEN)
    return post_id


class CommentAuthorContext(NamedTuple):
    post_id: int
    user_id: int
    comment_id: int


def require_comment_author(post_id: int = Path(..., ge=1, description="게시글 ID"), comment_id: int = Path(..., ge=1, description="댓글 ID"), user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)) -> CommentAuthorContext:
    from app.comments.model import CommentsModel
    from app.posts.model import PostsModel

    if PostsModel.get_post_author_id(post_id, db=db) is None:
        raise_http_error(404, ApiCode.POST_NOT_FOUND)
    comment = CommentsModel.find_comment_by_id(comment_id, db=db)
    if not comment:
        raise_http_error(404, ApiCode.COMMENT_NOT_FOUND)
    if comment["post_id"] != post_id:
        raise_http_error(400, ApiCode.INVALID_POSTID_FORMAT)
    if comment["author_id"] != user.id:
        raise_http_error(403, ApiCode.FORBIDDEN)
    return CommentAuthorContext(post_id=post_id, user_id=user.id, comment_id=comment_id)

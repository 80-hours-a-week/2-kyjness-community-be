# app/posts/controller.py

import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import CurrentUser
from app.core.response import raise_http_error, success_response
from app.core.codes import ApiCode
from app.media.model import MediaModel
from app.posts.model import PostLikesModel, PostsModel
from app.posts.schema import PostCreateRequest, PostUpdateRequest, PostResponse, PostListResponse
from app.users.model import UsersModel

logger = logging.getLogger(__name__)


def create_post(user: CurrentUser, data: PostCreateRequest, db: Session):
    try:
        if data.image_ids:
            for iid in data.image_ids:
                if MediaModel.get_url_by_id(iid, db=db) is None:
                    raise_http_error(400, ApiCode.INVALID_REQUEST)
        post_id = PostsModel.create_post(user.id, data.title, data.content, data.image_ids, db=db)
        return success_response(ApiCode.POST_UPLOADED, {"postId": post_id})
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("게시글 작성 실패 user_id=%s: %s", user.id, e)
        raise_http_error(500, ApiCode.INTERNAL_SERVER_ERROR)


def get_posts(page: int, size: int, db: Session):
    posts_with_files, has_more = PostsModel.get_all_posts(page, size, db=db)
    if not posts_with_files:
        return {"code": ApiCode.POSTS_RETRIEVED.value, "data": [], "hasMore": has_more}
    user_ids = list({post_row["user_id"] for post_row, _ in posts_with_files})
    authors_by_id = UsersModel.find_users_by_ids(user_ids, db=db)
    result = []
    for post_row, file_rows in posts_with_files:
        author = authors_by_id.get(post_row["user_id"])
        if author:
            result.append(
                PostListResponse.from_rows(post_row, file_rows, author).model_dump(by_alias=True)
            )
    return {"code": ApiCode.POSTS_RETRIEVED.value, "data": result, "hasMore": has_more}


def record_post_view(post_id: int, db: Session) -> None:
    if PostsModel.find_post_by_id(post_id, db=db) is None:
        raise_http_error(404, ApiCode.POST_NOT_FOUND)
    PostsModel.increment_view_count(post_id, db=db)


def get_post(post_id: int, db: Session):
    found = PostsModel.find_post_by_id(post_id, db=db)
    if not found:
        raise_http_error(404, ApiCode.POST_NOT_FOUND)
    post_row, file_rows = found
    author = UsersModel.find_user_by_id(post_row["user_id"], db=db)
    if not author:
        raise_http_error(404, ApiCode.USER_NOT_FOUND)
    data = PostResponse.from_rows(post_row, file_rows, author).model_dump(by_alias=True)
    return success_response(ApiCode.POST_RETRIEVED, data)


def update_post(post_id: int, data: PostUpdateRequest, db: Session):
    if PostsModel.find_post_by_id(post_id, db=db) is None:
        raise_http_error(404, ApiCode.POST_NOT_FOUND)
    if data.image_ids is not None:
        for iid in data.image_ids:
            if MediaModel.get_url_by_id(iid, db=db) is None:
                raise_http_error(400, ApiCode.INVALID_REQUEST)
    PostsModel.update_post(post_id, title=data.title, content=data.content, image_ids=data.image_ids, db=db)
    return success_response(ApiCode.POST_UPDATED)


def withdraw_post(post_id: int, db: Session):
    if not PostsModel.withdraw_post(post_id, db=db):
        raise_http_error(404, ApiCode.POST_NOT_FOUND)


def add_like(post_id: int, user: CurrentUser, db: Session) -> tuple[dict, int]:
    """(응답 dict, HTTP status_code) 반환. INSERT 성공 시 201, 중복(이미 좋아요) 시 200. UNIQUE(post_id, user_id)로 처리."""
    if PostsModel.find_post_by_id(post_id, db=db) is None:
        raise_http_error(404, ApiCode.POST_NOT_FOUND)
    like = PostLikesModel.add_like(post_id, user.id, db=db)
    if like:
        like_count = PostsModel.increment_like_count(post_id, db=db)
        return success_response(ApiCode.POSTLIKE_UPLOADED, {"likeCount": like_count}), 201
    like_count = PostsModel.get_like_count(post_id, db=db)
    return success_response(ApiCode.ALREADY_LIKED, {"likeCount": like_count}), 200


def remove_like(post_id: int, user: CurrentUser, db: Session):
    if PostsModel.find_post_by_id(post_id, db=db) is None:
        raise_http_error(404, ApiCode.POST_NOT_FOUND)
    if not PostLikesModel.remove_like(post_id, user.id, db=db):
        raise_http_error(404, ApiCode.LIKE_NOT_FOUND)
    like_count = PostsModel.decrement_like_count(post_id, db=db)
    return success_response(ApiCode.LIKE_DELETED, {"likeCount": like_count})

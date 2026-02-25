import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import CurrentUser
from app.core.response import raise_http_error, success_response
from app.core.codes import ApiCode
from app.posts.helpers import ensure_image_ids_exist, ensure_post_exists, post_valid_files
from app.posts.model import PostLikesModel, PostsModel
from app.posts.schema import PostCreateRequest, PostUpdateRequest, PostResponse, PostListResponse, AuthorInfo

logger = logging.getLogger(__name__)


def create_post(user: CurrentUser, data: PostCreateRequest, db: Session) -> dict:
    try:
        ensure_image_ids_exist(data.image_ids, db)
        post_id = PostsModel.create_post(user.id, data.title, data.content, data.image_ids, db=db)
        return success_response(ApiCode.POST_UPLOADED, {"postId": post_id})
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("게시글 작성 실패 user_id=%s: %s", user.id, e)
        raise_http_error(500, ApiCode.INTERNAL_SERVER_ERROR)


def get_posts(page: int, size: int, db: Session) -> dict:
    posts, has_more = PostsModel.get_all_posts(page, size, db=db)
    if not posts:
        return success_response(ApiCode.POSTS_RETRIEVED, {"list": [], "hasMore": has_more})
    result = []
    for post in posts:
        if not post.user or post.user.deleted_at is not None:
            continue
        content = (post.content or "").strip()
        content_preview = content[:100] if len(content) > 100 else content
        result.append(PostListResponse(id=post.id, title=post.title, content_preview=content_preview, view_count=post.view_count, like_count=post.like_count, comment_count=post.comment_count, author=AuthorInfo.model_validate(post.user), files=post_valid_files(post, 1), created_at=post.created_at))
    return success_response(ApiCode.POSTS_RETRIEVED, {"list": result, "hasMore": has_more})


def record_post_view(post_id: int, db: Session) -> None:
    ensure_post_exists(post_id, db)
    PostsModel.increment_view_count(post_id, db=db)


def get_post(post_id: int, db: Session) -> dict:
    post = ensure_post_exists(post_id, db)
    if not post.user or post.user.deleted_at is not None:
        raise_http_error(404, ApiCode.USER_NOT_FOUND)
    data = PostResponse(id=post.id, title=post.title, content=post.content, view_count=post.view_count, like_count=post.like_count, comment_count=post.comment_count, author=AuthorInfo.model_validate(post.user), files=post_valid_files(post, 5), created_at=post.created_at)
    return success_response(ApiCode.POST_RETRIEVED, data)


def update_post(post_id: int, data: PostUpdateRequest, db: Session) -> dict:
    ensure_post_exists(post_id, db)
    ensure_image_ids_exist(data.image_ids, db)
    PostsModel.update_post(post_id, title=data.title, content=data.content, image_ids=data.image_ids, db=db)
    return success_response(ApiCode.POST_UPDATED)


def withdraw_post(post_id: int, db: Session) -> None:
    ensure_post_exists(post_id, db)
    if not PostsModel.withdraw_post(post_id, db=db):
        raise_http_error(404, ApiCode.POST_NOT_FOUND)


def add_like(post_id: int, user: CurrentUser, db: Session) -> tuple[dict, int]:
    ensure_post_exists(post_id, db)
    like = PostLikesModel.add_like(post_id, user.id, db=db)
    if like:
        like_count = PostsModel.increment_like_count(post_id, db=db)
        return success_response(ApiCode.POSTLIKE_UPLOADED, {"likeCount": like_count}), 201
    like_count = PostsModel.get_like_count(post_id, db=db)
    return success_response(ApiCode.ALREADY_LIKED, {"likeCount": like_count}), 200


def remove_like(post_id: int, user: CurrentUser, db: Session) -> dict:
    ensure_post_exists(post_id, db)
    if not PostLikesModel.remove_like(post_id, user.id, db=db):
        raise_http_error(404, ApiCode.LIKE_NOT_FOUND)
    like_count = PostsModel.decrement_like_count(post_id, db=db)
    return success_response(ApiCode.LIKE_DELETED, {"likeCount": like_count})

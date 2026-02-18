# app/posts/posts_controller.py
"""게시글 비즈니스 로직. 권한(작성자)은 Route(require_post_author), 검증·응답은 core 사용."""

from typing import Optional

from fastapi import UploadFile

from app.posts.posts_model import PostsModel, PostLikesModel
from app.posts.posts_schema import PostResponse, AuthorInfo, FileInfo
from app.auth.auth_model import AuthModel
from app.core.codes import ApiCode
from app.core.response import success_response, raise_http_error
from app.core.file_upload import save_post_image


def create_post(user_id: int, title: str, content: str, file_url: str = ""):
    # fileUrl 형식 검증은 DTO(PostCreateRequest)에서 완료
    post = PostsModel.create_post(user_id, title, content, file_url or "")
    return success_response(ApiCode.POST_UPLOADED, {"postId": post["postId"]})


async def upload_post_image(post_id: int, user_id: int, file: Optional[UploadFile]):
    """게시글 이미지 업로드. 최대 5장. 검증·저장·URL은 file_upload.save_post_image에서 처리."""
    post = PostsModel.find_post_by_id(post_id)
    if not post:
        raise_http_error(404, ApiCode.POST_NOT_FOUND)
    if len(post.get("files", [])) >= PostsModel.MAX_POST_FILES:
        raise_http_error(400, ApiCode.POST_FILE_LIMIT_EXCEEDED)
    file_url = await save_post_image(post_id, file)
    PostsModel.update_post(post_id, title=None, content=None, file_url=file_url)
    return success_response(ApiCode.POST_IMAGE_UPLOADED, {"postFileUrl": file_url})


def _post_to_response_item(post: dict, author: dict) -> dict:
    """단일 게시글 dict를 PostResponse 스키마로 검증 후 반환."""
    item = PostResponse(
        postId=post["postId"],
        title=post["title"],
        content=post["content"],
        hits=post["hits"],
        likeCount=post["likeCount"],
        commentCount=post["commentCount"],
        author=AuthorInfo(
            userId=author["userId"],
            nickname=author["nickname"],
            profileImageUrl=author.get("profileImageUrl", ""),
        ),
        files=[FileInfo(**f) for f in post.get("files", [])],
        createdAt=post["createdAt"],
    )
    return item.model_dump()


def get_posts(page: int = 1, size: int = 10):
    """무한 스크롤용 게시글 목록. data, hasMore 반환."""
    posts_raw, has_more = PostsModel.get_all_posts(page, size)
    result = []
    for post in posts_raw:
        author = AuthModel.find_user_by_id(post["authorId"])
        if author:
            result.append(_post_to_response_item(post, author))
    return {"code": ApiCode.POSTS_RETRIEVED.value, "data": result, "hasMore": has_more}


def get_post(post_id: int):
    post = PostsModel.find_post_by_id(post_id)
    if not post:
        raise_http_error(404, ApiCode.POST_NOT_FOUND)
    PostsModel.increment_hits(post_id)
    author = AuthModel.find_user_by_id(post["authorId"])
    if not author:
        raise_http_error(404, ApiCode.USER_NOT_FOUND)
    post_with_hits = {**post, "hits": post["hits"] + 1}
    data = _post_to_response_item(post_with_hits, author)
    return success_response(ApiCode.POST_RETRIEVED, data)


def update_post(
    post_id: int,
    user_id: int,
    title: Optional[str] = None,
    content: Optional[str] = None,
    file_url: Optional[str] = None,
):
    """게시글 수정. 작성자 검사는 Route(require_post_author)에서 수행."""
    post = PostsModel.find_post_by_id(post_id)
    if not post:
        raise_http_error(404, ApiCode.POST_NOT_FOUND)
    # fileUrl 형식 검증은 DTO(PostUpdateRequest)에서 완료
    PostsModel.update_post(post_id, title, content, file_url)
    return success_response(ApiCode.POST_UPDATED)


def delete_post(post_id: int, user_id: int):
    """게시글 삭제. 작성자 검사는 Route(require_post_author)에서 수행."""
    post = PostsModel.find_post_by_id(post_id)
    if not post:
        raise_http_error(404, ApiCode.POST_NOT_FOUND)
    PostsModel.delete_post(post_id)
    return success_response(ApiCode.POST_DELETED, None)


def create_like(post_id: int, user_id: int):
    """게시글 좋아요 추가."""
    post = PostsModel.find_post_by_id(post_id)
    if not post:
        raise_http_error(404, ApiCode.POST_NOT_FOUND)
    if PostLikesModel.has_liked(post_id, user_id):
        raise_http_error(409, ApiCode.CONFLICT)
    like = PostLikesModel.create_like(post_id, user_id)
    if not like:
        raise_http_error(409, ApiCode.CONFLICT)
    PostsModel.increment_like_count(post_id)
    updated_post = PostsModel.find_post_by_id(post_id)
    like_count = updated_post["likeCount"] if updated_post else 0
    return success_response(ApiCode.POSTLIKE_UPLOADED, {"likeCount": like_count})


def delete_like(post_id: int, user_id: int):
    """게시글 좋아요 취소. 응답에 likeCount 포함."""
    post = PostsModel.find_post_by_id(post_id)
    if not post:
        raise_http_error(404, ApiCode.POST_NOT_FOUND)
    if not PostLikesModel.has_liked(post_id, user_id):
        raise_http_error(404, ApiCode.LIKE_NOT_FOUND)
    PostLikesModel.delete_like(post_id, user_id)
    PostsModel.decrement_like_count(post_id)
    updated_post = PostsModel.find_post_by_id(post_id)
    like_count = updated_post["likeCount"] if updated_post else 0
    return success_response(ApiCode.LIKE_DELETED, {"likeCount": like_count})

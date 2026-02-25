from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.codes import ApiCode
from app.core.response import raise_http_error
from app.media.model import MediaModel
from app.posts.model import PostsModel
from app.posts.schema import FileInfo


def post_valid_files(post, limit: int = 5) -> List[FileInfo]:
    valid = [pi for pi in post.post_images if pi.image and pi.image.deleted_at is None]
    return [FileInfo(id=pi.id, file_url=pi.image.file_url, image_id=pi.image_id) for pi in valid[:limit]]


def ensure_image_ids_exist(image_ids: Optional[List[int]], db: Session) -> None:
    if not image_ids:
        return
    for iid in image_ids:
        if MediaModel.get_url_by_id(iid, db=db) is None:
            raise_http_error(400, ApiCode.INVALID_REQUEST)


def ensure_post_exists(post_id: int, db: Session):
    post = PostsModel.find_post_by_id(post_id, db=db)
    if post is None:
        raise_http_error(404, ApiCode.POST_NOT_FOUND)
    return post

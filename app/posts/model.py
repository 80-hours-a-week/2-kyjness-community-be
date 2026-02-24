import logging
from typing import List, Optional

from sqlalchemy import text, bindparam
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class PostsModel:
    MAX_POST_IMAGES = 5

    @classmethod
    def create_post(cls, user_id: int, title: str, content: str, image_ids: Optional[List[int]] = None, *, db: Session) -> int:
        image_ids = image_ids or []
        db.execute(
            text("INSERT INTO posts (user_id, title, content) VALUES (:uid, :title, :content)"),
            {"uid": user_id, "title": title, "content": content},
        )
        post_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        for iid in image_ids[: cls.MAX_POST_IMAGES]:
            db.execute(text("INSERT INTO post_images (post_id, image_id) VALUES (:pid, :iid)"), {"pid": post_id, "iid": iid})
        return post_id

    @classmethod
    def find_post_by_id(cls, post_id: int, db: Session) -> Optional[tuple[dict, List[dict]]]:
        row = db.execute(
            text("SELECT id, user_id, title, content, view_count, like_count, comment_count, created_at FROM posts WHERE id = :pid AND deleted_at IS NULL"),
            {"pid": post_id},
        ).mappings().fetchone()
        if not row:
            return None
        file_rows = db.execute(
            text("SELECT pi.id, i.file_url, i.id AS image_id FROM post_images pi INNER JOIN images i ON pi.image_id = i.id AND i.deleted_at IS NULL WHERE pi.post_id = :pid ORDER BY pi.id"),
            {"pid": post_id},
        ).mappings().fetchall()
        return (dict(row), [dict(r) for r in file_rows] if file_rows else [])

    @classmethod
    def get_post_author_id(cls, post_id: int, db: Session) -> Optional[int]:
        row = db.execute(
            text("SELECT user_id FROM posts WHERE id = :pid AND deleted_at IS NULL"),
            {"pid": post_id},
        ).mappings().fetchone()
        return int(row["user_id"]) if row else None

    @classmethod
    def get_all_posts(cls, page: int = 1, size: int = 20, *, db: Session) -> tuple[List[tuple[dict, List[dict]]], bool]:
        offset = (page - 1) * size
        fetch_limit = size + 1
        rows = db.execute(
            text("SELECT id, user_id, title, content, view_count, like_count, comment_count, created_at FROM posts WHERE deleted_at IS NULL ORDER BY id DESC LIMIT :lim OFFSET :off"),
            {"lim": fetch_limit, "off": offset},
        ).mappings().fetchall()
        has_more = len(rows) > size
        rows = rows[:size]
        if not rows:
            return [], has_more
        post_ids = [r["id"] for r in rows]
        stmt = text("SELECT pi.post_id, pi.id, i.file_url, i.id AS image_id FROM post_images pi INNER JOIN images i ON pi.image_id = i.id AND i.deleted_at IS NULL WHERE pi.post_id IN :ids ORDER BY pi.post_id, pi.id").bindparams(bindparam("ids", expanding=True))
        all_file_rows = db.execute(stmt, {"ids": post_ids}).mappings().fetchall()
        files_by_post: dict[int, list] = {pid: [] for pid in post_ids}
        for fr in all_file_rows:
            files_by_post[fr["post_id"]].append(dict(fr))
        result = [(dict(row), files_by_post.get(row["id"]) or []) for row in rows]
        return result, has_more

    @classmethod
    def update_post(cls, post_id: int, title: Optional[str] = None, content: Optional[str] = None, image_ids: Optional[List[int]] = None, *, db: Session) -> bool:
        if title is not None:
            db.execute(text("UPDATE posts SET title = :title WHERE id = :pid AND deleted_at IS NULL"), {"title": title, "pid": post_id})
        if content is not None:
            db.execute(text("UPDATE posts SET content = :content WHERE id = :pid AND deleted_at IS NULL"), {"content": content, "pid": post_id})
        if image_ids is not None:
            old_rows = db.execute(text("SELECT image_id FROM post_images WHERE post_id = :pid"), {"pid": post_id}).mappings().fetchall()
            old_image_ids = {r["image_id"] for r in old_rows}
            new_image_ids_set = set(image_ids[: cls.MAX_POST_IMAGES])
            to_add = new_image_ids_set - old_image_ids
            to_remove = old_image_ids - new_image_ids_set
            for iid in to_add:
                db.execute(text("INSERT INTO post_images (post_id, image_id) VALUES (:pid, :iid)"), {"pid": post_id, "iid": iid})
            if to_remove:
                stmt = text("DELETE FROM post_images WHERE post_id = :pid AND image_id IN :ids").bindparams(bindparam("ids", expanding=True))
                db.execute(stmt, {"pid": post_id, "ids": list(to_remove)})
            for img_id in to_remove:
                row = db.execute(text("SELECT 1 FROM post_images WHERE image_id = :iid LIMIT 1"), {"iid": img_id}).mappings().fetchone()
                if row is None:
                    db.execute(text("UPDATE images SET deleted_at = NOW() WHERE id = :iid AND deleted_at IS NULL"), {"iid": img_id})
        return True

    @classmethod
    def withdraw_post(cls, post_id: int, db: Session) -> bool:
        db.execute(text("UPDATE comments SET deleted_at = NOW() WHERE post_id = :pid AND deleted_at IS NULL"), {"pid": post_id})
        db.execute(text("DELETE FROM likes WHERE post_id = :pid"), {"pid": post_id})
        img_rows = db.execute(text("SELECT image_id FROM post_images WHERE post_id = :pid"), {"pid": post_id}).mappings().fetchall()
        image_ids = [r["image_id"] for r in img_rows]
        db.execute(text("DELETE FROM post_images WHERE post_id = :pid"), {"pid": post_id})
        for img_id in image_ids:
            row = db.execute(text("SELECT 1 FROM post_images WHERE image_id = :iid LIMIT 1"), {"iid": img_id}).mappings().fetchone()
            if row is None:
                db.execute(text("UPDATE images SET deleted_at = NOW() WHERE id = :iid AND deleted_at IS NULL"), {"iid": img_id})
        result = db.execute(text("UPDATE posts SET deleted_at = NOW() WHERE id = :pid AND deleted_at IS NULL"), {"pid": post_id})
        return result.rowcount > 0

    @classmethod
    def increment_view_count(cls, post_id: int, db: Session) -> bool:
        db.execute(text("UPDATE posts SET view_count = view_count + 1 WHERE id = :pid AND deleted_at IS NULL"), {"pid": post_id})
        return True

    @classmethod
    def get_like_count(cls, post_id: int, db: Session) -> int:
        """동시성 고려: 응답용 like_count는 이 값 사용 (stale 방지)."""
        row = db.execute(text("SELECT like_count FROM posts WHERE id = :pid"), {"pid": post_id}).mappings().fetchone()
        return int(row["like_count"]) if row else 0

    @classmethod
    def increment_like_count(cls, post_id: int, db: Session) -> int:
        db.execute(text("UPDATE posts SET like_count = like_count + 1 WHERE id = :pid"), {"pid": post_id})
        row = db.execute(text("SELECT like_count FROM posts WHERE id = :pid"), {"pid": post_id}).mappings().fetchone()
        return row["like_count"] if row else 0

    @classmethod
    def decrement_like_count(cls, post_id: int, db: Session) -> int:
        db.execute(text("UPDATE posts SET like_count = GREATEST(0, like_count - 1) WHERE id = :pid"), {"pid": post_id})
        row = db.execute(text("SELECT like_count FROM posts WHERE id = :pid"), {"pid": post_id}).mappings().fetchone()
        return row["like_count"] if row else 0

    @classmethod
    def increment_comment_count(cls, post_id: int, db: Session) -> bool:
        db.execute(text("UPDATE posts SET comment_count = comment_count + 1 WHERE id = :pid"), {"pid": post_id})
        return True

    @classmethod
    def decrement_comment_count(cls, post_id: int, db: Session) -> bool:
        db.execute(text("UPDATE posts SET comment_count = GREATEST(0, comment_count - 1) WHERE id = :pid"), {"pid": post_id})
        return True


class PostLikesModel:
    """likes 테이블 (post_id, user_id) UNIQUE. 중복 좋아요 시 IntegrityError로 처리."""

    @classmethod
    def add_like(cls, post_id: int, user_id: int, *, db: Session) -> Optional[dict]:
        try:
            db.execute(text("INSERT INTO likes (post_id, user_id) VALUES (:pid, :uid)"), {"pid": post_id, "uid": user_id})
            return {"post_id": post_id, "user_id": user_id}
        except IntegrityError:
            return None
        except Exception as e:
            logger.exception("likes INSERT 실패: %s", e)
            raise

    @classmethod
    def remove_like(cls, post_id: int, user_id: int, db: Session) -> bool:
        result = db.execute(text("DELETE FROM likes WHERE post_id = :pid AND user_id = :uid"), {"pid": post_id, "uid": user_id})
        return result.rowcount > 0

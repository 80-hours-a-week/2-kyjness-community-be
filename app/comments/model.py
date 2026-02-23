# app/comments/model.py

from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


class CommentsModel:
    @classmethod
    def create_comment(cls, post_id: int, user_id: int, content: str, db: Session) -> dict:
        db.execute(
            text("INSERT INTO comments (post_id, author_id, content) VALUES (:pid, :uid, :content)"),
            {"pid": post_id, "uid": user_id, "content": content},
        )
        comment_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        row = db.execute(text("SELECT id, post_id, author_id, content, created_at FROM comments WHERE id = :cid"), {"cid": comment_id}).mappings().fetchone()
        return dict(row) if row else {}

    @classmethod
    def find_comment_by_id(cls, comment_id: int, db: Session) -> Optional[dict]:
        row = db.execute(
            text("SELECT id, post_id, author_id, content, created_at FROM comments WHERE id = :cid AND deleted_at IS NULL"),
            {"cid": comment_id},
        ).mappings().fetchone()
        return dict(row) if row else None

    @classmethod
    def get_comments_by_post_id(cls, post_id: int, page: int = 1, size: int = 10, *, db: Session) -> List[dict]:
        offset = (page - 1) * size
        rows = db.execute(
            text("""
                SELECT c.id, c.post_id, c.author_id, c.content, c.created_at,
                       u.id AS author_user_id, u.nickname AS author_nickname,
                       u.profile_image_url AS author_profile_image_url
                FROM comments c
                INNER JOIN users u ON u.id = c.author_id AND u.deleted_at IS NULL
                WHERE c.post_id = :pid AND c.deleted_at IS NULL
                ORDER BY c.id DESC LIMIT :sz OFFSET :off
            """),
            {"pid": post_id, "sz": size, "off": offset},
        ).mappings().fetchall()
        return [dict(r) for r in rows]

    @classmethod
    def get_comment_count_by_post_id(cls, post_id: int, db: Session) -> int:
        row = db.execute(
            text("SELECT COUNT(*) AS cnt FROM comments WHERE post_id = :pid AND deleted_at IS NULL"),
            {"pid": post_id},
        ).mappings().fetchone()
        return int(row["cnt"]) if row else 0

    @classmethod
    def update_comment(cls, post_id: int, comment_id: int, content: str, db: Session) -> int:
        result = db.execute(
            text("UPDATE comments SET content = :content WHERE id = :cid AND post_id = :pid AND deleted_at IS NULL"),
            {"content": content, "cid": comment_id, "pid": post_id},
        )
        return result.rowcount

    @classmethod
    def withdraw_comment(cls, post_id: int, comment_id: int, db: Session) -> bool:
        result = db.execute(
            text("UPDATE comments SET deleted_at = NOW() WHERE id = :cid AND post_id = :pid"),
            {"cid": comment_id, "pid": post_id},
        )
        return result.rowcount > 0

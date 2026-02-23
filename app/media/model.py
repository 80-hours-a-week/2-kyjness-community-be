# app/media/model.py

from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


class MediaModel:
    @classmethod
    def create_image(cls, file_key: str, file_url: str, content_type: Optional[str] = None, size: Optional[int] = None, uploader_id: Optional[int] = None, *, db: Session) -> dict:
        db.execute(
            text("INSERT INTO images (file_key, file_url, content_type, size, uploader_id) VALUES (:fk, :url, :ct, :sz, :uid)"),
            {"fk": file_key, "url": file_url, "ct": content_type, "sz": size, "uid": uploader_id},
        )
        image_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        return {"id": image_id, "file_url": file_url}

    @classmethod
    def get_url_by_id(cls, image_id: int, db: Session) -> Optional[str]:
        row = db.execute(
            text("SELECT file_url FROM images WHERE id = :iid AND deleted_at IS NULL"),
            {"iid": image_id},
        ).mappings().fetchone()
        return row["file_url"] if row else None

    @classmethod
    def withdraw_image_by_owner(cls, image_id: int, user_id: int, db: Session) -> bool:
        result = db.execute(
            text("UPDATE images SET deleted_at = NOW() WHERE id = :iid AND uploader_id = :uid AND deleted_at IS NULL"),
            {"iid": image_id, "uid": user_id},
        )
        return result.rowcount > 0

    @classmethod
    def withdraw_by_url(cls, file_url: str, db: Session) -> bool:
        if not file_url or not file_url.strip():
            return False
        result = db.execute(
            text("UPDATE images SET deleted_at = NOW() WHERE file_url = :url AND deleted_at IS NULL"),
            {"url": file_url.strip()},
        )
        return result.rowcount > 0

from datetime import datetime
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.orm import Session, mapped_column
from sqlalchemy import String, Integer, DateTime, ForeignKey

from app.core.database import Base
from app.core.storage import storage_delete


class Image(Base):
    __tablename__ = "images"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_key = mapped_column(String(255), nullable=False)
    file_url = mapped_column(String(999), nullable=False)
    content_type = mapped_column(String(255), nullable=True)
    size = mapped_column(Integer, nullable=True)
    uploader_id = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = mapped_column(DateTime, nullable=True)
    deleted_at = mapped_column(DateTime, nullable=True)


class MediaModel:
    @classmethod
    def create_image(cls, file_key: str, file_url: str, content_type: Optional[str] = None, size: Optional[int] = None, uploader_id: Optional[int] = None, *, db: Session) -> dict:
        img = Image(
            file_key=file_key,
            file_url=file_url,
            content_type=content_type,
            size=size,
            uploader_id=uploader_id,
        )
        db.add(img)
        db.flush()
        return {"id": img.id, "file_url": file_url}

    @classmethod
    def get_url_by_id(cls, image_id: int, db: Session) -> Optional[str]:
        row = db.execute(select(Image.file_url).where(Image.id == image_id, Image.deleted_at.is_(None))).scalar_one_or_none()
        return row

    @classmethod
    def withdraw_image_by_owner(cls, image_id: int, user_id: int, db: Session) -> bool:
        r = db.execute(
            update(Image)
            .where(Image.id == image_id, Image.uploader_id == user_id, Image.deleted_at.is_(None))
            .values(deleted_at=datetime.now())
        )
        return r.rowcount > 0

    @classmethod
    def withdraw_by_url(cls, file_url: str, db: Session) -> bool:
        if not file_url or not file_url.strip():
            return False
        row = db.execute(select(Image.file_key).where(Image.file_url == file_url.strip(), Image.deleted_at.is_(None))).scalar_one_or_none()
        if not row:
            return False
        try:
            storage_delete(row)
        except Exception:
            pass
        r = db.execute(update(Image).where(Image.file_url == file_url.strip(), Image.deleted_at.is_(None)).values(deleted_at=datetime.now()))
        return r.rowcount > 0

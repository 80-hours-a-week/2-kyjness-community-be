from datetime import datetime
from typing import List, Optional

from sqlalchemy import text, bindparam
from sqlalchemy.orm import Session


class UsersModel:

    @classmethod
    def create_user(cls, email: str, hashed_password: str, nickname: str, profile_image_url: Optional[str] = None, *, db: Session) -> dict:
        profile = profile_image_url if profile_image_url else ""
        db.execute(
            text("INSERT INTO users (email, password, nickname, profile_image_url) VALUES (:email, :pw, :nick, :profile)"),
            {"email": email.lower(), "pw": hashed_password, "nick": nickname, "profile": profile},
        )
        user_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        return {"id": user_id, "email": email, "nickname": nickname, "profile_image_url": profile, "created_at": datetime.now()}

    @classmethod
    def find_user_by_id(cls, user_id: int, db: Session) -> Optional[dict]:
        row = db.execute(
            text("SELECT id, email, nickname, profile_image_url, created_at FROM users WHERE id = :uid AND deleted_at IS NULL"),
            {"uid": user_id},
        ).mappings().fetchone()
        return dict(row) if row else None

    @classmethod
    def find_users_by_ids(cls, user_ids: List[int], db: Session) -> dict[int, dict]:
        """N+1 방지: 여러 user_id를 한 번에 조회해 id -> user dict 매핑 반환."""
        if not user_ids:
            return {}
        stmt = text(
            "SELECT id, email, nickname, profile_image_url, created_at FROM users WHERE id IN :ids AND deleted_at IS NULL"
        ).bindparams(bindparam("ids", expanding=True))
        rows = db.execute(stmt, {"ids": user_ids}).mappings().fetchall()
        return {int(r["id"]): dict(r) for r in rows}

    @classmethod
    def find_user_by_email(cls, email: str, db: Session) -> Optional[dict]:
        row = db.execute(
            text("SELECT id, email, password, nickname, profile_image_url, created_at FROM users WHERE email = :email AND deleted_at IS NULL"),
            {"email": email.lower()},
        ).mappings().fetchone()
        return dict(row) if row else None

    @classmethod
    def get_password_hash(cls, user_id: int, db: Session) -> Optional[str]:
        row = db.execute(
            text("SELECT password FROM users WHERE id = :uid AND deleted_at IS NULL"),
            {"uid": user_id},
        ).mappings().fetchone()
        return row["password"] if row and row.get("password") else None

    @classmethod
    def email_exists(cls, email: str, db: Session) -> bool:
        row = db.execute(
            text("SELECT 1 FROM users WHERE email = :email AND deleted_at IS NULL LIMIT 1"),
            {"email": email.lower()},
        ).mappings().fetchone()
        return row is not None

    @classmethod
    def nickname_exists(cls, nickname: str, db: Session) -> bool:
        row = db.execute(
            text("SELECT 1 FROM users WHERE nickname = :nick AND deleted_at IS NULL LIMIT 1"),
            {"nick": nickname},
        ).mappings().fetchone()
        return row is not None

    @classmethod
    def update_nickname(cls, user_id: int, new_nickname: str, db: Session) -> bool:
        result = db.execute(
            text("UPDATE users SET nickname = :nick WHERE id = :uid AND deleted_at IS NULL"),
            {"nick": new_nickname, "uid": user_id},
        )
        return result.rowcount > 0

    @classmethod
    def update_password(cls, user_id: int, hashed_password: str, db: Session) -> bool:
        result = db.execute(
            text("UPDATE users SET password = :pw WHERE id = :uid AND deleted_at IS NULL"),
            {"pw": hashed_password, "uid": user_id},
        )
        return result.rowcount > 0

    @classmethod
    def update_profile_image_url(cls, user_id: int, profile_image_url: str, db: Session) -> bool:
        result = db.execute(
            text("UPDATE users SET profile_image_url = :url WHERE id = :uid AND deleted_at IS NULL"),
            {"url": profile_image_url, "uid": user_id},
        )
        return result.rowcount > 0

    @classmethod
    def withdraw_user(cls, user_id: int, db: Session) -> bool:
        result = db.execute(text("UPDATE users SET deleted_at = NOW() WHERE id = :uid"), {"uid": user_id})
        return result.rowcount > 0

from datetime import datetime, timedelta
from typing import Optional

import secrets
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_connection


class AuthModel:
    SESSION_EXPIRY_TIME = settings.SESSION_EXPIRY_TIME

    @classmethod
    def create_session(cls, user_id: int, db: Session) -> str:
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(seconds=cls.SESSION_EXPIRY_TIME)
        db.execute(
            text("INSERT INTO sessions (session_id, user_id, expires_at) VALUES (:sid, :uid, :exp)"),
            {"sid": session_id, "uid": user_id, "exp": expires_at},
        )
        return session_id

    @classmethod
    def get_user_id_by_session(cls, session_id: Optional[str], db: Session) -> Optional[int]:
        if not session_id:
            return None
        row = db.execute(
            text("SELECT user_id FROM sessions WHERE session_id = :sid AND expires_at > NOW()"),
            {"sid": session_id},
        ).mappings().fetchone()
        return row["user_id"] if row else None

    @classmethod
    def revoke_session(cls, session_id: Optional[str], db: Session) -> bool:
        if not session_id:
            return False
        result = db.execute(text("DELETE FROM sessions WHERE session_id = :sid"), {"sid": session_id})
        affected = result.rowcount
        return affected > 0

    @classmethod
    def revoke_sessions_for_user(cls, user_id: int, db: Session) -> None:
        db.execute(text("DELETE FROM sessions WHERE user_id = :uid"), {"uid": user_id})

    @classmethod
    def cleanup_expired_sessions(cls) -> int:
        with get_connection() as db:
            result = db.execute(text("DELETE FROM sessions WHERE expires_at <= NOW()"))
            count = result.rowcount
        return count

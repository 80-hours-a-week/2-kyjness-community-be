from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, update, String, Integer, DateTime
from sqlalchemy.orm import Session, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    email = mapped_column(String(255), unique=True, nullable=False)
    password = mapped_column(String(999), nullable=False)
    nickname = mapped_column(String(255), unique=True, nullable=False)
    profile_image_url = mapped_column(String(999), nullable=True)
    created_at = mapped_column(DateTime, nullable=False)
    updated_at = mapped_column(DateTime, nullable=False)
    deleted_at = mapped_column(DateTime, nullable=True)


class UsersModel:

    @classmethod
    def create_user(cls, email: str, hashed_password: str, nickname: str, profile_image_url: Optional[str] = None, *, db: Session) -> dict:
        profile = profile_image_url if profile_image_url else ""
        now = datetime.now()
        user = User(
            email=email.lower(),
            password=hashed_password,
            nickname=nickname,
            profile_image_url=profile or None,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )
        db.add(user)
        db.flush()
        return {"id": user.id, "email": email, "nickname": nickname, "profile_image_url": profile, "created_at": now}

    @classmethod
    def _row_to_dict(cls, row: User, *, include_password: bool = False) -> dict:
        d = {
            "id": row.id,
            "email": row.email,
            "nickname": row.nickname,
            "profile_image_url": row.profile_image_url or "",
            "created_at": row.created_at,
        }
        if include_password:
            d["password"] = row.password
        return d

    @classmethod
    def find_user_by_id(cls, user_id: int, db: Session) -> Optional[dict]:
        row = db.execute(select(User).where(User.id == user_id, User.deleted_at.is_(None))).scalar_one_or_none()
        return cls._row_to_dict(row) if row else None

    @classmethod
    def find_users_by_ids(cls, user_ids: List[int], db: Session) -> dict[int, dict]:
        if not user_ids:
            return {}
        rows = db.execute(select(User).where(User.id.in_(user_ids), User.deleted_at.is_(None))).scalars().all()
        return {r.id: cls._row_to_dict(r) for r in rows}

    @classmethod
    def find_user_by_email(cls, email: str, db: Session) -> Optional[dict]:
        row = db.execute(select(User).where(User.email == email.lower(), User.deleted_at.is_(None))).scalar_one_or_none()
        return cls._row_to_dict(row, include_password=True) if row else None

    @classmethod
    def get_password_hash(cls, user_id: int, db: Session) -> Optional[str]:
        return db.execute(select(User.password).where(User.id == user_id, User.deleted_at.is_(None))).scalar_one_or_none()

    @classmethod
    def email_exists(cls, email: str, db: Session) -> bool:
        return db.execute(select(User.id).where(User.email == email.lower(), User.deleted_at.is_(None)).limit(1)).first() is not None

    @classmethod
    def nickname_exists(cls, nickname: str, db: Session) -> bool:
        return db.execute(select(User.id).where(User.nickname == nickname, User.deleted_at.is_(None)).limit(1)).first() is not None

    @classmethod
    def update_nickname(cls, user_id: int, new_nickname: str, db: Session) -> bool:
        r = db.execute(update(User).where(User.id == user_id, User.deleted_at.is_(None)).values(nickname=new_nickname))
        return r.rowcount > 0

    @classmethod
    def update_password(cls, user_id: int, hashed_password: str, db: Session) -> bool:
        r = db.execute(update(User).where(User.id == user_id, User.deleted_at.is_(None)).values(password=hashed_password))
        return r.rowcount > 0

    @classmethod
    def update_profile_image_url(cls, user_id: int, profile_image_url: str, db: Session) -> bool:
        r = db.execute(update(User).where(User.id == user_id, User.deleted_at.is_(None)).values(profile_image_url=profile_image_url))
        return r.rowcount > 0

    @classmethod
    def withdraw_user(cls, user_id: int, db: Session) -> bool:
        r = db.execute(update(User).where(User.id == user_id).values(deleted_at=datetime.now()))
        return r.rowcount > 0

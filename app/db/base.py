# SQLAlchemy DeclarativeBase. utc_now, soft_delete, before_update(updated_at 자동).
from datetime import datetime, timezone

from sqlalchemy import event
from sqlalchemy.orm import DeclarativeBase


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    def soft_delete(self) -> None:
        if hasattr(self, "deleted_at"):
            self.deleted_at = utc_now()


@event.listens_for(Base, "before_update")
def _set_updated_at(mapper, connection, target) -> None:
    if hasattr(target, "updated_at"):
        target.updated_at = utc_now()

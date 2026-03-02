"""post content MEDIUMTEXT, users is_active (탈퇴 시 조회 비식별화용)

Revision ID: 20250302_content_is_active
Revises: 20250228_users_fk
Create Date: 2025-03-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text
from sqlalchemy.dialects.mysql import MEDIUMTEXT


revision: str = "20250302_content_is_active"
down_revision: Union[str, None] = "20250228_users_fk"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)

    # 게시글 본문 50,000자 지원 (utf8mb4 → MEDIUMTEXT). 이미 MEDIUMTEXT면 스킵
    posts_cols = {c["name"]: c for c in insp.get_columns("posts")}
    if "content" in posts_cols:
        type_str = str(posts_cols["content"]["type"]).upper()
        if "MEDIUMTEXT" not in type_str:
            op.alter_column(
                "posts",
                "content",
                existing_type=sa.Text(),
                type_=MEDIUMTEXT(),
                existing_nullable=False,
            )

    # 탈퇴 여부 플래그 (조회 시 비식별화용). 이미 있으면 스킵(puppytalkdb.sql 등)
    user_cols = [c["name"] for c in insp.get_columns("users")]
    if "is_active" not in user_cols:
        op.add_column("users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")))
    op.execute(text("UPDATE users SET is_active = 0 WHERE deleted_at IS NOT NULL"))


def downgrade() -> None:
    op.drop_column("users", "is_active")
    op.alter_column(
        "posts",
        "content",
        existing_type=MEDIUMTEXT(),
        type_=sa.Text(),
        existing_nullable=False,
    )

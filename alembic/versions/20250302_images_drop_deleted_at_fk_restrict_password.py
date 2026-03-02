"""images deleted_at 제거, post_images FK RESTRICT, users.password 255

- images: deleted_at 제거(ref_count=0이면 로우 DELETE로 통일)
- post_images: ON DELETE CASCADE → RESTRICT(앱에서 ref_count 감소 후 처리)
- users.password: VARCHAR(999) → VARCHAR(255)

Revision ID: 20250302_cleanup
Revises: 20250302_ref_count
Create Date: 2025-03-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "20250302_cleanup"
down_revision: Union[str, None] = "20250302_ref_count"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)

    # images: deleted_at 제거
    image_cols = [c["name"] for c in insp.get_columns("images")]
    if "deleted_at" in image_cols:
        op.drop_column("images", "deleted_at")

    # post_images: post_id FK → ON DELETE RESTRICT
    fks = [fk["name"] for fk in insp.get_foreign_keys("post_images")]
    if "fk_post_images_post" in fks:
        op.drop_constraint("fk_post_images_post", "post_images", type_="foreignkey")
    op.create_foreign_key(
        "fk_post_images_post",
        "post_images",
        "posts",
        ["post_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    # users.password 길이 축소
    user_cols = {c["name"]: c for c in insp.get_columns("users")}
    if "password" in user_cols:
        op.alter_column(
            "users",
            "password",
            existing_type=sa.String(999),
            type_=sa.String(255),
            existing_nullable=False,
        )


def downgrade() -> None:
    op.alter_column(
        "users",
        "password",
        existing_type=sa.String(255),
        type_=sa.String(999),
        existing_nullable=False,
    )
    op.drop_constraint("fk_post_images_post", "post_images", type_="foreignkey")
    op.create_foreign_key(
        "fk_post_images_post",
        "post_images",
        "posts",
        ["post_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.add_column("images", sa.Column("deleted_at", sa.DateTime(), nullable=True))

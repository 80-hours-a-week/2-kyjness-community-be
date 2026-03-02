"""images ref_count (참조 카운팅). 삭제 판단은 decrement_ref_count 한 곳에서만.

Revision ID: 20250302_ref_count
Revises: 20250302_content_is_active
Create Date: 2025-03-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text


revision: str = "20250302_ref_count"
down_revision: Union[str, None] = "20250302_content_is_active"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)
    image_cols = [c["name"] for c in insp.get_columns("images")]
    if "ref_count" not in image_cols:
        op.add_column(
            "images",
            sa.Column("ref_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        )
    # 기존 데이터: 실제 참조 수로 보정 (프로필 + 게시글 첨부). 참조 없는 행만 1로 보수적 처리
    op.execute(text("""
        UPDATE images i
        SET i.ref_count = GREATEST(1,
            (SELECT COUNT(*) FROM users u WHERE u.profile_image_id = i.id)
            + (SELECT COUNT(*) FROM post_images p WHERE p.image_id = i.id)
        )
        WHERE i.deleted_at IS NULL
    """))


def downgrade() -> None:
    op.drop_column("images", "ref_count")

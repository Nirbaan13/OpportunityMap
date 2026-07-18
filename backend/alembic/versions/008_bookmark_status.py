"""Add status to bookmarks for saved vs completed opportunities

Revision ID: 008_bookmark_status
Revises: 007_activity_status
Create Date: 2026-07-18

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008_bookmark_status"
down_revision: Union[str, None] = "007_activity_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "bookmarks",
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="saved",
        ),
    )
    op.add_column(
        "bookmarks",
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("bookmarks", "completed_at")
    op.drop_column("bookmarks", "status")

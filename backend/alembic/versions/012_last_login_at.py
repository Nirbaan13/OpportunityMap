"""Add users.last_login_at for returning-user metrics.

Revision ID: 012_last_login_at
Revises: 011_password_reset_tokens
Create Date: 2026-08-01
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "012_last_login_at"
down_revision: str | None = "011_password_reset_tokens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_last_login_at", "users", ["last_login_at"])


def downgrade() -> None:
    op.drop_index("ix_users_last_login_at", table_name="users")
    op.drop_column("users", "last_login_at")

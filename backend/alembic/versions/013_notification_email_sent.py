"""Track whether a deadline reminder email was actually sent.

Revision ID: 013_notification_email_sent
Revises: 012_last_login_at
Create Date: 2026-08-06
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "013_notification_email_sent"
down_revision: str | None = "012_last_login_at"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "notifications",
        sa.Column(
            "email_sent",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("notifications", "email_sent")

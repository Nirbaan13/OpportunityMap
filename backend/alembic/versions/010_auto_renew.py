"""Add auto_renew preference and premium renewal reminder notification type

Revision ID: 010_auto_renew
Revises: 009_payment_webhooks
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "010_auto_renew"
down_revision: str | None = "009_payment_webhooks"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "auto_renew",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
    )
    # New notification type for renewal reminders (soft auto-renew).
    op.execute("ALTER TYPE notification_type ADD VALUE IF NOT EXISTS 'premium_renewal'")


def downgrade() -> None:
    op.drop_column("users", "auto_renew")
    # PostgreSQL cannot easily drop an enum value; leaving it is harmless.

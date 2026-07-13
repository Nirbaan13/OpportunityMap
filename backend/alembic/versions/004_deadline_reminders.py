"""Add remind_me on bookmarks and reminder_lead_days on notifications

Revision ID: 004_deadline_reminders
Revises: 003_trim_activities
Create Date: 2026-07-11

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_deadline_reminders"
down_revision: Union[str, None] = "003_trim_activities"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "bookmarks",
        sa.Column(
            "remind_me",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "notifications",
        sa.Column("reminder_lead_days", sa.Integer(), nullable=True),
    )
    op.create_index(
        "uq_notification_deadline_reminder",
        "notifications",
        ["user_id", "opportunity_id", "reminder_lead_days"],
        unique=True,
        postgresql_where=sa.text(
            "notification_type = 'deadline_reminder' AND opportunity_id IS NOT NULL "
            "AND reminder_lead_days IS NOT NULL"
        ),
    )


def downgrade() -> None:
    op.drop_index("uq_notification_deadline_reminder", table_name="notifications")
    op.drop_column("notifications", "reminder_lead_days")
    op.drop_column("bookmarks", "remind_me")

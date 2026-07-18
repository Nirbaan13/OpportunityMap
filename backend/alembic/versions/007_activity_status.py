"""Add planned/completed status on profile activities

Revision ID: 007_activity_status
Revises: 006_premium_yearly
Create Date: 2026-07-18

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007_activity_status"
down_revision: Union[str, None] = "006_premium_yearly"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "profile_activities",
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="completed",
        ),
    )


def downgrade() -> None:
    op.drop_column("profile_activities", "status")

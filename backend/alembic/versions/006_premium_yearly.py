"""Add premium_until for yearly membership

Revision ID: 006_premium_yearly
Revises: 005_premium_payments
Create Date: 2026-07-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006_premium_yearly"
down_revision: Union[str, None] = "005_premium_payments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("premium_until", sa.DateTime(timezone=True), nullable=True),
    )
    # Existing lifetime unlocks (if any) get 1 year from now
    op.execute(
        """
        UPDATE users
        SET premium_until = NOW() + INTERVAL '365 days'
        WHERE is_premium = true AND premium_until IS NULL
        """
    )


def downgrade() -> None:
    op.drop_column("users", "premium_until")

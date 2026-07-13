"""Add activities checklist for student profiles

Revision ID: 002_profile_activities
Revises: 001_initial_schema
Create Date: 2026-07-07

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_profile_activities"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_ACTIVITIES = [
    ("Olympiad", "olympiad"),
    ("Hackathon", "hackathon"),
    ("Research Program", "research-program"),
    ("Summer School", "summer-school"),
    ("Competition", "competition"),
    ("Scholarship", "scholarship"),
    ("Fellowship", "fellowship"),
    ("Science Fair", "science-fair"),
    ("Volunteering", "volunteering"),
]


def upgrade() -> None:
    op.create_table(
        "activities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_activities_slug", "activities", ["slug"], unique=False)

    op.create_table(
        "profile_activities",
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("activity_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["activity_id"], ["activities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("profile_id", "activity_id"),
    )

    activities_table = sa.table("activities", sa.column("name"), sa.column("slug"))
    op.bulk_insert(
        activities_table, [{"name": name, "slug": slug} for name, slug in DEFAULT_ACTIVITIES]
    )


def downgrade() -> None:
    op.drop_table("profile_activities")
    op.drop_index("ix_activities_slug", table_name="activities")
    op.drop_table("activities")

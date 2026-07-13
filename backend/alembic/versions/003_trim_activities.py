"""Trim activity checklist: drop competition/scholarship/fellowship; clarify olympiad

Revision ID: 003_trim_activities
Revises: 002_profile_activities
Create Date: 2026-07-11

"""

from typing import Sequence, Union

from alembic import op

revision: str = "003_trim_activities"
down_revision: Union[str, None] = "002_profile_activities"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OLYMPIAD_LABEL = "Olympiad (national rounds of olympiads like IOI, IMO, IPhO, etc)"


def upgrade() -> None:
    op.execute(
        "DELETE FROM activities WHERE slug IN ('competition', 'scholarship', 'fellowship')"
    )
    op.execute(
        f"UPDATE activities SET name = '{OLYMPIAD_LABEL}' WHERE slug = 'olympiad'"
    )


def downgrade() -> None:
    op.execute("UPDATE activities SET name = 'Olympiad' WHERE slug = 'olympiad'")
    op.execute(
        """
        INSERT INTO activities (name, slug)
        VALUES
          ('Competition', 'competition'),
          ('Scholarship', 'scholarship'),
          ('Fellowship', 'fellowship')
        ON CONFLICT (slug) DO NOTHING
        """
    )

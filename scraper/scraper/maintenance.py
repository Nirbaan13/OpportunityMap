"""Post-scrape maintenance: refresh timestamps and deactivate stale listings."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Opportunity

logger = logging.getLogger(__name__)


def deactivate_past_deadlines(db: Session) -> int:
    """Mark opportunities inactive when their deadline has passed."""
    now = datetime.now(UTC)
    rows = list(
        db.scalars(
            select(Opportunity).where(
                Opportunity.is_active.is_(True),
                Opportunity.deadline_at.is_not(None),
                Opportunity.deadline_at < now,
            )
        ).all()
    )
    for row in rows:
        row.is_active = False
    if rows:
        db.commit()
    logger.info("Deactivated %s opportunit(ies) with past deadlines", len(rows))
    return len(rows)

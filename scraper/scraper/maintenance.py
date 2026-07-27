"""Post-scrape maintenance: refresh timestamps and deactivate stale listings."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Opportunity

logger = logging.getLogger(__name__)

# How long an actively-scraped listing may go unseen before we retire it. Because
# undated opportunities never trip the past-deadline check, staleness is the only
# signal that a source has dropped a listing. Sources upsert every run and refresh
# last_scraped_at, so a fresh row is never at risk.
STALE_LISTING_MAX_AGE_DAYS = 30

# Titles that mean the scraper grabbed a JS-disabled fallback page, not a real name.
_UNUSABLE_TITLE_FRAGMENTS = (
    "javascript is disabled",
    "enable javascript",
    "please enable javascript",
)


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


def deactivate_stale_listings(
    db: Session, *, max_age_days: int = STALE_LISTING_MAX_AGE_DAYS
) -> int:
    """Retire listings not seen in a scrape for ``max_age_days``.

    Targets rows that were scraped at least once (``last_scraped_at`` is set) but
    have gone stale — this is how undated opportunities age out once a source stops
    listing them. Manually-added rows (no ``last_scraped_at``) are never touched.
    """
    cutoff = datetime.now(UTC) - timedelta(days=max_age_days)
    rows = list(
        db.scalars(
            select(Opportunity).where(
                Opportunity.is_active.is_(True),
                Opportunity.last_scraped_at.is_not(None),
                Opportunity.last_scraped_at < cutoff,
            )
        ).all()
    )
    for row in rows:
        row.is_active = False
    if rows:
        db.commit()
    logger.info(
        "Deactivated %s stale listing(s) unseen for %s+ days", len(rows), max_age_days
    )
    return len(rows)


def deactivate_unusable_titles(db: Session) -> int:
    """Hide listings whose title is a scrape artifact (e.g. Devpost noscript fallback)."""
    conditions = [
        Opportunity.title.ilike(f"%{fragment}%") for fragment in _UNUSABLE_TITLE_FRAGMENTS
    ]
    rows = list(
        db.scalars(
            select(Opportunity).where(
                Opportunity.is_active.is_(True),
                or_(*conditions),
            )
        ).all()
    )
    for row in rows:
        row.is_active = False
    if rows:
        db.commit()
    logger.info("Deactivated %s opportunit(ies) with unusable titles", len(rows))
    return len(rows)

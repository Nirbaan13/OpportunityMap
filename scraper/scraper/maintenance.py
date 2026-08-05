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
    """Mark opportunities inactive when their deadline has passed.

    Clears expired rows from the active feed so students only see open / undated
    listings. Safe to run repeatedly (idempotent).
    """
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


def backfill_eligible_countries(db: Session) -> int:
    """Infer countries for active rows that still have eligible_countries=null."""
    from scraper.parsers.eligibility import infer_eligible_countries

    rows = list(
        db.scalars(
            select(Opportunity).where(
                Opportunity.is_active.is_(True),
                Opportunity.eligible_countries.is_(None),
            )
        ).all()
    )
    updated = 0
    for row in rows:
        default: list[str] | None = None
        online_worldwide = False
        if row.source_name == "pathways_to_science":
            default = ["US"]
        elif row.source_name == "devpost":
            online_worldwide = True

        inferred = infer_eligible_countries(
            row.description,
            row.experience_requirements,
            row.source_url,
            row.application_url,
            title=row.title,
            opportunity_type=row.opportunity_type,
            online_worldwide_if_unspecified=online_worldwide,
            default_countries=default,
        )
        if inferred is None:
            continue
        row.eligible_countries = inferred
        updated += 1

    if updated:
        db.commit()
    logger.info("Backfilled eligible_countries on %s opportunit(ies)", updated)
    return updated


def backfill_opportunity_fields(db: Session) -> int:
    """Reclassify fields from title/description/type using shared mapping rules.

    Safe to re-run: only writes when the computed slug set differs from the row.
    Prefer this after deploying classification fixes so live Devpost Education→Social
    Science misfires are corrected without waiting for a full re-scrape.

    Scope (conservative — does not retag the whole catalog from keywords):
    - Devpost / hackathons: full classify + refine (always keep CS; drop weak SS).
    - Other rows that look like tech/social-good misfires: re-classify with
      social-science removed from the seed set, then refine (still no forced CS).
    - Remaining rows: refine only (no-op unless title contains \"hackathon\").

    Curated catalog field lists still win on the next upsert from ``--source all``.

    Production (from ``scraper/`` with DATABASE_URL pointing at prod)::

        python -c "from scraper.db import SessionLocal; from scraper.maintenance import backfill_opportunity_fields; db=SessionLocal(); print(backfill_opportunity_fields(db)); db.close()"

    Or run the normal scraper (maintenance runs automatically)::

        python -m scraper.main --source all --skip-enrichment
    """
    from scraper.parsers.field_mapping import (
        classify_field_slugs,
        looks_like_tech_social_mislabeled,
        refine_field_slugs,
    )
    from scraper.repository import _load_fields_by_slug

    rows = list(
        db.scalars(
            select(Opportunity).where(Opportunity.is_active.is_(True))
        ).all()
    )
    updated = 0
    for row in rows:
        current = [field.slug for field in row.fields]
        opportunity_type = (
            row.opportunity_type.value
            if hasattr(row.opportunity_type, "value")
            else str(row.opportunity_type or "")
        )
        if row.source_name == "devpost" or opportunity_type == "hackathon":
            recomputed = classify_field_slugs(
                row.title,
                row.description,
                source_slugs=current,
                opportunity_type=opportunity_type or "hackathon",
            )
        elif looks_like_tech_social_mislabeled(
            current, row.title, row.description
        ):
            # Drop the bad tag from the seed so classify cannot preserve it via merge;
            # other curated tags (ai, business, …) stay.
            seed = [slug for slug in current if slug != "social-science"]
            recomputed = classify_field_slugs(
                row.title,
                row.description,
                source_slugs=seed,
                opportunity_type=opportunity_type,
            )
        else:
            recomputed = refine_field_slugs(
                current,
                row.title,
                row.description,
                opportunity_type=opportunity_type,
            )

        if sorted(recomputed) == sorted(current):
            continue
        row.fields = _load_fields_by_slug(db, recomputed)
        updated += 1

    if updated:
        db.commit()
    logger.info("Reclassified fields on %s opportunit(ies)", updated)
    return updated

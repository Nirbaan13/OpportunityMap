from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Field, Opportunity
from app.models.enums import OpportunityType
from scraper.parsers.dates import deadline_is_upcoming

@dataclass
class ScrapedOpportunity:
    external_id: str
    title: str
    source_url: str
    application_url: str | None
    description: str | None
    opportunity_type: OpportunityType
    grade_eligibility: str | None
    grade_min: int | None
    grade_max: int | None
    eligible_countries: list[str] | None
    experience_requirements: str | None
    deadline_at: datetime | None
    deadline_summary: str | None
    field_slugs: list[str] = field(default_factory=list)


def _load_fields_by_slug(db: Session, slugs: list[str]) -> list[Field]:
    if not slugs:
        return []
    return list(db.scalars(select(Field).where(Field.slug.in_(slugs))).all())


def _is_active_for_deadline(deadline_at: datetime | None) -> bool:
    """Active unless a concrete deadline has already passed.

    Undated rows stay active so staleness maintenance can retire them later.
    """
    if deadline_at is None:
        return True
    return deadline_is_upcoming(deadline_at)


def upsert_opportunity(
    db: Session,
    data: ScrapedOpportunity,
    *,
    source_name: str,
) -> tuple[Opportunity, bool]:
    """Insert or update an opportunity. Returns (row, created)."""
    now = datetime.now(UTC)
    existing = db.scalar(
        select(Opportunity).where(
            Opportunity.source_name == source_name,
            Opportunity.external_id == data.external_id,
        )
    )

    fields = _load_fields_by_slug(db, data.field_slugs)
    description = data.description
    if data.deadline_summary:
        description = (description or "").strip()
        deadline_block = f"Deadlines:\n{data.deadline_summary}"
        description = f"{description}\n\n{deadline_block}".strip() if description else deadline_block

    if existing is None:
        row = Opportunity(
            title=data.title[:300],
            description=description,
            opportunity_type=data.opportunity_type,
            source_name=source_name,
            source_url=data.source_url,
            application_url=data.application_url,
            external_id=data.external_id,
            deadline_at=data.deadline_at,
            grade_eligibility=data.grade_eligibility,
            grade_min=data.grade_min,
            grade_max=data.grade_max,
            eligible_countries=data.eligible_countries,
            experience_requirements=data.experience_requirements,
            is_active=_is_active_for_deadline(data.deadline_at),
            last_scraped_at=now,
            fields=fields,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row, True

    existing.title = data.title[:300]
    existing.description = description
    existing.opportunity_type = data.opportunity_type
    existing.source_url = data.source_url
    existing.application_url = data.application_url
    # Catalog seeds often ship deadline_at=None. Don't wipe a previously enriched
    # (or scraped) future deadline on re-seed; clear only if the existing date is past.
    if data.deadline_at is not None:
        existing.deadline_at = data.deadline_at
    elif existing.deadline_at is not None and not deadline_is_upcoming(existing.deadline_at):
        existing.deadline_at = None
    existing.grade_eligibility = data.grade_eligibility
    existing.grade_min = data.grade_min
    existing.grade_max = data.grade_max
    # Don't wipe a previously inferred country with an unspecified null.
    if data.eligible_countries is not None:
        existing.eligible_countries = data.eligible_countries
    existing.experience_requirements = data.experience_requirements
    # Past deadline → inactive; new/updated future deadline (or undated) → active again.
    existing.is_active = _is_active_for_deadline(existing.deadline_at)
    existing.last_scraped_at = now
    existing.fields = fields
    db.commit()
    db.refresh(existing)
    return existing, False

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Field, Opportunity
from app.models.enums import OpportunityType

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
            is_active=True,
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
    existing.deadline_at = data.deadline_at
    existing.grade_eligibility = data.grade_eligibility
    existing.grade_min = data.grade_min
    existing.grade_max = data.grade_max
    existing.eligible_countries = data.eligible_countries
    existing.experience_requirements = data.experience_requirements
    existing.is_active = True
    existing.last_scraped_at = now
    existing.fields = fields
    db.commit()
    db.refresh(existing)
    return existing, False

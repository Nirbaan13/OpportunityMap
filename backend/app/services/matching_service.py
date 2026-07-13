"""Match opportunities to a student profile.

Hard filters (must pass):
  - opportunity is_active
  - grade within grade_min/grade_max (null bounds = unrestricted)
  - country in eligible_countries (null = worldwide)
  - at least one shared interest field

Soft score (higher = better):
  - +10 per shared interest field
  - +5 if student has research_experience text and opportunity is research-like
  - +5 if student has olympiad_experience text and opportunity is olympiad/competition
  - +3 if a completed activity maps to this opportunity type

Ties break by sooner deadline, then id.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models import Opportunity, Profile, User
from app.models.enums import OpportunityType
from app.schemas.profile import FieldOption

RESEARCH_TYPES = frozenset(
    {
        OpportunityType.RESEARCH_PROGRAM,
        OpportunityType.SUMMER_SCHOOL,
        OpportunityType.FELLOWSHIP,
        OpportunityType.SCHOLARSHIP,
    }
)

OLYMPIAD_TYPES = frozenset(
    {
        OpportunityType.OLYMPIAD,
        OpportunityType.COMPETITION,
    }
)

ACTIVITY_SLUG_TO_TYPE: dict[str, OpportunityType] = {
    "olympiad": OpportunityType.OLYMPIAD,
    "hackathon": OpportunityType.HACKATHON,
    "research-program": OpportunityType.RESEARCH_PROGRAM,
    "summer-school": OpportunityType.SUMMER_SCHOOL,
    "science-fair": OpportunityType.COMPETITION,
}

POINTS_PER_SHARED_FIELD = 10
POINTS_RESEARCH_BOOST = 5
POINTS_OLYMPIAD_BOOST = 5
POINTS_ACTIVITY_BOOST = 3


@dataclass(frozen=True)
class ScoredMatch:
    opportunity: Opportunity
    score: int
    shared_fields: list[FieldOption]
    reasons: list[str]


def _load_profile(db: Session, user: User) -> Profile:
    profile = db.scalar(
        select(Profile)
        .options(joinedload(Profile.fields), joinedload(Profile.activities))
        .where(Profile.user_id == user.id)
    )
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Create a profile before requesting matches.",
        )
    return profile


def _has_text(value: str | None) -> bool:
    return bool(value and value.strip())


def _eligible_query(
    *,
    grade: int,
    country_code: str,
    open_only: bool,
    opportunity_type: OpportunityType | None,
):
    stmt = (
        select(Opportunity)
        .options(joinedload(Opportunity.fields))
        .where(Opportunity.is_active.is_(True))
        .where(
            and_(
                or_(Opportunity.grade_min.is_(None), Opportunity.grade_min <= grade),
                or_(Opportunity.grade_max.is_(None), Opportunity.grade_max >= grade),
            )
        )
        .where(
            or_(
                Opportunity.eligible_countries.is_(None),
                Opportunity.eligible_countries.contains([country_code]),
            )
        )
    )

    if opportunity_type is not None:
        stmt = stmt.where(Opportunity.opportunity_type == opportunity_type)

    if open_only:
        now = datetime.now(UTC)
        stmt = stmt.where(Opportunity.deadline_at.is_not(None)).where(
            Opportunity.deadline_at >= now
        )

    return stmt


def score_opportunity(profile: Profile, opportunity: Opportunity) -> ScoredMatch | None:
    interest_ids = {field.id for field in profile.fields}
    shared = [field for field in opportunity.fields if field.id in interest_ids]
    if not shared:
        return None

    score = POINTS_PER_SHARED_FIELD * len(shared)
    reasons = [
        f"{len(shared)} shared interest{'s' if len(shared) != 1 else ''}: "
        + ", ".join(field.name for field in shared)
    ]

    if _has_text(profile.research_experience) and opportunity.opportunity_type in RESEARCH_TYPES:
        score += POINTS_RESEARCH_BOOST
        reasons.append("research experience boost")

    if _has_text(profile.olympiad_experience) and opportunity.opportunity_type in OLYMPIAD_TYPES:
        score += POINTS_OLYMPIAD_BOOST
        reasons.append("olympiad experience boost")

    activity_types = {
        ACTIVITY_SLUG_TO_TYPE[activity.slug]
        for activity in profile.activities
        if activity.slug in ACTIVITY_SLUG_TO_TYPE
    }
    if opportunity.opportunity_type in activity_types:
        score += POINTS_ACTIVITY_BOOST
        reasons.append(f"completed {opportunity.opportunity_type.value.replace('_', ' ')} activity")

    return ScoredMatch(
        opportunity=opportunity,
        score=score,
        shared_fields=[FieldOption.model_validate(field) for field in shared],
        reasons=reasons,
    )


def _deadline_sort_key(opportunity: Opportunity) -> tuple[int, float, int]:
    """Sooner deadlines first; null deadlines last."""
    if opportunity.deadline_at is None:
        return (1, 0.0, opportunity.id)
    return (0, opportunity.deadline_at.timestamp(), opportunity.id)


def get_matches(
    db: Session,
    user: User,
    *,
    open_only: bool = True,
    opportunity_type: OpportunityType | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[ScoredMatch], int]:
    profile = _load_profile(db, user)
    if not profile.fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile has no interests. Add interest_slugs before requesting matches.",
        )

    country = profile.country_code.upper()
    rows = list(
        db.scalars(
            _eligible_query(
                grade=profile.grade_level,
                country_code=country,
                open_only=open_only,
                opportunity_type=opportunity_type,
            )
        )
        .unique()
        .all()
    )

    scored: list[ScoredMatch] = []
    for opportunity in rows:
        match = score_opportunity(profile, opportunity)
        if match is not None:
            scored.append(match)

    scored.sort(key=lambda m: (-m.score, _deadline_sort_key(m.opportunity)))

    total = len(scored)
    start = (page - 1) * page_size
    return scored[start : start + page_size], total

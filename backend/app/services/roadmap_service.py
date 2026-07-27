"""Build a yearly opportunity roadmap from strong For-you matches."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import User
from app.schemas.profile import FieldOption
from app.services.matching_service import ScoredMatch, get_matches
from app.services.profile_service import get_profile, yearly_target_for_grade


def _is_open_or_undated(match: ScoredMatch, *, now: datetime) -> bool:
    deadline = match.opportunity.deadline_at
    if deadline is None:
        return True
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=UTC)
    return deadline >= now


def _is_strong(match: ScoredMatch, interest_count: int) -> bool:
    return interest_count > 0 and len(match.shared_fields) >= interest_count


def _deadline_key(match: ScoredMatch) -> tuple[int, float, int]:
    deadline = match.opportunity.deadline_at
    if deadline is None:
        return (1, 0.0, match.opportunity.id)
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=UTC)
    return (0, deadline.timestamp(), match.opportunity.id)


def build_roadmap_selection(db: Session, user: User) -> dict:
    """Return structured roadmap data for the API layer to serialize."""
    profile = get_profile(db, user)
    interest_count = len(profile.fields)
    if interest_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile has no interests. Add interest_slugs before requesting a roadmap.",
        )

    target_per_field = yearly_target_for_grade(profile.grade_level)
    total_target = target_per_field * interest_count

    # Pull a large For-you pool including undated deadlines; drop past deadlines.
    matches, _total = get_matches(
        db,
        user,
        open_only=False,
        page=1,
        page_size=200,
    )
    now = datetime.now(UTC)
    pool = [m for m in matches if _is_open_or_undated(m, now=now)]
    pool.sort(
        key=lambda m: (
            -int(_is_strong(m, interest_count)),
            -m.score,
            _deadline_key(m),
        )
    )

    used_ids: set[int] = set()
    selected: list[tuple[ScoredMatch, FieldOption]] = []
    field_plans: list[dict] = []

    for field in sorted(profile.fields, key=lambda item: item.name.lower()):
        field_option = FieldOption.model_validate(field)
        picked = 0
        for match in pool:
            if picked >= target_per_field:
                break
            if match.opportunity.id in used_ids:
                continue
            if field.id not in {f.id for f in match.opportunity.fields}:
                continue
            used_ids.add(match.opportunity.id)
            selected.append((match, field_option))
            picked += 1
        field_plans.append(
            {
                "field": field_option,
                "yearly_target": target_per_field,
                "selected_count": picked,
            }
        )

    selected.sort(key=lambda item: _deadline_key(item[0]))

    stops: list[dict] = []
    for index, (match, primary_field) in enumerate(selected, start=1):
        stops.append(
            {
                "order": index,
                "opportunity_id": match.opportunity.id,
                "match": match,
                "has_deadline": match.opportunity.deadline_at is not None,
                "primary_field": primary_field,
                "is_strong_match": _is_strong(match, interest_count),
            }
        )

    field_names = ", ".join(plan["field"].name for plan in field_plans)
    summary = (
        f"Grade {profile.grade_level}: aim for {target_per_field} opportunit"
        f"{'y' if target_per_field == 1 else 'ies'} per interest "
        f"({field_names}) — {total_target} stops this year. "
        f"Placed {len(stops)} For-you matches"
        f"{' chronologically by deadline' if stops else ''}."
    )

    return {
        "grade_level": profile.grade_level,
        "target_per_field": target_per_field,
        "total_target": total_target,
        "field_plans": field_plans,
        "stops": stops,
        "summary": summary,
    }

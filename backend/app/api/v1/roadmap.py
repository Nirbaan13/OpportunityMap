from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.opportunities import _to_summary
from app.core.deps import require_premium
from app.database import get_db
from app.models import User
from app.schemas.match import MatchItem
from app.schemas.roadmap import (
    RoadmapAlternativesResponse,
    RoadmapFieldPlan,
    RoadmapResponse,
    RoadmapStop,
)
from app.services.roadmap_service import build_roadmap_selection, list_roadmap_alternatives

router = APIRouter(prefix="/roadmap", tags=["roadmap"])


def _to_match_item(match) -> MatchItem:
    return MatchItem(
        opportunity=_to_summary(match.opportunity),
        score=match.score,
        shared_fields=match.shared_fields,
        reasons=match.reasons,
    )


@router.get("", response_model=RoadmapResponse)
def get_my_roadmap(
    current_user: User = Depends(require_premium),
    db: Session = Depends(get_db),
) -> RoadmapResponse:
    """Yearly road of strong For-you matches sized by grade × interest fields."""
    data = build_roadmap_selection(db, current_user)
    return RoadmapResponse(
        grade_level=data["grade_level"],
        target_per_field=data["target_per_field"],
        total_target=data["total_target"],
        field_plans=[RoadmapFieldPlan(**plan) for plan in data["field_plans"]],
        stops=[
            RoadmapStop(
                order=stop["order"],
                opportunity_id=stop["opportunity_id"],
                match=_to_match_item(stop["match"]),
                has_deadline=stop["has_deadline"],
                primary_field=stop["primary_field"],
                is_strong_match=stop["is_strong_match"],
                is_completed=stop["is_completed"],
            )
            for stop in data["stops"]
        ],
        summary=data["summary"],
    )


@router.get("/alternatives", response_model=RoadmapAlternativesResponse)
def get_roadmap_alternatives(
    current_user: User = Depends(require_premium),
    db: Session = Depends(get_db),
    exclude_ids: str = Query(
        "",
        description="Comma-separated opportunity IDs already on the roadmap",
    ),
    field_slug: str | None = Query(
        None,
        description="Prefer alternatives that include this interest slug",
    ),
) -> RoadmapAlternativesResponse:
    """For-you matches that can replace a roadmap stop."""
    parsed: set[int] = set()
    for part in exclude_ids.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            parsed.add(int(part))
        except ValueError:
            continue

    matches = list_roadmap_alternatives(
        db,
        current_user,
        exclude_ids=parsed,
        field_slug=field_slug,
    )
    return RoadmapAlternativesResponse(items=[_to_match_item(m) for m in matches])

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.opportunities import _to_summary
from app.core.deps import require_premium
from app.database import get_db
from app.models import User
from app.schemas.match import MatchItem
from app.schemas.roadmap import RoadmapFieldPlan, RoadmapResponse, RoadmapStop
from app.services.roadmap_service import build_roadmap_selection

router = APIRouter(prefix="/roadmap", tags=["roadmap"])


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
                match=MatchItem(
                    opportunity=_to_summary(stop["match"].opportunity),
                    score=stop["match"].score,
                    shared_fields=stop["match"].shared_fields,
                    reasons=stop["match"].reasons,
                ),
                has_deadline=stop["has_deadline"],
                primary_field=stop["primary_field"],
                is_strong_match=stop["is_strong_match"],
            )
            for stop in data["stops"]
        ],
        summary=data["summary"],
    )

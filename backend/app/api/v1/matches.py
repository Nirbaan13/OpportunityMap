from math import ceil

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.opportunities import _to_summary
from app.core.deps import require_premium
from app.database import get_db
from app.models import User
from app.models.enums import OpportunityType
from app.schemas.match import MatchItem, MatchListResponse
from app.services.matching_service import get_matches

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=MatchListResponse)
def list_my_matches(
    open_only: bool = Query(
        default=True,
        description="Only opportunities with a future deadline (recommended default)",
    ),
    opportunity_type: OpportunityType | None = Query(
        default=None,
        description="Optional type filter, e.g. hackathon, olympiad",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_premium),
    db: Session = Depends(get_db),
) -> MatchListResponse:
    """Personalized opportunity feed for the logged-in student."""
    matches, total = get_matches(
        db,
        current_user,
        open_only=open_only,
        opportunity_type=opportunity_type,
        page=page,
        page_size=page_size,
    )
    total_pages = ceil(total / page_size) if total else 0
    return MatchListResponse(
        items=[
            MatchItem(
                opportunity=_to_summary(match.opportunity),
                score=match.score,
                shared_fields=match.shared_fields,
                reasons=match.reasons,
            )
            for match in matches
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )

from datetime import datetime
from math import ceil

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Opportunity
from app.models.enums import OpportunityType
from app.schemas.opportunity import (
    OpportunityDetail,
    OpportunityListResponse,
    OpportunitySort,
    OpportunitySummary,
)
from app.schemas.profile import FieldOption
from app.services.opportunity_service import get_opportunity, list_opportunities

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


def _to_summary(opportunity: Opportunity) -> OpportunitySummary:
    return OpportunitySummary(
        id=opportunity.id,
        title=opportunity.title,
        opportunity_type=opportunity.opportunity_type,
        source_name=opportunity.source_name,
        source_url=opportunity.source_url,
        application_url=opportunity.application_url,
        deadline_at=opportunity.deadline_at,
        grade_eligibility=opportunity.grade_eligibility,
        grade_min=opportunity.grade_min,
        grade_max=opportunity.grade_max,
        eligible_countries=opportunity.eligible_countries,
        is_active=opportunity.is_active,
        fields=[FieldOption.model_validate(field) for field in opportunity.fields],
    )


def _to_detail(opportunity: Opportunity) -> OpportunityDetail:
    summary = _to_summary(opportunity)
    return OpportunityDetail(
        **summary.model_dump(),
        description=opportunity.description,
        experience_requirements=opportunity.experience_requirements,
        external_id=opportunity.external_id,
        last_scraped_at=opportunity.last_scraped_at,
        created_at=opportunity.created_at,
        updated_at=opportunity.updated_at,
    )


@router.get("", response_model=OpportunityListResponse)
def list_opportunities_endpoint(
    q: str | None = Query(
        default=None,
        description="Search title and description (case-insensitive)",
        max_length=200,
    ),
    opportunity_type: OpportunityType | None = Query(
        default=None,
        description="Filter by type, e.g. hackathon, olympiad",
    ),
    field: str | None = Query(
        default=None,
        description="Filter by interest field slug, e.g. mathematics, ai",
        max_length=100,
    ),
    source: str | None = Query(
        default=None,
        description="Filter by scraper source_name, e.g. devpost",
        max_length=100,
    ),
    country: str | None = Query(
        default=None,
        min_length=2,
        max_length=2,
        description="ISO country code the student is from (null eligibility = worldwide)",
    ),
    grade: int | None = Query(
        default=None,
        ge=6,
        le=12,
        description="Student grade; keeps opportunities with no grade bounds or matching range",
    ),
    deadline_before: datetime | None = Query(
        default=None,
        description="Only opportunities with deadline_at on or before this timestamp",
    ),
    deadline_after: datetime | None = Query(
        default=None,
        description="Only opportunities with deadline_at on or after this timestamp",
    ),
    open_only: bool = Query(
        default=False,
        description="If true, only opportunities with a future deadline",
    ),
    active: bool = Query(
        default=True,
        description="Filter by is_active. Default true (hide stale listings).",
    ),
    sort: OpportunitySort = Query(
        default=OpportunitySort.DEADLINE_ASC,
        description="deadline_asc | deadline_desc | newest | title",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> OpportunityListResponse:
    rows, total = list_opportunities(
        db,
        q=q,
        opportunity_type=opportunity_type,
        field_slug=field,
        source_name=source,
        country_code=country,
        grade=grade,
        deadline_before=deadline_before,
        deadline_after=deadline_after,
        open_only=open_only,
        is_active=active,
        sort=sort,
        page=page,
        page_size=page_size,
    )
    total_pages = ceil(total / page_size) if total else 0
    return OpportunityListResponse(
        items=[_to_summary(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{opportunity_id}", response_model=OpportunityDetail)
def get_opportunity_endpoint(
    opportunity_id: int,
    db: Session = Depends(get_db),
) -> OpportunityDetail:
    return _to_detail(get_opportunity(db, opportunity_id))

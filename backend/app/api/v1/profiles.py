from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_premium
from app.database import get_db
from app.models import Activity, Field, Profile, User
from app.schemas.profile import (
    ActivityOption,
    CompletedOpportunityBrief,
    FieldOption,
    ProfileResponse,
    ProfileWriteRequest,
)
from app.services import bookmark_service
from app.services.profile_service import (
    activity_options,
    build_field_insights,
    build_insight_summary,
    create_profile,
    get_profile,
    update_profile,
)

router = APIRouter(tags=["profiles"])


def _to_profile_response(db: Session, user: User, profile: Profile) -> ProfileResponse:
    completed = bookmark_service.list_completed_for_user(db, user)
    saved_rows, _ = bookmark_service.list_bookmarks(
        db, user, page=1, page_size=100, status_filter="saved"
    )
    insights = build_field_insights(
        profile,
        completed_bookmarks=completed,
        saved_bookmarks=saved_rows,
    )
    return ProfileResponse(
        id=profile.id,
        email=profile.user.email,
        full_name=profile.full_name,
        location=profile.location,
        grade_level=profile.grade_level,
        country_code=profile.country_code,
        research_experience=profile.research_experience,
        olympiad_experience=profile.olympiad_experience,
        interests=[FieldOption.model_validate(field) for field in profile.fields],
        completed_activities=activity_options(profile.completed_activity_list),
        planned_activities=activity_options(profile.planned_activity_list),
        completed_opportunities=[
            CompletedOpportunityBrief(
                id=row.opportunity.id,
                title=row.opportunity.title,
                opportunity_type=row.opportunity.opportunity_type.value,
                fields=[FieldOption.model_validate(f) for f in row.opportunity.fields],
                completed_at=row.completed_at,
            )
            for row in completed
            if row.opportunity is not None
        ],
        field_insights=insights,
        insight_summary=build_insight_summary(insights),
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.get("/fields", response_model=list[FieldOption])
def list_fields(db: Session = Depends(get_db)) -> list[Field]:
    return list(db.scalars(select(Field).order_by(Field.name)).all())


@router.get("/activities", response_model=list[ActivityOption])
def list_activities(db: Session = Depends(get_db)) -> list[Activity]:
    return list(db.scalars(select(Activity).order_by(Activity.name)).all())


@router.post("/profiles/me", response_model=ProfileResponse, status_code=201)
def create_my_profile(
    payload: ProfileWriteRequest,
    current_user: User = Depends(require_premium),
    db: Session = Depends(get_db),
) -> ProfileResponse:
    profile = create_profile(db, current_user, payload)
    return _to_profile_response(db, current_user, profile)


@router.get("/profiles/me", response_model=ProfileResponse)
def get_my_profile(
    current_user: User = Depends(require_premium),
    db: Session = Depends(get_db),
) -> ProfileResponse:
    profile = get_profile(db, current_user)
    return _to_profile_response(db, current_user, profile)


@router.put("/profiles/me", response_model=ProfileResponse)
def update_my_profile(
    payload: ProfileWriteRequest,
    current_user: User = Depends(require_premium),
    db: Session = Depends(get_db),
) -> ProfileResponse:
    profile = update_profile(db, current_user, payload)
    return _to_profile_response(db, current_user, profile)

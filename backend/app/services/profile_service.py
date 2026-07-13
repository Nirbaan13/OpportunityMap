from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Activity, Field, Profile, User
from app.schemas.profile import ProfileWriteRequest


def _load_profile_query(user_id: int):
    return (
        select(Profile)
        .options(
            joinedload(Profile.user),
            joinedload(Profile.fields),
            joinedload(Profile.activities),
        )
        .where(Profile.user_id == user_id)
    )


def _resolve_fields(db: Session, slugs: list[str]) -> list[Field]:
    if not slugs:
        return []
    fields = list(db.scalars(select(Field).where(Field.slug.in_(slugs))).all())
    found = {field.slug for field in fields}
    missing = [slug for slug in slugs if slug not in found]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown interest slugs: {', '.join(missing)}",
        )
    return fields


def _resolve_activities(db: Session, slugs: list[str]) -> list[Activity]:
    if not slugs:
        return []
    activities = list(db.scalars(select(Activity).where(Activity.slug.in_(slugs))).all())
    found = {activity.slug for activity in activities}
    missing = [slug for slug in slugs if slug not in found]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown activity slugs: {', '.join(missing)}",
        )
    return activities


def _apply_profile_data(profile: Profile, payload: ProfileWriteRequest) -> None:
    profile.full_name = payload.full_name
    profile.location = payload.location
    profile.grade_level = payload.grade_level
    profile.country_code = payload.country_code
    profile.research_experience = payload.research_experience
    profile.olympiad_experience = payload.olympiad_experience


def create_profile(db: Session, user: User, payload: ProfileWriteRequest) -> Profile:
    if user.profile is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profile already exists. Use PUT to update.",
        )

    profile = Profile(
        user_id=user.id,
        full_name=payload.full_name,
        location=payload.location,
        grade_level=payload.grade_level,
        country_code=payload.country_code,
        research_experience=payload.research_experience,
        olympiad_experience=payload.olympiad_experience,
    )
    profile.fields = _resolve_fields(db, payload.interest_slugs)
    profile.activities = _resolve_activities(db, payload.completed_activity_slugs)

    db.add(profile)
    db.commit()

    result = db.scalar(_load_profile_query(user.id))
    if result is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Profile not found")
    return result


def update_profile(db: Session, user: User, payload: ProfileWriteRequest) -> Profile:
    profile = db.scalar(_load_profile_query(user.id))
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Use POST to create one.",
        )

    _apply_profile_data(profile, payload)
    profile.fields = _resolve_fields(db, payload.interest_slugs)
    profile.activities = _resolve_activities(db, payload.completed_activity_slugs)

    db.commit()
    db.refresh(profile)
    return profile


def get_profile(db: Session, user: User) -> Profile:
    profile = db.scalar(_load_profile_query(user.id))
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile

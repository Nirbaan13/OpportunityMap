from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Activity, Field, Profile, User
from app.models.profile import ProfileActivity
from app.schemas.profile import (
    ActivityOption,
    FieldInsight,
    FieldOption,
    ProfileWriteRequest,
)
from app.services.activity_field_map import ACTIVITY_RELATED_FIELDS


def _load_profile_query(user_id: int):
    return (
        select(Profile)
        .options(
            joinedload(Profile.user),
            joinedload(Profile.fields),
            joinedload(Profile.activity_links).joinedload(ProfileActivity.activity),
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


def _set_activity_links(
    db: Session,
    profile: Profile,
    completed_slugs: list[str],
    planned_slugs: list[str],
) -> None:
    completed = _resolve_activities(db, completed_slugs)
    planned = _resolve_activities(db, planned_slugs)
    profile.activity_links.clear()
    for activity in completed:
        profile.activity_links.append(
            ProfileActivity(activity=activity, status="completed")
        )
    for activity in planned:
        profile.activity_links.append(
            ProfileActivity(activity=activity, status="planned")
        )


def build_field_insights(profile: Profile) -> list[FieldInsight]:
    completed = profile.completed_activity_list
    planned = profile.planned_activity_list
    insights: list[FieldInsight] = []

    for field in sorted(profile.fields, key=lambda item: item.name.lower()):
        completed_count = sum(
            1
            for activity in completed
            if field.slug in ACTIVITY_RELATED_FIELDS.get(activity.slug, [])
        )
        planned_count = sum(
            1
            for activity in planned
            if field.slug in ACTIVITY_RELATED_FIELDS.get(activity.slug, [])
        )
        if completed_count >= 2:
            status_label = "strong"
        elif completed_count == 1:
            status_label = "ok"
        else:
            status_label = "short"
        insights.append(
            FieldInsight(
                field=FieldOption.model_validate(field),
                completed_count=completed_count,
                planned_count=planned_count,
                status=status_label,
            )
        )
    return insights


def build_insight_summary(insights: list[FieldInsight]) -> str:
    if not insights:
        return "Add interests to see how your activities cover each field."

    strong_or_ok = [item for item in insights if item.completed_count > 0]
    short = [item for item in insights if item.status == "short"]

    parts: list[str] = []
    if strong_or_ok:
        coverage = ", ".join(
            f"{item.completed_count} in {item.field.name}" for item in strong_or_ok
        )
        parts.append(f"You've completed {coverage}.")
    else:
        parts.append("You haven't marked any completed activities yet for your interests.")

    if short:
        if len(short) == 1:
            parts.append(f"You're a little short on {short[0].field.name}.")
        elif len(short) == 2:
            parts.append(
                f"You're a little short on {short[0].field.name} and {short[1].field.name}."
            )
        else:
            named = ", ".join(item.field.name for item in short[:-1])
            parts.append(
                f"You're a little short on {named}, and {short[-1].field.name}."
            )

    return " ".join(parts)


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
    db.add(profile)
    db.flush()
    _set_activity_links(
        db,
        profile,
        payload.completed_activity_slugs,
        payload.planned_activity_slugs,
    )

    db.commit()

    result = db.scalar(_load_profile_query(user.id))
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Profile not found"
        )
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
    _set_activity_links(
        db,
        profile,
        payload.completed_activity_slugs,
        payload.planned_activity_slugs,
    )

    db.commit()
    result = db.scalar(_load_profile_query(user.id))
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Profile not found"
        )
    return result


def get_profile(db: Session, user: User) -> Profile:
    profile = db.scalar(_load_profile_query(user.id))
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


def activity_options(activities: list[Activity]) -> list[ActivityOption]:
    return [ActivityOption.model_validate(activity) for activity in activities]

from datetime import UTC, datetime
import math

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Activity, Field, Profile, User
from app.models.bookmark import Bookmark
from app.models.profile import ProfileActivity
from app.schemas.profile import (
    ActivityOption,
    FieldInsight,
    FieldOption,
    ProfileWriteRequest,
)
from app.services import bookmark_service


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _completion_time(bookmark: Bookmark) -> datetime | None:
    return bookmark.completed_at or bookmark.created_at


def resolve_joined_at(profile: Profile, user: User | None = None) -> datetime:
    """When progress tracking starts: account signup, else profile creation."""
    account = user or profile.user
    if account is not None and account.created_at is not None:
        return _as_utc(account.created_at)
    return _as_utc(profile.created_at)


def yearly_target_for_grade(grade: int) -> int:
    """How many done opportunities per interest field we aim for in a membership year."""
    if grade <= 8:
        return 2
    if grade <= 10:
        return 3
    if grade == 11:
        return 4
    # Grade 12 — still build, but the year is already late in the pipeline.
    return 3


def membership_year_start(joined_at: datetime, *, now: datetime | None = None) -> datetime:
    """Start of the user's current membership year (anniversary of join)."""
    now = _as_utc(now or datetime.now(UTC))
    joined = _as_utc(joined_at)
    try:
        anniversary = joined.replace(year=now.year)
    except ValueError:
        # Feb 29 → Feb 28 in non-leap years
        anniversary = joined.replace(year=now.year, day=28)
    if anniversary > now:
        try:
            anniversary = joined.replace(year=now.year - 1)
        except ValueError:
            anniversary = joined.replace(year=now.year - 1, day=28)
    return anniversary


def months_into_membership_year(joined_at: datetime, *, now: datetime | None = None) -> int:
    """1 in the first month after join/anniversary, up to 12."""
    now = _as_utc(now or datetime.now(UTC))
    start = membership_year_start(joined_at, now=now)
    months = (now.year - start.year) * 12 + (now.month - start.month) + 1
    return min(12, max(1, months))


def expected_completions_by_pace(
    *,
    grade: int,
    months_elapsed: int,
) -> int:
    target = yearly_target_for_grade(grade)
    months_elapsed = min(12, max(1, months_elapsed))
    return max(1, math.ceil(target * months_elapsed / 12))


def field_pace_status(
    completed_count: int,
    *,
    grade: int,
    months_elapsed: int,
) -> str:
    """
    Pace from join + grade:
    - Month 1 after joining: 1 done can be ok (depends on grade target)
    - Near end of membership year with only 1: usually short
    - Higher grades have a higher yearly target
    """
    target = yearly_target_for_grade(grade)
    expected = expected_completions_by_pace(grade=grade, months_elapsed=months_elapsed)
    if completed_count <= 0:
        return "short"
    if completed_count >= target and completed_count >= expected:
        return "strong"
    if completed_count >= expected:
        return "ok"
    return "short"


def filter_bookmarks_since(
    bookmarks: list[Bookmark],
    *,
    since: datetime,
) -> list[Bookmark]:
    since = _as_utc(since)
    out: list[Bookmark] = []
    for bookmark in bookmarks:
        when = _completion_time(bookmark)
        if when is None:
            continue
        if _as_utc(when) >= since:
            out.append(bookmark)
    return out


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


def build_field_insights(
    profile: Profile,
    *,
    completed_bookmarks: list[Bookmark],
    saved_bookmarks: list[Bookmark] | None = None,
    now: datetime | None = None,
    joined_at: datetime | None = None,
) -> list[FieldInsight]:
    """Count completed opportunities since membership-year start, paced by join + grade."""
    now = _as_utc(now or datetime.now(UTC))
    joined = _as_utc(joined_at or resolve_joined_at(profile))
    since = membership_year_start(joined, now=now)
    months_elapsed = months_into_membership_year(joined, now=now)
    grade = profile.grade_level

    saved_bookmarks = saved_bookmarks or []
    period_completed = filter_bookmarks_since(completed_bookmarks, since=since)
    insights: list[FieldInsight] = []

    for field in sorted(profile.fields, key=lambda item: item.name.lower()):
        completed_count = sum(
            1
            for bookmark in period_completed
            if bookmark.opportunity
            and any(f.slug == field.slug for f in bookmark.opportunity.fields)
        )
        planned_count = sum(
            1
            for bookmark in saved_bookmarks
            if bookmark.opportunity
            and any(f.slug == field.slug for f in bookmark.opportunity.fields)
        )
        insights.append(
            FieldInsight(
                field=FieldOption.model_validate(field),
                completed_count=completed_count,
                planned_count=planned_count,
                status=field_pace_status(
                    completed_count,
                    grade=grade,
                    months_elapsed=months_elapsed,
                ),
            )
        )
    return insights


def build_insight_summary(
    insights: list[FieldInsight],
    *,
    grade: int,
    joined_at: datetime,
    now: datetime | None = None,
) -> str:
    now = _as_utc(now or datetime.now(UTC))
    months_elapsed = months_into_membership_year(joined_at, now=now)
    expected = expected_completions_by_pace(grade=grade, months_elapsed=months_elapsed)
    target = yearly_target_for_grade(grade)

    if not insights:
        return (
            "Add interests to see how completed opportunities cover each field "
            "since you joined."
        )

    strong_or_ok = [item for item in insights if item.completed_count > 0]
    short = [item for item in insights if item.status == "short"]
    behind = [
        item
        for item in short
        if item.completed_count > 0 and item.completed_count < expected
    ]

    parts: list[str] = []
    if strong_or_ok:
        coverage = ", ".join(
            f"{item.completed_count} in {item.field.name}" for item in strong_or_ok
        )
        parts.append(
            f"Since your membership year started you've completed {coverage} "
            "opportunit(ies)."
        )
    else:
        parts.append(
            "You haven't marked any opportunities done yet in this membership year. "
            "Open an opportunity and tap Mark done."
        )

    if behind:
        names = ", ".join(item.field.name for item in behind)
        parts.append(
            f"For grade {grade}, about {expected}+ per field by now "
            f"(~{target}/year) keeps you on pace — you're running short on {names}."
        )
    elif short:
        if len(short) == 1:
            parts.append(
                f"You're a little short on {short[0].field.name} for a grade {grade} pace."
            )
        elif len(short) == 2:
            parts.append(
                f"You're a little short on {short[0].field.name} and "
                f"{short[1].field.name} for a grade {grade} pace."
            )
        else:
            named = ", ".join(item.field.name for item in short[:-1])
            parts.append(
                f"You're a little short on {named}, and {short[-1].field.name} "
                f"for a grade {grade} pace."
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

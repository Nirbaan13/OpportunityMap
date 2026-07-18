from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import Bookmark, Opportunity, User
from app.schemas.bookmark import BookmarkStatus


def _bookmark_query(user_id: int):
    return (
        select(Bookmark)
        .options(joinedload(Bookmark.opportunity).joinedload(Opportunity.fields))
        .where(Bookmark.user_id == user_id)
    )


def list_bookmarks(
    db: Session,
    user: User,
    *,
    page: int = 1,
    page_size: int = 20,
    status_filter: BookmarkStatus | None = None,
) -> tuple[list[Bookmark], int]:
    base = select(Bookmark).where(Bookmark.user_id == user.id)
    if status_filter is not None:
        base = base.where(Bookmark.status == status_filter)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0

    query = _bookmark_query(user.id)
    if status_filter is not None:
        query = query.where(Bookmark.status == status_filter)

    rows = list(
        db.scalars(
            query.order_by(Bookmark.created_at.desc(), Bookmark.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .unique()
        .all()
    )
    return rows, total


def get_bookmark(db: Session, user: User, opportunity_id: int) -> Bookmark:
    bookmark = db.scalar(
        _bookmark_query(user.id).where(Bookmark.opportunity_id == opportunity_id)
    )
    if bookmark is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found",
        )
    return bookmark


def get_bookmark_optional(db: Session, user: User, opportunity_id: int) -> Bookmark | None:
    return db.scalar(
        _bookmark_query(user.id).where(Bookmark.opportunity_id == opportunity_id)
    )


def create_bookmark(
    db: Session,
    user: User,
    opportunity_id: int,
    *,
    remind_me: bool = False,
    status_value: BookmarkStatus = "saved",
) -> Bookmark:
    opportunity = db.scalar(
        select(Opportunity)
        .options(joinedload(Opportunity.fields))
        .where(Opportunity.id == opportunity_id)
    )
    if opportunity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found",
        )

    existing = db.scalar(
        select(Bookmark).where(
            Bookmark.user_id == user.id,
            Bookmark.opportunity_id == opportunity_id,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Opportunity already bookmarked",
        )

    now = datetime.now(UTC)
    bookmark = Bookmark(
        user_id=user.id,
        opportunity_id=opportunity_id,
        remind_me=False if status_value == "completed" else remind_me,
        status=status_value,
        completed_at=now if status_value == "completed" else None,
    )
    db.add(bookmark)
    db.commit()
    return get_bookmark(db, user, opportunity_id)


def set_remind_me(
    db: Session,
    user: User,
    opportunity_id: int,
    remind_me: bool,
) -> Bookmark:
    """Opt in/out of 10-day and 1-day deadline reminders. Creates a bookmark if needed."""
    opportunity = db.scalar(select(Opportunity).where(Opportunity.id == opportunity_id))
    if opportunity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found",
        )

    bookmark = db.scalar(
        select(Bookmark).where(
            Bookmark.user_id == user.id,
            Bookmark.opportunity_id == opportunity_id,
        )
    )
    if bookmark is None:
        if not remind_me:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bookmark not found",
            )
        bookmark = Bookmark(
            user_id=user.id,
            opportunity_id=opportunity_id,
            remind_me=True,
            status="saved",
        )
        db.add(bookmark)
    else:
        if bookmark.status == "completed" and remind_me:
            # Completed items don't need deadline reminders
            bookmark.remind_me = False
        else:
            bookmark.remind_me = remind_me

    db.commit()
    return get_bookmark(db, user, opportunity_id)


def set_status(
    db: Session,
    user: User,
    opportunity_id: int,
    status_value: BookmarkStatus,
) -> Bookmark:
    """Mark an opportunity saved or completed. Creates a bookmark if needed."""
    opportunity = db.scalar(select(Opportunity).where(Opportunity.id == opportunity_id))
    if opportunity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found",
        )

    bookmark = db.scalar(
        select(Bookmark).where(
            Bookmark.user_id == user.id,
            Bookmark.opportunity_id == opportunity_id,
        )
    )
    now = datetime.now(UTC)
    if bookmark is None:
        bookmark = Bookmark(
            user_id=user.id,
            opportunity_id=opportunity_id,
            remind_me=False,
            status=status_value,
            completed_at=now if status_value == "completed" else None,
        )
        db.add(bookmark)
    else:
        bookmark.status = status_value
        if status_value == "completed":
            bookmark.completed_at = bookmark.completed_at or now
            bookmark.remind_me = False
        else:
            bookmark.completed_at = None

    db.commit()
    return get_bookmark(db, user, opportunity_id)


def delete_bookmark(db: Session, user: User, opportunity_id: int) -> None:
    bookmark = db.scalar(
        select(Bookmark).where(
            Bookmark.user_id == user.id,
            Bookmark.opportunity_id == opportunity_id,
        )
    )
    if bookmark is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found",
        )
    db.delete(bookmark)
    db.commit()


def list_completed_for_user(db: Session, user: User) -> list[Bookmark]:
    return list(
        db.scalars(
            _bookmark_query(user.id)
            .where(Bookmark.status == "completed")
            .order_by(Bookmark.completed_at.desc().nulls_last(), Bookmark.id.desc())
        )
        .unique()
        .all()
    )

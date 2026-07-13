from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import Bookmark, Opportunity, User


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
) -> tuple[list[Bookmark], int]:
    base = select(Bookmark).where(Bookmark.user_id == user.id)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0

    rows = list(
        db.scalars(
            _bookmark_query(user.id)
            .order_by(Bookmark.created_at.desc(), Bookmark.id.desc())
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


def create_bookmark(
    db: Session,
    user: User,
    opportunity_id: int,
    *,
    remind_me: bool = False,
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

    bookmark = Bookmark(
        user_id=user.id,
        opportunity_id=opportunity_id,
        remind_me=remind_me,
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
        )
        db.add(bookmark)
    else:
        bookmark.remind_me = remind_me

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

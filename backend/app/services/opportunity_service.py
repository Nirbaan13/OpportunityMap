from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models import Field, Opportunity
from app.models.enums import OpportunityType
from app.schemas.opportunity import OpportunitySort


def _base_query() -> Select[tuple[Opportunity]]:
    return select(Opportunity).options(joinedload(Opportunity.fields))


def _apply_filters(
    stmt: Select[tuple[Opportunity]],
    *,
    q: str | None,
    opportunity_type: OpportunityType | None,
    field_slug: str | None,
    source_name: str | None,
    country_code: str | None,
    grade: int | None,
    deadline_before: datetime | None,
    deadline_after: datetime | None,
    open_only: bool,
    is_active: bool,
) -> Select[tuple[Opportunity]]:
    stmt = stmt.where(Opportunity.is_active.is_(is_active))

    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Opportunity.title.ilike(pattern),
                Opportunity.description.ilike(pattern),
            )
        )

    if opportunity_type is not None:
        stmt = stmt.where(Opportunity.opportunity_type == opportunity_type)

    if source_name:
        stmt = stmt.where(Opportunity.source_name == source_name.strip().lower())

    if field_slug:
        slug = field_slug.strip().lower()
        stmt = stmt.where(
            Opportunity.fields.any(Field.slug == slug)  # type: ignore[arg-type]
        )

    if country_code:
        code = country_code.strip().upper()
        # null eligible_countries means open to all countries
        stmt = stmt.where(
            or_(
                Opportunity.eligible_countries.is_(None),
                Opportunity.eligible_countries.contains([code]),
            )
        )

    if grade is not None:
        stmt = stmt.where(
            and_(
                or_(Opportunity.grade_min.is_(None), Opportunity.grade_min <= grade),
                or_(Opportunity.grade_max.is_(None), Opportunity.grade_max >= grade),
            )
        )

    if deadline_before is not None:
        stmt = stmt.where(Opportunity.deadline_at.is_not(None)).where(
            Opportunity.deadline_at <= deadline_before
        )

    if deadline_after is not None:
        stmt = stmt.where(Opportunity.deadline_at.is_not(None)).where(
            Opportunity.deadline_at >= deadline_after
        )

    if open_only:
        now = datetime.now(UTC)
        stmt = stmt.where(Opportunity.deadline_at.is_not(None)).where(
            Opportunity.deadline_at >= now
        )

    return stmt


def _apply_sort(
    stmt: Select[tuple[Opportunity]],
    sort: OpportunitySort,
) -> Select[tuple[Opportunity]]:
    if sort == OpportunitySort.DEADLINE_ASC:
        # Null deadlines last so students see actionable deadlines first
        return stmt.order_by(
            Opportunity.deadline_at.asc().nulls_last(),
            Opportunity.id.asc(),
        )
    if sort == OpportunitySort.DEADLINE_DESC:
        return stmt.order_by(
            Opportunity.deadline_at.desc().nulls_last(),
            Opportunity.id.desc(),
        )
    if sort == OpportunitySort.TITLE:
        return stmt.order_by(Opportunity.title.asc(), Opportunity.id.asc())
    # newest
    return stmt.order_by(Opportunity.created_at.desc(), Opportunity.id.desc())


def list_opportunities(
    db: Session,
    *,
    q: str | None = None,
    opportunity_type: OpportunityType | None = None,
    field_slug: str | None = None,
    source_name: str | None = None,
    country_code: str | None = None,
    grade: int | None = None,
    deadline_before: datetime | None = None,
    deadline_after: datetime | None = None,
    open_only: bool = False,
    is_active: bool = True,
    sort: OpportunitySort = OpportunitySort.DEADLINE_ASC,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Opportunity], int]:
    filtered = _apply_filters(
        select(Opportunity.id),
        q=q,
        opportunity_type=opportunity_type,
        field_slug=field_slug,
        source_name=source_name,
        country_code=country_code,
        grade=grade,
        deadline_before=deadline_before,
        deadline_after=deadline_after,
        open_only=open_only,
        is_active=is_active,
    )
    total = db.scalar(select(func.count()).select_from(filtered.subquery())) or 0

    stmt = _apply_filters(
        _base_query(),
        q=q,
        opportunity_type=opportunity_type,
        field_slug=field_slug,
        source_name=source_name,
        country_code=country_code,
        grade=grade,
        deadline_before=deadline_before,
        deadline_after=deadline_after,
        open_only=open_only,
        is_active=is_active,
    )
    stmt = _apply_sort(stmt, sort)
    offset = (page - 1) * page_size
    rows = list(db.scalars(stmt.offset(offset).limit(page_size)).unique().all())
    return rows, total


def get_opportunity(db: Session, opportunity_id: int) -> Opportunity:
    opportunity = db.scalar(_base_query().where(Opportunity.id == opportunity_id))
    if opportunity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found",
        )
    return opportunity

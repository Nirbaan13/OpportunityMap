from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import OpportunityType

opportunity_fields = Table(
    "opportunity_fields",
    Base.metadata,
    Column("opportunity_id", ForeignKey("opportunities.id", ondelete="CASCADE"), primary_key=True),
    Column("field_id", ForeignKey("fields.id", ondelete="CASCADE"), primary_key=True),
)


class Opportunity(Base):
    """An opportunity scraped from an external site or added manually."""

    __tablename__ = "opportunities"
    __table_args__ = (UniqueConstraint("source_name", "external_id", name="uq_opportunity_source"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    opportunity_type: Mapped[OpportunityType] = mapped_column(
        Enum(
            OpportunityType,
            name="opportunity_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        index=True,
    )
    source_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    application_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    grade_eligibility: Mapped[str | None] = mapped_column(Text, nullable=True)
    grade_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    grade_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    eligible_countries: Mapped[list[str] | None] = mapped_column(ARRAY(String(2)), nullable=True)
    experience_requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_scraped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    fields: Mapped[list["Field"]] = relationship(
        secondary=opportunity_fields, back_populates="opportunities"
    )
    bookmarks: Mapped[list["Bookmark"]] = relationship(back_populates="opportunity")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="opportunity")

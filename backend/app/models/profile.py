from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

profile_fields = Table(
    "profile_fields",
    Base.metadata,
    Column("profile_id", ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True),
    Column("field_id", ForeignKey("fields.id", ondelete="CASCADE"), primary_key=True),
)


class ProfileActivity(Base):
    """Join between a profile and an activity type, with planned vs completed status."""

    __tablename__ = "profile_activities"

    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True
    )
    activity_id: Mapped[int] = mapped_column(
        ForeignKey("activities.id", ondelete="CASCADE"), primary_key=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")

    profile: Mapped["Profile"] = relationship(back_populates="activity_links")
    activity: Mapped["Activity"] = relationship(back_populates="profile_links")


class Profile(Base):
    """Student profile used for eligibility checks and interest matching."""

    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    grade_level: Mapped[int] = mapped_column(Integer, nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    research_experience: Mapped[str | None] = mapped_column(Text, nullable=True)
    olympiad_experience: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="profile")
    fields: Mapped[list["Field"]] = relationship(
        secondary=profile_fields, back_populates="profiles"
    )
    activity_links: Mapped[list[ProfileActivity]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def completed_activity_list(self) -> list["Activity"]:
        return [
            link.activity
            for link in self.activity_links
            if link.status == "completed" and link.activity is not None
        ]

    @property
    def planned_activity_list(self) -> list["Activity"]:
        return [
            link.activity
            for link in self.activity_links
            if link.status == "planned" and link.activity is not None
        ]


# Back-compat alias for imports that still expect the old Table name.
profile_activities = ProfileActivity.__table__

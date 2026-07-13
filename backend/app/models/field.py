from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Field(Base):
    """Shared taxonomy for student interests and opportunity topics (e.g. Physics, AI)."""

    __tablename__ = "fields"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    profiles: Mapped[list["Profile"]] = relationship(
        secondary="profile_fields", back_populates="fields"
    )
    opportunities: Mapped[list["Opportunity"]] = relationship(
        secondary="opportunity_fields", back_populates="fields"
    )

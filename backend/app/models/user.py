from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.bookmark import Bookmark
    from app.models.notification import Notification
    from app.models.payment import Payment, PremiumGrant
    from app.models.profile import Profile


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_premium: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    premium_activated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    premium_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    profile: Mapped[Profile | None] = relationship(back_populates="user", uselist=False)
    bookmarks: Mapped[list[Bookmark]] = relationship(back_populates="user")
    notifications: Mapped[list[Notification]] = relationship(back_populates="user")
    payments: Mapped[list[Payment]] = relationship(back_populates="user")
    premium_grants: Mapped[list[PremiumGrant]] = relationship(back_populates="user")

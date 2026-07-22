from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="razorpay")
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="created")
    razorpay_order_id: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    razorpay_signature: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="payments")
    attempts: Mapped[list[PaymentAttempt]] = relationship(
        back_populates="payment", cascade="all, delete-orphan"
    )


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    payment_id: Mapped[int] = mapped_column(
        ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    razorpay_payment_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_refunded_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    payment: Mapped[Payment] = relationship(back_populates="attempts")
    premium_grant: Mapped[PremiumGrant | None] = relationship(
        back_populates="payment_attempt", uselist=False
    )


class PaymentWebhookEvent(Base):
    __tablename__ = "payment_webhook_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_event_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)


class PremiumGrant(Base):
    __tablename__ = "premium_grants"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    payment_attempt_id: Mapped[int] = mapped_column(
        ForeignKey("payment_attempts.id", ondelete="RESTRICT"), unique=True, nullable=False
    )
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False, default=365)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revocation_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped[User] = relationship(back_populates="premium_grants")
    payment_attempt: Mapped[PaymentAttempt] = relationship(back_populates="premium_grant")

"""Add durable Razorpay events, attempts, and premium grants

Revision ID: 009_payment_webhooks
Revises: 008_bookmark_status
Create Date: 2026-07-21
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "009_payment_webhooks"
down_revision: str | None = "008_bookmark_status"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "payment_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "payment_id",
            sa.Integer(),
            sa.ForeignKey("payments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("razorpay_payment_id", sa.String(100), nullable=False, unique=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("amount_paise", sa.Integer(), nullable=False),
        sa.Column("amount_refunded_paise", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("error_code", sa.String(100), nullable=True),
        sa.Column("error_description", sa.Text(), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_payment_attempts_payment_id", "payment_attempts", ["payment_id"])

    op.create_table(
        "payment_webhook_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider_event_id", sa.String(128), nullable=False, unique=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processing_error", sa.Text(), nullable=True),
    )

    op.create_table(
        "premium_grants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "payment_attempt_id",
            sa.Integer(),
            sa.ForeignKey("payment_attempts.id", ondelete="RESTRICT"),
            nullable=False,
            unique=True,
        ),
        sa.Column("duration_days", sa.Integer(), nullable=False, server_default="365"),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revocation_reason", sa.String(255), nullable=True),
    )
    op.create_index("ix_premium_grants_user_id", "premium_grants", ["user_id"])

    # Preserve genuine historical purchases. Development unlocks are intentionally
    # excluded so their entitlement is removed by the recomputation below.
    op.execute(
        """
        INSERT INTO payment_attempts (
            payment_id, razorpay_payment_id, status, amount_paise, currency, captured_at
        )
        SELECT id, razorpay_payment_id, 'captured', amount_paise, currency,
               COALESCE(paid_at, created_at)
        FROM payments
        WHERE provider = 'razorpay'
          AND status = 'paid'
          AND razorpay_payment_id IS NOT NULL
        """
    )
    op.execute(
        """
        INSERT INTO premium_grants (user_id, payment_attempt_id, duration_days, granted_at)
        SELECT p.user_id, pa.id, 365, COALESCE(p.paid_at, p.created_at)
        FROM payment_attempts pa
        JOIN payments p ON p.id = pa.payment_id
        WHERE pa.status = 'captured'
        """
    )
    op.execute(
        """
        UPDATE users
        SET is_premium = false, premium_activated_at = NULL, premium_until = NULL
        WHERE EXISTS (SELECT 1 FROM payments p WHERE p.user_id = users.id)
        """
    )
    op.execute(
        """
        WITH RECURSIVE ordered AS (
            SELECT pg.user_id, pg.granted_at, pg.duration_days,
                   ROW_NUMBER() OVER (
                       PARTITION BY pg.user_id ORDER BY pg.granted_at, pg.id
                   ) AS rn
            FROM premium_grants pg
            WHERE pg.revoked_at IS NULL
        ),
        timeline AS (
            SELECT user_id, rn, granted_at,
                   granted_at + (duration_days * INTERVAL '1 day') AS expires_at
            FROM ordered
            WHERE rn = 1
            UNION ALL
            SELECT o.user_id, o.rn, o.granted_at,
                   GREATEST(o.granted_at, t.expires_at)
                       + (o.duration_days * INTERVAL '1 day')
            FROM timeline t
            JOIN ordered o ON o.user_id = t.user_id AND o.rn = t.rn + 1
        ),
        entitlement AS (
            SELECT user_id, MIN(granted_at) AS activated_at, MAX(expires_at) AS expires_at
            FROM timeline
            GROUP BY user_id
        )
        UPDATE users u
        SET premium_activated_at = e.activated_at,
            premium_until = e.expires_at,
            is_premium = e.expires_at >= NOW()
        FROM entitlement e
        WHERE u.id = e.user_id
        """
    )


def downgrade() -> None:
    op.drop_index("ix_premium_grants_user_id", table_name="premium_grants")
    op.drop_table("premium_grants")
    op.drop_table("payment_webhook_events")
    op.drop_index("ix_payment_attempts_payment_id", table_name="payment_attempts")
    op.drop_table("payment_attempts")

import hashlib
import logging
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.core.emails import normalize_email
from app.core.security import create_access_token, hash_password, verify_password
from app.models import PasswordResetToken, User
from app.services.email_service import send_email

logger = logging.getLogger(__name__)

RESET_TOKEN_TTL = timedelta(hours=1)


def _find_user_by_email(db: Session, email: str) -> User | None:
    """Match users case-insensitively (legacy rows may not be lowercased yet)."""
    normalized = normalize_email(email)
    return db.scalar(
        select(User).where(func.lower(User.email) == normalized)
    )


def register_user(db: Session, email: str, password: str) -> User:
    email = normalize_email(email)
    existing = _find_user_by_email(db, email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> str:
    email = normalize_email(email)
    user = _find_user_by_email(db, email)
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    # Heal mixed-case legacy emails so JWT subject stays stable.
    if user.email != email:
        user.email = email
    user.last_login_at = datetime.now(UTC)
    try:
        db.commit()
    except Exception:
        # Schema may lag a deploy by seconds; never block login on metadata write.
        db.rollback()
        logger.exception("Could not persist login metadata for %s", email)

    return create_access_token(email)


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _reset_url(raw_token: str) -> str:
    return f"{settings.frontend_url.rstrip('/')}/reset-password?token={raw_token}"


def _build_reset_email(raw_token: str) -> tuple[str, str]:
    url = _reset_url(raw_token)
    text_body = (
        "We received a request to reset your OpportunityMap password.\n\n"
        f"Reset it here (valid for 1 hour): {url}\n\n"
        "If you didn't request this, you can ignore this email.\n\n"
        "— OpportunityMap\n"
    )
    html_body = (
        '<html><body style="font-family: system-ui, sans-serif; line-height: 1.5; '
        'color: #1a1a1a;">'
        "<p>We received a request to reset your OpportunityMap password.</p>"
        f'<p><a href="{url}">Reset your password</a> (valid for 1 hour)</p>'
        '<p style="color:#666;font-size:12px;">If you didn\'t request this, you can '
        "safely ignore this email.</p>"
        "</body></html>"
    )
    return text_body, html_body


def request_password_reset(db: Session, email: str) -> None:
    """Always succeeds silently — does not reveal whether the email is registered."""
    user = _find_user_by_email(db, email)
    if user is None or not user.is_active:
        logger.info("Password reset requested for unknown/inactive email")
        return

    now = datetime.now(UTC)
    # Invalidate any earlier unused tokens for this user.
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None),
    ).update({"expires_at": now})

    raw_token = secrets.token_urlsafe(32)
    token = PasswordResetToken(
        user_id=user.id,
        token_hash=_hash_token(raw_token),
        expires_at=now + RESET_TOKEN_TTL,
    )
    db.add(token)
    db.commit()

    subject = "Reset your OpportunityMap password"
    text_body, html_body = _build_reset_email(raw_token)
    send_email(to_email=user.email, subject=subject, text_body=text_body, html_body=html_body)


def reset_password(db: Session, raw_token: str, new_password: str) -> None:
    token_hash = _hash_token(raw_token)
    now = datetime.now(UTC)
    token = db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )
    if (
        token is None
        or token.used_at is not None
        or token.expires_at.replace(tzinfo=token.expires_at.tzinfo or UTC) < now
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset link is invalid or has expired. Request a new one.",
        )

    user = db.get(User, token.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset link is invalid or has expired. Request a new one.",
        )

    user.password_hash = hash_password(new_password)
    token.used_at = now
    db.commit()

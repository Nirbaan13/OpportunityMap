from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UpdateAutoRenewRequest,
    UserResponse,
)
from app.services.auth_service import authenticate_user, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


def _to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at,
        has_profile=user.profile is not None,
        is_premium=user.is_premium,
        premium_until=user.premium_until,
        auto_renew=user.auto_renew,
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> UserResponse:
    user = register_user(db, payload.email, payload.password)
    return _to_user_response(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    token = authenticate_user(db, payload.email, payload.password)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return _to_user_response(current_user)


@router.patch("/me/auto-renew", response_model=UserResponse)
def update_auto_renew(
    payload: UpdateAutoRenewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    current_user.auto_renew = payload.auto_renew
    db.commit()
    db.refresh(current_user)
    return _to_user_response(current_user)

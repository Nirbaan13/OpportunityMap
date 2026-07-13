from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.auth import _to_user_response
from app.config import settings
from app.core.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.auth import UserResponse
from app.schemas.payment import (
    CreateOrderResponse,
    PaymentConfigResponse,
    VerifyPaymentRequest,
)
from app.services import payment_service

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/config", response_model=PaymentConfigResponse)
def payment_config() -> PaymentConfigResponse:
    """Public pricing + whether Razorpay checkout is available."""
    return PaymentConfigResponse(
        price_inr=settings.premium_price_inr,
        amount_paise=settings.premium_amount_paise,
        currency="INR",
        razorpay_enabled=settings.razorpay_enabled,
        razorpay_key_id=settings.razorpay_key_id or None,
        dev_unlock_available=settings.debug and not settings.razorpay_enabled,
        description=(
            f"Yearly ₹{settings.premium_price_inr} membership for profile, "
            "personalized recommendations, saved opportunities, and deadline alerts."
        ),
    )


@router.post("/create-order", response_model=CreateOrderResponse)
def create_order(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CreateOrderResponse:
    data = payment_service.create_razorpay_order(db, current_user)
    return CreateOrderResponse(**data)


@router.post("/verify", response_model=UserResponse)
def verify_payment(
    payload: VerifyPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    user = payment_service.verify_razorpay_payment(
        db,
        current_user,
        razorpay_order_id=payload.razorpay_order_id,
        razorpay_payment_id=payload.razorpay_payment_id,
        razorpay_signature=payload.razorpay_signature,
    )
    return _to_user_response(user)


@router.post("/dev-unlock", response_model=UserResponse)
def dev_unlock(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Testing only: unlock premium when DEBUG=true and Razorpay is not configured."""
    user = payment_service.dev_unlock(db, current_user)
    return _to_user_response(user)

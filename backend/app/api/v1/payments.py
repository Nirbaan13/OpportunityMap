from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from app.api.v1.auth import _to_user_response
from app.config import settings
from app.core.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.auth import UserResponse
from app.schemas.payment import (
    CreateOrderRequest,
    CreateOrderResponse,
    PaymentConfigResponse,
    PaymentStatusResponse,
    PolarCheckoutResponse,
    VerifyPaymentRequest,
    WebhookResponse,
)
from app.services import payment_service, polar_service

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/config", response_model=PaymentConfigResponse)
def payment_config() -> PaymentConfigResponse:
    """Public pricing + whether checkout providers are available."""
    return PaymentConfigResponse(
        price_inr=settings.premium_price_inr,
        amount_paise=settings.premium_amount_paise,
        currency="INR",
        razorpay_enabled=settings.razorpay_enabled,
        polar_enabled=settings.polar_enabled,
        razorpay_key_id=settings.razorpay_key_id or None,
        dev_unlock_available=settings.dev_unlock_available,
        description=(
            f"Yearly ₹{settings.premium_price_inr} membership for profile, "
            "personalized recommendations, saved opportunities, and deadline alerts."
        ),
    )


@router.post("/create-order", response_model=CreateOrderResponse)
def create_order(
    payload: CreateOrderRequest = CreateOrderRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CreateOrderResponse:
    data = payment_service.create_razorpay_order(
        db, current_user, currency=payload.currency
    )
    return CreateOrderResponse(**data)


@router.post("/polar/create-checkout", response_model=PolarCheckoutResponse)
def create_polar_checkout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PolarCheckoutResponse:
    data = polar_service.create_checkout(db, current_user)
    return PolarCheckoutResponse(**data)


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


@router.get("/status/{order_id}", response_model=PaymentStatusResponse)
def payment_status(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaymentStatusResponse:
    return PaymentStatusResponse(
        **payment_service.reconcile_order(db, current_user, order_id)
    )


@router.post("/webhooks/razorpay", response_model=WebhookResponse)
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(default=""),
    x_razorpay_event_id: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> WebhookResponse:
    raw_body = await request.body()
    payment_service.process_razorpay_webhook(
        db,
        raw_body=raw_body,
        signature=x_razorpay_signature,
        event_id=x_razorpay_event_id,
    )
    return WebhookResponse()


@router.post("/webhooks/polar", response_model=WebhookResponse)
async def polar_webhook(
    request: Request,
    webhook_id: str = Header(default=""),
    webhook_timestamp: str = Header(default=""),
    webhook_signature: str = Header(default=""),
    db: Session = Depends(get_db),
) -> WebhookResponse:
    raw_body = await request.body()
    polar_service.process_webhook(
        db,
        raw_body=raw_body,
        webhook_id=webhook_id,
        webhook_timestamp=webhook_timestamp,
        webhook_signature=webhook_signature,
    )
    return WebhookResponse()


if settings.dev_unlock_available:

    @router.post("/dev-unlock", response_model=UserResponse)
    def dev_unlock(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> UserResponse:
        """Explicit development-only premium unlock."""
        user = payment_service.dev_unlock(db, current_user)
        return _to_user_response(user)

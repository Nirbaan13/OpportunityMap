from datetime import datetime

from pydantic import BaseModel, Field


class PaymentConfigResponse(BaseModel):
    price_inr: int
    amount_paise: int
    currency: str = "INR"
    razorpay_enabled: bool
    razorpay_key_id: str | None = None
    dev_unlock_available: bool
    description: str


class CreateOrderResponse(BaseModel):
    order_id: str
    amount_paise: int
    currency: str
    key_id: str
    name: str
    description: str
    prefill_email: str
    payment_id: int


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str = Field(min_length=1, max_length=100)
    razorpay_payment_id: str = Field(min_length=1, max_length=100)
    razorpay_signature: str = Field(min_length=1, max_length=255)


class PaymentStatusResponse(BaseModel):
    order_id: str
    status: str
    is_premium: bool
    premium_until: datetime | None


class WebhookResponse(BaseModel):
    received: bool = True

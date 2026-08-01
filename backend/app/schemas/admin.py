from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class AdminTotals(BaseModel):
    users: int
    active_users: int
    premium_users: int
    users_with_profile: int
    signups_last_7_days: int
    signups_last_30_days: int
    logins_last_7_days: int = 0
    logins_last_30_days: int = 0
    opportunities_active: int
    opportunities_total: int
    payments_paid: int
    payments_created: int
    paid_amount_inr: float = Field(description="Sum of paid INR amounts")
    paid_amount_usd: float = Field(description="Sum of paid USD amounts")


class AdminCountRow(BaseModel):
    key: str
    count: int


class AdminUserRow(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    is_premium: bool
    premium_until: datetime | None
    has_profile: bool
    created_at: datetime
    last_login_at: datetime | None = None


class AdminPaymentRow(BaseModel):
    id: int
    user_id: int
    user_email: EmailStr
    provider: str
    status: str
    amount: float
    currency: str
    created_at: datetime
    paid_at: datetime | None


class AdminOverviewResponse(BaseModel):
    totals: AdminTotals
    payments_by_status: list[AdminCountRow]
    payments_by_provider: list[AdminCountRow]
    recent_users: list[AdminUserRow]
    recent_payments: list[AdminPaymentRow]

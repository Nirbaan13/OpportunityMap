from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_database_url(url: str) -> str:
    """Railway/Render/Neon often provide postgres:// without the psycopg driver."""
    value = url.strip()
    if value.startswith("postgres://"):
        value = "postgresql://" + value[len("postgres://") :]
    if value.startswith("postgresql://") and "+psycopg" not in value.split("://", 1)[0]:
        value = "postgresql+psycopg://" + value[len("postgresql://") :]
    # Neon and most cloud Postgres require TLS
    if "sslmode=" not in value and ("neon.tech" in value or "supabase.co" in value):
        sep = "&" if "?" in value else "?"
        value = f"{value}{sep}sslmode=require"
    return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    database_url: str = "postgresql+psycopg://opportunitymap:opportunitymap_dev@localhost:5432/opportunitymap"
    secret_key: str = "change-me-in-production"
    cors_origins: str = "http://localhost:3000"
    app_name: str = "OpportunityMap API"
    environment: str = "development"
    debug: bool = False
    allow_dev_premium_unlock: bool = False
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    jwt_algorithm: str = "HS256"

    # Public site URL used in reminder emails
    frontend_url: str = "http://localhost:3000"

    # Premium unlock. Change prices without code changes.
    premium_price_inr: int = 299
    # Used for Polar international product amount recording (not shown on site).
    premium_price_usd: float = 3.99
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""
    # Polar (international checkout). Create a $3.99 one-time product in Polar dashboard.
    polar_access_token: str = ""
    polar_product_id: str = ""
    polar_webhook_secret: str = ""
    polar_api_base: str = "https://api.polar.sh/v1"

    # SMTP — leave SMTP_HOST empty to skip email (inbox still works)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_db_url(cls, value: object) -> object:
        if isinstance(value, str) and value.strip():
            return normalize_database_url(value)
        return value

    @field_validator("environment")
    @classmethod
    def _normalize_environment(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"development", "test", "preview", "production"}:
            raise ValueError("ENVIRONMENT must be development, test, preview, or production")
        return normalized

    @model_validator(mode="after")
    def _validate_payment_security(self) -> "Settings":
        has_key_id = bool(self.razorpay_key_id.strip())
        has_key_secret = bool(self.razorpay_key_secret.strip())
        if has_key_id != has_key_secret:
            raise ValueError("RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must be configured together")
        if self.environment == "production":
            if self.debug:
                raise ValueError("DEBUG must be false in production")
            if self.allow_dev_premium_unlock:
                raise ValueError("ALLOW_DEV_PREMIUM_UNLOCK cannot be enabled in production")
            if self.secret_key == "change-me-in-production":
                raise ValueError("SECRET_KEY must be changed in production")
            if has_key_id and not self.razorpay_webhook_secret.strip():
                raise ValueError(
                    "RAZORPAY_WEBHOOK_SECRET is required when Razorpay is enabled in production"
                )
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def email_enabled(self) -> bool:
        return bool(self.smtp_host.strip() and self.smtp_from.strip())

    @property
    def premium_amount_paise(self) -> int:
        return max(100, self.premium_price_inr) * 100

    @property
    def premium_amount_usd_cents(self) -> int:
        cents = int(round(max(0.5, self.premium_price_usd) * 100))
        return max(50, cents)

    @property
    def razorpay_enabled(self) -> bool:
        return bool(self.razorpay_key_id.strip() and self.razorpay_key_secret.strip())

    @property
    def polar_enabled(self) -> bool:
        return bool(self.polar_access_token.strip() and self.polar_product_id.strip())

    @property
    def dev_unlock_available(self) -> bool:
        return (
            self.environment in {"development", "test"}
            and self.debug
            and self.allow_dev_premium_unlock
            and not self.razorpay_enabled
        )


settings = Settings()

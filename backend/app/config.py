from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_database_url(url: str) -> str:
    """Railway/Render often provide postgres:// or postgresql:// without the psycopg driver."""
    value = url.strip()
    if value.startswith("postgres://"):
        value = "postgresql://" + value[len("postgres://") :]
    if value.startswith("postgresql://") and "+psycopg" not in value.split("://", 1)[0]:
        value = "postgresql+psycopg://" + value[len("postgresql://") :]
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
    debug: bool = False
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    jwt_algorithm: str = "HS256"

    # Public site URL used in reminder emails
    frontend_url: str = "http://localhost:3000"

    # Premium unlock (INR / year). Change PREMIUM_PRICE_INR later without code changes.
    premium_price_inr: int = 299
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""

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
    def razorpay_enabled(self) -> bool:
        return bool(self.razorpay_key_id.strip() and self.razorpay_key_secret.strip())


settings = Settings()

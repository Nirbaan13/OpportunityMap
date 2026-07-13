from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    database_url: str = "postgresql+psycopg://opportunitymap:opportunitymap_dev@localhost:5432/opportunitymap"
    api_url: str | None = None
    api_key: str | None = None


settings = Settings()

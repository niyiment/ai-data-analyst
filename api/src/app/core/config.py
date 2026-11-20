"""Typed application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Single source of configuration for the API."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url_app: str = (
        "postgresql+psycopg://app_rw:local_app_rw_password@localhost:5433/ai_data_analyst"
    )
    database_url_analyst: str = (
        "postgresql+psycopg://analyst_ro:local_analyst_ro_password@localhost:5433/ai_data_analyst"
    )
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    session_ttl_hours: int = 24
    cleanup_secret: str = ""
    allowed_origin: str = "http://localhost:3000"
    rate_limit_per_minute: int = 30
    max_upload_mb: int = 10
    max_rows: int = 500
    query_timeout_seconds: int = 10
    log_level: str = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()

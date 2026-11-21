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
    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_cloud_base_url: str = "https://ollama.com"
    ollama_cloud_api_key: str = ""
    ollama_cloud_model: str = "llama3.2"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    anthropic_api_key: str = ""
    claude_model: str = "claude-3-5-sonnet-latest"
    session_ttl_hours: int = 24
    cleanup_secret: str = ""
    allowed_origin: str = "http://localhost:3000"
    rate_limit_per_minute: int = 30
    questions_per_session_per_hour: int = 30
    llm_daily_call_budget: int = 1000
    max_upload_mb: int = 10
    max_rows: int = 500
    query_timeout_seconds: int = 10
    log_level: str = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings — all values come from environment variables or .env file.

    No secret values are committed to source control.
    See .env.example for the full list of supported variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_name: str = "AISYS Library Management System"
    app_version: str = "0.1.0"
    environment: Literal["development", "testing", "production"] = "development"
    debug: bool = False
    secret_key: str = Field(
        default="CHANGE-ME-IN-PRODUCTION",
        description="Used for JWT signing and session cookies.",
    )

    # ── Server ────────────────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000
    allowed_hosts: list[str] = ["*"]

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="sqlite+aiosqlite:///./aisys_lms.db",
        description="Async SQLAlchemy connection URL.",
    )
    database_url_sync: str = Field(
        default="sqlite:///./aisys_lms.db",
        description="Sync URL for Alembic migrations.",
    )
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # ── Auth / JWT ────────────────────────────────────────────────────────────
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # ── RFID middleware ───────────────────────────────────────────────────────
    rfid_adapter: Literal["mock", "ncip", "sip2"] = "mock"
    ncip_endpoint: str = "http://localhost:9000/ncip"
    sip2_host: str = "localhost"
    sip2_port: int = 6001
    rfid_event_timeout_seconds: int = 10
    rfid_retry_attempts: int = 3

    # ── Notifications ─────────────────────────────────────────────────────────
    email_adapter: Literal["mock", "smtp"] = "mock"
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "library@aisys.local"

    sms_adapter: Literal["mock", "twilio"] = "mock"
    print_adapter: Literal["mock"] = "mock"
    cctv_adapter: Literal["mock"] = "mock"

    # ── Circulation rules ─────────────────────────────────────────────────────
    default_loan_days: int = 14
    max_renewals: int = 2
    max_fine_before_block: float = 50.0   # configurable fine limit (AC04)
    fine_per_day: float = 1.0

    # ── Data migration ────────────────────────────────────────────────────────
    migration_batch_size: int = 500
    migration_staging_schema: str = "staging"

    # ── Offline / ops ─────────────────────────────────────────────────────────
    log_level: str = "INFO"
    log_format: Literal["json", "console"] = "console"
    health_check_path: str = "/health"

    @field_validator("database_url", "database_url_sync", mode="before")
    @classmethod
    def validate_db_url(cls, v: str) -> str:  # noqa: ANN001
        if not v:
            raise ValueError("database_url must not be empty")
        return v

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_testing(self) -> bool:
        return self.environment == "testing"


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings singleton.

    Use FastAPI's dependency injection in routes::

        from app.core.config import get_settings
        settings = Depends(get_settings)
    """
    return Settings()


# Module-level convenience alias
settings: Settings = get_settings()

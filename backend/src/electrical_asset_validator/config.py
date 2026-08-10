from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="EAV_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Electrical Asset Validator API"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./electrical_asset_validator.db"
    max_upload_mb: int = Field(default=10, ge=1, le=100)
    # Minutes to keep stored runs before they are swept; 0 keeps them
    # forever. Meant for public demo deployments.
    demo_retention_minutes: int = Field(default=0, ge=0)
    docs_enabled: bool = True
    static_dir: str | None = None
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
        ]
    )

    @field_validator("api_prefix")
    @classmethod
    def validate_api_prefix(cls, value: str) -> str:
        if (
            not value
            or value == "/"
            or not value.startswith("/")
            or value.endswith("/")
            or "//" in value
        ):
            raise ValueError(
                "api_prefix must be a non-root path such as '/api/v1' "
                "without a trailing slash"
            )
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()

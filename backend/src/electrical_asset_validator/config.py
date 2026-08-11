from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="EAV_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Electrical Asset Validator API"
    app_version: str = "0.2.0"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./electrical_asset_validator.db"
    max_upload_mb: int = Field(default=10, ge=1, le=100)
    # Minutes to keep stored runs before they are swept; 0 keeps them
    # forever. Meant for public demo deployments.
    demo_retention_minutes: int = Field(default=0, ge=0)
    docs_enabled: bool = True
    # Comma-separated shared bearer tokens ("alpha-token,beta-token"). Empty
    # keeps the API open with session-cookie scoping; any tokens switch every
    # data route to mandatory bearer auth with per-token run isolation.
    # NoDecode stops pydantic-settings from expecting JSON for the list.
    api_tokens: Annotated[list[str], NoDecode] = Field(default_factory=list)
    static_dir: str | None = None
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
        ]
    )

    @field_validator("api_tokens", mode="before")
    @classmethod
    def split_api_tokens(cls, value: object) -> object:
        if isinstance(value, str):
            if not value.strip():
                return []
            return [token.strip() for token in value.split(",")]
        return value

    @field_validator("api_tokens")
    @classmethod
    def reject_empty_api_tokens(cls, value: list[str]) -> list[str]:
        # An empty accepted token would make "Authorization: Bearer" with no
        # credentials a valid login, so a blank entry is a configuration
        # error rather than something to silently drop.
        if any(not token for token in value):
            raise ValueError(
                "EAV_API_TOKENS must be a comma-separated list of non-empty tokens; "
                "remove the empty entry"
            )
        return value

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
                "api_prefix must be a non-root path such as '/api/v1' without a trailing slash"
            )
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()

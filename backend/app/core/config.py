"""Centralized application configuration.

All runtime settings come from environment variables (or a local `.env`
file). No secrets are hardcoded. See `.env.example` at the repo root.
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from the environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(
        default="postgresql+psycopg2://postgres:postgres@localhost:5432/flakytestpi",
        description="SQLAlchemy database URL.",
    )
    app_env: str = Field(default="local", description="Runtime environment name.")
    log_level: str = Field(default="INFO", description="Logging level.")
    # Keep the raw env value as a string so Pydantic Settings does not try to
    # JSON-decode comma-separated values before our validator can split them.
    cors_origins_value: str = Field(
        default="http://localhost:5173",
        alias="CORS_ORIGINS",
        description="Comma-separated allowed CORS origins.",
    )
    min_sample_size: int = Field(
        default=5, ge=1, description="Minimum executions before classification."
    )
    flaky_score_threshold: float = Field(
        default=40.0,
        ge=0.0,
        le=100.0,
        description="Score at/above which a test is suspected flaky.",
    )
    highly_flaky_score_threshold: float = Field(
        default=70.0,
        ge=0.0,
        le=100.0,
        description="Score at/above which a test is highly flaky.",
    )
    slow_test_threshold: float = Field(
        default=5.0, ge=0.0, description="Seconds above which a test counts as slow."
    )
    consistently_failing_threshold: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Failure rate at/above which a test is consistently failing.",
    )

    @property
    def cors_origins(self) -> list[str]:
        """Allowed origins parsed from the comma-separated environment value."""
        return [origin.strip() for origin in self.cors_origins_value.split(",") if origin.strip()]

    @field_validator("log_level", mode="before")
    @classmethod
    def _upper_log_level(cls, value: object) -> object:
        if isinstance(value, str):
            return value.upper()
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()

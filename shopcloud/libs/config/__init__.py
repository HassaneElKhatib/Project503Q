"""Shared configuration loaded from environment variables.

Every service extends BaseServiceSettings with its own fields.
All fields have env var equivalents; nothing is hardcoded.
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseServiceSettings(BaseSettings):
    """Base settings every service needs."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Service identity
    service_name: str = Field(..., description="Service name, e.g. 'catalog'")
    service_version: str = Field(default="dev", description="Version/commit SHA")
    environment: Literal["dev", "prod", "local", "test"] = Field(default="local")

    # HTTP
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")

    # AWS region (services that talk to AWS need this)
    aws_region: str = Field(default="us-east-1")


class CognitoSettings(BaseSettings):
    """Cognito JWT verification settings.

    Used by any service that needs to validate customer tokens.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    cognito_user_pool_id: str = Field(..., description="e.g. us-east-1_AbCdEfGhI")
    cognito_app_client_id: str = Field(..., description="App client ID")
    cognito_region: str = Field(default="us-east-1")

    @property
    def issuer(self) -> str:
        return (
            f"https://cognito-idp.{self.cognito_region}.amazonaws.com/"
            f"{self.cognito_user_pool_id}"
        )

    @property
    def jwks_url(self) -> str:
        return f"{self.issuer}/.well-known/jwks.json"


@lru_cache
def get_base_settings() -> BaseServiceSettings:
    """Cached singleton. Use FastAPI dependency injection in handlers."""
    return BaseServiceSettings()  # type: ignore[call-arg]

"""Checkout service settings."""
from pydantic import Field
from pydantic_settings import SettingsConfigDict

from libs.config import BaseServiceSettings


class CheckoutSettings(BaseServiceSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    service_name: str = Field(default="checkout")

    # PostgreSQL (write endpoint - never the read replica)
    database_url: str = Field(...)
    db_pool_size: int = Field(default=5)
    db_max_overflow: int = Field(default=5)

    # Redis (where the cart lives)
    redis_url: str = Field(...)

    # SQS invoice queue
    invoice_queue_url: str = Field(...)
    sqs_max_attempts: int = Field(default=3)

    # Cognito (for verifying customer JWTs)
    cognito_user_pool_id: str = Field(...)
    cognito_app_client_id: str = Field(...)
    cognito_region: str = Field(default="us-east-1")

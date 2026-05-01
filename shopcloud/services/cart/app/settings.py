"""Cart service settings."""
from pydantic import Field
from pydantic_settings import SettingsConfigDict

from libs.config import BaseServiceSettings


class CartSettings(BaseServiceSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    service_name: str = Field(default="cart")

    # Redis is the canonical cart store
    redis_url: str = Field(...)

    # TTL on cart keys - carts older than this disappear (matches typical
    # session lifetime; customer just gets a fresh empty cart)
    cart_ttl_seconds: int = Field(default=7 * 24 * 3600)  # 7 days

    # Cognito (for verifying customer JWTs)
    cognito_user_pool_id: str = Field(...)
    cognito_app_client_id: str = Field(...)
    cognito_region: str = Field(default="us-east-1")

    # Catalog service base URL - used to validate that products exist + get prices
    catalog_base_url: str = Field(
        default="http://catalog.app.svc.cluster.local",
        description="In-cluster DNS for the catalog service",
    )
    catalog_timeout_seconds: float = Field(default=2.0)

    # Cart constraints
    max_items_per_cart: int = Field(default=50)
    max_quantity_per_item: int = Field(default=99)

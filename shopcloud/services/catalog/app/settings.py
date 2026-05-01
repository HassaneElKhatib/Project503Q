"""Catalog-specific settings."""
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from libs.config import BaseServiceSettings


class CatalogSettings(BaseServiceSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Override the base default
    service_name: str = Field(default="catalog")

    # Data source: 'json' for local/dev bootstrap, 'sql' for production
    products_source: Literal["json", "sql"] = Field(default="json")

    # If products_source == 'json'
    products_json_path: Path = Field(
        default=Path(__file__).parent.parent / "data" / "products.json"
    )

    # If products_source == 'sql'
    database_url: str | None = Field(default=None)
    db_pool_size: int = Field(default=5)

    # Redis cache (optional - graceful fallback if missing)
    redis_url: str | None = Field(default=None)
    cache_ttl_seconds: int = Field(default=60, ge=0)

    # Pagination
    default_page_size: int = Field(default=20, ge=1, le=100)
    max_page_size: int = Field(default=100, ge=1, le=500)

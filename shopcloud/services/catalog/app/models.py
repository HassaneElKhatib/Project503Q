"""Catalog domain models.

Product is the canonical shape returned by the API. Currency is in minor units
(cents) to avoid floating-point money bugs.
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


Category = Literal[
    "books",
    "electronics",
    "home",
    "office",
    "skincare",
    "makeup",
    "haircare",
    "bodycare",
    "fragrance",
]


class Product(BaseModel):
    id: str = Field(..., examples=["p-001"])
    sku: str
    name: str
    description: str
    category: Category
    price_cents: int = Field(..., ge=0, description="Price in minor units (cents)")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    stock: int = Field(..., ge=0)
    image_url: str
    tags: list[str] = Field(default_factory=list)

    @property
    def in_stock(self) -> bool:
        return self.stock > 0


class ProductListResponse(BaseModel):
    items: list[Product]
    total: int = Field(..., description="Total matching products (before pagination)")
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=100)
    total_pages: int = Field(..., ge=0)


class CategoryInfo(BaseModel):
    name: Category
    product_count: int


class CategoriesResponse(BaseModel):
    categories: list[CategoryInfo]


class HealthInfo(BaseModel):
    """Used by the / route to advertise service identity."""

    service: str
    version: str
    environment: str
    started_at: datetime

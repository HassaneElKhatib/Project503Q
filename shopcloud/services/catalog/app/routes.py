"""Catalog HTTP routes."""
import math

from fastapi import APIRouter, Depends, Query

from app.cache import ProductCache
from app.deps import get_cache, get_repository, get_settings
from app.models import (
    CategoriesResponse,
    CategoryInfo,
    Product,
    ProductListResponse,
)
from app.repository import ProductRepository
from app.settings import CatalogSettings
from libs.errors import NotFoundError
from libs.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/products", tags=["catalog"])


@router.get(
    "",
    response_model=ProductListResponse,
    summary="List products",
)
async def list_products(
    category: str | None = Query(default=None, description="Filter by category"),
    in_stock: bool = Query(default=False, description="Only return in-stock items"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    repo: ProductRepository = Depends(get_repository),
    settings: CatalogSettings = Depends(get_settings),
) -> ProductListResponse:
    page_size = min(page_size, settings.max_page_size)
    offset = (page - 1) * page_size

    items, total = await repo.list_products(
        category=category,
        in_stock_only=in_stock,
        offset=offset,
        limit=page_size,
    )

    return ProductListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


@router.get(
    "/search",
    response_model=list[Product],
    summary="Search products by name, description, or tag",
)
async def search_products(
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(default=20, ge=1, le=100),
    repo: ProductRepository = Depends(get_repository),
) -> list[Product]:
    return await repo.search(q, limit=limit)


@router.get(
    "/{product_id}",
    response_model=Product,
    summary="Get one product by id",
    responses={404: {"description": "Product not found"}},
)
async def get_product(
    product_id: str,
    repo: ProductRepository = Depends(get_repository),
    cache: ProductCache = Depends(get_cache),
) -> Product:
    # Cache-aside lookup
    cached = await cache.get_product(product_id)
    if cached is not None:
        logger.debug("cache hit", extra={"product_id": product_id})
        return cached

    product = await repo.get_by_id(product_id)
    if product is None:
        raise NotFoundError(f"Product {product_id} not found")

    await cache.set_product(product)
    return product


# Categories live on a sibling router because /categories isn't under /products
categories_router = APIRouter(tags=["catalog"])


@categories_router.get(
    "/categories",
    response_model=CategoriesResponse,
    summary="List product categories with counts",
)
async def list_categories(
    repo: ProductRepository = Depends(get_repository),
) -> CategoriesResponse:
    counts = await repo.list_categories()
    # Sort alphabetically for stable output
    items = [
        CategoryInfo(name=name, product_count=count)  # type: ignore[arg-type]
        for name, count in sorted(counts.items())
    ]
    return CategoriesResponse(categories=items)

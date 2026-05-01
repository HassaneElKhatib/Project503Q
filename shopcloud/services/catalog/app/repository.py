"""Catalog data access.

Two implementations of the same interface:
- JsonProductRepository: reads from a JSON file. Used for local dev and
  bootstrap, before RDS is provisioned.
- SqlProductRepository: reads from PostgreSQL. Production.

Settings.products_source picks which one. The handler code never changes.
"""
import json
from abc import ABC, abstractmethod
from pathlib import Path

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import Product
from libs.db import Inventory as InventoryModel
from libs.db import Product as ProductModel
from libs.logger import get_logger

logger = get_logger(__name__)


class ProductRepository(ABC):
    """Abstract repository - swap implementations without touching handlers."""

    @abstractmethod
    async def get_by_id(self, product_id: str) -> Product | None: ...

    @abstractmethod
    async def list_products(
        self,
        *,
        category: str | None = None,
        in_stock_only: bool = False,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Product], int]:
        """Return (items, total_matching_before_pagination)."""

    @abstractmethod
    async def search(self, query: str, *, limit: int = 20) -> list[Product]: ...

    @abstractmethod
    async def list_categories(self) -> dict[str, int]:
        """Map category name -> product count."""


class JsonProductRepository(ProductRepository):
    """Reads products from a JSON file. For Day 1 only.

    Loads once at startup and keeps everything in memory. Production never
    sees this - it gets replaced with SqlProductRepository.
    """

    def __init__(self, json_path: Path) -> None:
        self._path = json_path
        self._products: dict[str, Product] = {}

    def load(self) -> None:
        """Read the JSON file and parse into Product objects."""
        if not self._path.exists():
            raise FileNotFoundError(f"Product data not found: {self._path}")

        raw = json.loads(self._path.read_text())
        if not isinstance(raw, list):
            raise ValueError("Product data must be a JSON array")

        self._products = {p["id"]: Product(**p) for p in raw}
        logger.info(
            "loaded products from json",
            extra={"count": len(self._products), "path": str(self._path)},
        )

    async def get_by_id(self, product_id: str) -> Product | None:
        return self._products.get(product_id)

    async def list_products(
        self,
        *,
        category: str | None = None,
        in_stock_only: bool = False,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Product], int]:
        items = list(self._products.values())

        if category:
            items = [p for p in items if p.category == category]
        if in_stock_only:
            items = [p for p in items if p.in_stock]

        # Stable ordering by id so pagination is deterministic
        items.sort(key=lambda p: p.id)
        total = len(items)
        return items[offset : offset + limit], total

    async def search(self, query: str, *, limit: int = 20) -> list[Product]:
        if not query:
            return []
        q = query.lower().strip()
        # Naive contains-match - fine for 20 products. Real impl uses Postgres FTS.
        results = [
            p
            for p in self._products.values()
            if q in p.name.lower()
            or q in p.description.lower()
            or any(q in tag.lower() for tag in p.tags)
        ]
        results.sort(key=lambda p: p.id)
        return results[:limit]

    async def list_categories(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for product in self._products.values():
            counts[product.category] = counts.get(product.category, 0) + 1
        return counts


def _row_to_api_product(row: ProductModel, inventory: InventoryModel | None) -> Product:
    """Convert DB row + inventory to the API Product shape.

    The API exposes `stock` (single int) but the DB splits it into stock and
    reserved. We expose available stock (stock - reserved) so customers see
    what they can actually buy.
    """
    available = 0
    if inventory is not None:
        available = max(0, inventory.stock - inventory.reserved)
    return Product(
        id=row.id,
        sku=row.sku,
        name=row.name,
        description=row.description or "",
        category=row.category,  # type: ignore[arg-type]
        price_cents=row.price_cents,
        currency=row.currency,
        stock=available,
        image_url=row.image_url or "",
        tags=row.tags or [],
    )


class SqlProductRepository(ProductRepository):
    """PostgreSQL-backed catalog. Joins products + inventory."""

    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sessionmaker = sessionmaker

    async def get_by_id(self, product_id: str) -> Product | None:
        async with self._sessionmaker() as session:
            result = await session.execute(
                select(ProductModel, InventoryModel)
                .outerjoin(InventoryModel, InventoryModel.product_id == ProductModel.id)
                .where(ProductModel.id == product_id)
                .where(ProductModel.is_active.is_(True))
            )
            row = result.first()
            if row is None:
                return None
            product, inventory = row
            return _row_to_api_product(product, inventory)

    async def list_products(
        self,
        *,
        category: str | None = None,
        in_stock_only: bool = False,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Product], int]:
        async with self._sessionmaker() as session:
            base = (
                select(ProductModel, InventoryModel)
                .outerjoin(InventoryModel, InventoryModel.product_id == ProductModel.id)
                .where(ProductModel.is_active.is_(True))
            )
            if category:
                base = base.where(ProductModel.category == category)
            if in_stock_only:
                # Only include rows where (stock - reserved) > 0
                base = base.where(
                    InventoryModel.stock > InventoryModel.reserved
                )

            # Count first
            count_q = select(func.count()).select_from(base.subquery())
            total = (await session.execute(count_q)).scalar_one()

            # Page
            page_q = base.order_by(ProductModel.id).offset(offset).limit(limit)
            rows = (await session.execute(page_q)).all()
            items = [_row_to_api_product(p, i) for p, i in rows]
            return items, total

    async def search(self, query: str, *, limit: int = 20) -> list[Product]:
        if not query:
            return []
        q = f"%{query.strip()}%"
        async with self._sessionmaker() as session:
            result = await session.execute(
                select(ProductModel, InventoryModel)
                .outerjoin(InventoryModel, InventoryModel.product_id == ProductModel.id)
                .where(ProductModel.is_active.is_(True))
                .where(
                    or_(
                        ProductModel.name.ilike(q),
                        ProductModel.description.ilike(q),
                    )
                )
                .order_by(ProductModel.id)
                .limit(limit)
            )
            return [_row_to_api_product(p, i) for p, i in result.all()]

    async def list_categories(self) -> dict[str, int]:
        async with self._sessionmaker() as session:
            result = await session.execute(
                select(ProductModel.category, func.count(ProductModel.id))
                .where(ProductModel.is_active.is_(True))
                .group_by(ProductModel.category)
            )
            return {category: int(count) for category, count in result.all()}

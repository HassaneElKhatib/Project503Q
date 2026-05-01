"""SqlProductRepository tests.

Use SQLite for tests so they need no external Postgres. The shared models
in libs/db/models.py are cross-database, so the same code works against
both.
"""
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.repository import SqlProductRepository
from libs.db import Base, Inventory, Product


@pytest.fixture
async def sessionmaker():
    """Build an in-memory SQLite engine + sessionmaker, schema applied."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


async def _seed(sessionmaker, products: list[tuple[str, str, str, int, int, bool]]) -> None:
    """(id, name, category, price_cents, stock, active)."""
    async with sessionmaker() as session:
        for pid, name, cat, price, stock, active in products:
            session.add(
                Product(
                    id=pid, sku=f"SKU-{pid}", name=name, description=name,
                    category=cat, price_cents=price, currency="USD",
                    image_url="", is_active=active,
                )
            )
            session.add(Inventory(product_id=pid, stock=stock, reserved=0))
        await session.commit()


async def test_get_by_id(sessionmaker):
    await _seed(sessionmaker, [("p-1", "Widget", "books", 1000, 5, True)])
    repo = SqlProductRepository(sessionmaker)
    product = await repo.get_by_id("p-1")
    assert product is not None
    assert product.name == "Widget"
    assert product.stock == 5


async def test_inactive_products_hidden(sessionmaker):
    await _seed(sessionmaker, [("p-1", "Widget", "books", 1000, 5, False)])
    repo = SqlProductRepository(sessionmaker)
    assert await repo.get_by_id("p-1") is None


async def test_list_products_pagination(sessionmaker):
    await _seed(sessionmaker, [
        (f"p-{i}", f"Item {i}", "books", 1000, 1, True) for i in range(1, 11)
    ])
    repo = SqlProductRepository(sessionmaker)

    page1, total = await repo.list_products(limit=5)
    assert total == 10
    assert len(page1) == 5
    page2, _ = await repo.list_products(offset=5, limit=5)
    assert {p.id for p in page1}.isdisjoint({p.id for p in page2})


async def test_list_filter_by_category(sessionmaker):
    await _seed(sessionmaker, [
        ("p-1", "Book A", "books", 1000, 1, True),
        ("p-2", "Lamp", "home", 5000, 1, True),
        ("p-3", "Book B", "books", 1500, 1, True),
    ])
    repo = SqlProductRepository(sessionmaker)
    items, total = await repo.list_products(category="books", limit=10)
    assert total == 2
    assert all(p.category == "books" for p in items)


async def test_in_stock_only(sessionmaker):
    await _seed(sessionmaker, [
        ("p-1", "In stock", "books", 1000, 5, True),
        ("p-2", "Sold out", "books", 1000, 0, True),
    ])
    repo = SqlProductRepository(sessionmaker)
    items, total = await repo.list_products(in_stock_only=True, limit=10)
    assert total == 1
    assert items[0].id == "p-1"


async def test_search(sessionmaker):
    await _seed(sessionmaker, [
        ("p-1", "Espresso machine", "home", 5000, 1, True),
        ("p-2", "Coffee grinder", "home", 2000, 1, True),
        ("p-3", "Lamp", "home", 5000, 1, True),
    ])
    repo = SqlProductRepository(sessionmaker)
    results = await repo.search("coffee")
    assert len(results) == 1  # only p-2's name contains 'coffee'
    assert results[0].id == "p-2"


async def test_search_case_insensitive(sessionmaker):
    await _seed(sessionmaker, [
        ("p-1", "Espresso Machine", "home", 5000, 1, True),
    ])
    repo = SqlProductRepository(sessionmaker)
    upper = await repo.search("ESPRESSO")
    lower = await repo.search("espresso")
    assert {p.id for p in upper} == {p.id for p in lower}


async def test_list_categories(sessionmaker):
    await _seed(sessionmaker, [
        ("p-1", "A", "books", 1000, 1, True),
        ("p-2", "B", "books", 1000, 1, True),
        ("p-3", "C", "home", 1000, 1, True),
        ("p-4", "D", "home", 1000, 1, False),  # inactive - excluded from counts
    ])
    repo = SqlProductRepository(sessionmaker)
    counts = await repo.list_categories()
    assert counts == {"books": 2, "home": 1}


async def test_stock_reflects_available_not_total(sessionmaker):
    """Stock visible to customers should be (stock - reserved)."""
    async with sessionmaker() as session:
        session.add(
            Product(
                id="p-1", sku="X", name="X", description="x",
                category="books", price_cents=1000, currency="USD",
                image_url="", is_active=True,
            )
        )
        session.add(Inventory(product_id="p-1", stock=10, reserved=3))
        await session.commit()

    repo = SqlProductRepository(sessionmaker)
    product = await repo.get_by_id("p-1")
    assert product.stock == 7  # 10 - 3

"""Unit tests for the JSON-backed repository."""
from pathlib import Path

import pytest

from app.repository import JsonProductRepository


@pytest.fixture
def repo() -> JsonProductRepository:
    json_path = Path(__file__).parent.parent / "data" / "products.json"
    r = JsonProductRepository(json_path)
    r.load()
    return r


async def test_load_populates_products(repo: JsonProductRepository):
    items, total = await repo.list_products(limit=100)
    assert total == 20
    assert len(items) == 20


async def test_get_by_id_existing(repo: JsonProductRepository):
    product = await repo.get_by_id("p-001")
    assert product is not None
    assert product.name == "Hydra Calm Gel Cleanser"
    assert product.sku == "SKN-001"
    assert product.price_cents == 1299


async def test_get_by_id_missing(repo: JsonProductRepository):
    assert await repo.get_by_id("does-not-exist") is None


async def test_filter_by_category(repo: JsonProductRepository):
    items, total = await repo.list_products(category="skincare", limit=100)
    assert total == 6
    assert all(p.category == "skincare" for p in items)


async def test_in_stock_only_includes_all_current_seed_products(repo: JsonProductRepository):
    items, total = await repo.list_products(in_stock_only=True, limit=100)
    assert total == 20
    assert all(p.stock > 0 for p in items)


async def test_pagination_offset_and_limit(repo: JsonProductRepository):
    page1, total = await repo.list_products(offset=0, limit=5)
    page2, _ = await repo.list_products(offset=5, limit=5)
    assert len(page1) == 5
    assert len(page2) == 5
    assert {p.id for p in page1}.isdisjoint({p.id for p in page2})
    assert total == 20


async def test_pagination_is_stable(repo: JsonProductRepository):
    """Same query must return same order across calls."""
    a, _ = await repo.list_products(offset=0, limit=10)
    b, _ = await repo.list_products(offset=0, limit=10)
    assert [p.id for p in a] == [p.id for p in b]


async def test_search_matches_name(repo: JsonProductRepository):
    results = await repo.search("cleanser")
    assert len(results) == 1
    assert results[0].id == "p-001"


async def test_search_matches_tag(repo: JsonProductRepository):
    results = await repo.search("serum")
    assert len(results) >= 2
    assert all(
        "serum" in p.name.lower()
        or "serum" in p.description.lower()
        or any("serum" in tag.lower() for tag in p.tags)
        for p in results
    )


async def test_search_case_insensitive(repo: JsonProductRepository):
    lower = await repo.search("serum")
    upper = await repo.search("SERUM")
    assert {p.id for p in lower} == {p.id for p in upper}


async def test_search_empty_returns_empty(repo: JsonProductRepository):
    assert await repo.search("") == []


async def test_search_no_match(repo: JsonProductRepository):
    assert await repo.search("xyzxyzxyz") == []


async def test_list_categories(repo: JsonProductRepository):
    counts = await repo.list_categories()
    assert counts == {
        "skincare": 6,
        "makeup": 7,
        "haircare": 3,
        "bodycare": 2,
        "fragrance": 2,
    }

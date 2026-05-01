"""Tests for ProductCache against fakeredis."""
import fakeredis.aioredis
import pytest

from app.cache import ProductCache
from app.models import Product


@pytest.fixture
def redis_client():
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


@pytest.fixture
def cache(redis_client) -> ProductCache:
    return ProductCache(redis_client, default_ttl=10)


@pytest.fixture
def sample_product() -> Product:
    return Product(
        id="p-test",
        sku="TEST-001",
        name="Test Product",
        description="For unit tests",
        category="books",
        price_cents=1000,
        currency="USD",
        stock=5,
        image_url="https://example/img.jpg",
        tags=["test"],
    )


async def test_set_and_get(cache: ProductCache, sample_product: Product):
    await cache.set_product(sample_product)
    cached = await cache.get_product(sample_product.id)
    assert cached is not None
    assert cached.id == sample_product.id
    assert cached.price_cents == sample_product.price_cents


async def test_get_miss_returns_none(cache: ProductCache):
    assert await cache.get_product("not-cached") is None


async def test_invalidate(cache: ProductCache, sample_product: Product):
    await cache.set_product(sample_product)
    await cache.invalidate_product(sample_product.id)
    assert await cache.get_product(sample_product.id) is None


async def test_ping_returns_true_when_connected(cache: ProductCache):
    assert await cache.ping() is True


async def test_no_redis_client_disables_cache():
    """ProductCache(None) silently no-ops - service stays up if Redis is down."""
    cache = ProductCache(None)
    assert await cache.get_product("anything") is None
    # set should not raise
    await cache.set_product(
        Product(
            id="x",
            sku="X",
            name="x",
            description="x",
            category="books",
            price_cents=0,
            currency="USD",
            stock=0,
            image_url="",
            tags=[],
        )
    )
    assert await cache.ping() is False

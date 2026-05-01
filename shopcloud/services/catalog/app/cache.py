"""Redis cache for catalog.

Cache-aside pattern:
    1. Check cache
    2. Miss -> query repo, write to cache with TTL
    3. Hit -> return cached value

If Redis is down, we log and fall through to the repo. The catalog stays
available even if ElastiCache has an issue - reads just get slower.
"""
import json

from app.models import Product
from libs.logger import get_logger

logger = get_logger(__name__)


class ProductCache:
    """Thin wrapper around redis.asyncio with graceful degradation."""

    def __init__(self, redis_client, default_ttl: int = 60) -> None:
        # redis_client is an instance of redis.asyncio.Redis. We accept Any so
        # tests can pass an in-memory fake without importing redis.
        self._redis = redis_client
        self._default_ttl = default_ttl

    @staticmethod
    def _product_key(product_id: str) -> str:
        return f"catalog:product:{product_id}"

    async def get_product(self, product_id: str) -> Product | None:
        if self._redis is None:
            return None
        try:
            raw = await self._redis.get(self._product_key(product_id))
            if raw is None:
                return None
            data = json.loads(raw)
            return Product(**data)
        except Exception as exc:
            logger.warning("cache get failed", extra={"error": str(exc)})
            return None

    async def set_product(self, product: Product, ttl: int | None = None) -> None:
        if self._redis is None:
            return
        try:
            await self._redis.set(
                self._product_key(product.id),
                product.model_dump_json(),
                ex=ttl or self._default_ttl,
            )
        except Exception as exc:
            logger.warning("cache set failed", extra={"error": str(exc)})

    async def invalidate_product(self, product_id: str) -> None:
        if self._redis is None:
            return
        try:
            await self._redis.delete(self._product_key(product_id))
        except Exception as exc:
            logger.warning("cache invalidate failed", extra={"error": str(exc)})

    async def ping(self) -> bool:
        """Used by the readiness probe."""
        if self._redis is None:
            return False
        try:
            return bool(await self._redis.ping())
        except Exception:
            return False

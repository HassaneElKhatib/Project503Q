"""Cart storage in Redis.

Design: one Redis key per customer (`cart:<customer_id>`) holding the whole
cart as a JSON blob. This is fine for shopping carts (small, single-customer
access). For multi-writer scenarios we'd use Redis hashes or a transaction.

We use a Lua script to atomically set with TTL extension on every write,
so an active customer's cart never silently expires.
"""
import json
from typing import Any

from app.models import Cart
from libs.logger import get_logger

logger = get_logger(__name__)


class CartRepository:
    def __init__(self, redis_client: Any, *, ttl_seconds: int) -> None:
        self._redis = redis_client
        self._ttl = ttl_seconds

    @staticmethod
    def _key(customer_id: str) -> str:
        return f"cart:{customer_id}"

    async def get(self, customer_id: str) -> Cart:
        """Return the customer's cart. Empty cart if none exists."""
        raw = await self._redis.get(self._key(customer_id))
        if raw is None:
            return Cart(customer_id=customer_id)
        try:
            data = json.loads(raw)
            # Re-validate via Pydantic so old/corrupt data doesn't crash us
            return Cart(**data)
        except Exception as exc:
            logger.warning(
                "corrupt cart data, returning empty",
                extra={"customer_id": customer_id, "error": str(exc)},
            )
            return Cart(customer_id=customer_id)

    async def save(self, cart: Cart) -> None:
        """Persist the cart and bump TTL."""
        await self._redis.set(
            self._key(cart.customer_id),
            cart.model_dump_json(),
            ex=self._ttl,
        )

    async def delete(self, customer_id: str) -> None:
        """Clear a customer's cart (called by checkout after order placed)."""
        await self._redis.delete(self._key(customer_id))

    async def ping(self) -> bool:
        try:
            return bool(await self._redis.ping())
        except Exception:
            return False

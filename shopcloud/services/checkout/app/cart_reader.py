"""Read the customer's cart from Redis.

Checkout doesn't own the cart - cart service does. But checkout needs
to read it to know what to charge. We read directly from the same Redis
keys (catalog:cart:<customer_id>) and clear them after a successful order.

Same shape as cart service's Cart model. We re-declare it here to keep
checkout independent of the cart service's import path.
"""
import json
from typing import Any

from pydantic import BaseModel, Field

from libs.errors import NotFoundError, ValidationError
from libs.logger import get_logger

logger = get_logger(__name__)


class CartItem(BaseModel):
    product_id: str
    product_name: str
    unit_price_cents: int = Field(..., ge=0)
    quantity: int = Field(..., ge=1)
    currency: str = Field(default="USD")

    @property
    def line_total_cents(self) -> int:
        return self.unit_price_cents * self.quantity


class Cart(BaseModel):
    customer_id: str
    items: list[CartItem] = Field(default_factory=list)
    currency: str = Field(default="USD")

    @property
    def total_cents(self) -> int:
        return sum(item.line_total_cents for item in self.items)


class CartReader:
    def __init__(self, redis_client: Any) -> None:
        self._redis = redis_client

    @staticmethod
    def _key(customer_id: str) -> str:
        return f"cart:{customer_id}"

    async def read_for_checkout(self, customer_id: str) -> Cart:
        """Read the cart. Validate it's not empty."""
        raw = await self._redis.get(self._key(customer_id))
        if raw is None:
            raise NotFoundError("Cart is empty")

        try:
            data = json.loads(raw)
            cart = Cart(**data)
        except Exception as exc:
            logger.error(
                "cart deserialization failed",
                extra={"customer_id": customer_id, "error": str(exc)},
            )
            raise ValidationError("Cart data is corrupt") from exc

        if not cart.items:
            raise ValidationError("Cart is empty")

        return cart

    async def clear(self, customer_id: str) -> None:
        """Empty the cart after a successful order."""
        await self._redis.delete(self._key(customer_id))

    async def ping(self) -> bool:
        try:
            return bool(await self._redis.ping())
        except Exception:
            return False

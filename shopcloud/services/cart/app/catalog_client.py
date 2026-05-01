"""HTTP client to the catalog service.

When a customer adds a product to their cart, we don't trust the client to
send the correct price. We fetch the canonical product from catalog and
snapshot the price + name into the cart. That way:

- Price changes between add-to-cart and checkout are handled deterministically
  (we use the price at the time of add).
- The client can't tamper with prices.
- If the product gets deactivated, we know not to add it.
"""
import httpx

from app.models import CartItem
from libs.errors import NotFoundError, UpstreamError, ValidationError
from libs.logger import get_logger

logger = get_logger(__name__)


class CatalogClient:
    def __init__(self, base_url: str, *, timeout: float = 2.0) -> None:
        self._base = base_url.rstrip("/")
        self._http = httpx.AsyncClient(timeout=timeout)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def fetch_product_for_cart(
        self, product_id: str, quantity: int
    ) -> CartItem:
        """Fetch a product and turn it into a CartItem."""
        try:
            response = await self._http.get(f"{self._base}/products/{product_id}")
        except httpx.HTTPError as exc:
            logger.error("catalog unreachable", extra={"error": str(exc)})
            raise UpstreamError("Catalog service unreachable") from exc

        if response.status_code == 404:
            raise NotFoundError(f"Product {product_id} not found")
        if response.status_code != 200:
            logger.warning(
                "catalog returned error",
                extra={"status": response.status_code, "product_id": product_id},
            )
            raise UpstreamError("Catalog returned an error")

        product = response.json()
        # Defensive: validate response shape
        if "id" not in product or "price_cents" not in product:
            raise UpstreamError("Catalog response malformed")

        if not product.get("is_active", True):
            raise ValidationError(f"Product {product_id} is not available")

        return CartItem(
            product_id=product["id"],
            product_name=product["name"],
            unit_price_cents=product["price_cents"],
            quantity=quantity,
            currency=product.get("currency", "USD"),
        )

    async def ping(self) -> bool:
        try:
            response = await self._http.get(f"{self._base}/health/live")
            return response.status_code == 200
        except Exception:
            return False

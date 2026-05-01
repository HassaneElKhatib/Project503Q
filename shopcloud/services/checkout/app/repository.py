"""Order persistence.

Writes orders + items + invoice row + inventory decrement, all in one
transaction. If anything fails the whole thing rolls back - no half-orders.
"""
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.cart_reader import Cart
from libs.db import Customer, Inventory, Invoice, Order, OrderItem
from libs.errors import ConflictError
from libs.logger import get_logger

logger = get_logger(__name__)


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_idempotency_key(
        self, customer_id: str, key: str
    ) -> Order | None:
        """Same key from same customer? Return the existing order with items
        + invoice eagerly loaded so the caller can read them outside this
        session without triggering lazy IO.
        """
        result = await self._session.execute(
            select(Order)
            .where(Order.customer_id == customer_id)
            .where(Order.idempotency_key == key)
            .options(selectinload(Order.items), selectinload(Order.invoice))
        )
        return result.scalar_one_or_none()

    async def ensure_customer(self, customer_id: str, email: str) -> Customer:
        """Upsert the customer mirror row."""
        existing = await self._session.get(Customer, customer_id)
        if existing:
            if existing.email != email:
                existing.email = email
            return existing

        customer = Customer(id=customer_id, email=email)
        self._session.add(customer)
        await self._session.flush()
        return customer

    async def reserve_inventory(self, cart: Cart) -> None:
        """Atomically decrement stock for each item. Raises if insufficient.

        We use a single UPDATE per item with a WHERE clause that prevents
        going negative. If 0 rows are affected, stock was insufficient.
        """
        for item in cart.items:
            result = await self._session.execute(
                update(Inventory)
                .where(Inventory.product_id == item.product_id)
                .where(Inventory.stock >= item.quantity)
                .values(stock=Inventory.stock - item.quantity)
            )
            if result.rowcount == 0:
                # Either product has no inventory row or stock < quantity
                raise ConflictError(
                    f"Insufficient stock for {item.product_id}"
                )

    async def create_order(
        self,
        *,
        customer_id: str,
        customer_email: str,
        cart: Cart,
        idempotency_key: str | None,
        metadata: dict,
    ) -> Order:
        """Create an order in 'confirmed' status with all line items."""
        order = Order(
            customer_id=customer_id,
            customer_email=customer_email,
            status="confirmed",
            total_cents=cart.total_cents,
            currency=cart.currency,
            idempotency_key=idempotency_key,
            metadata_json=metadata or {},
        )
        for item in cart.items:
            order.items.append(
                OrderItem(
                    product_id=item.product_id,
                    product_name=item.product_name,
                    unit_price_cents=item.unit_price_cents,
                    quantity=item.quantity,
                )
            )
        order.invoice = Invoice(status="queued")
        self._session.add(order)
        await self._session.flush()
        return order

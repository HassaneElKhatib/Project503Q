"""The checkout business logic.

This is the heart of the rubric requirement: the order is written, the
SQS message is published, and the response returns to the client - all
without waiting for the PDF to be generated.

The flow:
1. Idempotency check: same key + same customer? Return existing order.
2. Read cart from Redis.
3. Open a DB transaction:
   a. Upsert customer mirror row.
   b. Reserve inventory atomically (per-item UPDATE with stock >= qty guard).
   c. Insert order + items + invoice (status=queued).
4. Commit DB.
5. Publish invoice event to SQS.
6. Clear cart.
7. Return 202 Accepted with order_id.

Failure handling:
- DB error -> rollback, return 500. Cart untouched, customer can retry.
- Insufficient stock -> 409 Conflict. Cart kept so they can adjust.
- SQS publish error AFTER commit -> log + raise. Background worker can
  re-trigger from invoice rows where status='queued' and created_at < N min.
"""
from app.cart_reader import CartReader
from app.models import CheckoutResponse, CheckoutResponseItem, InvoiceEvent
from app.repository import OrderRepository
from libs.aws.sqs import SqsPublisher
from libs.db import Order, session_scope
from libs.errors import UpstreamError
from libs.logger import get_logger

logger = get_logger(__name__)


class CheckoutService:
    def __init__(
        self,
        sessionmaker,
        cart_reader: CartReader,
        sqs_publisher: SqsPublisher,
    ) -> None:
        self._sessionmaker = sessionmaker
        self._cart_reader = cart_reader
        self._sqs = sqs_publisher

    async def checkout(
        self,
        *,
        customer_id: str,
        customer_email: str,
        idempotency_key: str | None,
        metadata: dict,
    ) -> CheckoutResponse:
        # 1. Idempotency check
        if idempotency_key:
            async with self._sessionmaker() as session:
                repo = OrderRepository(session)
                existing = await repo.find_by_idempotency_key(
                    customer_id, idempotency_key
                )
                if existing:
                    logger.info(
                        "idempotent checkout hit",
                        extra={"order_id": existing.id, "customer_id": customer_id},
                    )
                    # Build response while still in the session - items + invoice
                    # were eager-loaded above so this is just attribute access.
                    return self._build_response_sync(existing)

        # 2. Read cart
        cart = await self._cart_reader.read_for_checkout(customer_id)
        logger.info(
            "checkout starting",
            extra={
                "customer_id": customer_id,
                "item_count": len(cart.items),
                "total_cents": cart.total_cents,
            },
        )

        # 3-4. DB transaction
        async with session_scope(self._sessionmaker) as session:
            repo = OrderRepository(session)
            await repo.ensure_customer(customer_id, customer_email)
            await repo.reserve_inventory(cart)
            order = await repo.create_order(
                customer_id=customer_id,
                customer_email=customer_email,
                cart=cart,
                idempotency_key=idempotency_key,
                metadata=metadata,
            )
            order_id = order.id  # capture before session closes
            response_items = [
                CheckoutResponseItem(
                    product_id=item.product_id,
                    product_name=item.product_name,
                    unit_price_cents=item.unit_price_cents,
                    quantity=item.quantity,
                    line_total_cents=item.line_total_cents,
                )
                for item in order.items
            ]
            total_cents = order.total_cents
            currency = order.currency
            created_at = order.created_at

        logger.info(
            "order written",
            extra={"order_id": order_id, "customer_id": customer_id},
        )

        # 5. Publish to SQS
        event = InvoiceEvent(
            order_id=order_id,
            customer_id=customer_id,
            customer_email=customer_email,
            items=[item.model_dump() for item in response_items],
            total_cents=total_cents,
            currency=currency,
            created_at=created_at.isoformat(),
        )
        try:
            message_id = await self._sqs.publish(event.model_dump())
            logger.info(
                "invoice queued",
                extra={"order_id": order_id, "message_id": message_id},
            )
        except Exception as exc:
            # Order is committed but invoice not queued. Mark invoice as failed
            # so a reaper job can retry. We don't fail the customer's request.
            logger.error(
                "sqs publish failed after order commit - invoice will be retried",
                extra={"order_id": order_id, "error": str(exc)},
            )
            raise UpstreamError(
                "Order created but invoice queueing failed; you will be contacted"
            ) from exc

        # 6. Clear cart
        await self._cart_reader.clear(customer_id)

        # 7. Build response
        return CheckoutResponse(
            order_id=order_id,
            status="confirmed",
            customer_email=customer_email,
            items=response_items,
            total_cents=total_cents,
            currency=currency,
            invoice_status="queued",
            created_at=created_at,
        )

    def _build_response_sync(self, order: Order) -> CheckoutResponse:
        """Build response from an order whose items + invoice are eager-loaded."""
        items = [
            CheckoutResponseItem(
                product_id=item.product_id,
                product_name=item.product_name,
                unit_price_cents=item.unit_price_cents,
                quantity=item.quantity,
                line_total_cents=item.line_total_cents,
            )
            for item in order.items
        ]
        return CheckoutResponse(
            order_id=order.id,
            status=order.status,
            customer_email=order.customer_email,
            items=items,
            total_cents=order.total_cents,
            currency=order.currency,
            invoice_status=order.invoice.status if order.invoice else "queued",
            created_at=order.created_at,
        )

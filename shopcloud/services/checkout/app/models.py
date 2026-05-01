"""Checkout API models."""
from datetime import datetime

from pydantic import BaseModel, Field


class CheckoutRequest(BaseModel):
    """Customer initiates checkout. The cart we're checking out lives in Redis,
    keyed by the customer's JWT subject. The client doesn't pass items - we
    read them from Redis. This prevents tampering with prices/quantities.

    The optional idempotency_key lets the client retry safely. Same key from
    the same customer = same order returned (not a duplicate).
    """

    idempotency_key: str | None = Field(default=None, max_length=100)
    metadata: dict = Field(default_factory=dict)


class CheckoutResponseItem(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    unit_price_cents: int
    line_total_cents: int


class CheckoutResponse(BaseModel):
    """Returned with HTTP 202 Accepted. Invoice email arrives later."""

    order_id: str
    status: str = Field(..., description="Always 'confirmed' on success")
    customer_email: str
    items: list[CheckoutResponseItem]
    total_cents: int
    currency: str
    invoice_status: str = Field(
        default="queued",
        description="Invoice generation runs asynchronously",
    )
    created_at: datetime


class InvoiceEvent(BaseModel):
    """The shape we publish to SQS. The Lambda worker consumes this."""

    event_version: int = Field(default=1)
    order_id: str
    customer_id: str
    customer_email: str
    items: list[dict]  # serialized CheckoutResponseItem
    total_cents: int
    currency: str
    created_at: str  # ISO 8601 string for JSON serialization

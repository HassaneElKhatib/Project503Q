"""Admin API models."""
from datetime import datetime

from pydantic import BaseModel, Field


class OrderSummary(BaseModel):
    """Listed in /admin/orders - one row per order, no items."""

    id: str
    customer_id: str
    customer_email: str
    status: str
    total_cents: int
    currency: str
    item_count: int
    created_at: datetime
    invoice_status: str | None = None


class OrderItemDetail(BaseModel):
    product_id: str
    product_name: str
    unit_price_cents: int
    quantity: int
    line_total_cents: int


class OrderDetail(BaseModel):
    """GET /admin/orders/{id}."""

    id: str
    customer_id: str
    customer_email: str
    status: str
    total_cents: int
    currency: str
    items: list[OrderItemDetail]
    invoice_status: str | None
    invoice_s3_key: str | None
    invoice_sent_at: datetime | None
    created_at: datetime
    updated_at: datetime


class PagedOrders(BaseModel):
    items: list[OrderSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class CustomerSummary(BaseModel):
    id: str
    email: str
    full_name: str | None
    order_count: int
    total_spent_cents: int
    created_at: datetime


class PagedCustomers(BaseModel):
    items: list[CustomerSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class UpdateOrderStatusRequest(BaseModel):
    status: str = Field(..., pattern="^(pending|confirmed|fulfilled|cancelled|failed)$")

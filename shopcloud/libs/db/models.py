"""Shared SQLAlchemy ORM models.

This is the canonical schema for ShopCloud. Every service that touches
the database imports models from here. Migrations (Alembic) live alongside
this file and are run as a Kubernetes Job before any service deploy.

Tables:
    products       - catalog read; admin write
    inventory      - stock per product (separate so we can lock just inventory)
    customers      - mirror of Cognito users we want to query locally
    orders         - one row per checkout
    order_items    - line items (FK to products)
    invoices       - bookkeeping for the async pipeline
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _new_uuid_str() -> str:
    """Cross-database UUID generator. Works on Postgres and SQLite alike."""
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    """Common base for all models. Adds created_at/updated_at to everything."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ---------------- products ----------------

class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    image_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    tags: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, server_default="[]"
    )
    is_active: Mapped[bool] = mapped_column(
        nullable=False, server_default="true"
    )

    inventory: Mapped["Inventory"] = relationship(
        back_populates="product",
        uselist=False,
        cascade="all, delete-orphan",
    )
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="product")

    __table_args__ = (
        CheckConstraint("price_cents >= 0", name="products_price_nonneg"),
        Index("ix_products_category_active", "category", "is_active"),
    )


class Inventory(Base):
    __tablename__ = "inventory"

    product_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("products.id", ondelete="CASCADE"), primary_key=True
    )
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reserved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    product: Mapped[Product] = relationship(back_populates="inventory")

    __table_args__ = (
        CheckConstraint("stock >= 0", name="inventory_stock_nonneg"),
        CheckConstraint("reserved >= 0", name="inventory_reserved_nonneg"),
        CheckConstraint("reserved <= stock", name="inventory_reserved_le_stock"),
    )

    @property
    def available(self) -> int:
        return self.stock - self.reserved


# ---------------- customers ----------------

class Customer(Base):
    """Local mirror of Cognito users. Cognito holds auth; we hold profile data."""

    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # Cognito sub
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    orders: Mapped[list["Order"]] = relationship(back_populates="customer")


# ---------------- orders ----------------

ORDER_STATUSES = ("pending", "confirmed", "fulfilled", "cancelled", "failed")


class Order(Base):
    """A confirmed order. Created by checkout service."""

    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_new_uuid_str
    )
    customer_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("customers.id"), nullable=False, index=True
    )
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    total_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    # Idempotency key from the client; same key = same order, returned without re-creating
    idempotency_key: Mapped[str | None] = mapped_column(String(100), unique=True, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, server_default="{}")

    customer: Mapped[Customer] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    invoice: Mapped["Invoice | None"] = relationship(
        back_populates="order", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'confirmed', 'fulfilled', 'cancelled', 'failed')",
            name="orders_status_valid",
        ),
        CheckConstraint("total_cents >= 0", name="orders_total_nonneg"),
        Index("ix_orders_status_created", "status", "created_at"),
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("products.id"), nullable=False
    )
    # Snapshot fields - prices/names are frozen at order time so later product
    # edits don't rewrite history.
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    order: Mapped[Order] = relationship(back_populates="items")
    product: Mapped[Product] = relationship(back_populates="order_items")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="order_items_qty_positive"),
        CheckConstraint("unit_price_cents >= 0", name="order_items_price_nonneg"),
    )

    @property
    def line_total_cents(self) -> int:
        return self.unit_price_cents * self.quantity


# ---------------- invoices ----------------

INVOICE_STATUSES = ("queued", "generating", "delivered", "failed")


class Invoice(Base):
    """Tracks the async invoice pipeline. One per order."""

    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="queued")
    s3_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    order: Mapped[Order] = relationship(back_populates="invoice")

    __table_args__ = (
        CheckConstraint(
            "status IN " + str(INVOICE_STATUSES), name="invoices_status_valid"
        ),
    )


# Helper to convert price cents <-> Decimal for display
def cents_to_decimal(cents: int) -> Decimal:
    return Decimal(cents) / Decimal(100)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)

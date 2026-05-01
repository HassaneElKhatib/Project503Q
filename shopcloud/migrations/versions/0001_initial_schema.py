"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-29 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---- products ----
    op.create_table(
        "products",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("sku", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("price_cents", sa.Integer, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("image_url", sa.String(500), nullable=False, server_default=""),
        sa.Column("tags", sa.JSON, nullable=False, server_default="[]"),
        sa.Column(
            "is_active", sa.Boolean, nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("price_cents >= 0", name="products_price_nonneg"),
    )
    op.create_index("ix_products_category", "products", ["category"])
    op.create_index(
        "ix_products_category_active", "products", ["category", "is_active"]
    )

    # ---- inventory ----
    op.create_table(
        "inventory",
        sa.Column(
            "product_id",
            sa.String(50),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("stock", sa.Integer, nullable=False, server_default="0"),
        sa.Column("reserved", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("stock >= 0", name="inventory_stock_nonneg"),
        sa.CheckConstraint("reserved >= 0", name="inventory_reserved_nonneg"),
        sa.CheckConstraint("reserved <= stock", name="inventory_reserved_le_stock"),
    )

    # ---- customers ----
    op.create_table(
        "customers",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ---- orders ----
    op.create_table(
        "orders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "customer_id",
            sa.String(64),
            sa.ForeignKey("customers.id"),
            nullable=False,
        ),
        sa.Column("customer_email", sa.String(255), nullable=False),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="pending"
        ),
        sa.Column("total_cents", sa.Integer, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("idempotency_key", sa.String(100), unique=True, nullable=True),
        sa.Column(
            "metadata_json", sa.JSON, nullable=False, server_default="{}"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'confirmed', 'fulfilled', 'cancelled', 'failed')",
            name="orders_status_valid",
        ),
        sa.CheckConstraint("total_cents >= 0", name="orders_total_nonneg"),
    )
    op.create_index("ix_orders_customer_id", "orders", ["customer_id"])
    op.create_index("ix_orders_idempotency_key", "orders", ["idempotency_key"])
    op.create_index("ix_orders_status_created", "orders", ["status", "created_at"])

    # ---- order_items ----
    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "order_id",
            sa.String(36),
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.String(50),
            sa.ForeignKey("products.id"),
            nullable=False,
        ),
        sa.Column("product_name", sa.String(255), nullable=False),
        sa.Column("unit_price_cents", sa.Integer, nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("quantity > 0", name="order_items_qty_positive"),
        sa.CheckConstraint(
            "unit_price_cents >= 0", name="order_items_price_nonneg"
        ),
    )
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])

    # ---- invoices ----
    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "order_id",
            sa.String(36),
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="queued"
        ),
        sa.Column("s3_key", sa.String(500), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('queued', 'generating', 'delivered', 'failed')",
            name="invoices_status_valid",
        ),
    )


def downgrade() -> None:
    op.drop_table("invoices")
    op.drop_table("order_items")
    op.drop_index("ix_orders_status_created", "orders")
    op.drop_index("ix_orders_idempotency_key", "orders")
    op.drop_index("ix_orders_customer_id", "orders")
    op.drop_table("orders")
    op.drop_table("customers")
    op.drop_table("inventory")
    op.drop_index("ix_products_category_active", "products")
    op.drop_index("ix_products_category", "products")
    op.drop_table("products")

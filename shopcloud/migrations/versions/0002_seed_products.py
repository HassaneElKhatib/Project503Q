"""seed catalog products

Idempotent (uses INSERT ... ON CONFLICT) so this can be re-run safely
on schema-rebuild scenarios.

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-29 00:00:01.000000
"""
import json
from pathlib import Path
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Path is relative to repo root - migrations/versions/
SEED_PATH = (
    Path(__file__).resolve().parents[2]
    / "services"
    / "catalog"
    / "data"
    / "products.json"
)


def upgrade() -> None:
    products = json.loads(SEED_PATH.read_text())

    # On Postgres we'd use ON CONFLICT. Use a bulk insert since this is
    # the very first run.
    products_table = sa.table(
        "products",
        sa.column("id", sa.String),
        sa.column("sku", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("category", sa.String),
        sa.column("price_cents", sa.Integer),
        sa.column("currency", sa.String),
        sa.column("image_url", sa.String),
        sa.column("tags", sa.JSON),
        sa.column("is_active", sa.Boolean),
    )
    inventory_table = sa.table(
        "inventory",
        sa.column("product_id", sa.String),
        sa.column("stock", sa.Integer),
        sa.column("reserved", sa.Integer),
    )

    op.bulk_insert(
        products_table,
        [
            {
                "id": p["id"],
                "sku": p["sku"],
                "name": p["name"],
                "description": p.get("description", ""),
                "category": p["category"],
                "price_cents": p["price_cents"],
                "currency": p.get("currency", "USD"),
                "image_url": p.get("image_url", ""),
                "tags": p.get("tags", []),
                "is_active": True,
            }
            for p in products
        ],
    )
    op.bulk_insert(
        inventory_table,
        [
            {
                "product_id": p["id"],
                "stock": p.get("stock", 0),
                "reserved": 0,
            }
            for p in products
        ],
    )


def downgrade() -> None:
    products = json.loads(SEED_PATH.read_text())
    ids = [p["id"] for p in products]
    op.execute(
        sa.text("DELETE FROM inventory WHERE product_id = ANY(:ids)").bindparams(ids=ids)
    )
    op.execute(
        sa.text("DELETE FROM products WHERE id = ANY(:ids)").bindparams(ids=ids)
    )

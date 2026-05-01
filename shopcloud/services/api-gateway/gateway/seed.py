"""Seed initial users and products into the gateway local store.

Loads products from libs-shared seed file when present, otherwise writes a
small built-in catalog so the customer-web SPA always has something to
render on first run.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from sqlalchemy import select

from .db import Product, SessionLocal, User
from .security import hash_password
from .settings import settings

_BUILTIN_PRODUCTS = [
    {
        "name": "Velvet Lipstick — Ruby",
        "altNames": ["Lipstick", "Velvet Ruby"],
        "description": "A long-wear matte lipstick in a deep ruby tone.",
        "images": ["https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?auto=format&fit=crop&w=900&q=80"],
        "price": 19.99,
        "lastPrice": 24.99,
        "stock": 120,
        "category": "lips",
    },
    {
        "name": "Hydration Serum 30ml",
        "altNames": ["Serum", "Hyaluronic"],
        "description": "Hyaluronic acid serum for plump, hydrated skin.",
        "images": ["https://images.unsplash.com/photo-1620916566398-39f1143ab7be?auto=format&fit=crop&w=900&q=80"],
        "price": 32.0,
        "lastPrice": 38.0,
        "stock": 85,
        "category": "skincare",
    },
    {
        "name": "Foundation Stick — Beige",
        "altNames": ["Foundation"],
        "description": "Buildable, blendable medium coverage stick foundation.",
        "images": ["https://images.unsplash.com/photo-1631214540242-5d6c4d2d72f8?auto=format&fit=crop&w=900&q=80"],
        "price": 27.5,
        "lastPrice": 30.0,
        "stock": 60,
        "category": "face",
    },
    {
        "name": "Volume Mascara",
        "altNames": ["Mascara"],
        "description": "Builds volume without clumps. Smudge-resistant formula.",
        "images": ["https://images.unsplash.com/photo-1596462502278-27bfdc403348?auto=format&fit=crop&w=900&q=80"],
        "price": 15.99,
        "lastPrice": 18.99,
        "stock": 200,
        "category": "eyes",
    },
    {
        "name": "Rose Eau de Parfum 50ml",
        "altNames": ["Perfume", "Rose"],
        "description": "Floral fragrance with notes of damask rose, jasmine and vanilla.",
        "images": ["https://images.unsplash.com/photo-1594035910387-fea47794261f?auto=format&fit=crop&w=900&q=80"],
        "price": 64.0,
        "lastPrice": 72.0,
        "stock": 40,
        "category": "fragrance",
    },
    {
        "name": "Brow Pencil — Soft Brown",
        "altNames": ["Brow", "Eyebrow Pencil"],
        "description": "Twist-up brow pencil with built-in spoolie brush.",
        "images": ["https://images.unsplash.com/photo-1512496015851-a90fb38ba796?auto=format&fit=crop&w=900&q=80"],
        "price": 12.5,
        "lastPrice": 14.0,
        "stock": 150,
        "category": "eyes",
    },
]


async def seed_database() -> None:
    """Idempotent: seed admin only in local-auth mode; products inserted once."""
    async with SessionLocal() as session:
        if settings.use_local_gateway_auth:
            admin_row = await session.execute(
                select(User).where(User.email == settings.seed_admin_email)
            )
            if admin_row.scalar_one_or_none() is None:
                session.add(
                    User(
                        email=settings.seed_admin_email,
                        name=settings.seed_admin_name,
                        password_hash=hash_password(settings.seed_admin_password),
                        role="admin",
                    )
                )

        existing_product = await session.execute(select(Product).limit(1))
        if existing_product.scalar_one_or_none() is None:
            products = _load_seed_products()
            for entry in products:
                session.add(
                    Product(
                        name=entry.get("name", "Unnamed product"),
                        altNames=json.dumps(entry.get("altNames", [])),
                        description=entry.get("description", ""),
                        images=json.dumps(entry.get("images", [])),
                        price=float(entry.get("price", 0.0)),
                        lastPrice=float(entry.get("lastPrice", entry.get("price", 0.0))),
                        stock=int(entry.get("stock", 0)),
                        category=entry.get("category", "general"),
                        isActive=bool(entry.get("isActive", True)),
                    )
                )

        await session.commit()


def _load_seed_products() -> list[dict]:
    """Try the catalog service's bundled seed first, fall back to built-in."""
    resolved = Path(__file__).resolve()
    repo_root = resolved.parents[3] if len(resolved.parents) > 3 else None
    candidates = [
        (repo_root / "services" / "catalog" / "data" / "products.json") if repo_root else None,
        Path("/app/data/products.json"),
        Path(os.environ.get("SEED_PRODUCTS_FILE", "")) if os.environ.get("SEED_PRODUCTS_FILE") else None,
    ]
    for candidate in candidates:
        if not candidate or not candidate.exists():
            continue
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
            if isinstance(data, list) and data:
                return _normalise_catalog_payload(data)
        except (OSError, json.JSONDecodeError):
            continue
    return _BUILTIN_PRODUCTS


def _normalise_catalog_payload(rows: list[dict]) -> list[dict]:
    """Map the catalog service's product schema into the gateway shape."""
    out: list[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        cents = row.get("price_cents")
        price = (cents / 100.0) if isinstance(cents, (int, float)) else float(row.get("price", 0.0))
        out.append(
            {
                "name": row.get("name", "Unnamed product"),
                "altNames": row.get("altNames", []),
                "description": row.get("description", ""),
                "images": (
                    row.get("images")
                    if isinstance(row.get("images"), list)
                    else ([row.get("image_url")] if row.get("image_url") else [])
                ),
                "price": price,
                "lastPrice": price,
                "stock": int(row.get("stock", row.get("available", 0)) or 0),
                "category": row.get("category", "general"),
                "isActive": bool(row.get("active", True)),
            }
        )
    return out

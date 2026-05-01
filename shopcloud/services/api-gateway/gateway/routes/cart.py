"""Cart endpoints used by the React UI.

The schema mirrors what cart.js expects: `{ cart: { items: [...] } }`,
with each item carrying `productId`, `quantity`, and a snapshot of the
product (name, price, image) so the cart page can render without
hitting the catalog again.
"""
from __future__ import annotations

import json
from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import CartItem, Product, SessionLocal
from ..security import require_user
from ..settings import settings

router = APIRouter()


async def _session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


class CartItemIn(BaseModel):
    productId: str
    quantity: int = Field(ge=-100, le=100)


class MergeIn(BaseModel):
    cart: list[dict[str, Any]] = Field(default_factory=list)


def _serialize(items: list[CartItem]) -> list[dict[str, Any]]:
    out = []
    for item in items:
        snapshot = {}
        try:
            snapshot = json.loads(item.snapshot or "{}")
        except json.JSONDecodeError:
            snapshot = {}
        out.append(
            {
                "_id": item.id,
                "productId": item.productId,
                "quantity": item.quantity,
                "name": snapshot.get("name", ""),
                "price": snapshot.get("price", 0),
                "image": snapshot.get("image", ""),
            }
        )
    return out


async def _user_items(session: AsyncSession, user_id: str) -> list[CartItem]:
    res = await session.execute(select(CartItem).where(CartItem.user_id == user_id))
    return list(res.scalars())


async def _snapshot(session: AsyncSession, product_id: str) -> dict[str, Any]:
    res = await session.execute(select(Product).where(Product.id == product_id))
    product = res.scalar_one_or_none()
    if not product and settings.catalog_base_url:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{settings.catalog_base_url}/products/{product_id}")
                if resp.status_code == 200:
                    upstream = resp.json()
                    upstream_price = upstream.get("price")
                    if upstream_price is None and upstream.get("price_cents") is not None:
                        upstream_price = float(upstream.get("price_cents", 0)) / 100.0
                    return {
                        "name": upstream.get("name", ""),
                        "price": float(upstream_price or 0),
                        "image": upstream.get("image_url", ""),
                    }
        except (httpx.HTTPError, ValueError, TypeError):
            pass

    if not product:
        return {"name": "", "price": 0, "image": ""}
    images = []
    try:
        images = json.loads(product.images or "[]")
    except json.JSONDecodeError:
        images = []
    return {"name": product.name, "price": product.price, "image": images[0] if images else ""}


@router.get("")
async def get_cart(
    claims: Annotated[dict, Depends(require_user)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    items = await _user_items(session, claims["sub"])
    return {"cart": {"items": _serialize(items)}}


@router.post("/add")
async def add_to_cart(
    payload: CartItemIn,
    claims: Annotated[dict, Depends(require_user)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    user_id = claims["sub"]
    res = await session.execute(
        select(CartItem).where(CartItem.user_id == user_id, CartItem.productId == payload.productId)
    )
    existing = res.scalar_one_or_none()
    if existing:
        new_qty = existing.quantity + payload.quantity
        if new_qty <= 0:
            await session.delete(existing)
        else:
            existing.quantity = new_qty
    elif payload.quantity > 0:
        snapshot = await _snapshot(session, payload.productId)
        session.add(
            CartItem(
                user_id=user_id,
                productId=payload.productId,
                quantity=payload.quantity,
                snapshot=json.dumps(snapshot),
            )
        )
    await session.commit()
    items = await _user_items(session, user_id)
    return {"cart": {"items": _serialize(items)}}


@router.delete("/clear")
async def clear_cart(
    claims: Annotated[dict, Depends(require_user)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    items = await _user_items(session, claims["sub"])
    for item in items:
        await session.delete(item)
    await session.commit()
    return {"cart": {"items": []}}


@router.delete("/{product_id}")
async def remove_from_cart(
    product_id: str,
    claims: Annotated[dict, Depends(require_user)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    user_id = claims["sub"]
    res = await session.execute(
        select(CartItem).where(CartItem.user_id == user_id, CartItem.productId == product_id)
    )
    item = res.scalar_one_or_none()
    if item:
        await session.delete(item)
        await session.commit()
    items = await _user_items(session, user_id)
    return {"cart": {"items": _serialize(items)}}


@router.post("/merge")
async def merge_cart(
    payload: MergeIn,
    claims: Annotated[dict, Depends(require_user)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    user_id = claims["sub"]
    for guest_item in payload.cart:
        if not isinstance(guest_item, dict):
            continue
        product_id = guest_item.get("productId")
        if not product_id:
            continue
        try:
            qty = int(guest_item.get("quantity", 0))
        except (TypeError, ValueError):
            continue
        if qty == 0:
            continue
        res = await session.execute(
            select(CartItem).where(CartItem.user_id == user_id, CartItem.productId == product_id)
        )
        existing = res.scalar_one_or_none()
        if existing:
            existing.quantity = max(1, existing.quantity + qty)
        else:
            snapshot = await _snapshot(session, product_id)
            session.add(
                CartItem(
                    user_id=user_id,
                    productId=product_id,
                    quantity=max(1, qty),
                    snapshot=json.dumps(snapshot),
                )
            )
    await session.commit()
    items = await _user_items(session, user_id)
    return {"cart": {"items": _serialize(items)}}

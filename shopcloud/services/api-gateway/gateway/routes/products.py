"""Product catalog. Reads optionally proxy to the upstream catalog
service; writes always live in the gateway store so admin CRUD works
without depending on the AWS-native catalog deployment."""
from __future__ import annotations

import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import Product, SessionLocal, to_dict
from ..security import require_admin

router = APIRouter()


async def _session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


class ProductIn(BaseModel):
    name: str
    altNames: list[str] = Field(default_factory=list)
    description: str = ""
    images: list[str] = Field(default_factory=list)
    price: float
    lastPrice: float | None = None
    stock: int = 0
    category: str = "general"
    isActive: bool = True


class StockAdjustmentIn(BaseModel):
    delta: int


def _row_to_dict(row: Product) -> dict[str, Any]:
    payload = to_dict(row, json_fields=("altNames", "images"))
    images = payload.get("images") or []
    if isinstance(images, list):
        payload["images"] = [
            img for img in images if isinstance(img, str) and img and not img.startswith(("http://", "https://"))
        ]
    else:
        payload["images"] = []
    return payload


@router.get("")
async def list_products(session: Annotated[AsyncSession, Depends(_session)], page: int = 1, limit: int = 20, category: str | None = None):
    page = max(1, page)
    limit = max(1, min(100, limit))

    stmt = select(Product).where(Product.isActive.is_(True))
    if category:
        stmt = stmt.where(Product.category == category)
    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.execute(total_stmt)).scalar_one()

    stmt = stmt.order_by(Product.created_at.desc()).offset((page - 1) * limit).limit(limit)
    rows = (await session.execute(stmt)).scalars().all()
    return {
        "products": [_row_to_dict(r) for r in rows],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/admin")
async def admin_list_products(
    _admin: Annotated[dict, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(_session)],
    page: int = 1,
    limit: int = 50,
    category: str | None = None,
    q: str | None = None,
    includeInactive: bool = True,
):
    page = max(1, page)
    limit = max(1, min(200, limit))

    stmt = select(Product)
    if not includeInactive:
        stmt = stmt.where(Product.isActive.is_(True))
    if category:
        stmt = stmt.where(Product.category == category)
    if q:
        search = f"%{q.strip()}%"
        stmt = stmt.where(Product.name.ilike(search))

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.execute(total_stmt)).scalar_one()
    rows = (
        await session.execute(stmt.order_by(Product.created_at.desc()).offset((page - 1) * limit).limit(limit))
    ).scalars().all()
    return {"products": [_row_to_dict(r) for r in rows], "total": total, "page": page, "limit": limit}


@router.get("/{product_id}")
async def get_product(product_id: str, session: Annotated[AsyncSession, Depends(_session)]):
    row = await session.execute(select(Product).where(Product.id == product_id))
    product = row.scalar_one_or_none()
    if not product:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="product not found")
    return _row_to_dict(product)


@router.post("", status_code=201)
async def create_product(
    payload: ProductIn,
    _admin: Annotated[dict, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    p = Product(
        name=payload.name,
        altNames=json.dumps(payload.altNames),
        description=payload.description,
        images=json.dumps(payload.images),
        price=payload.price,
        lastPrice=payload.lastPrice if payload.lastPrice is not None else payload.price,
        stock=payload.stock,
        category=payload.category,
        isActive=payload.isActive,
    )
    session.add(p)
    await session.commit()
    await session.refresh(p)
    return _row_to_dict(p)


@router.put("/{product_id}")
async def update_product(
    product_id: str,
    payload: ProductIn,
    _admin: Annotated[dict, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    row = await session.execute(select(Product).where(Product.id == product_id))
    product = row.scalar_one_or_none()
    if not product:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="product not found")
    product.name = payload.name
    product.altNames = json.dumps(payload.altNames)
    product.description = payload.description
    product.images = json.dumps(payload.images)
    product.price = payload.price
    product.lastPrice = payload.lastPrice if payload.lastPrice is not None else payload.price
    product.stock = payload.stock
    product.category = payload.category
    product.isActive = payload.isActive
    await session.commit()
    return _row_to_dict(product)


@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    _admin: Annotated[dict, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    row = await session.execute(select(Product).where(Product.id == product_id))
    product = row.scalar_one_or_none()
    if not product:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="product not found")
    product.isActive = False
    await session.commit()
    return {"message": "product disabled", "_id": product.id, "isActive": product.isActive}


@router.put("/{product_id}/stock")
async def adjust_stock(
    product_id: str,
    payload: StockAdjustmentIn,
    _admin: Annotated[dict, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    row = await session.execute(select(Product).where(Product.id == product_id))
    product = row.scalar_one_or_none()
    if not product:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="product not found")

    product.stock = max(0, int(product.stock) + int(payload.delta))
    await session.commit()
    return {"_id": product.id, "stock": product.stock}

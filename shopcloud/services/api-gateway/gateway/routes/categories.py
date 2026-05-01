from __future__ import annotations

import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import distinct, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import Category, Product, SessionLocal
from ..security import require_admin

router = APIRouter()


async def _session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "category"


class CategoryIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)


@router.get("")
async def list_categories(session: Annotated[AsyncSession, Depends(_session)]):
    all_rows = (await session.execute(select(Category).order_by(Category.name.asc()))).scalars().all()
    active_rows = [c for c in all_rows if c.is_active]
    all_known_names = {c.name for c in all_rows}
    product_categories = (
        await session.execute(select(distinct(Product.category)).where(Product.category.is_not(None), Product.category != ""))
    ).scalars().all()
    synthetic = [
        {"_id": f"product-{_slugify(name)}", "name": name, "slug": _slugify(name), "isActive": True}
        for name in product_categories
        if name not in all_known_names
    ]
    categories = [{"_id": c.id, "name": c.name, "slug": c.slug, "isActive": c.is_active} for c in active_rows] + synthetic
    categories.sort(key=lambda x: x["name"].lower())
    return {"categories": categories}


@router.post("", status_code=201)
async def create_category(
    payload: CategoryIn,
    _admin: Annotated[dict, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    name = payload.name.strip()
    slug = _slugify(name)
    existing = await session.execute(select(Category).where((Category.name == name) | (Category.slug == slug)))
    category = existing.scalar_one_or_none()
    if category:
        if not category.is_active:
            category.is_active = True
            category.name = name
            category.slug = slug
            await session.commit()
            return {"_id": category.id, "name": category.name, "slug": category.slug, "isActive": category.is_active}
        raise HTTPException(status.HTTP_409_CONFLICT, detail="category already exists")

    category = Category(name=name, slug=slug, is_active=True)
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return {"_id": category.id, "name": category.name, "slug": category.slug, "isActive": category.is_active}


@router.put("/{category_id}")
async def update_category(
    category_id: str,
    payload: CategoryIn,
    _admin: Annotated[dict, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    row = await session.execute(select(Category).where(Category.id == category_id))
    category = row.scalar_one_or_none()

    if not category and category_id.startswith("product-"):
        slug = category_id[len("product-"):]
        product_cats = (
            await session.execute(
                select(distinct(Product.category)).where(
                    Product.category.is_not(None), Product.category != ""
                )
            )
        ).scalars().all()
        matched_name = next((n for n in product_cats if _slugify(n) == slug), None)
        if matched_name:
            category = Category(name=matched_name, slug=slug, is_active=True)
            session.add(category)
            await session.flush()

    if not category:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="category not found")

    name = payload.name.strip()
    new_slug = _slugify(name)
    existing = await session.execute(
        select(Category).where(
            (Category.name == name) | (Category.slug == new_slug),
            Category.id != category.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, detail="category already exists")

    old_name = category.name
    category.name = name
    category.slug = new_slug
    products = (await session.execute(select(Product).where(Product.category == old_name))).scalars().all()
    for product in products:
        product.category = name
    await session.commit()
    return {"_id": category.id, "name": category.name, "slug": category.slug, "isActive": category.is_active}


@router.delete("/{category_id}")
async def delete_category(
    category_id: str,
    _admin: Annotated[dict, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    row = await session.execute(select(Category).where(Category.id == category_id))
    category = row.scalar_one_or_none()

    if not category and category_id.startswith("product-"):
        slug = category_id[len("product-"):]
        product_cats = (
            await session.execute(
                select(distinct(Product.category)).where(
                    Product.category.is_not(None), Product.category != ""
                )
            )
        ).scalars().all()
        matched_name = next((n for n in product_cats if _slugify(n) == slug), None)
        if matched_name:
            category = Category(name=matched_name, slug=slug, is_active=False)
            session.add(category)
            await session.commit()
            await session.refresh(category)
            return {"message": "category disabled", "_id": category.id, "isActive": False}

    if not category:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="category not found")
    category.is_active = False
    await session.commit()
    return {"message": "category disabled", "_id": category.id, "isActive": category.is_active}

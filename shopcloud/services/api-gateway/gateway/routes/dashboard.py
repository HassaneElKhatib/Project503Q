"""Admin + client dashboards."""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import Order, Product, ReturnRequest, Review, SessionLocal, SiteReview, User
from ..security import require_admin, require_user

router = APIRouter()


async def _session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


@router.get("")
async def admin_dashboard(
    _admin: Annotated[dict, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    now = datetime.now(timezone.utc)
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

    total_users = (await session.execute(select(func.count()).select_from(User))).scalar_one()
    total_products = (await session.execute(select(func.count()).select_from(Product))).scalar_one()
    total_orders = (await session.execute(select(func.count()).select_from(Order))).scalar_one()
    revenue_row = (await session.execute(select(func.coalesce(func.sum(Order.total), 0)))).scalar_one()
    month_revenue = (
        await session.execute(select(func.coalesce(func.sum(Order.total), 0)).where(Order.created_at >= month_start))
    ).scalar_one()
    avg_rating_row = (await session.execute(select(func.coalesce(func.avg(Review.rating), 0)))).scalar_one()

    status_counts: dict[str, int] = defaultdict(int)
    rows = (await session.execute(select(Order.status, func.count()).group_by(Order.status))).all()
    for status_value, count in rows:
        status_counts[status_value] = count

    monthly: dict[str, dict[str, float | int]] = defaultdict(lambda: {"orders": 0, "revenue": 0.0})
    order_rows = (await session.execute(select(Order))).scalars().all()
    for order in order_rows:
        if not order.created_at:
            continue
        bucket = order.created_at.strftime("%Y-%m")
        monthly[bucket]["orders"] += 1
        monthly[bucket]["revenue"] += order.total

    monthly_sorted = sorted(
        [{"month": m, **vals} for m, vals in monthly.items()],
        key=lambda r: r["month"],
    )

    top_products: dict[str, dict] = defaultdict(lambda: {"units": 0, "revenue": 0.0, "name": ""})
    for order in order_rows:
        try:
            for item in json.loads(order.items_json or "[]"):
                pid = item.get("productId") or "unknown"
                top_products[pid]["units"] += int(item.get("quantity", 0))
                top_products[pid]["revenue"] += float(item.get("price", 0)) * int(item.get("quantity", 0))
                top_products[pid]["name"] = item.get("name", top_products[pid]["name"])
        except json.JSONDecodeError:
            continue
    top_sorted = sorted(
        [{"productId": pid, **vals} for pid, vals in top_products.items()],
        key=lambda r: r["units"],
        reverse=True,
    )[:5]

    low_stock_rows = (
        await session.execute(select(Product).where(Product.stock <= 5, Product.isActive.is_(True)).order_by(Product.stock.asc()))
    ).scalars().all()
    missing_image_rows = (
        await session.execute(select(Product).where(Product.isActive.is_(True)).order_by(Product.created_at.desc()))
    ).scalars().all()
    missing_images = []
    for product in missing_image_rows:
        try:
            images = json.loads(product.images or "[]")
        except json.JSONDecodeError:
            images = []
        if not images:
            missing_images.append(product)

    pending_orders_rows = (
        await session.execute(select(Order).where(Order.status.in_(["pending", "confirmed", "processing"])).order_by(Order.created_at.desc()))
    ).scalars().all()
    pending_returns = (
        await session.execute(select(func.count()).select_from(ReturnRequest).where(ReturnRequest.status == "requested"))
    ).scalar_one()
    pending_reviews = (
        await session.execute(select(func.count()).select_from(Review).where(Review.is_approved.is_(False)))
    ).scalar_one()

    user_rows = (await session.execute(select(User))).scalars().all()
    user_map = {u.id: u.name or u.email for u in user_rows}
    recent_orders = (
        await session.execute(select(Order).order_by(Order.created_at.desc()).limit(10))
    ).scalars().all()

    return {
        "totals": {
            "users": total_users,
            "products": total_products,
            "orders": total_orders,
            "revenue": float(revenue_row),
            "revenueThisMonth": float(month_revenue),
            "pendingOrders": len(pending_orders_rows),
            "lowStockProducts": len(low_stock_rows),
            "averageReviewRating": float(avg_rating_row),
        },
        "ordersByStatus": dict(status_counts),
        "monthly": monthly_sorted,
        "topProducts": top_sorted,
        "recentOrders": [
            {
                "_id": order.id,
                "customerName": user_map.get(order.user_id, "Customer"),
                "total": order.total,
                "status": order.status,
                "createdAt": order.created_at.isoformat() if order.created_at else None,
            }
            for order in recent_orders
        ],
        "lowStockTable": [
            {
                "_id": product.id,
                "name": product.name,
                "category": product.category,
                "stock": product.stock,
                "status": "Low Stock" if product.stock > 0 else "Out of Stock",
            }
            for product in low_stock_rows[:10]
        ],
        "needsAttention": {
            "lowStockProducts": len(low_stock_rows),
            "pendingOrders": len(pending_orders_rows),
            "productsMissingImages": len(missing_images),
            "pendingReviews": int(pending_reviews),
            "pendingReturnRequests": int(pending_returns),
        },
    }


@router.get("/client")
async def client_dashboard(
    claims: Annotated[dict, Depends(require_user)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    user_id = claims["sub"]
    orders = (
        await session.execute(select(Order).where(Order.user_id == user_id))
    ).scalars().all()
    spent = sum(o.total for o in orders)
    review_count = (
        await session.execute(
            select(func.count()).select_from(Review).where(Review.user_id == user_id)
        )
    ).scalar_one()
    site_review_count = (
        await session.execute(
            select(func.count()).select_from(SiteReview).where(SiteReview.user_id == user_id)
        )
    ).scalar_one()
    status_counts: dict[str, int] = defaultdict(int)
    for o in orders:
        status_counts[o.status] += 1
    return {
        "totals": {
            "orders": len(orders),
            "spent": spent,
            "reviews": review_count,
            "siteReviews": site_review_count,
        },
        "ordersByStatus": dict(status_counts),
    }

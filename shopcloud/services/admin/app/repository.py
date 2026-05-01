"""Admin DB queries.

Read-mostly. The only writes admins do today are order-status changes
(e.g. mark fulfilled).
"""
import math

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    CustomerSummary,
    OrderDetail,
    OrderItemDetail,
    OrderSummary,
    PagedCustomers,
    PagedOrders,
)
from libs.db import Customer, Order


class AdminRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ---- orders ----

    async def list_orders(
        self,
        *,
        status: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> PagedOrders:
        # Count
        count_q = select(func.count()).select_from(Order)
        if status:
            count_q = count_q.where(Order.status == status)
        total = (await self._session.execute(count_q)).scalar_one()

        # Page
        items_q = (
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.invoice))
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if status:
            items_q = items_q.where(Order.status == status)

        result = await self._session.execute(items_q)
        rows = result.scalars().all()

        items = [
            OrderSummary(
                id=o.id,
                customer_id=o.customer_id,
                customer_email=o.customer_email,
                status=o.status,
                total_cents=o.total_cents,
                currency=o.currency,
                item_count=sum(i.quantity for i in o.items),
                created_at=o.created_at,
                invoice_status=o.invoice.status if o.invoice else None,
            )
            for o in rows
        ]
        page_size = limit
        page = (offset // limit) + 1 if limit else 1
        return PagedOrders(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total else 0,
        )

    async def get_order(self, order_id: str) -> OrderDetail | None:
        result = await self._session.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items), selectinload(Order.invoice))
        )
        order = result.scalar_one_or_none()
        if order is None:
            return None
        return OrderDetail(
            id=order.id,
            customer_id=order.customer_id,
            customer_email=order.customer_email,
            status=order.status,
            total_cents=order.total_cents,
            currency=order.currency,
            items=[
                OrderItemDetail(
                    product_id=i.product_id,
                    product_name=i.product_name,
                    unit_price_cents=i.unit_price_cents,
                    quantity=i.quantity,
                    line_total_cents=i.line_total_cents,
                )
                for i in order.items
            ],
            invoice_status=order.invoice.status if order.invoice else None,
            invoice_s3_key=order.invoice.s3_key if order.invoice else None,
            invoice_sent_at=order.invoice.sent_at if order.invoice else None,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

    async def update_order_status(self, order_id: str, status: str) -> bool:
        order = await self._session.get(Order, order_id)
        if order is None:
            return False
        order.status = status
        return True

    # ---- customers ----

    async def list_customers(
        self, *, offset: int = 0, limit: int = 20
    ) -> PagedCustomers:
        # Aggregate per-customer totals in a single query
        sub = (
            select(
                Order.customer_id.label("customer_id"),
                func.count(Order.id).label("order_count"),
                func.coalesce(func.sum(Order.total_cents), 0).label("total_spent"),
            )
            .group_by(Order.customer_id)
            .subquery()
        )

        total_q = select(func.count()).select_from(Customer)
        total = (await self._session.execute(total_q)).scalar_one()

        q = (
            select(
                Customer,
                func.coalesce(sub.c.order_count, 0),
                func.coalesce(sub.c.total_spent, 0),
            )
            .outerjoin(sub, sub.c.customer_id == Customer.id)
            .order_by(Customer.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(q)
        rows = result.all()

        items = [
            CustomerSummary(
                id=c.id,
                email=c.email,
                full_name=c.full_name,
                order_count=int(order_count),
                total_spent_cents=int(total_spent),
                created_at=c.created_at,
            )
            for c, order_count, total_spent in rows
        ]
        page_size = limit
        page = (offset // limit) + 1 if limit else 1
        return PagedCustomers(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total else 0,
        )

    # ---- stats ----

    async def order_stats(self) -> dict:
        """Quick dashboard numbers."""
        result = await self._session.execute(
            select(
                Order.status,
                func.count(Order.id),
                func.coalesce(func.sum(Order.total_cents), 0),
            ).group_by(Order.status)
        )
        rows = result.all()
        by_status = {row[0]: {"count": int(row[1]), "total_cents": int(row[2])} for row in rows}
        total_orders = sum(v["count"] for v in by_status.values())
        total_revenue = sum(
            v["total_cents"] for k, v in by_status.items() if k in ("confirmed", "fulfilled")
        )
        return {
            "total_orders": total_orders,
            "total_revenue_cents": total_revenue,
            "by_status": by_status,
        }

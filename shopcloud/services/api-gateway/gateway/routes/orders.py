"""Orders.

Customers see their own orders; admins see all orders. Order placement
clears the cart and (when CHECKOUT_BASE_URL is configured) forwards the
order to the upstream checkout service which publishes the SQS invoice
event. In local-only mode the order is just stored in the gateway DB.
"""
from __future__ import annotations

import json
import logging
from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from datetime import datetime, timezone

from ..db import CartItem, Order, Product, ReturnRequest, SessionLocal, User
from ..invoice_email import send_invoice_email, send_order_status_update_email
from ..security import require_admin, require_user
from ..settings import settings

router = APIRouter()
logger = logging.getLogger(__name__)
ADMIN_ALLOWED_ORDER_STATUSES = {
    "pending",
    "confirmed",
    "processing",
    "shipped",
    "delivered",
    "completed",
    "cancelled",
    "returned",
}


async def _session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


class AddressIn(BaseModel):
    name: str = ""
    line1: str = ""
    line2: str = ""
    city: str = ""
    postalCode: str = ""
    country: str = ""
    phone: str = ""


class OrderItemIn(BaseModel):
    productId: str
    name: str = ""
    price: float
    quantity: int = Field(ge=1)
    image: str = ""


class CreateOrderIn(BaseModel):
    items: list[OrderItemIn] = Field(default_factory=list)
    address: AddressIn = AddressIn()
    idempotencyKey: str | None = None


class StatusUpdateIn(BaseModel):
    status: str


class ReturnRequestIn(BaseModel):
    reason: str = Field(min_length=3)


class ReturnStatusIn(BaseModel):
    status: str


def _invoice_payload(order: Order, claims: dict, *, email_queued: bool = False) -> dict[str, Any]:
    return {
        "invoiceId": f"INV-{order.id[:8].upper()}",
        "orderId": order.id,
        "emailTo": claims.get("email", ""),
        "emailQueued": email_queued,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }


def _serialize(order: Order) -> dict[str, Any]:
    items = []
    try:
        items = json.loads(order.items_json or "[]")
    except json.JSONDecodeError:
        items = []
    address = {}
    try:
        address = json.loads(order.address_json or "{}")
    except json.JSONDecodeError:
        address = {}
    return {
        "_id": order.id,
        "userId": order.user_id,
        "status": order.status,
        "total": order.total,
        "items": items,
        "address": address,
        "createdAt": order.created_at.isoformat() if order.created_at else None,
    }


@router.get("/history/{page}/{limit}")
async def list_orders(
    page: int,
    limit: int,
    claims: Annotated[dict, Depends(require_user)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    page = max(1, page)
    limit = max(1, min(100, limit))
    base = select(Order).order_by(Order.created_at.desc())
    if claims.get("role") != "admin":
        base = base.where(Order.user_id == claims["sub"])

    total = (await session.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (await session.execute(base.offset((page - 1) * limit).limit(limit))).scalars().all()
    return {
        "orders": [_serialize(r) for r in rows],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.post("", status_code=201)
async def create_order(
    payload: CreateOrderIn,
    claims: Annotated[dict, Depends(require_user)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    if not payload.items:
        # Fall back to cart contents if the UI sends an empty items list.
        cart_rows = (
            await session.execute(select(CartItem).where(CartItem.user_id == claims["sub"]))
        ).scalars().all()
        if not cart_rows:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="cart is empty")
        for cart_item in cart_rows:
            snapshot = {}
            try:
                snapshot = json.loads(cart_item.snapshot or "{}")
            except json.JSONDecodeError:
                snapshot = {}
            payload.items.append(
                OrderItemIn(
                    productId=cart_item.productId,
                    name=snapshot.get("name", ""),
                    price=float(snapshot.get("price", 0)),
                    quantity=cart_item.quantity,
                    image=snapshot.get("image", ""),
                )
            )

    total = sum(item.price * item.quantity for item in payload.items)
    # Inventory validation and deduction (single source of truth: gateway DB).
    product_ids = [item.productId for item in payload.items]
    products = (
        await session.execute(select(Product).where(Product.id.in_(product_ids), Product.isActive.is_(True)))
    ).scalars().all()
    product_by_id = {p.id: p for p in products}
    for item in payload.items:
        product = product_by_id.get(item.productId)
        if not product:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"product not found: {item.productId}")
        if int(product.stock) < int(item.quantity):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f"insufficient stock for product {product.name}",
            )

    for item in payload.items:
        product = product_by_id[item.productId]
        product.stock = max(0, int(product.stock) - int(item.quantity))
        if product.stock == 0:
            product.isActive = False

    order = Order(
        user_id=claims["sub"],
        status="pending",
        total=total,
        items_json=json.dumps([item.model_dump() for item in payload.items]),
        address_json=json.dumps(payload.address.model_dump()),
    )
    session.add(order)

    # Clear server-side cart on successful place.
    cart_rows = (
        await session.execute(select(CartItem).where(CartItem.user_id == claims["sub"]))
    ).scalars().all()
    for row in cart_rows:
        await session.delete(row)

    await session.commit()
    await session.refresh(order)

    # Best-effort fan-out to the upstream checkout service (which would
    # publish an SQS event for the invoice worker). Failures are logged
    # but do not block the customer response.
    if settings.checkout_base_url:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    f"{settings.checkout_base_url}/checkout",
                    json={
                        "idempotency_key": payload.idempotencyKey or order.id,
                        "order_id": order.id,
                    },
                    headers={"x-user-id": claims["sub"], "x-user-email": claims.get("email", "")},
                )
        except httpx.HTTPError:
            pass

    payload = _serialize(order)
    payload["invoice"] = _invoice_payload(order, claims, email_queued=False)
    payload["confirmation"] = {"message": "Order placed successfully", "orderId": order.id}

    recipient_email = (claims.get("email") or "").strip()
    if not recipient_email:
        user_row = await session.execute(select(User).where(User.id == claims["sub"]))
        user = user_row.scalar_one_or_none()
        recipient_email = (user.email if user else "") or ""

    try:
        payload["invoice"]["emailQueued"] = send_invoice_email(
            to_email=recipient_email,
            customer_name=(payload.get("address", {}) or {}).get("name", ""),
            order=payload,
            invoice=payload["invoice"],
        )
    except Exception as exc:
        # Invoice emails are best-effort in local mode.
        logger.warning("Invoice email failed for order %s: %s", order.id, exc)
        payload["invoice"]["emailQueued"] = False

    return payload


@router.put("/{order_id}")
async def update_order_status(
    order_id: str,
    payload: StatusUpdateIn,
    claims: Annotated[dict, Depends(require_user)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    res = await session.execute(select(Order).where(Order.id == order_id))
    order = res.scalar_one_or_none()
    if not order:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="order not found")

    is_admin = claims.get("role") == "admin"
    if not is_admin and order.user_id != claims["sub"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="not your order")

    new_status = payload.status.strip().lower()
    if is_admin and new_status not in ADMIN_ALLOWED_ORDER_STATUSES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid order status")
    if not is_admin:
        # Customers can only cancel their own pending orders.
        if new_status != "cancelled" or order.status not in {"pending"}:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="customers can only cancel pending orders")

    old_status = order.status
    order.status = new_status
    await session.commit()
    try:
        user_row = await session.execute(select(User).where(User.id == order.user_id))
        user = user_row.scalar_one_or_none()
        if user:
            send_order_status_update_email(
                to_email=user.email,
                customer_name=user.name,
                order_id=order.id,
                old_status=old_status,
                new_status=new_status,
            )
    except Exception as exc:
        logger.warning("Order status email failed for order %s: %s", order.id, exc)
    return _serialize(order)


@router.get("")
async def admin_list_all_orders(
    _admin: Annotated[dict, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    rows = (await session.execute(select(Order).order_by(Order.created_at.desc()))).scalars().all()
    return {"orders": [_serialize(r) for r in rows]}


@router.post("/{order_id}/returns", status_code=201)
async def create_return_request(
    order_id: str,
    payload: ReturnRequestIn,
    claims: Annotated[dict, Depends(require_user)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    row = await session.execute(select(Order).where(Order.id == order_id))
    order = row.scalar_one_or_none()
    if not order:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="order not found")
    if order.user_id != claims["sub"] and claims.get("role") != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="not your order")
    if order.status not in {"completed", "delivered"}:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="returns allowed only for completed orders")

    existing_row = await session.execute(
        select(ReturnRequest).where(
            ReturnRequest.order_id == order_id,
            ReturnRequest.user_id == order.user_id,
            ReturnRequest.status.in_(["requested", "approved"]),
        )
    )
    existing = existing_row.scalar_one_or_none()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="active return request already exists")

    request = ReturnRequest(order_id=order_id, user_id=order.user_id, reason=payload.reason.strip(), status="requested")
    session.add(request)
    await session.commit()
    await session.refresh(request)
    return {
        "_id": request.id,
        "orderId": request.order_id,
        "userId": request.user_id,
        "reason": request.reason,
        "status": request.status,
        "createdAt": request.created_at.isoformat() if request.created_at else None,
    }


@router.get("/returns")
async def list_return_requests(
    claims: Annotated[dict, Depends(require_user)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    stmt = select(ReturnRequest).order_by(ReturnRequest.created_at.desc())
    if claims.get("role") != "admin":
        stmt = stmt.where(ReturnRequest.user_id == claims["sub"])
    rows = (await session.execute(stmt)).scalars().all()
    return {
        "returns": [
            {
                "_id": r.id,
                "orderId": r.order_id,
                "userId": r.user_id,
                "reason": r.reason,
                "status": r.status,
                "createdAt": r.created_at.isoformat() if r.created_at else None,
                "resolvedAt": r.resolved_at.isoformat() if r.resolved_at else None,
            }
            for r in rows
        ]
    }


@router.put("/returns/{return_id}")
async def update_return_request_status(
    return_id: str,
    payload: ReturnStatusIn,
    _admin: Annotated[dict, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    row = await session.execute(select(ReturnRequest).where(ReturnRequest.id == return_id))
    request = row.scalar_one_or_none()
    if not request:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="return request not found")

    new_status = payload.status.strip().lower()
    if new_status not in {"approved", "rejected", "received"}:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid return status")

    request.status = new_status
    request.resolved_at = datetime.now(timezone.utc) if new_status in {"approved", "rejected", "received"} else None
    await session.commit()
    return {
        "_id": request.id,
        "orderId": request.order_id,
        "userId": request.user_id,
        "reason": request.reason,
        "status": request.status,
        "createdAt": request.created_at.isoformat() if request.created_at else None,
        "resolvedAt": request.resolved_at.isoformat() if request.resolved_at else None,
    }


@router.get("/{order_id}/invoice")
async def get_invoice_for_order(
    order_id: str,
    claims: Annotated[dict, Depends(require_user)],
    session: Annotated[AsyncSession, Depends(_session)],
):
    row = await session.execute(select(Order).where(Order.id == order_id))
    order = row.scalar_one_or_none()
    if not order:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="order not found")
    if claims.get("role") != "admin" and order.user_id != claims["sub"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="not your order")
    return {
        "invoice": _invoice_payload(order, claims),
        "order": _serialize(order),
    }

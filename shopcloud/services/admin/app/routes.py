"""Admin HTTP routes.

Every route requires a valid admin JWT (Depends(current_admin)).
"""
from fastapi import APIRouter, Depends, Query

from app.deps import current_admin, get_sessionmaker, get_settings
from app.models import (
    OrderDetail,
    PagedCustomers,
    PagedOrders,
    UpdateOrderStatusRequest,
)
from app.repository import AdminRepository
from app.settings import AdminSettings
from libs.auth import CognitoUser
from libs.errors import NotFoundError
from libs.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", summary="Quick dashboard stats")
async def stats(
    _admin: CognitoUser = Depends(current_admin),
    sessionmaker=Depends(get_sessionmaker),
):
    async with sessionmaker() as session:
        repo = AdminRepository(session)
        return await repo.order_stats()


# ---- orders ----

@router.get("/orders", response_model=PagedOrders, summary="List all orders")
async def list_orders(
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _admin: CognitoUser = Depends(current_admin),
    sessionmaker=Depends(get_sessionmaker),
    settings: AdminSettings = Depends(get_settings),
):
    page_size = min(page_size, settings.max_page_size)
    offset = (page - 1) * page_size
    async with sessionmaker() as session:
        repo = AdminRepository(session)
        return await repo.list_orders(status=status, offset=offset, limit=page_size)


@router.get(
    "/orders/{order_id}",
    response_model=OrderDetail,
    summary="Get one order with items",
)
async def get_order(
    order_id: str,
    _admin: CognitoUser = Depends(current_admin),
    sessionmaker=Depends(get_sessionmaker),
):
    async with sessionmaker() as session:
        repo = AdminRepository(session)
        order = await repo.get_order(order_id)
        if order is None:
            raise NotFoundError(f"Order {order_id} not found")
        return order


@router.patch(
    "/orders/{order_id}/status",
    response_model=OrderDetail,
    summary="Change an order's status (e.g. mark fulfilled)",
)
async def update_order_status(
    order_id: str,
    request: UpdateOrderStatusRequest,
    admin: CognitoUser = Depends(current_admin),
    sessionmaker=Depends(get_sessionmaker),
):
    async with sessionmaker() as session:
        repo = AdminRepository(session)
        ok = await repo.update_order_status(order_id, request.status)
        if not ok:
            raise NotFoundError(f"Order {order_id} not found")
        await session.commit()
        # Re-read so the response reflects committed state with eager-loaded relations
        updated = await repo.get_order(order_id)
        logger.info(
            "order status updated",
            extra={
                "order_id": order_id,
                "new_status": request.status,
                "admin": admin.sub,
            },
        )
        return updated


# ---- customers ----

@router.get("/customers", response_model=PagedCustomers, summary="List customers")
async def list_customers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _admin: CognitoUser = Depends(current_admin),
    sessionmaker=Depends(get_sessionmaker),
    settings: AdminSettings = Depends(get_settings),
):
    page_size = min(page_size, settings.max_page_size)
    offset = (page - 1) * page_size
    async with sessionmaker() as session:
        repo = AdminRepository(session)
        return await repo.list_customers(offset=offset, limit=page_size)

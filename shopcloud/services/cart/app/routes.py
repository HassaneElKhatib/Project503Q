"""Cart HTTP routes.

Cart is per-customer, identified by the JWT subject. Customers cannot read
or modify other customers' carts because we always derive customer_id
from the verified token, never from the request body or path.
"""
from fastapi import APIRouter, Depends, Header, status
from fastapi.responses import Response

from app.catalog_client import CatalogClient
from app.deps import get_catalog_client, get_repository, get_settings, get_verifier
from app.models import AddItemRequest, Cart, UpdateQuantityRequest
from app.repository import CartRepository
from app.settings import CartSettings
from libs.auth import CognitoUser, CognitoVerifier
from libs.errors import NotFoundError, ValidationError
from libs.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/cart", tags=["cart"])


async def current_user(
    authorization: str | None = Header(default=None),
    verifier: CognitoVerifier = Depends(get_verifier),
) -> CognitoUser:
    """Dependency: validate Bearer token and return the user."""
    return await verifier.require_user(authorization)


@router.get("", response_model=Cart, summary="Get the current customer's cart")
async def get_cart(
    user: CognitoUser = Depends(current_user),
    repo: CartRepository = Depends(get_repository),
) -> Cart:
    return await repo.get(user.sub)


@router.post(
    "/items",
    response_model=Cart,
    status_code=status.HTTP_200_OK,
    summary="Add a product to the cart",
)
async def add_item(
    request: AddItemRequest,
    user: CognitoUser = Depends(current_user),
    repo: CartRepository = Depends(get_repository),
    catalog: CatalogClient = Depends(get_catalog_client),
    settings: CartSettings = Depends(get_settings),
) -> Cart:
    cart = await repo.get(user.sub)

    existing = next(
        (i for i in cart.items if i.product_id == request.product_id), None
    )
    if existing:
        new_qty = existing.quantity + request.quantity
        if new_qty > settings.max_quantity_per_item:
            raise ValidationError(
                f"Quantity exceeds maximum of {settings.max_quantity_per_item}"
            )
        existing.quantity = new_qty
    else:
        if len(cart.items) >= settings.max_items_per_cart:
            raise ValidationError(
                f"Cart cannot contain more than {settings.max_items_per_cart} distinct items"
            )
        new_item = await catalog.fetch_product_for_cart(
            request.product_id, request.quantity
        )
        cart.items.append(new_item)

    await repo.save(cart)
    logger.info(
        "cart updated",
        extra={
            "customer_id": user.sub,
            "product_id": request.product_id,
            "item_count": cart.item_count,
        },
    )
    return cart


@router.patch(
    "/items/{product_id}",
    response_model=Cart,
    summary="Update an item's quantity (0 to remove)",
)
async def update_quantity(
    product_id: str,
    request: UpdateQuantityRequest,
    user: CognitoUser = Depends(current_user),
    repo: CartRepository = Depends(get_repository),
) -> Cart:
    cart = await repo.get(user.sub)
    item = next((i for i in cart.items if i.product_id == product_id), None)
    if item is None:
        raise NotFoundError(f"Product {product_id} not in cart")

    if request.quantity == 0:
        cart.items = [i for i in cart.items if i.product_id != product_id]
    else:
        item.quantity = request.quantity

    await repo.save(cart)
    return cart


@router.delete(
    "/items/{product_id}",
    response_model=Cart,
    summary="Remove an item entirely",
)
async def remove_item(
    product_id: str,
    user: CognitoUser = Depends(current_user),
    repo: CartRepository = Depends(get_repository),
) -> Cart:
    cart = await repo.get(user.sub)
    before = len(cart.items)
    cart.items = [i for i in cart.items if i.product_id != product_id]
    if len(cart.items) == before:
        raise NotFoundError(f"Product {product_id} not in cart")

    await repo.save(cart)
    return cart


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Empty the cart entirely",
)
async def clear_cart(
    user: CognitoUser = Depends(current_user),
    repo: CartRepository = Depends(get_repository),
) -> Response:
    await repo.delete(user.sub)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

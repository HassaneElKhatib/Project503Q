"""Checkout routes."""
from fastapi import APIRouter, Depends, status

from app.deps import current_user, get_service
from app.models import CheckoutRequest, CheckoutResponse
from app.service import CheckoutService
from libs.auth import CognitoUser
from libs.errors import ValidationError

router = APIRouter(tags=["checkout"])


@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Place an order from the current cart",
    description=(
        "Reads the customer's cart, writes the order, and queues an invoice. "
        "Returns 202 Accepted - the invoice email arrives later."
    ),
)
async def checkout(
    request: CheckoutRequest,
    user: CognitoUser = Depends(current_user),
    service: CheckoutService = Depends(get_service),
) -> CheckoutResponse:
    if not user.email:
        raise ValidationError("Customer token has no email claim")

    return await service.checkout(
        customer_id=user.sub,
        customer_email=user.email,
        idempotency_key=request.idempotency_key,
        metadata=request.metadata,
    )

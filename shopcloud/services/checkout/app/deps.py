"""Checkout dependencies."""
from fastapi import Depends, Header, Request

from app.service import CheckoutService
from app.settings import CheckoutSettings
from libs.auth import CognitoUser, CognitoVerifier


def get_settings(request: Request) -> CheckoutSettings:
    return request.app.state.settings


def get_service(request: Request) -> CheckoutService:
    return request.app.state.service


def get_verifier(request: Request) -> CognitoVerifier:
    return request.app.state.verifier


async def current_user(
    authorization: str | None = Header(default=None),
    verifier: CognitoVerifier = Depends(get_verifier),
) -> CognitoUser:
    return await verifier.require_user(authorization)

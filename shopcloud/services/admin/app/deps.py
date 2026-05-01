"""Admin dependencies.

The current_admin dependency is the security boundary for this service.
Two checks: token verifies (JWT signature + issuer + audience match the
admin pool), and the user's groups include the required admin group.
"""
from fastapi import Depends, Header, HTTPException, Request, status

from app.settings import AdminSettings
from libs.auth import CognitoUser, CognitoVerifier


def get_settings(request: Request) -> AdminSettings:
    return request.app.state.settings


def get_verifier(request: Request) -> CognitoVerifier:
    return request.app.state.verifier


def get_sessionmaker(request: Request):
    return request.app.state.sessionmaker


async def current_admin(
    authorization: str | None = Header(default=None),
    verifier: CognitoVerifier = Depends(get_verifier),
    settings: AdminSettings = Depends(get_settings),
) -> CognitoUser:
    """Validate token AND enforce admin group membership."""
    user = await verifier.require_user(authorization)
    if settings.required_admin_group not in user.groups:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Admin group '{settings.required_admin_group}' required",
        )
    return user

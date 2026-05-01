"""FastAPI deps for the auth service."""
from fastapi import HTTPException, Request, status

from app.admin_pool_settings import AdminPoolAuthSettings
from app.cognito import CognitoClient
from app.settings import AuthSettings
from app.state import StateSigner
from libs.auth import CognitoVerifier


def get_settings(request: Request) -> AuthSettings:
    return request.app.state.settings


def get_cognito_client(request: Request) -> CognitoClient:
    return request.app.state.cognito_client


def get_verifier(request: Request) -> CognitoVerifier:
    return request.app.state.verifier


def get_state_signer(request: Request) -> StateSigner:
    return request.app.state.state_signer


def get_admin_settings(request: Request) -> AdminPoolAuthSettings:
    settings = getattr(request.app.state, "admin_settings", None)
    if settings is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin OAuth is not configured",
        )
    return settings


def get_admin_cognito_client(request: Request) -> CognitoClient:
    return request.app.state.admin_cognito_client


def get_admin_state_signer(request: Request) -> StateSigner:
    return request.app.state.admin_state_signer

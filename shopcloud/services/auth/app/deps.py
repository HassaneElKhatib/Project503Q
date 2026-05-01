"""FastAPI deps for the auth service."""
from fastapi import Request

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

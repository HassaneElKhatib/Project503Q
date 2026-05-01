"""FastAPI dependencies for cart."""
from fastapi import Request

from app.catalog_client import CatalogClient
from app.repository import CartRepository
from app.settings import CartSettings
from libs.auth import CognitoVerifier


def get_settings(request: Request) -> CartSettings:
    return request.app.state.settings


def get_repository(request: Request) -> CartRepository:
    return request.app.state.repository


def get_catalog_client(request: Request) -> CatalogClient:
    return request.app.state.catalog_client


def get_verifier(request: Request) -> CognitoVerifier:
    return request.app.state.verifier

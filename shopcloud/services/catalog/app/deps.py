"""FastAPI dependency providers.

We construct the repo + cache once at startup and stash them on app.state.
Handlers ask for them via Depends() so tests can inject fakes.
"""
from fastapi import Request

from app.cache import ProductCache
from app.repository import ProductRepository
from app.settings import CatalogSettings


def get_settings(request: Request) -> CatalogSettings:
    return request.app.state.settings


def get_repository(request: Request) -> ProductRepository:
    return request.app.state.repository


def get_cache(request: Request) -> ProductCache:
    return request.app.state.cache

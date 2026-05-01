"""Shared test fixtures."""
import os
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

# Set env BEFORE the app imports settings
os.environ["SERVICE_NAME"] = "catalog"
os.environ["ENVIRONMENT"] = "test"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["PRODUCTS_JSON_PATH"] = str(
    Path(__file__).parent.parent / "data" / "products.json"
)
# No REDIS_URL -> caching disabled in tests by default


@pytest.fixture
async def client():
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Trigger lifespan startup
        async with app.router.lifespan_context(app):
            yield ac

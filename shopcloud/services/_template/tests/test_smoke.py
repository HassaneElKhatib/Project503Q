"""Smoke test for the template service."""
import os

import pytest
from httpx import ASGITransport, AsyncClient

# Set required env vars before importing the app
os.environ.setdefault("SERVICE_NAME", "template")
os.environ.setdefault("ENVIRONMENT", "test")


@pytest.fixture
async def client():
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def test_root(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "template"


async def test_liveness(client):
    response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_readiness_no_checks(client):
    """With no readiness checks registered, ready returns ok."""
    response = await client.get("/health/ready")
    assert response.status_code == 200


async def test_metrics_exposed(client):
    response = await client.get("/metrics")
    assert response.status_code == 200
    # Prometheus exposition format starts with HELP/TYPE comments
    assert "# HELP" in response.text


async def test_request_id_echoed(client):
    response = await client.get("/", headers={"X-Request-ID": "test-123"})
    assert response.headers["X-Request-ID"] == "test-123"


async def test_request_id_generated(client):
    response = await client.get("/")
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0

"""Shared fixtures for cart tests."""
import base64
import os
import time

import pytest
import respx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient
from jose import jwt as jose_jwt

# Env BEFORE app import
os.environ["SERVICE_NAME"] = "cart"
os.environ["ENVIRONMENT"] = "test"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["REDIS_URL"] = "redis://fake"  # fakeredis intercepts this
os.environ["COGNITO_USER_POOL_ID"] = "us-east-1_TestPool"
os.environ["COGNITO_APP_CLIENT_ID"] = "test-client-id"
os.environ["COGNITO_REGION"] = "us-east-1"
os.environ["CATALOG_BASE_URL"] = "http://catalog.test"


@pytest.fixture(scope="session")
def rsa_keypair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()

    pn = private_key.public_key().public_numbers()

    def _b64(n: int) -> str:
        b = n.to_bytes((n.bit_length() + 7) // 8, "big")
        return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

    return {
        "private_pem": private_pem,
        "public_jwk": {
            "kty": "RSA",
            "kid": "test-kid-1",
            "use": "sig",
            "alg": "RS256",
            "n": _b64(pn.n),
            "e": _b64(pn.e),
        },
    }


@pytest.fixture
def mint_token(rsa_keypair):
    """Mint a customer JWT for tests."""
    def _mint(*, sub: str = "customer-1", email: str = "c@example.com",
             groups: list[str] | None = None, expires_in: int = 3600) -> str:
        now = int(time.time())
        return jose_jwt.encode(
            {
                "sub": sub,
                "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_TestPool",
                "iat": now,
                "exp": now + expires_in,
                "token_use": "access",
                "client_id": "test-client-id",
                "username": email,
                "cognito:groups": groups or [],
            },
            rsa_keypair["private_pem"],
            algorithm="RS256",
            headers={"kid": "test-kid-1"},
        )
    return _mint


@pytest.fixture
async def client(rsa_keypair, monkeypatch):
    """ASGI client. Mocks JWKS and catalog. Patches Redis to fakeredis."""
    import fakeredis.aioredis

    fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    # Patch Redis.from_url to return our fake client
    from redis import asyncio as redis_async

    monkeypatch.setattr(redis_async.Redis, "from_url", lambda *a, **kw: fake_redis)

    with respx.mock(assert_all_called=False) as respx_mock:
        # Mock JWKS
        respx_mock.get(
            "https://cognito-idp.us-east-1.amazonaws.com/"
            "us-east-1_TestPool/.well-known/jwks.json"
        ).respond(json={"keys": [rsa_keypair["public_jwk"]]})

        # Mock catalog liveness (used by readiness check)
        respx_mock.get("http://catalog.test/health/live").respond(
            status_code=200, json={"status": "ok"}
        )

        from app.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            async with app.router.lifespan_context(app):
                yield ac, respx_mock, fake_redis

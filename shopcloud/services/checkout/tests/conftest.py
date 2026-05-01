"""Fixtures for checkout tests.

We use SQLite (via aiosqlite) for tests so they need no external Postgres.
The schema is created via SQLAlchemy metadata.create_all(). Production uses
real Postgres via Alembic migrations.

The shared models in libs/db/models.py use only cross-database types
(String for UUIDs with Python defaults, JSON for arrays/objects), so the
same code works on SQLite and Postgres.

We also patch AwsSqsPublisher with InMemorySqsPublisher so checkout never
hits real AWS. Tests assert messages were published, content is correct,
and that publish failures are surfaced sanely.
"""
import base64
import json
import os
import time

import pytest
import respx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient
from jose import jwt as jose_jwt

# Env BEFORE app import
os.environ["SERVICE_NAME"] = "checkout"
os.environ["ENVIRONMENT"] = "test"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://fake"
os.environ["INVOICE_QUEUE_URL"] = "https://sqs.test/123/invoice"
os.environ["COGNITO_USER_POOL_ID"] = "us-east-1_TestPool"
os.environ["COGNITO_APP_CLIENT_ID"] = "test-client-id"
os.environ["COGNITO_REGION"] = "us-east-1"


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
            "kty": "RSA", "kid": "test-kid-1", "use": "sig", "alg": "RS256",
            "n": _b64(pn.n), "e": _b64(pn.e),
        },
    }


@pytest.fixture
def mint_token(rsa_keypair):
    """Mint a customer token. Email is required - checkout uses it."""
    def _mint(*, sub: str = "customer-1", email: str = "c@example.com",
             expires_in: int = 3600) -> str:
        now = int(time.time())
        return jose_jwt.encode(
            {
                "sub": sub,
                "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_TestPool",
                "iat": now, "exp": now + expires_in,
                "token_use": "access",
                "client_id": "test-client-id",
                "username": email,
                "email": email,
            },
            rsa_keypair["private_pem"], algorithm="RS256",
            headers={"kid": "test-kid-1"},
        )
    return _mint


@pytest.fixture
async def client(rsa_keypair, monkeypatch):
    """ASGI client with SQLite DB, fakeredis, in-memory SQS."""
    import fakeredis.aioredis

    fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    from redis import asyncio as redis_async
    monkeypatch.setattr(redis_async.Redis, "from_url", lambda *a, **kw: fake_redis)

    # Replace AwsSqsPublisher with InMemorySqsPublisher
    from libs.aws import InMemorySqsPublisher
    fake_sqs = InMemorySqsPublisher()
    import app.main as app_main_module
    monkeypatch.setattr(app_main_module, "AwsSqsPublisher", lambda *a, **kw: fake_sqs)

    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.get(
            "https://cognito-idp.us-east-1.amazonaws.com/"
            "us-east-1_TestPool/.well-known/jwks.json"
        ).respond(json={"keys": [rsa_keypair["public_jwk"]]})

        from app.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            async with app.router.lifespan_context(app):
                # Create schema in SQLite
                from libs.db import Base
                async with app.state.engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                yield ac, respx_mock, fake_redis, fake_sqs, app


def make_cart_payload(items: list[dict]) -> str:
    """Serialize a cart for fakeredis."""
    return json.dumps({"customer_id": "x", "items": items, "currency": "USD"})


async def seed_inventory(app, products: list[tuple[str, str, int, int]]) -> None:
    """Insert (product_id, name, price_cents, stock) rows.

    Each row creates a Product + Inventory pair so checkout's reserve_inventory
    can actually decrement.
    """
    from libs.db import Inventory, Product

    async with app.state.sessionmaker() as session:
        for product_id, name, price_cents, stock in products:
            session.add(
                Product(
                    id=product_id,
                    sku=f"SKU-{product_id}",
                    name=name,
                    description="seeded for tests",
                    category="books",
                    price_cents=price_cents,
                    currency="USD",
                    image_url="",
                    is_active=True,
                )
            )
            session.add(Inventory(product_id=product_id, stock=stock, reserved=0))
        await session.commit()


async def seed_cart(redis_client, customer_id: str, items: list[dict]) -> None:
    """Write a cart blob to fakeredis with the same key format cart service uses."""
    payload = json.dumps(
        {
            "customer_id": customer_id,
            "items": items,
            "currency": "USD",
        }
    )
    await redis_client.set(f"cart:{customer_id}", payload)

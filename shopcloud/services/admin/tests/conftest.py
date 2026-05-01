"""Admin test fixtures."""
import base64
import os
import time

import pytest
import respx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient
from jose import jwt as jose_jwt

# Env BEFORE app import - notice we use a DIFFERENT pool ID than customer services
os.environ["SERVICE_NAME"] = "admin"
os.environ["ENVIRONMENT"] = "test"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["COGNITO_USER_POOL_ID"] = "us-east-1_AdminPool"      # admin pool
os.environ["COGNITO_APP_CLIENT_ID"] = "admin-client-id"
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
def mint_admin_token(rsa_keypair):
    """Mint a token from the ADMIN pool."""
    def _mint(*, sub: str = "admin-1", groups: list[str] | None = None,
             pool: str = "us-east-1_AdminPool",
             client_id: str = "admin-client-id",
             expires_in: int = 3600) -> str:
        now = int(time.time())
        return jose_jwt.encode(
            {
                "sub": sub,
                "iss": f"https://cognito-idp.us-east-1.amazonaws.com/{pool}",
                "iat": now, "exp": now + expires_in,
                "token_use": "access",
                "client_id": client_id,
                "username": f"{sub}@admin.test",
                "cognito:groups": groups if groups is not None else ["admin"],
            },
            rsa_keypair["private_pem"], algorithm="RS256",
            headers={"kid": "test-kid-1"},
        )
    return _mint


@pytest.fixture
async def client(rsa_keypair):
    """ASGI client with SQLite + mocked admin JWKS."""
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.get(
            "https://cognito-idp.us-east-1.amazonaws.com/"
            "us-east-1_AdminPool/.well-known/jwks.json"
        ).respond(json={"keys": [rsa_keypair["public_jwk"]]})

        from app.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            async with app.router.lifespan_context(app):
                from libs.db import Base
                async with app.state.engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                yield ac, respx_mock, app


async def seed_data(app):
    """Insert some customers and orders so list endpoints have content."""

    from libs.db import Customer, Invoice, Order, OrderItem, Product, Inventory

    async with app.state.sessionmaker() as session:
        # Products + inventory
        for i in range(1, 4):
            session.add(
                Product(
                    id=f"p-{i}",
                    sku=f"SKU-{i}",
                    name=f"Product {i}",
                    description="x",
                    category="books",
                    price_cents=1000 * i,
                    currency="USD",
                    image_url="",
                    is_active=True,
                )
            )
            session.add(Inventory(product_id=f"p-{i}", stock=10, reserved=0))

        # Customers
        alice = Customer(id="alice", email="alice@test.com", full_name="Alice A")
        bob = Customer(id="bob", email="bob@test.com")
        session.add(alice)
        session.add(bob)
        await session.flush()

        # Orders for alice (2) and bob (1)
        for i, (cust, total) in enumerate([("alice", 2000), ("alice", 1500), ("bob", 3000)]):
            order = Order(
                customer_id=cust,
                customer_email=f"{cust}@test.com",
                status="confirmed",
                total_cents=total,
                currency="USD",
            )
            order.items.append(
                OrderItem(
                    product_id="p-1",
                    product_name="Product 1",
                    unit_price_cents=total,
                    quantity=1,
                )
            )
            order.invoice = Invoice(status="queued")
            session.add(order)

        await session.commit()

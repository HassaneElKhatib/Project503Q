"""Shared auth test fixtures.

The Cognito verifier needs a real RSA-signed JWT to test against. We generate
a keypair at test setup, expose a fake JWKS endpoint via respx, and mint
tokens using the same key. This exercises the real signature-verification
path without depending on an external Cognito.
"""
import os
import time
from typing import Any

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient
from jose import jwt

# ---- env BEFORE any app imports ----
os.environ["SERVICE_NAME"] = "auth"
os.environ["ENVIRONMENT"] = "test"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["COGNITO_USER_POOL_ID"] = "us-east-1_TestPool"
os.environ["COGNITO_APP_CLIENT_ID"] = "test-client-id"
os.environ["COGNITO_REGION"] = "us-east-1"
os.environ["COGNITO_DOMAIN"] = "test.auth.us-east-1.amazoncognito.com"
os.environ["CALLBACK_URL"] = "https://app.test/auth/callback"
os.environ["LOGOUT_REDIRECT_URL"] = "https://app.test/"
os.environ["COOKIE_SECURE"] = "false"
os.environ["STATE_SIGNING_KEY"] = "a" * 48


# ---- RSA keypair for signing test JWTs ----

@pytest.fixture(scope="session")
def rsa_keypair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_numbers = private_key.public_key().public_numbers()

    # Build the JWK representation Cognito would publish
    import base64

    def _b64(n: int) -> str:
        byte_len = (n.bit_length() + 7) // 8
        return (
            base64.urlsafe_b64encode(n.to_bytes(byte_len, "big"))
            .rstrip(b"=")
            .decode()
        )

    public_jwk = {
        "kty": "RSA",
        "kid": "test-kid-1",
        "use": "sig",
        "alg": "RS256",
        "n": _b64(public_numbers.n),
        "e": _b64(public_numbers.e),
    }

    return {
        "private_pem": private_pem.decode(),
        "public_jwk": public_jwk,
    }


@pytest.fixture(scope="session")
def jwks_payload(rsa_keypair) -> dict[str, Any]:
    return {"keys": [rsa_keypair["public_jwk"]]}


def _mint_token(
    rsa_keypair: dict,
    *,
    token_use: str = "access",
    sub: str = "user-123",
    email: str = "test@example.com",
    username: str = "tester",
    groups: list[str] | None = None,
    issuer_override: str | None = None,
    expires_in: int = 3600,
    audience_override: str | None = None,
) -> str:
    now = int(time.time())
    issuer = issuer_override or (
        "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_TestPool"
    )
    claims = {
        "sub": sub,
        "iss": issuer,
        "iat": now,
        "exp": now + expires_in,
        "token_use": token_use,
        "cognito:username": username,
        "cognito:groups": groups or [],
    }
    if token_use == "id":
        claims["email"] = email
        claims["aud"] = audience_override or "test-client-id"
    else:  # access
        claims["client_id"] = audience_override or "test-client-id"

    return jwt.encode(
        claims,
        rsa_keypair["private_pem"],
        algorithm="RS256",
        headers={"kid": "test-kid-1"},
    )


@pytest.fixture
def mint_token(rsa_keypair):
    """Returns a callable that mints JWTs with custom claims."""
    def _mint(**kwargs: Any) -> str:
        return _mint_token(rsa_keypair, **kwargs)
    return _mint


# ---- HTTP client against the auth app ----

@pytest.fixture
async def client(jwks_payload):
    """ASGI client with the JWKS endpoint mocked via respx."""
    import respx

    with respx.mock(assert_all_called=False) as respx_mock:
        # Mock the JWKS endpoint Cognito would expose
        respx_mock.get(
            "https://cognito-idp.us-east-1.amazonaws.com/"
            "us-east-1_TestPool/.well-known/jwks.json"
        ).respond(json=jwks_payload)

        from app.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            async with app.router.lifespan_context(app):
                yield ac, respx_mock

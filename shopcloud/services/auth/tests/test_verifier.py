"""Tests for the shared CognitoVerifier.

These exercise the real RS256 signature path against a JWKS we control.
"""
import time

import pytest
import respx
from fastapi import HTTPException

from libs.auth import CognitoVerifier
from libs.config import CognitoSettings


@pytest.fixture
def verifier_settings() -> CognitoSettings:
    return CognitoSettings(
        cognito_user_pool_id="us-east-1_TestPool",
        cognito_app_client_id="test-client-id",
        cognito_region="us-east-1",
    )


@pytest.fixture
def verifier(verifier_settings, jwks_payload):
    """A verifier with the JWKS endpoint mocked."""
    with respx.mock(assert_all_called=False) as mock:
        mock.get(verifier_settings.jwks_url).respond(json=jwks_payload)
        v = CognitoVerifier(verifier_settings)
        yield v


def test_verify_valid_access_token(verifier, mint_token):
    token = mint_token(token_use="access")
    user = verifier.verify_token(token)
    assert user.sub == "user-123"
    assert user.token_use == "access"
    assert user.is_admin is False


def test_verify_valid_id_token(verifier, mint_token):
    token = mint_token(token_use="id", email="alice@example.com")
    user = verifier.verify_token(token)
    assert user.email == "alice@example.com"
    assert user.token_use == "id"


def test_admin_group_recognised(verifier, mint_token):
    token = mint_token(groups=["admin"])
    user = verifier.verify_token(token)
    assert user.is_admin is True


def test_garbage_token_rejected(verifier):
    with pytest.raises(HTTPException) as exc:
        verifier.verify_token("not-a-jwt")
    assert exc.value.status_code == 401


def test_expired_token_rejected(verifier, mint_token):
    token = mint_token(expires_in=-100)  # already expired
    with pytest.raises(HTTPException) as exc:
        verifier.verify_token(token)
    assert exc.value.status_code == 401
    assert "expired" in exc.value.detail.lower()


def test_wrong_issuer_rejected(verifier, mint_token):
    token = mint_token(
        issuer_override="https://cognito-idp.us-east-1.amazonaws.com/us-east-1_OtherPool"
    )
    with pytest.raises(HTTPException) as exc:
        verifier.verify_token(token)
    assert exc.value.status_code == 401
    assert "issuer" in exc.value.detail.lower()


def test_wrong_audience_rejected_on_id_token(verifier, mint_token):
    token = mint_token(token_use="id", audience_override="some-other-client")
    with pytest.raises(HTTPException) as exc:
        verifier.verify_token(token)
    assert exc.value.status_code == 401
    assert "audience" in exc.value.detail.lower()


def test_wrong_client_id_rejected_on_access_token(verifier, mint_token):
    token = mint_token(token_use="access", audience_override="some-other-client")
    with pytest.raises(HTTPException) as exc:
        verifier.verify_token(token)
    assert exc.value.status_code == 401
    assert "client_id" in exc.value.detail.lower()


def test_unknown_kid_triggers_jwks_refresh(verifier_settings, mint_token, rsa_keypair):
    """If a token's kid isn't in our cache, we should refresh JWKS once."""
    from jose import jwt as jose_jwt

    token = jose_jwt.encode(
        {
            "sub": "u",
            "iss": verifier_settings.issuer,
            "exp": int(time.time()) + 60,
            "iat": int(time.time()),
            "token_use": "access",
            "client_id": "test-client-id",
        },
        rsa_keypair["private_pem"],
        algorithm="RS256",
        headers={"kid": "unknown-kid"},
    )

    with respx.mock(assert_all_called=False) as mock:
        # JWKS only contains test-kid-1, not unknown-kid
        mock.get(verifier_settings.jwks_url).respond(
            json={"keys": [rsa_keypair["public_jwk"]]}
        )
        v = CognitoVerifier(verifier_settings)
        with pytest.raises(HTTPException) as exc:
            v.verify_token(token)
        assert "signing key" in exc.value.detail.lower()


def test_token_signed_with_different_key_rejected(
    verifier_settings, jwks_payload, rsa_keypair
):
    """A JWT signed by an attacker's key must not pass even with a matching kid."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa as rsa_mod
    from jose import jwt as jose_jwt

    # Generate a different RSA key
    attacker_key = rsa_mod.generate_private_key(public_exponent=65537, key_size=2048)
    attacker_pem = attacker_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()

    bad_token = jose_jwt.encode(
        {
            "sub": "attacker",
            "iss": verifier_settings.issuer,
            "exp": int(time.time()) + 60,
            "iat": int(time.time()),
            "token_use": "access",
            "client_id": "test-client-id",
        },
        attacker_pem,
        algorithm="RS256",
        headers={"kid": "test-kid-1"},  # matches our published kid!
    )

    with respx.mock(assert_all_called=False) as mock:
        mock.get(verifier_settings.jwks_url).respond(json=jwks_payload)
        v = CognitoVerifier(verifier_settings)
        with pytest.raises(HTTPException) as exc:
            v.verify_token(bad_token)
        assert exc.value.status_code == 401

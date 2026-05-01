"""Unit tests for the OAuth state signer."""
import time

import pytest

from app.state import StateError, StateSigner


def test_round_trip_recovers_next_url():
    signer = StateSigner(signing_key="x" * 48, ttl_seconds=300)
    token = signer.issue(next_url="/cart")
    assert signer.verify(token) == "/cart"


def test_default_next_url_is_root():
    signer = StateSigner(signing_key="x" * 48)
    token = signer.issue()
    assert signer.verify(token) == "/"


def test_two_issued_tokens_are_different():
    signer = StateSigner(signing_key="x" * 48)
    a = signer.issue("/")
    b = signer.issue("/")
    # Random nonce makes every token unique
    assert a != b


def test_tampered_payload_rejected():
    signer = StateSigner(signing_key="x" * 48)
    token = signer.issue("/checkout")
    payload, sig = token.split(".", 1)
    # Flip a character in the payload
    bad_payload = "A" + payload[1:]
    with pytest.raises(StateError, match="signature"):
        signer.verify(f"{bad_payload}.{sig}")


def test_tampered_signature_rejected():
    signer = StateSigner(signing_key="x" * 48)
    token = signer.issue("/")
    payload, sig = token.split(".", 1)
    with pytest.raises(StateError):
        signer.verify(f"{payload}.AAAAA")


def test_different_key_rejects_token():
    a = StateSigner(signing_key="a" * 48)
    b = StateSigner(signing_key="b" * 48)
    token = a.issue("/")
    with pytest.raises(StateError):
        b.verify(token)


def test_malformed_token_rejected():
    signer = StateSigner(signing_key="x" * 48)
    with pytest.raises(StateError):
        signer.verify("garbage")


def test_short_signing_key_rejected_at_construction():
    with pytest.raises(ValueError):
        StateSigner(signing_key="too-short")


def test_expired_token_rejected(monkeypatch):
    signer = StateSigner(signing_key="x" * 48, ttl_seconds=10)
    token = signer.issue("/")

    # Move clock forward past TTL
    real_time = time.time
    monkeypatch.setattr(time, "time", lambda: real_time() + 60)

    with pytest.raises(StateError, match="expired"):
        signer.verify(token)


def test_url_with_query_params_round_trips():
    signer = StateSigner(signing_key="x" * 48)
    next_url = "/products?category=books&page=2"
    token = signer.issue(next_url=next_url)
    assert signer.verify(token) == next_url

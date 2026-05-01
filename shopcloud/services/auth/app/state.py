"""Signed OAuth state tokens.

The OAuth `state` parameter is round-tripped from /auth/login through Cognito
back to /auth/callback. To prevent CSRF and to verify it really originated
from us, we sign it with HMAC-SHA256 and include a timestamp.

Format: base64url(payload).base64url(signature)
Payload: nonce.timestamp.next_url
"""
import base64
import hashlib
import hmac
import secrets
import time
from urllib.parse import quote, unquote


class StateError(Exception):
    """Raised when an inbound state token fails any verification step."""


class StateSigner:
    def __init__(self, signing_key: str, ttl_seconds: int = 300) -> None:
        if len(signing_key) < 32:
            raise ValueError("State signing key must be at least 32 chars")
        self._key = signing_key.encode("utf-8")
        self._ttl = ttl_seconds

    def _sign(self, payload: bytes) -> str:
        sig = hmac.new(self._key, payload, hashlib.sha256).digest()
        return base64.urlsafe_b64encode(sig).rstrip(b"=").decode("ascii")

    def issue(self, next_url: str = "/") -> str:
        """Generate a fresh signed state token."""
        nonce = secrets.token_urlsafe(16)
        timestamp = str(int(time.time()))
        # next_url is URL-encoded so '.' separator is unambiguous
        encoded_next = quote(next_url, safe="")
        payload = f"{nonce}.{timestamp}.{encoded_next}".encode("utf-8")
        b64_payload = base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")
        signature = self._sign(payload)
        return f"{b64_payload}.{signature}"

    def verify(self, token: str) -> str:
        """Verify a state token and return the next_url. Raises StateError on failure."""
        try:
            b64_payload, signature = token.split(".", 1)
        except ValueError as exc:
            raise StateError("Malformed state token") from exc

        # Re-pad the base64 (we stripped padding when issuing)
        padding = "=" * (-len(b64_payload) % 4)
        try:
            payload = base64.urlsafe_b64decode(b64_payload + padding)
        except Exception as exc:
            raise StateError("Cannot decode state payload") from exc

        expected = self._sign(payload)
        if not hmac.compare_digest(expected, signature):
            raise StateError("State signature mismatch")

        try:
            nonce, timestamp_str, encoded_next = payload.decode("utf-8").split(".", 2)
        except ValueError as exc:
            raise StateError("Malformed state payload") from exc

        try:
            timestamp = int(timestamp_str)
        except ValueError as exc:
            raise StateError("Invalid state timestamp") from exc

        age = int(time.time()) - timestamp
        if age < 0:
            raise StateError("State timestamp from the future")
        if age > self._ttl:
            raise StateError("State expired")

        return unquote(encoded_next)

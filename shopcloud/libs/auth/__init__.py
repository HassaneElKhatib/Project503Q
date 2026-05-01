"""Cognito JWT verifier.

Validates JWTs issued by AWS Cognito. Caches the JWKS keys in memory and
refreshes on key-not-found (handles key rotation transparently).

Usage in a service:

    from fastapi import Depends, FastAPI
    from libs.auth import CognitoVerifier, CognitoUser

    verifier = CognitoVerifier(settings)
    app = FastAPI()

    @app.get("/me")
    async def me(user: CognitoUser = Depends(verifier.require_user)):
        return {"sub": user.sub, "email": user.email}
"""
import time
from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import Header, HTTPException, status
from jose import jwk, jwt
from jose.utils import base64url_decode

from libs.config import CognitoSettings
from libs.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CognitoUser:
    """Verified user identity extracted from a Cognito JWT."""

    sub: str  # Cognito user ID
    email: str | None
    username: str | None
    groups: list[str]
    token_use: str  # "access" or "id"
    raw_claims: dict[str, Any]

    @property
    def is_admin(self) -> bool:
        return "admin" in self.groups


class CognitoVerifier:
    """Verifies Cognito JWTs against the user pool's JWKS."""

    # Refresh keys at most this often when we get a key-not-found
    _MIN_REFRESH_INTERVAL = 60  # seconds

    def __init__(self, settings: CognitoSettings) -> None:
        self._settings = settings
        self._keys: dict[str, dict] = {}
        self._last_refresh: float = 0.0

    def _refresh_keys(self) -> None:
        """Download JWKS from Cognito and cache by kid."""
        now = time.time()
        if now - self._last_refresh < self._MIN_REFRESH_INTERVAL and self._keys:
            return

        logger.info("refreshing cognito jwks", extra={"url": self._settings.jwks_url})
        response = httpx.get(self._settings.jwks_url, timeout=5.0)
        response.raise_for_status()
        jwks = response.json()
        self._keys = {key["kid"]: key for key in jwks["keys"]}
        self._last_refresh = now

    def _get_key(self, kid: str) -> dict:
        if kid not in self._keys:
            self._refresh_keys()
        if kid not in self._keys:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unknown signing key",
            )
        return self._keys[kid]

    def verify_token(self, token: str) -> CognitoUser:
        """Verify a JWT and return the parsed user.

        Raises HTTPException(401) on any failure.
        """
        try:
            self._refresh_keys()
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            if not kid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token missing kid",
                )

            key_data = self._get_key(kid)
            public_key = jwk.construct(key_data)

            # Verify signature manually so we control error messages
            message, encoded_sig = token.rsplit(".", 1)
            decoded_sig = base64url_decode(encoded_sig.encode())
            if not public_key.verify(message.encode(), decoded_sig):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid signature",
                )

            # Decode claims (signature already verified above)
            claims = jwt.get_unverified_claims(token)

            # Validate expiry
            if claims.get("exp", 0) < time.time():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired",
                )

            # Validate issuer
            if claims.get("iss") != self._settings.issuer:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Wrong issuer",
                )

            # Validate audience (only on id tokens; access tokens use client_id)
            token_use = claims.get("token_use")
            if token_use == "id":
                if claims.get("aud") != self._settings.cognito_app_client_id:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Wrong audience",
                    )
            elif token_use == "access":
                if claims.get("client_id") != self._settings.cognito_app_client_id:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Wrong client_id",
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Unexpected token_use: {token_use}",
                )

            return CognitoUser(
                sub=claims["sub"],
                email=claims.get("email"),
                username=claims.get("cognito:username") or claims.get("username"),
                groups=claims.get("cognito:groups", []),
                token_use=token_use,
                raw_claims=claims,
            )

        except HTTPException:
            raise
        except Exception as exc:
            logger.warning("token verification failed", extra={"error": str(exc)})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            ) from exc

    # ---- FastAPI dependencies -------------------------------------------------

    async def require_user(
        self, authorization: str | None = Header(default=None)
    ) -> CognitoUser:
        """Dependency that extracts and validates the Bearer token."""
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Bearer token",
            )
        token = authorization.split(" ", 1)[1]
        return self.verify_token(token)

    async def require_admin(
        self, authorization: str | None = Header(default=None)
    ) -> CognitoUser:
        """Same as require_user but additionally checks admin group."""
        user = await self.require_user(authorization)
        if not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin group required",
            )
        return user

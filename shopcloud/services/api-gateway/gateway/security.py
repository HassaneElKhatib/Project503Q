"""Password hashing, optional local JWT, and Cognito verification."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import bcrypt
from fastapi import HTTPException, Request, status
from jose import JWTError, jwt
from libs.auth import CognitoVerifier
from libs.config import CognitoSettings

from .settings import settings

_customer_verifier: CognitoVerifier | None = None
_admin_verifier: CognitoVerifier | None = None


def init_gateway_verifiers() -> None:
    """Build Cognito verifiers from settings (call once at startup)."""
    global _customer_verifier, _admin_verifier
    _customer_verifier = None
    _admin_verifier = None

    if settings.cognito_user_pool_id and settings.cognito_app_client_id:
        _customer_verifier = CognitoVerifier(
            CognitoSettings(
                cognito_user_pool_id=settings.cognito_user_pool_id,
                cognito_app_client_id=settings.cognito_app_client_id,
                cognito_region=settings.cognito_region,
            )
        )
    if settings.cognito_admin_user_pool_id and settings.cognito_admin_app_client_id:
        _admin_verifier = CognitoVerifier(
            CognitoSettings(
                cognito_user_pool_id=settings.cognito_admin_user_pool_id,
                cognito_app_client_id=settings.cognito_admin_app_client_id,
                cognito_region=settings.cognito_admin_region or settings.cognito_region,
            )
        )


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def issue_token(*, user_id: str, email: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token") from exc


def _bearer_token(request: Request) -> str | None:
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    return auth.split(" ", 1)[1].strip() or None


def _claims_from_cognito(verifier: CognitoVerifier, token: str) -> dict:
    user = verifier.verify_token(token)
    role = "admin" if user.is_admin else "user"
    email = user.email or ""
    if not email and user.username and "@" in user.username:
        email = user.username
    return {"sub": user.sub, "email": email, "role": role}


def _enrich_claims_with_id_cookie(request: Request, claims: dict) -> dict:
    """When access token lacks email, try matching id-token cookies for profile claims."""
    if (claims.get("email") or "").strip():
        return claims

    id_attempts: list[tuple[str | None, CognitoVerifier | None]] = [
        (request.cookies.get(settings.customer_id_cookie_name), _customer_verifier),
        (request.cookies.get(settings.admin_id_cookie_name), _admin_verifier),
    ]
    for token, verifier in id_attempts:
        if not token or not verifier:
            continue
        try:
            extra = _claims_from_cognito(verifier, token)
        except HTTPException:
            continue
        if extra.get("sub") != claims.get("sub"):
            continue
        email = (extra.get("email") or "").strip()
        if email:
            claims["email"] = email
            if extra.get("role") == "admin":
                claims["role"] = "admin"
            return claims
    return claims


def optional_user(request: Request) -> dict | None:
    bearer = _bearer_token(request)

    if settings.use_local_gateway_auth and bearer:
        try:
            return decode_token(bearer)
        except HTTPException:
            return None

    # Try customer Cognito first, then admin pool (admin SPA uses the same /api/users/me).
    attempts: list[tuple[str, CognitoVerifier | None]] = []
    if bearer:
        attempts.append((bearer, _customer_verifier))
        attempts.append((bearer, _admin_verifier))
    cust_cookie = request.cookies.get(settings.customer_access_cookie_name)
    adm_cookie = request.cookies.get(settings.admin_access_cookie_name)
    if cust_cookie:
        attempts.append((cust_cookie, _customer_verifier))
    if adm_cookie:
        attempts.append((adm_cookie, _admin_verifier))

    seen: set[str] = set()
    for token, verifier in attempts:
        if not token or not verifier or token in seen:
            continue
        seen.add(token)
        try:
            claims = _claims_from_cognito(verifier, token)
            return _enrich_claims_with_id_cookie(request, claims)
        except HTTPException:
            continue
    return None


def require_user(request: Request) -> dict:
    claims = optional_user(request)
    if claims:
        return claims
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="auth required")


def require_admin(request: Request) -> dict:
    token = _bearer_token(request)

    if _admin_verifier:
        token = token or request.cookies.get(settings.admin_access_cookie_name)
        if token:
            try:
                return _claims_from_cognito(_admin_verifier, token)
            except HTTPException:
                pass
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="admin auth required")

    if settings.use_local_gateway_auth:
        claims = require_user(request)
        if claims.get("role") != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin only")
        return claims

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Admin Cognito pool is not configured",
    )

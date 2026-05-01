"""Auth HTTP routes.

Flow:
    GET  /auth/login            -> 302 to Cognito hosted UI (sets state cookie)
    GET  /auth/callback?code=&state=  -> validates state, swaps code for tokens,
                                          sets HttpOnly cookies, redirects to SPA
    POST /auth/refresh          -> uses refresh cookie to mint a new access token
    GET  /me                    -> returns identity from the verified access token
    POST /auth/logout           -> clears cookies and redirects to Cognito logout
"""
from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse

from app.cognito import CognitoClient, TokenSet
from app.deps import (
    get_cognito_client,
    get_settings,
    get_state_signer,
    get_verifier,
)
from app.settings import AuthSettings
from app.state import StateError, StateSigner
from libs.auth import CognitoUser, CognitoVerifier
from libs.errors import ValidationError
from libs.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["auth"])


def _set_token_cookies(
    response: Response, tokens: TokenSet, settings: AuthSettings
) -> None:
    """Persist the access (and refresh) tokens as HttpOnly cookies."""
    common = {
        "httponly": True,
        "secure": settings.cookie_secure,
        "samesite": "lax",
    }
    if settings.cookie_domain:
        common["domain"] = settings.cookie_domain  # type: ignore[assignment]

    response.set_cookie(
        settings.access_cookie_name,
        tokens.access_token,
        max_age=tokens.expires_in,
        path="/",
        **common,
    )
    if tokens.refresh_token:
        # Refresh tokens are long-lived (Cognito default 30 days). Scope to /auth.
        response.set_cookie(
            settings.refresh_cookie_name,
            tokens.refresh_token,
            max_age=30 * 24 * 60 * 60,
            path="/auth",
            **common,
        )


def _clear_token_cookies(response: Response, settings: AuthSettings) -> None:
    response.delete_cookie(settings.access_cookie_name, path="/")
    response.delete_cookie(settings.refresh_cookie_name, path="/auth")
    response.delete_cookie(settings.state_cookie_name, path="/auth")


@router.get("/auth/login")
async def login(
    next: str = Query(default="/", max_length=500),
    settings: AuthSettings = Depends(get_settings),
    cognito: CognitoClient = Depends(get_cognito_client),
    state_signer: StateSigner = Depends(get_state_signer),
) -> RedirectResponse:
    """Start the OAuth flow by redirecting to Cognito's hosted UI."""
    if not next.startswith("/"):
        # Only allow same-site redirects to prevent open-redirect bugs
        next = "/"

    state = state_signer.issue(next_url=next)
    authorize_url = cognito.build_authorize_url(state)

    response = RedirectResponse(url=authorize_url, status_code=status.HTTP_302_FOUND)
    # Also stash the state in a cookie as defense-in-depth (double-submit pattern)
    response.set_cookie(
        settings.state_cookie_name,
        state,
        max_age=settings.state_ttl_seconds,
        path="/auth",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )
    return response


@router.get("/auth/callback")
async def callback(
    request: Request,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    error_description: str | None = Query(default=None),
    settings: AuthSettings = Depends(get_settings),
    cognito: CognitoClient = Depends(get_cognito_client),
    state_signer: StateSigner = Depends(get_state_signer),
) -> RedirectResponse:
    """Cognito redirects the browser here with ?code=&state= after login."""
    if error:
        logger.warning(
            "cognito returned error to callback",
            extra={"error": error, "description": error_description},
        )
        raise ValidationError(f"Auth failed: {error}")

    if not code or not state:
        raise ValidationError("Missing code or state")

    # Double-submit: state from query must equal state we set in the cookie.
    cookie_state = request.cookies.get(settings.state_cookie_name)
    if not cookie_state or cookie_state != state:
        logger.warning("state cookie mismatch")
        raise ValidationError("State mismatch")

    # Verify the signed state and recover the original next_url
    try:
        next_url = state_signer.verify(state)
    except StateError as exc:
        logger.warning("state verification failed", extra={"error": str(exc)})
        raise ValidationError("Invalid state") from exc

    # Exchange the code for tokens
    tokens = await cognito.exchange_code(code)

    # Redirect the SPA to wherever it asked to land, with cookies set
    redirect = RedirectResponse(url=next_url, status_code=status.HTTP_302_FOUND)
    _set_token_cookies(redirect, tokens, settings)
    redirect.delete_cookie(settings.state_cookie_name, path="/auth")
    return redirect


@router.post("/auth/refresh")
async def refresh(
    request: Request,
    settings: AuthSettings = Depends(get_settings),
    cognito: CognitoClient = Depends(get_cognito_client),
) -> JSONResponse:
    """Mint a new access token using the refresh-token cookie."""
    refresh_token = request.cookies.get(settings.refresh_cookie_name)
    if not refresh_token:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": {"code": "no_refresh_token", "message": "No refresh cookie"}
            },
        )

    tokens = await cognito.refresh(refresh_token)
    response = JSONResponse(content={"expires_in": tokens.expires_in})
    _set_token_cookies(response, tokens, settings)
    return response


@router.post("/auth/logout")
async def logout(
    settings: AuthSettings = Depends(get_settings),
    cognito: CognitoClient = Depends(get_cognito_client),
) -> RedirectResponse:
    """Clear cookies and redirect to Cognito's /logout endpoint."""
    response = RedirectResponse(
        url=cognito.build_logout_url(),
        status_code=status.HTTP_302_FOUND,
    )
    _clear_token_cookies(response, settings)
    return response


# /me lives at the root of the service so it can be reached at /api/me
me_router = APIRouter(tags=["auth"])


@me_router.get("/me")
async def me(
    request: Request,
    verifier: CognitoVerifier = Depends(get_verifier),
    settings: AuthSettings = Depends(get_settings),
) -> dict:
    """Return the current user's identity.

    Accepts the access token from EITHER:
    - Authorization: Bearer <token> header (for service-to-service or SDKs)
    - The HttpOnly access cookie (for the browser SPA)
    """
    token = None
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1]
    else:
        token = request.cookies.get(settings.access_cookie_name)

    if not token:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": {"code": "unauthenticated", "message": "Not signed in"}
            },
        )

    user: CognitoUser = verifier.verify_token(token)
    return {
        "sub": user.sub,
        "email": user.email,
        "username": user.username,
        "groups": user.groups,
        "is_admin": user.is_admin,
    }

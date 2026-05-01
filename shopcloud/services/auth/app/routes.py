from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse, RedirectResponse

from app.cognito import CognitoClient
from app.deps import (
    get_cognito_client,
    get_settings,
    get_state_signer,
    get_verifier,
)
from app.oauth_cookies import (
    clear_token_cookies,
    delete_oauth_state_cookie,
    http_only_cookie_kwargs,
    set_token_cookies,
)
from app.settings import AuthSettings
from app.state import StateError, StateSigner
from libs.auth import CognitoUser, CognitoVerifier
from libs.errors import ValidationError
from libs.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["auth"])


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
        path=settings.state_cookie_path,
        **http_only_cookie_kwargs(settings),
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
    set_token_cookies(redirect, tokens, settings)
    delete_oauth_state_cookie(redirect, settings)
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
    set_token_cookies(response, tokens, settings)
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
    clear_token_cookies(response, settings)
    return response


# /me lives at the root of the service so it can be reached at /api/me
me_router = APIRouter(tags=["auth"])


@me_router.get("/me")
async def me(
    request: Request,
    verifier: CognitoVerifier = Depends(get_verifier),
    settings: AuthSettings = Depends(get_settings),
) -> dict:
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

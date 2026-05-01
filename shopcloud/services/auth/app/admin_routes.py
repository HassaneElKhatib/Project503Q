from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse, RedirectResponse

from app.admin_pool_settings import AdminPoolAuthSettings
from app.cognito import CognitoClient, TokenSet
from app.deps import (
    get_admin_cognito_client,
    get_admin_settings,
    get_admin_state_signer,
)
from app.oauth_cookies import (
    clear_token_cookies,
    delete_oauth_state_cookie,
    http_only_cookie_kwargs,
    set_token_cookies,
)
from app.state import StateError, StateSigner
from libs.errors import ValidationError
from libs.logger import get_logger

logger = get_logger(__name__)

admin_router = APIRouter(tags=["auth-admin"])


@admin_router.get("/login")
async def admin_login(
    next: str = Query(default="/admin", max_length=500),
    settings: AdminPoolAuthSettings = Depends(get_admin_settings),
    cognito: CognitoClient = Depends(get_admin_cognito_client),
    state_signer: StateSigner = Depends(get_admin_state_signer),
) -> RedirectResponse:
    if not next.startswith("/"):
        next = "/admin"

    state = state_signer.issue(next_url=next)
    authorize_url = cognito.build_authorize_url(state)

    response = RedirectResponse(url=authorize_url, status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        settings.state_cookie_name,
        state,
        max_age=settings.state_ttl_seconds,
        path=settings.state_cookie_path,
        **http_only_cookie_kwargs(settings),
    )
    return response


@admin_router.get("/callback")
async def admin_callback(
    request: Request,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    error_description: str | None = Query(default=None),
    settings: AdminPoolAuthSettings = Depends(get_admin_settings),
    cognito: CognitoClient = Depends(get_admin_cognito_client),
    state_signer: StateSigner = Depends(get_admin_state_signer),
) -> RedirectResponse:
    if error:
        logger.warning(
            "admin cognito callback error",
            extra={"error": error, "description": error_description},
        )
        raise ValidationError(f"Auth failed: {error}")

    if not code or not state:
        raise ValidationError("Missing code or state")

    cookie_state = request.cookies.get(settings.state_cookie_name)
    if not cookie_state or cookie_state != state:
        logger.warning("admin oauth state cookie mismatch")
        raise ValidationError("State mismatch")

    try:
        next_url = state_signer.verify(state)
    except StateError as exc:
        logger.warning("admin state verification failed", extra={"error": str(exc)})
        raise ValidationError("Invalid state") from exc

    tokens: TokenSet = await cognito.exchange_code(code)

    redirect = RedirectResponse(url=next_url, status_code=status.HTTP_302_FOUND)
    set_token_cookies(redirect, tokens, settings)
    delete_oauth_state_cookie(redirect, settings)
    return redirect


@admin_router.post("/refresh")
async def admin_refresh(
    request: Request,
    settings: AdminPoolAuthSettings = Depends(get_admin_settings),
    cognito: CognitoClient = Depends(get_admin_cognito_client),
) -> JSONResponse:
    refresh_token = request.cookies.get(settings.refresh_cookie_name)
    if not refresh_token:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": {"code": "no_refresh_token", "message": "No refresh cookie"}},
        )

    tokens = await cognito.refresh(refresh_token)
    response = JSONResponse(content={"expires_in": tokens.expires_in})
    set_token_cookies(response, tokens, settings)
    return response


@admin_router.post("/logout")
async def admin_logout(
    settings: AdminPoolAuthSettings = Depends(get_admin_settings),
    cognito: CognitoClient = Depends(get_admin_cognito_client),
) -> RedirectResponse:
    response = RedirectResponse(
        url=cognito.build_logout_url(),
        status_code=status.HTTP_302_FOUND,
    )
    clear_token_cookies(response, settings)
    return response

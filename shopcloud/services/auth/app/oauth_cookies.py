from fastapi import Response

from app.cognito import TokenSet
from app.settings import AuthSettings


def http_only_cookie_kwargs(settings: AuthSettings) -> dict:
    kw: dict = {
        "httponly": True,
        "secure": settings.cookie_secure,
        "samesite": "lax",
    }
    if settings.cookie_domain:
        kw["domain"] = settings.cookie_domain
    return kw


def delete_oauth_state_cookie(response: Response, settings: AuthSettings) -> None:
    kwargs: dict = {"path": settings.state_cookie_path}
    if settings.cookie_domain:
        kwargs["domain"] = settings.cookie_domain
    response.delete_cookie(settings.state_cookie_name, **kwargs)


def set_token_cookies(response: Response, tokens: TokenSet, settings: AuthSettings) -> None:
    common = http_only_cookie_kwargs(settings)

    response.set_cookie(
        settings.access_cookie_name,
        tokens.access_token,
        max_age=tokens.expires_in,
        path="/",
        **common,
    )
    if tokens.id_token:
        response.set_cookie(
            settings.id_cookie_name,
            tokens.id_token,
            max_age=tokens.expires_in,
            path="/",
            **common,
        )
    if tokens.refresh_token:
        response.set_cookie(
            settings.refresh_cookie_name,
            tokens.refresh_token,
            max_age=30 * 24 * 60 * 60,
            path="/auth",
            **common,
        )


def clear_token_cookies(response: Response, settings: AuthSettings) -> None:
    del_kw: dict = {}
    if settings.cookie_domain:
        del_kw["domain"] = settings.cookie_domain
    response.delete_cookie(settings.access_cookie_name, path="/", **del_kw)
    response.delete_cookie(settings.id_cookie_name, path="/", **del_kw)
    response.delete_cookie(settings.refresh_cookie_name, path="/auth", **del_kw)
    delete_oauth_state_cookie(response, settings)

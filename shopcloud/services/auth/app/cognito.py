"""Thin Cognito OAuth client.

Wraps the calls to Cognito's /oauth2/token endpoint. We handle:
- Authorization code exchange (called from /auth/callback)
- Refresh token exchange (called from /auth/refresh)
- Building the authorize URL (called from /auth/login)

Cognito requires Basic auth with client_id:client_secret if the app client
has a secret. App clients used by SPAs typically have no secret, but we
support both.
"""
import base64
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

from app.settings import AuthSettings
from libs.errors import UpstreamError
from libs.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TokenSet:
    """The bundle Cognito returns from /oauth2/token."""

    access_token: str
    id_token: str | None
    refresh_token: str | None
    token_type: str
    expires_in: int  # seconds


class CognitoClient:
    def __init__(self, settings: AuthSettings) -> None:
        self._settings = settings
        self._http = httpx.AsyncClient(timeout=10.0)

    async def aclose(self) -> None:
        await self._http.aclose()

    def build_authorize_url(self, state: str) -> str:
        """Build the URL to redirect the browser to, to start login."""
        params = {
            "response_type": "code",
            "client_id": self._settings.cognito_app_client_id,
            "redirect_uri": self._settings.callback_url,
            "scope": " ".join(self._settings.oauth_scopes),
            "state": state,
        }
        return f"{self._settings.authorize_url}?{urlencode(params)}"

    def build_logout_url(self) -> str:
        params = {
            "client_id": self._settings.cognito_app_client_id,
            "logout_uri": self._settings.logout_redirect_url,
        }
        return f"{self._settings.logout_url}?{urlencode(params)}"

    def _auth_header(self) -> dict[str, str]:
        """Basic auth header if a client secret is configured."""
        if not self._settings.cognito_app_client_secret:
            return {}
        creds = (
            f"{self._settings.cognito_app_client_id}:"
            f"{self._settings.cognito_app_client_secret}"
        )
        encoded = base64.b64encode(creds.encode()).decode()
        return {"Authorization": f"Basic {encoded}"}

    async def exchange_code(self, code: str) -> TokenSet:
        """Exchange an authorization code for an access/id/refresh token set."""
        body = {
            "grant_type": "authorization_code",
            "client_id": self._settings.cognito_app_client_id,
            "code": code,
            "redirect_uri": self._settings.callback_url,
        }
        return await self._post_token(body)

    async def refresh(self, refresh_token: str) -> TokenSet:
        """Use a refresh token to mint a new access (and id) token."""
        body = {
            "grant_type": "refresh_token",
            "client_id": self._settings.cognito_app_client_id,
            "refresh_token": refresh_token,
        }
        return await self._post_token(body)

    async def _post_token(self, body: dict[str, str]) -> TokenSet:
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            **self._auth_header(),
        }
        try:
            response = await self._http.post(
                self._settings.token_url,
                data=body,
                headers=headers,
            )
        except httpx.HTTPError as exc:
            logger.error("cognito token request failed", extra={"error": str(exc)})
            raise UpstreamError("Cognito unreachable") from exc

        if response.status_code != 200:
            logger.warning(
                "cognito token request rejected",
                extra={
                    "status": response.status_code,
                    "body": response.text[:200],  # don't log full body in prod
                },
            )
            raise UpstreamError("Cognito rejected token request")

        data = response.json()
        return TokenSet(
            access_token=data["access_token"],
            id_token=data.get("id_token"),
            refresh_token=data.get("refresh_token"),
            token_type=data.get("token_type", "Bearer"),
            expires_in=int(data.get("expires_in", 3600)),
        )

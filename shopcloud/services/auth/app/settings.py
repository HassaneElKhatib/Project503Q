"""Auth service settings.

Cognito values are populated by Terraform (via External Secrets Operator
pulling from Secrets Manager). For local dev, set them in .env.
"""
from pydantic import Field
from pydantic_settings import SettingsConfigDict

from libs.config import BaseServiceSettings


class AuthSettings(BaseServiceSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    service_name: str = Field(default="auth")

    # Cognito user pool (customer pool, NOT admin)
    cognito_user_pool_id: str = Field(...)
    cognito_app_client_id: str = Field(...)
    cognito_app_client_secret: str | None = Field(
        default=None,
        description="Required only if the app client is configured with a secret",
    )
    cognito_region: str = Field(default="us-east-1")

    # Hosted UI domain (e.g. shopcloud-auth.auth.us-east-1.amazoncognito.com)
    cognito_domain: str = Field(...)

    # OAuth redirect targets
    callback_url: str = Field(
        ...,
        description="Public URL of /auth/callback - must be in the app client's allow-list",
    )
    logout_redirect_url: str = Field(
        ...,
        description="Where to send the user after Cognito logout",
    )
    post_login_redirect: str = Field(
        default="/",
        description="Where the SPA should land after successful login",
    )

    # OAuth scopes requested
    oauth_scopes: list[str] = Field(
        default_factory=lambda: ["openid", "email", "profile"]
    )

    # Cookie security
    cookie_domain: str | None = Field(
        default=None,
        description="If set, cookies are scoped to this domain (e.g. .shopcloud.example)",
    )
    cookie_secure: bool = Field(
        default=True,
        description="Set False only for local http dev",
    )
    access_cookie_name: str = Field(default="sc_access")
    refresh_cookie_name: str = Field(default="sc_refresh")
    state_cookie_name: str = Field(default="sc_state")

    # CSRF protection on the OAuth state param - signed with this key
    state_signing_key: str = Field(
        ...,
        description="Random secret used to HMAC-sign the OAuth state parameter",
    )
    state_ttl_seconds: int = Field(default=300)

    @property
    def issuer(self) -> str:
        return (
            f"https://cognito-idp.{self.cognito_region}.amazonaws.com/"
            f"{self.cognito_user_pool_id}"
        )

    @property
    def jwks_url(self) -> str:
        return f"{self.issuer}/.well-known/jwks.json"

    @property
    def authorize_url(self) -> str:
        return f"https://{self.cognito_domain}/oauth2/authorize"

    @property
    def token_url(self) -> str:
        return f"https://{self.cognito_domain}/oauth2/token"

    @property
    def logout_url(self) -> str:
        return f"https://{self.cognito_domain}/logout"

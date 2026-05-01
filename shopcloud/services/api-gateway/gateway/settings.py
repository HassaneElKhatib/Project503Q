from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Gateway runtime configuration."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "api-gateway"
    log_level: str = "info"

    allowed_origins: str = "http://localhost:5173,http://localhost:8080"

    gateway_db_url: str = "sqlite+aiosqlite:///./gateway.db"

    # Local docker/tests: password + OTP + HS256 JWT. Prod: Cognito cookies / Bearer + Postgres.
    use_local_gateway_auth: bool = False

    cognito_user_pool_id: str = ""
    cognito_app_client_id: str = ""
    cognito_region: str = "us-east-1"
    customer_access_cookie_name: str = "sc_access"
    customer_id_cookie_name: str = "sc_id"

    cognito_admin_user_pool_id: str = ""
    cognito_admin_app_client_id: str = ""
    cognito_admin_region: str = ""
    admin_access_cookie_name: str = "sc_access_adm"
    admin_id_cookie_name: str = "sc_id_adm"

    @model_validator(mode="after")
    def postgres_use_asyncpg(self) -> "Settings":
        """RDS secrets use postgresql://; SQLAlchemy async engine needs postgresql+asyncpg://."""
        u = self.gateway_db_url
        if u.startswith("postgresql://") and not u.startswith("postgresql+"):
            self.gateway_db_url = u.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif u.startswith("postgres://"):
            self.gateway_db_url = u.replace("postgres://", "postgresql+asyncpg://", 1)
        return self

    @model_validator(mode="after")
    def enforce_cognito_and_postgres(self) -> "Settings":
        if self.use_local_gateway_auth:
            return self
        if "sqlite" in self.gateway_db_url.lower():
            raise ValueError(
                "Gateway DATABASE_URL must be PostgreSQL when USE_LOCAL_GATEWAY_AUTH=false "
                "(SQLite is only allowed for local auth)."
            )
        if not self.cognito_user_pool_id.strip() or not self.cognito_app_client_id.strip():
            raise ValueError(
                "COGNITO_USER_POOL_ID and COGNITO_APP_CLIENT_ID are required when "
                "USE_LOCAL_GATEWAY_AUTH=false."
            )
        return self

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 720

    # Optional upstreams. When empty the gateway answers the request
    # itself from its local store.
    catalog_base_url: str = ""
    cart_base_url: str = ""
    checkout_base_url: str = ""
    admin_base_url: str = ""
    auth_base_url: str = ""

    seed_admin_email: str = "admin@shopcloud.io"
    seed_admin_password: str = "AdminPass1!"
    seed_admin_name: str = "ShopCloud Admin"

    smtp_enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "tayma.merhebi@gmail.com"
    smtp_from_name: str = "The Glow Lab Billing"
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False

    s3_images_bucket: str = ""
    s3_images_region: str = ""

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()

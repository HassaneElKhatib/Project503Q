from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Gateway runtime configuration."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "api-gateway"
    log_level: str = "info"

    allowed_origins: str = "http://localhost:5173,http://localhost:8080"

    gateway_db_url: str = "sqlite+aiosqlite:///./gateway.db"

    @model_validator(mode="after")
    def postgres_use_asyncpg(self) -> "Settings":
        """RDS secrets use postgresql://; SQLAlchemy async engine needs postgresql+asyncpg://."""
        u = self.gateway_db_url
        if u.startswith("postgresql://") and not u.startswith("postgresql+"):
            self.gateway_db_url = u.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif u.startswith("postgres://"):
            self.gateway_db_url = u.replace("postgres://", "postgresql+asyncpg://", 1)
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

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()

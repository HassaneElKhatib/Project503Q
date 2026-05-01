"""Admin service settings.

Admin uses a SEPARATE Cognito user pool from customers. The architecture diagram
shows two user pools - customers and admins. Admin tokens MUST come from the
admin pool. A customer token cannot be used here even if it has 'admin' in
groups - the issuer/audience checks fail.
"""
from pydantic import Field
from pydantic_settings import SettingsConfigDict

from libs.config import BaseServiceSettings


class AdminSettings(BaseServiceSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    service_name: str = Field(default="admin")

    # Database (read-mostly; we don't write anything in this slice)
    database_url: str = Field(...)
    db_pool_size: int = Field(default=5)

    # ADMIN Cognito user pool - distinct from the customer pool
    cognito_user_pool_id: str = Field(...)
    cognito_app_client_id: str = Field(...)
    cognito_region: str = Field(default="us-east-1")

    # Required group claim - admins MUST be in this group
    required_admin_group: str = Field(default="admin")

    # Pagination
    default_page_size: int = Field(default=20, ge=1, le=100)
    max_page_size: int = Field(default=100, ge=1, le=500)

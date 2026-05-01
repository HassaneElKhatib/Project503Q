from pydantic import Field
from pydantic_settings import SettingsConfigDict

from app.settings import AuthSettings


class AdminPoolAuthSettings(AuthSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="ADMIN_",
    )

    port: int = Field(default=8000, validation_alias="SERVICE_HTTP_PORT")

    access_cookie_name: str = Field(default="sc_access_adm")
    id_cookie_name: str = Field(default="sc_id_adm")
    refresh_cookie_name: str = Field(default="sc_refresh_adm")
    state_cookie_name: str = Field(default="sc_state_adm")
    state_cookie_path: str = Field(default="/auth/admin")

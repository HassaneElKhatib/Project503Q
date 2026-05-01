"""Auth service entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.cognito import CognitoClient
from app.routes import me_router, router
from app.settings import AuthSettings
from app.state import StateSigner
from libs.auth import CognitoVerifier
from libs.config import CognitoSettings
from libs.errors import install_exception_handlers
from libs.health import HealthRouter, metrics_middleware_factory, service_info
from libs.logger import configure_root_logger, get_logger, init_service_context
from libs.middleware import RequestIDMiddleware

settings = AuthSettings()  # type: ignore[call-arg]
logger = get_logger("auth")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---- startup ----
    configure_root_logger(level=settings.log_level)
    init_service_context(
        service=settings.service_name,
        version=settings.service_version,
        environment=settings.environment,
    )
    service_info.labels(
        service=settings.service_name,
        version=settings.service_version,
        environment=settings.environment,
    ).set(1)

    # JWT verifier (shares the JWKS-fetching logic with every other service)
    verifier_settings = CognitoSettings(
        cognito_user_pool_id=settings.cognito_user_pool_id,
        cognito_app_client_id=settings.cognito_app_client_id,
        cognito_region=settings.cognito_region,
    )
    app.state.verifier = CognitoVerifier(verifier_settings)

    # OAuth client
    app.state.cognito_client = CognitoClient(settings)

    # Signed state tokens
    app.state.state_signer = StateSigner(
        signing_key=settings.state_signing_key,
        ttl_seconds=settings.state_ttl_seconds,
    )

    app.state.settings = settings

    # Readiness check: can we reach the Cognito JWKS URL?
    health_router = app.state.health_router

    async def check_jwks() -> bool:
        try:
            app.state.verifier._refresh_keys()
            return bool(app.state.verifier._keys)
        except Exception:
            return False

    health_router.add_readiness_check("cognito_jwks", check_jwks)

    logger.info("auth ready")
    yield

    # ---- shutdown ----
    await app.state.cognito_client.aclose()
    logger.info("auth shutting down")


app = FastAPI(
    title=settings.service_name,
    version=settings.service_version,
    description="Cognito wrapper - login, callback, refresh, logout, /me",
    lifespan=lifespan,
)

app.add_middleware(metrics_middleware_factory())
app.add_middleware(RequestIDMiddleware)

install_exception_handlers(app)

health_router = HealthRouter()
app.state.health_router = health_router
app.include_router(health_router.router)
app.include_router(router)
app.include_router(me_router)


@app.get("/", include_in_schema=False)
async def root() -> dict:
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "environment": settings.environment,
    }

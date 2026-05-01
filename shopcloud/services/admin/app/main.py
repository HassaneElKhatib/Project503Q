"""Admin service entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routes import router
from app.settings import AdminSettings
from libs.auth import CognitoVerifier
from libs.config import CognitoSettings
from libs.db import build_engine, build_sessionmaker, healthcheck
from libs.errors import install_exception_handlers
from libs.health import HealthRouter, metrics_middleware_factory, service_info
from libs.logger import configure_root_logger, get_logger, init_service_context
from libs.middleware import RequestIDMiddleware

settings = AdminSettings()  # type: ignore[call-arg]
logger = get_logger("admin")


@asynccontextmanager
async def lifespan(app: FastAPI):
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

    engine = build_engine(settings.database_url, pool_size=settings.db_pool_size)
    sessionmaker = build_sessionmaker(engine)

    # ADMIN pool verifier (separate from customer pool!)
    verifier_settings = CognitoSettings(
        cognito_user_pool_id=settings.cognito_user_pool_id,
        cognito_app_client_id=settings.cognito_app_client_id,
        cognito_region=settings.cognito_region,
    )
    verifier = CognitoVerifier(verifier_settings)

    app.state.settings = settings
    app.state.engine = engine
    app.state.sessionmaker = sessionmaker
    app.state.verifier = verifier

    health_router = app.state.health_router

    async def db_check() -> bool:
        return await healthcheck(sessionmaker)

    health_router.add_readiness_check("postgres", db_check)

    logger.info("admin ready")
    yield

    await engine.dispose()
    logger.info("admin shutting down")


app = FastAPI(
    title=settings.service_name,
    version=settings.service_version,
    description="Admin API - internal ALB only",
    lifespan=lifespan,
)

app.add_middleware(metrics_middleware_factory())
app.add_middleware(RequestIDMiddleware)
install_exception_handlers(app)

health_router = HealthRouter()
app.state.health_router = health_router
app.include_router(health_router.router)
app.include_router(router)


@app.get("/", include_in_schema=False)
async def root() -> dict:
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "environment": settings.environment,
    }

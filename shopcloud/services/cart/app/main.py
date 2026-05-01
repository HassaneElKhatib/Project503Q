"""Cart service entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.catalog_client import CatalogClient
from app.repository import CartRepository
from app.routes import router
from app.settings import CartSettings
from libs.auth import CognitoVerifier
from libs.config import CognitoSettings
from libs.errors import install_exception_handlers
from libs.health import HealthRouter, metrics_middleware_factory, service_info
from libs.logger import configure_root_logger, get_logger, init_service_context
from libs.middleware import RequestIDMiddleware

settings = CartSettings()  # type: ignore[call-arg]
logger = get_logger("cart")


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

    # Redis (mandatory for cart)
    from redis.asyncio import Redis

    redis_client = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )
    await redis_client.ping()
    logger.info("connected to redis")

    repo = CartRepository(redis_client, ttl_seconds=settings.cart_ttl_seconds)

    # Catalog client
    catalog_client = CatalogClient(
        settings.catalog_base_url, timeout=settings.catalog_timeout_seconds
    )

    # JWT verifier
    verifier_settings = CognitoSettings(
        cognito_user_pool_id=settings.cognito_user_pool_id,
        cognito_app_client_id=settings.cognito_app_client_id,
        cognito_region=settings.cognito_region,
    )
    verifier = CognitoVerifier(verifier_settings)

    app.state.settings = settings
    app.state.repository = repo
    app.state.catalog_client = catalog_client
    app.state.verifier = verifier

    # Readiness checks
    health_router = app.state.health_router
    health_router.add_readiness_check("redis", repo.ping)
    health_router.add_readiness_check("catalog", catalog_client.ping)

    logger.info("cart ready")
    yield

    await catalog_client.aclose()
    await redis_client.close()
    logger.info("cart shutting down")


app = FastAPI(
    title=settings.service_name,
    version=settings.service_version,
    description="Shopping cart service (Redis-backed)",
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

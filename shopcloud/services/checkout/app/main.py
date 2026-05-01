"""Checkout service entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.cart_reader import CartReader
from app.routes import router
from app.service import CheckoutService
from app.settings import CheckoutSettings
from libs.auth import CognitoVerifier
from libs.aws.sqs import AwsSqsPublisher
from libs.config import CognitoSettings
from libs.db import build_engine, build_sessionmaker, healthcheck
from libs.errors import install_exception_handlers
from libs.health import HealthRouter, metrics_middleware_factory, service_info
from libs.logger import configure_root_logger, get_logger, init_service_context
from libs.middleware import RequestIDMiddleware

settings = CheckoutSettings()  # type: ignore[call-arg]
logger = get_logger("checkout")


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

    # DB
    engine = build_engine(
        settings.database_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
    )
    sessionmaker = build_sessionmaker(engine)

    # Redis (cart)
    from redis.asyncio import Redis

    redis_client = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )
    cart_reader = CartReader(redis_client)

    # SQS
    sqs_publisher = AwsSqsPublisher(
        queue_url=settings.invoice_queue_url,
        region=settings.aws_region,
        max_attempts=settings.sqs_max_attempts,
    )

    # JWT
    verifier_settings = CognitoSettings(
        cognito_user_pool_id=settings.cognito_user_pool_id,
        cognito_app_client_id=settings.cognito_app_client_id,
        cognito_region=settings.cognito_region,
    )
    verifier = CognitoVerifier(verifier_settings)

    # Service
    service = CheckoutService(sessionmaker, cart_reader, sqs_publisher)

    app.state.settings = settings
    app.state.service = service
    app.state.verifier = verifier
    app.state.engine = engine
    app.state.sessionmaker = sessionmaker
    app.state.redis_client = redis_client
    app.state.cart_reader = cart_reader

    # Readiness
    health_router = app.state.health_router

    async def db_check() -> bool:
        return await healthcheck(sessionmaker)

    health_router.add_readiness_check("postgres", db_check)
    health_router.add_readiness_check("redis", cart_reader.ping)

    logger.info("checkout ready")
    yield

    await redis_client.close()
    await engine.dispose()
    logger.info("checkout shutting down")


app = FastAPI(
    title=settings.service_name,
    version=settings.service_version,
    description="Order placement + async invoice publish",
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

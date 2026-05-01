"""Catalog service entrypoint."""
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI

from app.cache import ProductCache
from app.repository import (
    JsonProductRepository,
    ProductRepository,
    SqlProductRepository,
)
from app.routes import categories_router, router
from app.settings import CatalogSettings
from libs.db import build_engine, build_sessionmaker, healthcheck
from libs.errors import install_exception_handlers
from libs.health import HealthRouter, metrics_middleware_factory, service_info
from libs.logger import configure_root_logger, get_logger, init_service_context
from libs.middleware import RequestIDMiddleware

settings = CatalogSettings()  # type: ignore[call-arg]
logger = get_logger("catalog")


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

    # Pick repository implementation
    repo: ProductRepository
    engine = None

    if settings.products_source == "sql":
        if not settings.database_url:
            raise RuntimeError(
                "PRODUCTS_SOURCE=sql but DATABASE_URL is not set"
            )
        engine = build_engine(settings.database_url, pool_size=settings.db_pool_size)
        sessionmaker = build_sessionmaker(engine)
        repo = SqlProductRepository(sessionmaker)
        app.state.engine = engine
        app.state.sessionmaker = sessionmaker
        logger.info("using SqlProductRepository")
    else:
        json_repo = JsonProductRepository(settings.products_json_path)
        json_repo.load()
        repo = json_repo
        logger.info("using JsonProductRepository")

    app.state.repository = repo

    # Connect to Redis if configured
    redis_client = None
    if settings.redis_url:
        try:
            from redis.asyncio import Redis

            redis_client = Redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            await redis_client.ping()
            logger.info("connected to redis")
        except Exception as exc:
            logger.warning(
                "redis unavailable - running without cache",
                extra={"error": str(exc)},
            )
            redis_client = None

    cache = ProductCache(redis_client, default_ttl=settings.cache_ttl_seconds)
    app.state.cache = cache
    app.state.settings = settings
    app.state.started_at = datetime.now(timezone.utc)

    # Wire readiness checks
    health_router = app.state.health_router

    if settings.products_source == "sql" and engine is not None:
        async def db_check() -> bool:
            return await healthcheck(app.state.sessionmaker)

        health_router.add_readiness_check("postgres", db_check)
    else:
        async def data_check() -> bool:
            items, _ = await repo.list_products(limit=1)
            return True  # success means JSON loaded

        health_router.add_readiness_check("data", data_check)

    if cache._redis is not None:
        health_router.add_readiness_check("redis", cache.ping)

    logger.info("catalog ready")

    yield

    if redis_client is not None:
        await redis_client.close()
    if engine is not None:
        await engine.dispose()
    logger.info("catalog shutting down")


app = FastAPI(
    title=settings.service_name,
    version=settings.service_version,
    description="Product catalog API",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(metrics_middleware_factory())
app.add_middleware(RequestIDMiddleware)

# Error handlers
install_exception_handlers(app)

# Routers
health_router = HealthRouter()
app.state.health_router = health_router  # so lifespan can register checks
app.include_router(health_router.router)
app.include_router(router)
app.include_router(categories_router)


@app.get("/", include_in_schema=False)
async def root() -> dict:
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "environment": settings.environment,
    }

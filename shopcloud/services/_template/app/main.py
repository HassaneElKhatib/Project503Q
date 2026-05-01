"""Template service entrypoint.

Copy this whole `services/_template/` folder to start a new service.
Then:
1. Rename the folder
2. Update pyproject.toml [project] name
3. Replace the example route with your real routes
4. Add readiness checks for your service's dependencies
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from libs.config import get_base_settings
from libs.errors import install_exception_handlers
from libs.health import HealthRouter, metrics_middleware_factory, service_info
from libs.logger import configure_root_logger, get_logger, init_service_context
from libs.middleware import RequestIDMiddleware

settings = get_base_settings()


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

    logger = get_logger(__name__)
    logger.info("service starting", extra={"port": settings.port})

    yield

    # ---- shutdown ----
    logger.info("service shutting down")


app = FastAPI(
    title=settings.service_name,
    version=settings.service_version,
    lifespan=lifespan,
)

# Middleware order matters: outermost first.
# RequestID must run before metrics so log lines have the request_id.
app.add_middleware(metrics_middleware_factory())
app.add_middleware(RequestIDMiddleware)

install_exception_handlers(app)

# Health + metrics
health = HealthRouter()
app.include_router(health.router)


# ---- example route (delete when adding real routes) ----
@app.get("/")
async def root() -> dict:
    return {"service": settings.service_name, "version": settings.service_version}

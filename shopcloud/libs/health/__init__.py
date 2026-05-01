"""Reusable health + metrics endpoints.

Every service mounts these via:

    from libs.health import HealthRouter

    health = HealthRouter()
    health.add_readiness_check("postgres", check_postgres)
    health.add_readiness_check("redis", check_redis)
    app.include_router(health.router)

- /health/live always returns 200 if the process is up
- /health/ready returns 200 only if all readiness checks pass
- /metrics exposes Prometheus metrics (request count, latency histograms)
"""
import time
from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Response, status
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# Metrics are module-globals so they're shared across the whole service process.
# Each service bumps service_info on startup with its own labels.
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
service_info = Gauge(
    "service_info",
    "Service metadata (always 1)",
    ["service", "version", "environment"],
)
readiness_check_status = Gauge(
    "readiness_check_status",
    "1 if check passed last evaluation, 0 otherwise",
    ["check"],
)


ReadinessCheck = Callable[[], Awaitable[bool]]


class HealthRouter:
    """Builds /health/live, /health/ready, /metrics routes."""

    def __init__(self) -> None:
        self.router = APIRouter(tags=["health"])
        self._readiness_checks: dict[str, ReadinessCheck] = {}
        self._register_routes()

    def add_readiness_check(self, name: str, check: ReadinessCheck) -> None:
        """Register an async function returning True if the dependency is healthy."""
        self._readiness_checks[name] = check

    def _register_routes(self) -> None:
        @self.router.get("/health/live", include_in_schema=False)
        async def live() -> dict:
            return {"status": "ok"}

        @self.router.get("/health/ready", include_in_schema=False)
        async def ready(response: Response) -> dict:
            results: dict[str, bool] = {}
            all_ok = True
            for name, check in self._readiness_checks.items():
                try:
                    ok = await check()
                except Exception:
                    ok = False
                results[name] = ok
                readiness_check_status.labels(check=name).set(1 if ok else 0)
                if not ok:
                    all_ok = False

            if not all_ok:
                response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return {"status": "ok" if all_ok else "degraded", "checks": results}

        @self.router.get("/metrics", include_in_schema=False)
        async def metrics() -> Response:
            return Response(
                content=generate_latest(),
                media_type=CONTENT_TYPE_LATEST,
            )


def metrics_middleware_factory():
    """Returns a Starlette middleware function that records request metrics."""
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request

    class MetricsMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            start = time.perf_counter()
            # Use route path template (e.g. /products/{id}) not the actual URL,
            # otherwise we get one metric per id and Prometheus dies.
            path = request.url.path
            try:
                response = await call_next(request)
                status_code = response.status_code
            except Exception:
                status_code = 500
                raise
            finally:
                duration = time.perf_counter() - start
                # Resolve route template if available
                route = request.scope.get("route")
                template = getattr(route, "path", path) if route else path
                http_request_duration_seconds.labels(
                    method=request.method, path=template
                ).observe(duration)
                http_requests_total.labels(
                    method=request.method,
                    path=template,
                    status=str(status_code),
                ).inc()
            return response

    return MetricsMiddleware

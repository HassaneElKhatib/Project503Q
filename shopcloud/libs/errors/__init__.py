"""Standard error types + FastAPI exception handlers.

All errors return JSON with shape:
    {"error": {"code": "...", "message": "...", "request_id": "..."}}
"""
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from libs.logger import get_logger

logger = get_logger(__name__)


class ServiceError(Exception):
    """Base class for application errors that should map to a clean HTTP response."""

    code: str = "internal_error"
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code:
            self.code = code


class NotFoundError(ServiceError):
    code = "not_found"
    status_code = status.HTTP_404_NOT_FOUND


class ValidationError(ServiceError):
    code = "validation_error"
    status_code = status.HTTP_400_BAD_REQUEST


class ConflictError(ServiceError):
    code = "conflict"
    status_code = status.HTTP_409_CONFLICT


class UpstreamError(ServiceError):
    """A dependency we call (DB, Cognito, etc.) failed."""

    code = "upstream_error"
    status_code = status.HTTP_502_BAD_GATEWAY


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def install_exception_handlers(app: FastAPI) -> None:
    """Wire up handlers on the FastAPI app."""

    @app.exception_handler(ServiceError)
    async def handle_service_error(request: Request, exc: ServiceError) -> JSONResponse:
        logger.info(
            "service error",
            extra={
                "code": exc.code,
                "status": exc.status_code,
                "path": request.url.path,
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "request_id": _request_id(request),
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "http_error",
                    "message": exc.detail,
                    "request_id": _request_id(request),
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Invalid request",
                    "details": exc.errors(),
                    "request_id": _request_id(request),
                }
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        # Log full traceback but don't leak it to the client
        logger.exception("unhandled exception", extra={"path": request.url.path})
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "Internal server error",
                    "request_id": _request_id(request),
                }
            },
        )

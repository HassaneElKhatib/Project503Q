"""Request ID middleware.

For every incoming request:
- Read X-Request-ID if the upstream LB set one, else generate a UUID
- Stash it on request.state.request_id
- Bind it into the logger context so every log line for this request includes it
- Echo it back in the response header

This is what makes "find all logs for this customer's failed checkout" possible.
"""
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from libs.logger import bind_request_context, clear_request_context


class RequestIDMiddleware(BaseHTTPMiddleware):
    HEADER = "X-Request-ID"

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get(self.HEADER) or str(uuid.uuid4())
        request.state.request_id = request_id

        clear_request_context()
        bind_request_context(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        response = await call_next(request)
        response.headers[self.HEADER] = request_id
        return response

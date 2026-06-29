import time

from aquilia.http.client import HTTPClientRequest, HTTPClientResponse
from aquilia.http.middleware import HTTPClientMiddleware, MiddlewareHandler

from .redaction import redact_url
from .trace import Lane, SpanStatus, current_trace


class InspectorHTTPClientMiddleware(HTTPClientMiddleware):
    async def __call__(self, request: HTTPClientRequest, call_next: MiddlewareHandler) -> HTTPClientResponse:
        trace = current_trace()
        if trace is None:
            return await call_next(request)
        t0 = time.monotonic()
        status = None
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            dt = (time.monotonic() - t0) * 1000.0
            trace.add_span(
                Lane.EXTERNAL_HTTP,
                f"{request.method} {redact_url(request.url)}",
                start_offset_ms=(t0 - trace.started_monotonic) * 1000.0,
                duration_ms=dt,
                status=SpanStatus.ERROR if status is None or status >= 500 else SpanStatus.OK,
                detail={"status": status},
            )

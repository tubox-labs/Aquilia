"""
OTelMiddleware — ASGI middleware that creates a span for every HTTP request.

Follows OpenTelemetry semantic conventions for HTTP spans:
https://opentelemetry.io/docs/specs/semconv/http/http-spans/
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("aquilia.otel.middleware")


class OTelMiddleware:
    """
    ASGI middleware creating an OTel span for every HTTP request.

    Span attributes set:
        http.method         GET, POST, etc.
        http.route          Matched route pattern (e.g. /users/{id:int})
        http.url            Full request URL
        http.status_code    Response status (set in on_send hook)
        http.user_agent     From User-Agent header
        net.host.name       Server hostname
        net.host.port       Server port
    """

    def __init__(self, app: Any) -> None:
        self._app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self._app(scope, receive, send)
            return

        from aquilia.otel._tracer import get_tracer

        tracer = get_tracer()
        method = scope.get("method", "GET")
        path = scope.get("path", "/")
        span_name = f"{method} {path}"

        headers = dict(scope.get("headers", []))
        carrier = {k.decode("latin-1"): v.decode("latin-1") for k, v in headers.items()}

        try:
            from opentelemetry.propagate import extract

            ctx = extract(carrier)
        except ImportError:
            ctx = None

        span_kwargs: dict[str, Any] = {}
        if ctx is not None:
            span_kwargs["context"] = ctx

        status_code = 0

        async def send_with_capture(message: Any) -> None:
            nonlocal status_code
            if message.get("type") == "http.response.start":
                status_code = message.get("status", 0)
            await send(message)

        try:
            with tracer.start_as_current_span(span_name, **span_kwargs) as span:
                try:
                    span.set_attribute("http.method", method)
                    span.set_attribute("http.target", path)
                    span.set_attribute(
                        "http.url",
                        f"{scope.get('scheme', 'http')}://{scope.get('server', ('localhost', 8000))[0]}{path}",
                    )
                    ua = headers.get(b"user-agent", b"").decode("latin-1")
                    if ua:
                        span.set_attribute("http.user_agent", ua)

                    await self._app(scope, receive, send_with_capture)

                    if status_code:
                        span.set_attribute("http.status_code", status_code)
                        if status_code >= 500:
                            try:
                                from opentelemetry.trace import StatusCode

                                span.set_status(StatusCode.ERROR)
                            except ImportError:
                                pass
                except Exception as exc:
                    try:
                        span.record_exception(exc)
                        from opentelemetry.trace import StatusCode

                        span.set_status(StatusCode.ERROR, str(exc))
                    except ImportError:
                        pass
                    raise
        except Exception:
            await self._app(scope, receive, send)

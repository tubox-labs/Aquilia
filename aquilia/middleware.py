"""
Middleware system - Composable, async-first middleware with effect awareness.

Performance (v3 — scalability):
- ``build_fast_handler()`` builds a minimal chain skipping Logging / Timeout
  middleware for latency-sensitive routes.
- ``CompressionMiddleware`` offloads ``gzip.compress`` to a thread pool to
  avoid blocking the event loop.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from .faults import Fault, FaultDomain
from .faults.domains import HTTPFault
from .request import Request
from .response import Response
from .typing.middleware import MiddlewareCallable, RequestHandler

_FD_SECURITY = cast(FaultDomain, getattr(FaultDomain, "SECURITY"))
_FD_IO = cast(FaultDomain, getattr(FaultDomain, "IO"))
_FD_ROUTING = cast(FaultDomain, getattr(FaultDomain, "ROUTING"))
_FD_EFFECT = cast(FaultDomain, getattr(FaultDomain, "EFFECT"))
_FD_MODEL = cast(FaultDomain, getattr(FaultDomain, "MODEL"))
_FD_CACHE = cast(FaultDomain, getattr(FaultDomain, "CACHE"))
_FD_CONFIG = cast(FaultDomain, getattr(FaultDomain, "CONFIG"))
_FD_REGISTRY = cast(FaultDomain, getattr(FaultDomain, "REGISTRY"))
_FD_DI = cast(FaultDomain, getattr(FaultDomain, "DI"))
_FD_FLOW = cast(FaultDomain, getattr(FaultDomain, "FLOW"))
_FD_SYSTEM = cast(FaultDomain, getattr(FaultDomain, "SYSTEM"))
_FD_STORAGE = cast(FaultDomain, getattr(FaultDomain, "STORAGE"))
_FD_TASKS = cast(FaultDomain, getattr(FaultDomain, "TASKS"))
_FD_TEMPLATE = cast(FaultDomain, getattr(FaultDomain, "TEMPLATE"))
_FD_HTTP = cast(FaultDomain, getattr(FaultDomain, "HTTP"))

if TYPE_CHECKING:
    from .controller.base import RequestCtx

# Type alias for middleware - use string annotation to avoid circular import
Handler = RequestHandler
Middleware = MiddlewareCallable

# Names of middleware that are safe to skip on the fast path.
# Only non-essential (observability / timeout) middleware.
_FAST_SKIP_NAMES = frozenset({"LoggingMiddleware", "TimeoutMiddleware"})

# Last-resort HTML when the debug/error page renderer itself crashes.
# Must be a plain string with zero dependencies.
_FALLBACK_500_HTML = (
    '<!DOCTYPE html><html><head><meta charset="utf-8">'
    "<title>500 Internal Server Error</title>"
    "<style>body{font-family:system-ui,sans-serif;background:#000;color:#ededed;"
    "display:flex;justify-content:center;align-items:center;height:100vh;margin:0;}"
    ".c{text-align:center;}.s{font-size:72px;font-weight:700;color:#ef4444;}"
    "p{color:#888;}</style></head>"
    '<body><div class="c"><div class="s">500</div>'
    "<h1>Internal Server Error</h1>"
    "<p>An unexpected error occurred.</p></div></body></html>"
)


@dataclass
class MiddlewareDescriptor:
    """Descriptor for middleware registration."""

    middleware: Middleware
    scope: str  # "global", "app:name", "controller:name", "route:pattern"
    priority: int
    name: str


class MiddlewareStack:
    """
    Manages middleware stack with deterministic ordering.
    Order: Global < App < Controller < Route, then by priority.
    """

    def __init__(self):
        self.middlewares: list[MiddlewareDescriptor] = []
        self._sorted = True  # Track if sorting is needed

    def add(
        self,
        middleware: Middleware,
        scope: str = "global",
        priority: int = 50,
        name: str | None = None,
    ):
        """Add middleware to stack."""
        if name is None:
            name = middleware.__name__ if hasattr(middleware, "__name__") else "middleware"

        descriptor = MiddlewareDescriptor(
            middleware=middleware,
            scope=scope,
            priority=priority,
            name=name,
        )

        self.middlewares.append(descriptor)
        self._sorted = False  # Defer sorting until build_handler()

    def _sort_middlewares(self):
        """Sort middlewares by scope and priority."""
        scope_order = {"global": 0, "app": 1, "controller": 2, "route": 3}

        def sort_key(desc: MiddlewareDescriptor):
            scope_type = desc.scope.split(":")[0]
            scope_rank = scope_order.get(scope_type, 99)
            return (scope_rank, desc.priority)

        self.middlewares.sort(key=sort_key)

    def build_handler(self, final_handler: Handler) -> Handler:
        """Build middleware chain wrapping the final handler."""
        # Sort only if needed (deferred from add())
        if not self._sorted:
            self._sort_middlewares()
            self._sorted = True

        handler = final_handler

        # Wrap in reverse order so first middleware is outermost
        for desc in reversed(self.middlewares):
            handler = self._wrap_middleware(desc.middleware, handler)

        return handler

    def build_fast_handler(self, final_handler: Handler) -> Handler:
        """Build a *minimal* middleware chain for latency-sensitive routes.

        Skips middleware whose class name is in ``_FAST_SKIP_NAMES``
        (e.g. ``LoggingMiddleware``, ``TimeoutMiddleware``).
        Essential middleware (RequestId, Exception, CORS, Compression) is
        kept.

        Returns: A callable identical in signature to ``build_handler()``.
        """
        if not self._sorted:
            self._sort_middlewares()
            self._sorted = True

        handler = final_handler

        for desc in reversed(self.middlewares):
            # Derive class name from the middleware callable
            mw = desc.middleware
            cls_name = type(mw).__name__ if not isinstance(mw, type) else mw.__name__
            if cls_name in _FAST_SKIP_NAMES:
                continue  # skip this middleware
            handler = self._wrap_middleware(mw, handler)

        return handler

    def _wrap_middleware(self, middleware: Middleware, next_handler: Handler) -> Handler:
        """Wrap a handler with middleware."""

        async def wrapped(request: Request, ctx: RequestCtx) -> Response:
            return await middleware(request, ctx, next_handler)

        return wrapped


# Default middleware implementations


class RequestIdMiddleware:
    """Adds unique request ID to each request.

    Uses os.urandom (16 bytes hex) which is ~4× faster than uuid.uuid4().
    Scans raw ASGI headers directly to avoid triggering full Headers parsing.
    """

    def __init__(self, header_name: str = "X-Request-ID"):
        self.header_name = header_name
        self._header_name_bytes = header_name.lower().encode("latin-1")
        import os

        self._urandom = os.urandom

    async def __call__(self, request: Request, ctx: RequestCtx, next: Handler) -> Response:
        # Scan raw ASGI headers directly (avoids building Headers object)
        request_id = None
        target = self._header_name_bytes
        for name, value in request.scope.get("headers", ()):
            if name == target:
                request_id = value.decode("latin-1")
                break

        if not request_id:
            request_id = self._urandom(16).hex()

        request.state["request_id"] = request_id
        ctx.request_id = request_id

        response = await next(request, ctx)
        response.headers[self.header_name] = request_id
        return response


class ExceptionMiddleware:
    """Catches exceptions and converts them to error responses.

    When ``debug=True`` and the request ``Accept`` header includes
    ``text/html``, renders beautiful React-style debug pages using the
    MongoDB Atlas color palette with dark/light mode support.
    Otherwise, returns structured JSON error responses.
    """

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.logger = logging.getLogger("aquilia.exceptions")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _wants_html(self, request: Request) -> bool:
        """Check if the client prefers an HTML response."""
        try:
            accept = ""
            if hasattr(request, "headers"):
                h = request.headers
                if hasattr(h, "get"):
                    accept = h.get("accept", "") or ""
                elif isinstance(h, dict):
                    accept = h.get("accept", "") or h.get("Accept", "")
            return "text/html" in accept
        except Exception:
            return False

    def _html_response(self, body: str, status: int) -> Response:
        """Build an HTML response from rendered page string."""
        return Response(
            content=body.encode("utf-8"),
            status=status,
            headers={"content-type": "text/html; charset=utf-8"},
        )

    def _get_version(self) -> str:
        """Get Aquilia version string."""
        try:
            from aquilia import __version__

            return __version__
        except Exception:
            return ""

    def _render_debug_exception(self, exc: BaseException, request: Request) -> Response:
        """Render a full debug exception page."""
        from .debug.pages import render_debug_exception_page

        html_body = render_debug_exception_page(
            exc,
            request,
            aquilia_version=self._get_version(),
        )
        return self._html_response(html_body, 500)

    def _render_debug_http_error(
        self,
        status: int,
        message: str,
        detail: str,
        request: Request,
    ) -> Response:
        """Render a styled HTTP error page."""
        from .debug.pages import render_http_error_page

        html_body = render_http_error_page(
            status,
            message,
            detail,
            request,
            aquilia_version=self._get_version(),
        )
        return self._html_response(html_body, status)

    # ------------------------------------------------------------------
    # Main handler
    # ------------------------------------------------------------------

    async def __call__(self, request: Request, ctx: RequestCtx, next: Handler) -> Response:
        try:
            return await next(request, ctx)

        except PermissionError as e:
            # Forbidden -- 403
            self.logger.warning(f"PermissionError: {e}")
            # Only reveal raw exception detail in debug mode;
            # production gets a generic message to prevent info leakage.
            detail = str(e) if self.debug else "You do not have permission to access this resource."
            if self._wants_html(request):
                return self._render_debug_http_error(403, "Forbidden", detail, request)
            return Response.json(
                {"error": "Forbidden"},
                status=403,
            )

        except HTTPFault as e:
            # ── First-class HTTP error faults (explicit status code) ──
            status = e.status
            reason = str(e.message)
            detail = str(e.detail or e.message)

            if status >= 500:
                self.logger.error(f"HTTPFault {status} {e.code}: {reason}")
            else:
                self.logger.warning(f"HTTPFault {status} {e.code}: {reason}")

            # Collect any extra headers (Allow, Retry-After, WWW-Authenticate, etc.)
            extra_headers: dict[str, str] = e.metadata.get("headers", {})

            if self._wants_html(request):
                try:
                    if status >= 500 and self.debug:
                        return self._render_debug_exception(e, request)
                    resp = self._render_debug_http_error(status, reason, detail, request)
                    for hk, hv in extra_headers.items():
                        resp.headers[hk] = hv
                    return resp
                except Exception as render_exc:
                    self.logger.error(f"Error page renderer crashed: {render_exc}", exc_info=True)
                    return self._html_response(_FALLBACK_500_HTML, status)

            body = {
                "error": {
                    "code": e.code,
                    "message": reason,
                    "status": status,
                }
            }
            if e.public and e.detail:
                body["error"]["detail"] = e.detail
            resp = Response.json(body, status=status)
            for hk, hv in extra_headers.items():
                resp.headers[hk] = hv
            return resp

        except Fault as e:
            # Typed Fault
            # Authentication faults (unauthenticated) → 401
            # Authorization faults (authenticated but forbidden) → 403
            _UNAUTHENTICATED_CODES = {
                "AUTH_010",  # AUTH_REQUIRED
                "AUTHENTICATION_REQUIRED",  # AuthenticationRequiredFault / session decorators
                "SESSION_REQUIRED",  # SessionRequiredFault
                "INVALID_CREDENTIALS",  # Auth module login failure
            }
            _CONFLICT_CODES = {
                "USER_ALREADY_EXISTS",  # Auth module registration failure
            }

            status_map = {
                _FD_ROUTING: 404,
                _FD_SECURITY: 403,
                _FD_IO: 502,
                _FD_EFFECT: 503,
                _FD_MODEL: 404,  # DB Not Found usually
                _FD_CACHE: 502,
                _FD_CONFIG: 500,
                _FD_REGISTRY: 500,
                _FD_DI: 500,
                _FD_FLOW: 500,
                _FD_SYSTEM: 500,
                _FD_STORAGE: 502,
                _FD_TASKS: 503,
                _FD_TEMPLATE: 500,
                _FD_HTTP: 500,  # Fallback (HTTPFault caught above)
            }

            code = getattr(e, "code", None)
            if code in _UNAUTHENTICATED_CODES:
                status = 401
            elif code in _CONFLICT_CODES:
                status = 409
            elif code and ("NOT_FOUND" in code or "MISSING" in code):
                status = 404
            elif code and ("VALIDATION" in code or "INVALID" in code):
                status = 400
            elif str(e.domain) == "auth":  # Catch-all for our custom AUTH domain
                status = 401
            else:
                domain = e.domain if isinstance(e.domain, FaultDomain) else None
                status = status_map[domain] if domain is not None and domain in status_map else 500

            message = str(e.message) if (e.public or self.debug) else "Internal server error"
            code_text = str(e.code)

            if status >= 500:
                self.logger.error(f"Fault {e.code}: {e.message}")
            else:
                self.logger.warning(f"Fault {e.code}: {e.message}")

            # HTML error pages for browser clients
            if self._wants_html(request):
                try:
                    if status >= 500 and self.debug:
                        # Full traceback only in debug mode
                        return self._render_debug_exception(e, request)
                    else:
                        # Styled error page for all HTML clients (debug or production)
                        return self._render_debug_http_error(status, code_text, message, request)
                except Exception as render_exc:
                    self.logger.error(f"Error page renderer crashed: {render_exc}", exc_info=True)
                    return self._html_response(_FALLBACK_500_HTML, status)

            return Response.json(
                {
                    "error": {
                        "code": e.code,
                        "message": message,
                        "domain": e.domain.value if isinstance(e.domain, FaultDomain) else str(e.domain),
                    }
                },
                status=status,
            )

        except Exception as e:
            # Internal error -- 500
            self.logger.error(f"Unhandled exception: {e}", exc_info=True)

            if self._wants_html(request):
                try:
                    if self.debug:
                        # Full traceback with source context in debug mode
                        return self._render_debug_exception(e, request)
                    else:
                        # Styled error page in production (no traceback leak)
                        return self._render_debug_http_error(
                            500,
                            "Internal Server Error",
                            "An unexpected error occurred processing your request.",
                            request,
                        )
                except Exception as render_exc:
                    # Debug renderer itself crashed — last-resort safe response
                    self.logger.error(
                        f"Debug page renderer crashed: {render_exc}",
                        exc_info=True,
                    )
                    return self._html_response(
                        _FALLBACK_500_HTML,
                        500,
                    )

            # ARCH-04: Never leak tracebacks or exception messages in JSON
            # responses, even in debug mode.  Detailed stack traces are only
            # rendered in the HTML debug pages where they are useful for local
            # development and cannot be scraped by automated bots/scanners.
            return Response.json({"error": "Internal server error"}, status=500)


class LoggingMiddleware:
    """Logs request/response with timing.

    Performance (v2):
    - Checks logger.isEnabledFor(INFO) once; skips all work if disabled.
    - Only formats strings when actually logging.
    - Skips per-request 'extra' dict allocation when not needed.
    """

    def __init__(self):
        self.logger = logging.getLogger("aquilia.requests")
        self._log_enabled: bool = True  # Updated lazily

    async def __call__(self, request: Request, ctx: RequestCtx, next: Handler) -> Response:
        if not self.logger.isEnabledFor(logging.INFO):
            return await next(request, ctx)

        start = time.monotonic()
        response = await next(request, ctx)
        elapsed_ms = (time.monotonic() - start) * 1000.0

        if elapsed_ms > 1000:
            self.logger.warning(
                "Slow request: %s %s took %.1fms",
                request.method,
                request.path,
                elapsed_ms,
            )

        return response


class TimeoutMiddleware:
    """Enforces request timeout.

    Raises ``RequestTimeoutFault`` on timeout so the exception flows
    through the fault system and ExceptionMiddleware can render a
    proper HTML or JSON response via content negotiation.
    """

    def __init__(self, timeout_seconds: float = 30.0):
        self.timeout = timeout_seconds

    async def __call__(self, request: Request, ctx: RequestCtx, next: Handler) -> Response:
        import asyncio

        try:
            return await asyncio.wait_for(next(request, ctx), timeout=self.timeout)
        except asyncio.TimeoutError:
            from .faults.domains import RequestTimeoutFault

            raise RequestTimeoutFault(
                detail=f"Request exceeded {self.timeout}s timeout",
            ) from None


class CORSMiddleware:
    """Handles CORS headers."""

    def __init__(
        self,
        allow_origins: list[str] | None = None,
        allow_methods: list[str] | None = None,
        allow_headers: list[str] | None = None,
        allow_credentials: bool = False,
        max_age: int = 3600,
    ):
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allow_headers = allow_headers or ["*"]
        self.allow_credentials = allow_credentials
        self.max_age = max_age

    async def __call__(self, request: Request, ctx: RequestCtx, next: Handler) -> Response:
        # Handle preflight
        if request.method == "OPTIONS":
            return self._preflight_response(request)

        # Process request
        response = await next(request, ctx)

        # Add CORS headers
        origin = request.header("origin")
        if origin and self._is_allowed_origin(origin):
            response.headers["access-control-allow-origin"] = origin
        elif "*" in self.allow_origins:
            response.headers["access-control-allow-origin"] = "*"

        if self.allow_credentials:
            response.headers["access-control-allow-credentials"] = "true"

        return response

    def _is_allowed_origin(self, origin: str) -> bool:
        """Check if origin is allowed."""
        return "*" in self.allow_origins or origin in self.allow_origins

    def _preflight_response(self, request: Request) -> Response:
        """Handle OPTIONS preflight request.

        ARCH-11: Validates ``Access-Control-Request-Method`` against the
        configured *allow_methods* list before echoing it back.  Returns
        403 if the requested method is not allowed.
        """
        requested_method = request.header("access-control-request-method")
        if requested_method and requested_method.upper() not in (m.upper() for m in self.allow_methods):
            return Response(b"", status=403, headers={})

        headers = {
            "access-control-allow-methods": ", ".join(self.allow_methods),
            "access-control-allow-headers": ", ".join(self.allow_headers),
            "access-control-max-age": str(self.max_age),
        }

        origin = request.header("origin")
        if origin and self._is_allowed_origin(origin):
            headers["access-control-allow-origin"] = origin
        elif "*" in self.allow_origins:
            headers["access-control-allow-origin"] = "*"

        if self.allow_credentials:
            headers["access-control-allow-credentials"] = "true"

        return Response(b"", status=204, headers=headers)


class CompressionMiddleware:
    """Compresses response bodies.

    Performance (v3 — scalability):
    - ``gzip.compress`` is offloaded to a thread pool via
      ``asyncio.to_thread()`` so the event loop is never blocked.
    - Pre-bound ``gzip.compress`` avoids repeated module-level lookup.
    """

    def __init__(self, minimum_size: int = 500):
        self.minimum_size = minimum_size
        import gzip as _gzip

        self._compress = _gzip.compress  # pre-bind for speed

    async def __call__(self, request: Request, ctx: RequestCtx, next: Handler) -> Response:
        import asyncio as _aio

        response = await next(request, ctx)

        # Check if client accepts gzip
        accept_encoding = request.header("accept-encoding", "") or ""
        if "gzip" not in accept_encoding.lower():
            return response

        # Don't compress streaming responses
        if hasattr(response._content, "__aiter__"):
            return response

        # Get body
        body = response._encode_body(response._content)

        # Only compress if large enough
        if len(body) < self.minimum_size:
            return response

        # Compress in a thread pool to avoid blocking the event loop
        compressed = await _aio.to_thread(self._compress, body)

        # Update response
        response._content = compressed
        response.headers["content-encoding"] = "gzip"
        response.headers["content-length"] = str(len(compressed))
        # ARCH-13: Vary header prevents caches from serving gzipped content
        # to clients that don't support it (and vice versa).
        response.headers["vary"] = "Accept-Encoding"

        return response

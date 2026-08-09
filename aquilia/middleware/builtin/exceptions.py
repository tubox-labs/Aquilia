"""Top-level exception handling and error rendering.

This was a 270-line class. The two pieces that did not belong to it — deciding
whether the client wants HTML, and mapping a fault to a status code — now live
in :mod:`aquilia.middleware.utils.negotiation` and
:mod:`aquilia.middleware.utils.status`, where they are testable without
constructing a request and reusable by the fault engine.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aquilia.debug.pages import render_debug_exception_page, render_http_error_page
from aquilia.faults import Fault, FaultDomain
from aquilia.faults.domains import HTTPFault
from aquilia.middleware.core.base import Middleware
from aquilia.middleware.core.priority import Priority
from aquilia.middleware.core.types import Handler
from aquilia.middleware.utils.negotiation import wants_html
from aquilia.middleware.utils.status import fault_to_status

if TYPE_CHECKING:
    from aquilia.controller.base import RequestCtx
    from aquilia.request import Request
    from aquilia.response import Response

__all__ = ["ExceptionMiddleware"]

# Last-resort HTML for when the error-page renderer itself crashes. A plain
# string with zero dependencies, because at this point nothing else is trusted.
FALLBACK_500_HTML = (
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


class ExceptionMiddleware(Middleware):
    """Converts exceptions into responses.

    HTML clients get a styled error page — with a full traceback only when
    ``debug`` is on. Everyone else gets structured JSON.

    Tracebacks and exception messages never appear in JSON, even in debug mode.
    They are rendered only into the HTML debug pages, which are useful locally
    and are not what an automated scanner scrapes.
    """

    name = "exception"
    priority = Priority.EXCEPTION

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.logger = logging.getLogger("aquilia.exceptions")

    # ── Rendering helpers ─────────────────────────────────────────────────

    def _html_response(self, body: str, status: int) -> Response:
        from aquilia.response import Response

        return Response(
            content=body.encode("utf-8"),
            status=status,
            headers={"content-type": "text/html; charset=utf-8"},
        )

    def _version(self) -> str:
        try:
            from aquilia import __version__

            return __version__
        except Exception:
            return ""

    def _render_exception_page(self, exc: BaseException, request: Request) -> Response:
        return self._html_response(
            render_debug_exception_page(exc, request, aquilia_version=self._version()),
            500,
        )

    def _render_error_page(self, status: int, message: str, detail: str, request: Request) -> Response:
        return self._html_response(
            render_http_error_page(status, message, detail, request, aquilia_version=self._version()),
            status,
        )

    def _render_html(
        self,
        exc: BaseException,
        request: Request,
        status: int,
        title: str,
        detail: str,
    ) -> Response:
        """Render an HTML error page, falling back to static HTML if the
        renderer itself raises — an error page that crashes is worse than a
        plain one."""
        try:
            if status >= 500 and self.debug:
                return self._render_exception_page(exc, request)
            return self._render_error_page(status, title, detail, request)
        except Exception as render_exc:
            self.logger.error(f"Error page renderer crashed: {render_exc}", exc_info=True)
            return self._html_response(FALLBACK_500_HTML, status)

    def _log(self, status: int, summary: str) -> None:
        if status >= 500:
            self.logger.error(summary)
        else:
            self.logger.warning(summary)

    # ── Handlers, one per exception family ────────────────────────────────

    def _handle_permission_error(self, exc: PermissionError, request: Request) -> Response:
        from aquilia.response import Response

        self.logger.warning(f"PermissionError: {exc}")
        # Raw detail only in debug; production gets a generic message so the
        # exception text cannot leak resource names or paths.
        detail = str(exc) if self.debug else "You do not have permission to access this resource."
        if wants_html(request):
            return self._render_html(exc, request, 403, "Forbidden", detail)
        return Response.json({"error": "Forbidden"}, status=403)

    def _handle_http_fault(self, exc: HTTPFault, request: Request) -> Response:
        from aquilia.response import Response

        status = exc.status
        reason = str(exc.message)
        detail = str(exc.detail or exc.message)
        self._log(status, f"HTTPFault {status} {exc.code}: {reason}")

        # Allow, Retry-After, WWW-Authenticate, and friends.
        extra_headers: dict[str, str] = exc.metadata.get("headers", {})

        if wants_html(request):
            response = self._render_html(exc, request, status, reason, detail)
        else:
            body: dict = {"error": {"code": exc.code, "message": reason, "status": status}}
            if exc.public and exc.detail:
                body["error"]["detail"] = exc.detail
            response = Response.json(body, status=status)

        for key, value in extra_headers.items():
            response.headers[key] = value
        return response

    def _handle_fault(self, exc: Fault, request: Request) -> Response:
        from aquilia.response import Response

        status = fault_to_status(exc)
        message = str(exc.message) if (exc.public or self.debug) else "Internal server error"
        self._log(status, f"Fault {exc.code}: {exc.message}")

        if wants_html(request):
            return self._render_html(exc, request, status, str(exc.code), message)

        error: dict = {
            "code": exc.code,
            "message": message,
            "domain": exc.domain.value if isinstance(exc.domain, FaultDomain) else str(exc.domain),
        }

        # Safe metadata for client-visible faults: always on 4xx, plus debug
        # mode for diagnosis. Keys prefixed with "_" are internal and never sent.
        metadata = getattr(exc, "metadata", None)
        if isinstance(metadata, dict) and (status < 500 or self.debug):
            public = {k: v for k, v in metadata.items() if not str(k).startswith("_")}
            if public:
                error["metadata"] = public

        # BP200 is the Contract validation fault; its per-field details are the
        # entire point of the response.
        if exc.code == "BP200" and metadata:
            details = metadata.get("details")
            if details:
                error["details"] = details

        return Response.json({"error": error}, status=status)

    def _handle_unexpected(self, exc: Exception, request: Request) -> Response:
        from aquilia.response import Response

        self.logger.error(f"Unhandled exception: {exc}", exc_info=True)

        if wants_html(request):
            return self._render_html(
                exc,
                request,
                500,
                "Internal Server Error",
                "An unexpected error occurred processing your request.",
            )

        # Never leak tracebacks or exception text into JSON, debug or not.
        return Response.json({"error": "Internal server error"}, status=500)

    # ── Entry point ───────────────────────────────────────────────────────

    async def handle(self, request: Request, ctx: RequestCtx, next_handler: Handler) -> Response:
        try:
            return await next_handler(request, ctx)
        except PermissionError as exc:
            return self._handle_permission_error(exc, request)
        except HTTPFault as exc:
            return self._handle_http_fault(exc, request)
        except Fault as exc:
            return self._handle_fault(exc, request)
        except Exception as exc:
            return self._handle_unexpected(exc, request)

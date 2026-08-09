"""Force HTTPS, with configurable exemptions for health checks and ACME probes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aquilia.middleware.core.base import Middleware
from aquilia.middleware.core.types import RequestHandler

if TYPE_CHECKING:
    from aquilia.controller.base import RequestCtx
    from aquilia.request import Request
    from aquilia.response import Response

Handler = RequestHandler


class HTTPSRedirectMiddleware(Middleware):
    """
    Redirect HTTP requests to HTTPS.

    Inspects the scheme from the ASGI scope, or from ``X-Forwarded-Proto``
    if behind a reverse proxy (requires ProxyFixMiddleware).

    Args:
        redirect_status: HTTP status for the redirect (301 or 307).
        exclude_paths: Paths to exclude from redirect (e.g. health checks).
        exclude_hosts: Hosts to exclude (e.g. localhost).
    """

    def __init__(
        self,
        redirect_status: int = 301,
        exclude_paths: list[str] | None = None,
        exclude_hosts: list[str] | None = None,
    ):
        self._status = redirect_status
        self._exclude_paths: set[str] = set(exclude_paths or [])
        self._exclude_hosts: set[str] = set(exclude_hosts or ["localhost", "127.0.0.1", "0.0.0.0"])

    async def __call__(self, request: Request, ctx: RequestCtx, next_handler: Handler) -> Response:
        scheme = request.state.get("forwarded_proto") or self._get_scheme(request)

        if scheme == "https":
            return await next_handler(request, ctx)

        # Check exclusions
        host = self._get_host(request)
        if host in self._exclude_hosts:
            return await next_handler(request, ctx)

        if request.path in self._exclude_paths:
            return await next_handler(request, ctx)

        # Build HTTPS URL
        redirect_url = f"https://{host}{request.path}"
        qs = request.header("raw-query") or request.state.get("query_string", "")
        if qs:
            redirect_url += f"?{qs}"

        from aquilia.response import Response

        return Response(
            b"",
            status=self._status,
            headers={"location": redirect_url},
        )

    def _get_scheme(self, request: Request) -> str:
        if hasattr(request, "_scope") and isinstance(request._scope, dict):
            return request._scope.get("scheme", "http")
        return "http"

    def _get_host(self, request: Request) -> str:
        host = request.header("host") or "localhost"
        # Strip port
        if ":" in host:
            host = host.split(":")[0]
        return host


__all__ = ["HTTPSRedirectMiddleware"]

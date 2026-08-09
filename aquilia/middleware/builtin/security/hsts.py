"""HTTP Strict Transport Security (RFC 6797)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aquilia.middleware.core.base import Middleware
from aquilia.middleware.core.types import RequestHandler

if TYPE_CHECKING:
    from aquilia.controller.base import RequestCtx
    from aquilia.request import Request
    from aquilia.response import Response

Handler = RequestHandler


class HSTSMiddleware(Middleware):
    """
    HTTP Strict Transport Security middleware.

    Sets the Strict-Transport-Security header on every response.

    Args:
        max_age: Duration (seconds) the browser should remember HTTPS-only.
        include_subdomains: Apply to subdomains.
        preload: Opt-in to browser HSTS preload lists.
    """

    def __init__(
        self,
        max_age: int = 31536000,  # 1 year
        include_subdomains: bool = True,
        preload: bool = False,
    ):
        parts = [f"max-age={max_age}"]
        if include_subdomains:
            parts.append("includeSubDomains")
        if preload:
            parts.append("preload")
        self._header_value = "; ".join(parts)

    async def __call__(self, request: Request, ctx: RequestCtx, next_handler: Handler) -> Response:
        response = await next_handler(request, ctx)
        response.headers["strict-transport-security"] = self._header_value
        return response


__all__ = ["HSTSMiddleware"]

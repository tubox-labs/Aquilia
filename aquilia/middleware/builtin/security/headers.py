"""Helmet-style catch-all security response headers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aquilia.middleware.core.base import Middleware
from aquilia.middleware.core.types import RequestHandler

if TYPE_CHECKING:
    from aquilia.controller.base import RequestCtx
    from aquilia.request import Request
    from aquilia.response import Response

Handler = RequestHandler


class SecurityHeadersMiddleware(Middleware):
    """
    Catch-all security headers middleware (like Helmet.js for Node).

    Applies sensible default security headers to every response:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY (or SAMEORIGIN)
    - X-XSS-Protection: 0 (modern browsers deprecated this)
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy (formerly Feature-Policy)
    - Cross-Origin-Opener-Policy
    - Cross-Origin-Embedder-Policy
    - Cross-Origin-Resource-Policy

    Args:
        frame_options: "DENY" or "SAMEORIGIN".
        referrer_policy: Referrer-Policy value.
        permissions_policy: Permissions-Policy directives dict.
        cross_origin_opener_policy: COOP value.
        cross_origin_embedder_policy: COEP value.
        cross_origin_resource_policy: CORP value.
        content_type_nosniff: Set X-Content-Type-Options.
        remove_server_header: Remove the Server header.
    """

    def __init__(
        self,
        frame_options: str = "DENY",
        referrer_policy: str = "strict-origin-when-cross-origin",
        permissions_policy: dict[str, str] | None = None,
        cross_origin_opener_policy: str = "same-origin",
        cross_origin_embedder_policy: str | None = None,
        cross_origin_resource_policy: str = "same-origin",
        content_type_nosniff: bool = True,
        remove_server_header: bool = True,
    ):
        self._headers: dict[str, str] = {}

        if content_type_nosniff:
            self._headers["x-content-type-options"] = "nosniff"

        self._headers["x-frame-options"] = frame_options
        # Modern browsers deprecated XSS Auditor; disable to avoid false positives
        self._headers["x-xss-protection"] = "0"
        self._headers["referrer-policy"] = referrer_policy
        self._headers["cross-origin-opener-policy"] = cross_origin_opener_policy
        self._headers["cross-origin-resource-policy"] = cross_origin_resource_policy

        if cross_origin_embedder_policy:
            self._headers["cross-origin-embedder-policy"] = cross_origin_embedder_policy

        # Permissions-Policy
        pp = permissions_policy or {
            "camera": "()",
            "microphone": "()",
            "geolocation": "()",
            "payment": "()",
            "usb": "()",
        }
        pp_parts = [f"{key}={value}" for key, value in pp.items()]
        self._headers["permissions-policy"] = ", ".join(pp_parts)

        self._remove_server = remove_server_header

    async def __call__(self, request: Request, ctx: RequestCtx, next_handler: Handler) -> Response:
        response = await next_handler(request, ctx)

        for name, value in self._headers.items():
            response.headers.setdefault(name, value)

        if self._remove_server and "server" in response.headers:
            del response.headers["server"]

        return response


__all__ = ["SecurityHeadersMiddleware"]

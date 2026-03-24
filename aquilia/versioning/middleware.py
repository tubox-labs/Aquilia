"""
Aquilia Versioning — Version Middleware

Injects the resolved API version into the ``RequestCtx`` on every
request. Also adds version response headers.

This middleware integrates with the ``VersionStrategy`` to:
1. Resolve the version from the request
2. Strip the version segment from the URL (if URL path versioning)
3. Store the version in ``request.state["api_version"]``
4. Add response headers (``X-API-Version``, ``Deprecation``, etc.)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

from .errors import (
    InvalidVersionError,
    MissingVersionError,
    UnsupportedVersionError,
    VersionSunsetError,
)
from .strategy import VersionStrategy

if TYPE_CHECKING:
    from ..controller.base import RequestCtx
    from ..request import Request
    from ..response import Response

logger = logging.getLogger("aquilia.versioning")


class VersionMiddleware:
    """
    Middleware that resolves API version for every request.

    Integrates with Aquilia's middleware stack::

        middleware_stack.add(
            VersionMiddleware(strategy),
            scope="global",
            priority=8,  # Before auth but after faults
            name="versioning",
        )

    After this middleware runs, the resolved version is available via:
    - ``request.state["api_version"]`` → ``ApiVersion`` instance
    - ``ctx.state["api_version"]`` → same
    - ``request.state["api_version_raw"]`` → raw string from request
    """

    def __init__(self, strategy: VersionStrategy) -> None:
        self._strategy = strategy

    @staticmethod
    def _wants_html(request: Request) -> bool:
        """Return True when the client prefers HTML responses."""
        try:
            accept = (request.header("accept") or "").lower()
        except Exception:
            accept = ""
        return "text/html" in accept

    @staticmethod
    def _aquilia_version() -> str:
        try:
            from aquilia import __version__

            return str(__version__)
        except Exception:
            return ""

    def _version_error_response(
        self,
        request: Request,
        *,
        status: int,
        error_code: str,
        message: str,
        detail: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> Response:
        from ..response import Response as Resp

        if self._wants_html(request):
            from ..debug import render_version_error_page

            html_body = render_version_error_page(
                status_code=status,
                error_code=error_code,
                message=message,
                detail=message,
                request=request,
                metadata=detail,
                aquilia_version=self._aquilia_version(),
            )
            merged_headers: dict[str, str] = {"content-type": "text/html; charset=utf-8"}
            if headers:
                merged_headers.update(headers)
            return Resp(
                content=html_body.encode("utf-8"),
                status=status,
                headers=merged_headers,
            )

        return Resp.json(
            {
                "error": error_code,
                "message": message,
                "detail": detail,
            },
            status=status,
            headers=headers,
        )

    async def __call__(
        self,
        request: Request,
        ctx: RequestCtx,
        next_handler: Any,
    ) -> Response:
        """
        Middleware handler.

        Resolves version, stores it, strips URL if needed,
        then passes to next middleware/handler.
        """
        from ..response import Response as Resp

        try:
            # Resolve version
            version = self._strategy.resolve(request)

            # Store in request state
            request.state["api_version"] = version
            request.state["api_version_str"] = str(version)

            # Strip version from URL path if using URL versioning
            stripped_path = self._strategy.strip_version_from_path(request)
            if stripped_path is not None:
                request.state["_original_path"] = request.path
                # Update the request path for routing
                if hasattr(request, "_path"):
                    request._path = stripped_path
                elif hasattr(request, "scope") and isinstance(request.scope, dict):
                    request.scope["path"] = stripped_path

        except MissingVersionError as e:
            logger.debug("Missing API version: %s", e)
            return self._version_error_response(
                request,
                status=400,
                error_code=e.code,
                message=str(e.message),
                detail=e.metadata,
            )

        except InvalidVersionError as e:
            logger.debug("Invalid API version: %s", e)
            return self._version_error_response(
                request,
                status=400,
                error_code=e.code,
                message=str(e.message),
                detail={"raw_version": e.raw_version},
            )

        except UnsupportedVersionError as e:
            logger.debug("Unsupported API version: %s", e)
            return self._version_error_response(
                request,
                status=400,
                error_code=e.code,
                message=str(e.message),
                detail={
                    "requested": str(e.version),
                    "supported": [str(v) for v in e.supported],
                },
            )

        except VersionSunsetError as e:
            logger.info("Sunset API version requested: %s", e.version)
            headers = self._strategy.get_response_headers(e.version)
            return self._version_error_response(
                request,
                status=410,
                error_code=e.code,
                message=str(e.message),
                detail={
                    "version": str(e.version),
                    "successor": str(e.successor) if e.successor else None,
                    "migration_url": e.migration_url,
                },
                headers=headers,
            )

        # Continue to next middleware/handler
        response = cast(Resp, await next_handler(request, ctx))

        # Add version response headers
        if version:
            version_headers = self._strategy.get_response_headers(version)
            for key, value in version_headers.items():
                response.headers[key] = value

        return response

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
from typing import Any, TYPE_CHECKING

from .core import ApiVersion, VERSION_NEUTRAL
from .errors import (
    InvalidVersionError,
    MissingVersionError,
    UnsupportedVersionError,
    VersionSunsetError,
)
from .strategy import VersionStrategy

if TYPE_CHECKING:
    from ..request import Request
    from ..response import Response
    from ..controller.base import RequestCtx

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

    async def __call__(
        self,
        request: "Request",
        ctx: "RequestCtx",
        next_handler: Any,
    ) -> "Response":
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
            return Resp.json(
                {
                    "error": e.code,
                    "message": str(e.message),
                    "detail": e.metadata,
                },
                status=400,
            )

        except InvalidVersionError as e:
            logger.debug("Invalid API version: %s", e)
            return Resp.json(
                {
                    "error": e.code,
                    "message": str(e.message),
                    "detail": {"raw_version": e.raw_version},
                },
                status=400,
            )

        except UnsupportedVersionError as e:
            logger.debug("Unsupported API version: %s", e)
            return Resp.json(
                {
                    "error": e.code,
                    "message": str(e.message),
                    "detail": {
                        "requested": str(e.version),
                        "supported": [str(v) for v in e.supported],
                    },
                },
                status=400,
            )

        except VersionSunsetError as e:
            logger.info("Sunset API version requested: %s", e.version)
            headers = self._strategy.get_response_headers(e.version)
            return Resp.json(
                {
                    "error": e.code,
                    "message": str(e.message),
                    "detail": {
                        "version": str(e.version),
                        "successor": str(e.successor) if e.successor else None,
                        "migration_url": e.migration_url,
                    },
                },
                status=410,
                headers=headers,
            )

        # Continue to next middleware/handler
        response = await next_handler(request, ctx)

        # Add version response headers
        if version:
            version_headers = self._strategy.get_response_headers(version)
            for key, value in version_headers.items():
                response.headers[key] = value

        return response

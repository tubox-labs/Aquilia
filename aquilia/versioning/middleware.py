"""
versioning/middleware.py — VersionMiddleware never mutates request.scope.
Routing has already happened by the time this middleware runs (asgi.py
resolves + matches before the middleware chain starts), so there is
nothing left for a path rewrite to do here, and rewriting scope["path"]
in place corrupts whatever the ASGI server / outer instrumentation
observes for this request.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

from aquilia.middleware import Middleware

from .errors import InvalidVersionError, MissingVersionError, UnsupportedVersionError, VersionError, VersionSunsetError
from .strategy import VersionStrategy

if TYPE_CHECKING:
    from ..request import Request
    from ..response import Response

logger = logging.getLogger("aquilia.versioning")

STATE_RESOLVED_VERSION = "_pre_resolved_api_version"
STATE_RESOLUTION_ERROR = "_version_resolution_error"
STATE_CONTROLLER_MATCH = "_controller_match"


def _wants_html(request: Request) -> bool:
    try:
        accept = (request.header("accept") or "").lower()
    except Exception:
        accept = ""
    if "text/html" in accept:
        return True
    try:
        user_agent = (request.header("user-agent") or "").lower()
    except Exception:
        user_agent = ""
    try:
        fetch_dest = (request.header("sec-fetch-dest") or "").lower()
    except Exception:
        fetch_dest = ""
    browser_hint = "mozilla" in user_agent or fetch_dest == "document"
    wildcard_accept = not accept or "*/*" in accept
    return browser_hint and wildcard_accept


def _aquilia_version() -> str:
    try:
        from aquilia import __version__

        return str(__version__)
    except Exception:
        return ""


def _version_error_response(request, *, status, error_code, message, detail, headers=None):
    from ..response import Response as Resp

    if _wants_html(request):
        from ..debug import render_version_error_page

        html_body = render_version_error_page(
            status_code=status,
            error_code=error_code,
            message=message,
            detail=message,
            request=request,
            metadata=detail,
            aquilia_version=_aquilia_version(),
        )
        merged = {"content-type": "text/html; charset=utf-8"}
        if headers:
            merged.update(headers)
        return Resp(content=html_body.encode("utf-8"), status=status, headers=merged)
    return Resp.json({"error": error_code, "message": message, "detail": detail}, status=status, headers=headers)


def build_version_error_response(strategy: VersionStrategy, request, exc: VersionError):
    """Single source of truth for VersionError -> HTTP Response, shared by
    asgi.py's fast pre-routing path and this middleware's mid-pipeline path
    so the two never drift."""
    if isinstance(exc, MissingVersionError):
        return _version_error_response(
            request, status=400, error_code=exc.code, message=str(exc.message), detail=exc.metadata
        )
    if isinstance(exc, InvalidVersionError):
        return _version_error_response(
            request, status=400, error_code=exc.code, message=str(exc.message), detail={"raw_version": exc.raw_version}
        )
    if isinstance(exc, UnsupportedVersionError):
        return _version_error_response(
            request,
            status=400,
            error_code=exc.code,
            message=str(exc.message),
            detail={"requested": str(exc.version), "supported": [str(v) for v in exc.supported]},
        )
    if isinstance(exc, VersionSunsetError):
        headers = strategy.get_response_headers(exc.version)
        return _version_error_response(
            request,
            status=410,
            error_code=exc.code,
            message=str(exc.message),
            detail={
                "version": str(exc.version),
                "successor": str(exc.successor) if exc.successor else None,
                "migration_url": exc.migration_url,
            },
            headers=headers,
        )
    return _version_error_response(
        request,
        status=400,
        error_code=getattr(exc, "code", "API_VERSION_ERROR"),
        message=str(getattr(exc, "message", exc)),
        detail=getattr(exc, "metadata", {}) or {},
    )


class VersionMiddleware(Middleware):
    def __init__(self, strategy: VersionStrategy) -> None:
        self._strategy = strategy

    def _resolved_version_for(self, request):
        cached = request.state.get(STATE_RESOLVED_VERSION)
        if cached is not None:
            return cached
        if self._strategy.is_structural_url_versioning:
            match = request.state.get(STATE_CONTROLLER_MATCH)
            if match is not None:
                route = getattr(match, "route", None)
                bound_version = getattr(route, "bound_version", None)
                if bound_version is not None:
                    return bound_version
        return None

    async def __call__(self, request, ctx, next_handler):
        pending_error = request.state.get(STATE_RESOLUTION_ERROR)
        if isinstance(pending_error, VersionError):
            return build_version_error_response(self._strategy, request, pending_error)

        version = self._resolved_version_for(request)
        routing_ran = STATE_CONTROLLER_MATCH in request.state

        if version is None:
            if not self._strategy.is_structural_url_versioning or not routing_ran:
                try:
                    version = self._strategy.resolve(request, check_sunset=False)
                    request.state[STATE_RESOLVED_VERSION] = version
                except VersionError as e:
                    return build_version_error_response(self._strategy, request, e)

        module_sunset_policy = None
        if version is not None:
            request.state["api_version"] = version
            request.state["api_version_str"] = str(version)
            ctx.state["api_version"] = version
            if not self._strategy.is_structural_url_versioning:
                if "_original_path" not in request.state:
                    request.state["_original_path"] = request.path

            # Retrieve module-level sunset policy override
            app_name = None
            match = request.state.get(STATE_CONTROLLER_MATCH)
            if match is not None:
                route = getattr(match, "route", None)
                app_name = getattr(route, "app_name", None)

            if app_name:
                # 1. Try manifest-level override first
                if hasattr(self._strategy, "_module_versioning_overrides"):
                    module_versioning = self._strategy._module_versioning_overrides.get(app_name)
                    if isinstance(module_versioning, dict):
                        module_sunset_policy = module_versioning.get("sunset_policy")

                # 2. Fallback to workspace-level override
                if module_sunset_policy is None and hasattr(self._strategy, "_workspace_modules"):
                    module_config = self._strategy._workspace_modules.get(app_name)
                    if isinstance(module_config, dict):
                        versioning_opts = module_config.get("versioning")
                        if isinstance(versioning_opts, dict):
                            module_sunset_policy = versioning_opts.get("sunset_policy")

            path = request.path if hasattr(request, "path") else "/"
            is_neutral = False
            if hasattr(self._strategy, "is_neutral_path"):
                is_neutral = self._strategy.is_neutral_path(path)

            if not is_neutral:
                try:
                    self._strategy.check_sunset(version, sunset_policy=module_sunset_policy)
                except VersionSunsetError as e:
                    return build_version_error_response(self._strategy, request, e)

        response = cast("Response", await next_handler(request, ctx))

        if version is not None:
            for key, value in self._strategy.get_response_headers(version, sunset_policy=module_sunset_policy).items():
                response.headers[key] = value
        return response

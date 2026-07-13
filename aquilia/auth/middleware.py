"""
AquilAuth - Unified Authentication Middleware

Resolves identity from pluggable backends on every request.
Stores the resolved identity on ``ctx.identity`` and ``request.state["identity"]``.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from aquilia.middleware import Handler, Middleware
from aquilia.request import Request
from aquilia.response import Response

if TYPE_CHECKING:
    from aquilia.di import RequestCtx
    from aquilia.sessions import SessionEngine

    from .backends.base import AuthBackend
    from .core import Identity
    from .manager import AuthManager

_log = logging.getLogger("aquilia.auth.middleware")


class AuthMiddleware(Middleware):
    """
    HTTP Middleware that authenticates incoming requests using backends.

    Resolves identity from pluggable backends on every request.
    Stores the resolved identity on ``ctx.identity`` and
    ``request.state["identity"]``.

    Args:
        auth_manager:    ``AuthManager`` instance for backend initialization.
        session_engine:  Optional ``SessionEngine``. Required when the
                         ``SessionBackend`` is configured.
        require_auth:    When ``True``, reject unauthenticated requests with
                         a 401.  Defaults to ``False`` (opt-in per route).
        backends:        Ordered list of active backends. Defaults to
                         ``TokenBackend`` and ``SessionBackend``.
        logger:          Optional logger.  Defaults to
                         ``aquilia.auth.middleware``.
    """

    def __init__(
        self,
        auth_manager: AuthManager,
        session_engine: SessionEngine | None = None,
        *,
        require_auth: bool = False,
        backends: list[AuthBackend] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.auth_manager = auth_manager
        self.session_engine = session_engine
        self.require_auth = require_auth
        self.logger = logger or _log

        _backends = (
            backends
            if backends is not None
            else [
                "aquilia.auth.backends.TokenBackend",
                "aquilia.auth.backends.SessionBackend",
            ]
        )
        from .backends.base import resolve_backend

        resolved_backends = [resolve_backend(b, auth_manager) for b in _backends]

        has_session = any(b.__class__.__name__ == "SessionBackend" for b in resolved_backends)
        if has_session and session_engine is None:
            raise ValueError("session_engine is required when 'session' backend is enabled.")

        self.backends = resolved_backends

    async def __call__(
        self,
        request: Request,
        ctx: RequestCtx,
        next: Handler,
    ) -> Response:
        """
        Resolve identity and call next handler.
        """
        # ── Phase 1: Resolve session ──
        session = None
        if self.session_engine is not None:
            container = getattr(ctx, "container", None)
            session = await self.session_engine.resolve(request, container)
            request.state["session"] = session
            ctx.session = session

        # ── Phase 2: Extract credentials and authenticate ──
        credentials: dict[str, Any] = {}

        # 1. Extract Bearer token
        auth_header = request.header("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            credentials["token"] = auth_header[7:]

        # 2. Extract API Key
        if auth_header and auth_header.startswith("ApiKey "):
            credentials["api_key"] = auth_header[7:]
        elif request.header("x-api-key"):
            credentials["api_key"] = request.header("x-api-key")

        # 3. Extract Session
        if session is not None:
            credentials["session"] = session

        identity: Identity | None = None
        for backend in self.backends:
            if backend.accepts(credentials):
                try:
                    identity = await backend.authenticate(credentials)
                    if identity is not None:
                        break
                except Exception as e:
                    # Propagate explicit auth faults (e.g. EXPIRED, REVOKED)
                    if hasattr(e, "code") and str(e.code).startswith("AUTH"):
                        raise
                    self.logger.warning(
                        f"Backend {backend.__class__.__name__} failed authentication: {e}",
                        exc_info=True,
                    )

        # ── Phase 3: Enforce auth requirement ──
        if self.require_auth and identity is None:
            return Response.json(
                {
                    "error": {
                        "code": "AUTH_REQUIRED",
                        "message": "Authentication required.",
                        "retryable": False,
                    }
                },
                status=401,
            )

        # ── Phase 4: Propagate identity ──
        request.state["identity"] = identity
        request.state["authenticated"] = identity is not None
        ctx.identity = identity

        initial_auth_state = session.is_authenticated if session is not None else False

        # ── Phase 5: Execute downstream ──
        response = await next(request, ctx)

        # ── Phase 6: Commit session ──
        if self.session_engine is not None and session is not None:
            privilege_changed = session.is_authenticated != initial_auth_state
            await self.session_engine.commit(
                session,
                response,
                privilege_changed=privilege_changed,
            )

        return response


__all__ = ["AuthMiddleware"]

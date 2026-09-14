"""
AquilAuth - Unified Middleware (Integration Layer)

This module contains the ``AquilAuthMiddleware`` used by the Aquilia server
during bootstrap (``aquilia/server.py``).  For new application code, prefer
the cleaner ``aquilia.auth.middleware.AuthMiddleware`` which is driven
directly from ``AquilaConfig.Auth``.

Middleware ordering::

    RequestScopeMiddleware          # creates DI container
    ExceptionMiddleware             # maps Fault -> HTTP status
    AquilAuthMiddleware             # this one - resolves identity
    <application handlers>
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from aquilia.auth.backends.base import resolve_backend
from aquilia.auth.core import Authentication, Identity
from aquilia.auth.faults import AUTH_REQUIRED
from aquilia.auth.integration.aquila_sessions import SessionAuthBridge, bind_identity, bind_token_claims
from aquilia.auth.integration.runtime_context import (
    AuthRuntimeContext,
    reset_auth_runtime_context,
    set_auth_runtime_context,
)
from aquilia.auth.manager import AuthManager
from aquilia.auth.state import AuthState, apply_auth_state_views, route_is_public
from aquilia.di import Container
from aquilia.di.providers import ValueProvider
from aquilia.faults import Fault, FaultDomain, FaultEngine
from aquilia.middleware.core.base import Middleware
from aquilia.middleware.core.types import Handler
from aquilia.request import Request
from aquilia.response import Response
from aquilia.sessions import SessionEngine

if TYPE_CHECKING:
    from aquilia.auth.backends import AuthBackend
    from aquilia.di import RequestCtx


# ============================================================================
# Unified Auth Middleware
# ============================================================================


class AquilAuthMiddleware(Middleware):
    """
    Unified middleware for Auth + Sessions + DI integration.

    Architecture (v2 — *authenticate, then enforce*):

    **Phase 1 — resolve session** (when a SessionEngine is mounted).

    **Phase 2 — optional authentication** through the configured strategies.
    Authentication **never raises here**: a failed credential is recorded on
    the canonical :class:`~aquilia.auth.state.AuthState` and the request
    stays anonymous. This is what makes public routes tolerant — an invalid
    or expired Bearer token on a ``@Public()`` route degrades to anonymous
    instead of rejecting the request (the passport-jwt ``@Public()``
    semantics).

    **Phase 3 — principal materialization**: the ``principal_factory``
    (``Auth.principal_factory`` dotted path) maps ``(identity, claims)`` to
    an application-defined principal, carried on ``auth_state.principal``
    and registered in the request DI container.

    **Phase 4 — canonical state propagation**: one write point
    (:func:`aquilia.auth.state.apply_auth_state_views`) sets every legacy
    mirror (``request.state["identity"|"authenticated"|"principal"|
    "token_claims"]``, ``ctx.identity``, ``ctx.auth_state``, the request-scoped
    ``Identity``/principal DI registrations).

    **Phase 5 — enforcement**: only now. The global ``require_auth`` flag
    rejects unauthenticated requests — *unless the matched route is*
    ``@Public()`` — by raising a fault, so the ExceptionMiddleware renders it
    through the application's configured ``error_renderer`` (auth errors use
    the same pluggable error contract as every other fault). A recorded
    resolution error is re-raised in preference to the generic
    ``AUTH_REQUIRED`` so protected routes keep precise 401s.

    **Phase 6 — handler** → **Phase 7 — session commit** (privilege-change
    aware).

    Order in middleware stack:
    1. RequestScopeMiddleware (creates DI container)
    2. FaultHandlerMiddleware / ExceptionMiddleware (fault handling — OUTSIDE
       auth, so faults raised here are rendered with the app's error contract)
    3. AquilAuthMiddleware (this one)
    4. Guard pipeline (engine) + application handlers
    """

    def __init__(
        self,
        session_engine: SessionEngine | None,
        auth_manager: AuthManager,
        fault_engine: FaultEngine | None = None,
        require_auth: bool = False,
        backends: list[AuthBackend] | None = None,
        logger: logging.Logger | None = None,
        principal_factory: Any = None,
    ):
        """
        Initialize unified auth middleware.

        Args:
            session_engine: Optional Aquilia SessionEngine instance.
            auth_manager: AquilAuth AuthManager instance.
            fault_engine: Optional FaultEngine for error handling.
            require_auth: If True, require authentication for all routes
                (routes marked ``@Public()`` are exempt).
            backends: Ordered list of active backends (strategy names,
                dotted paths, classes, or instances).
            logger: Optional logger instance.
            principal_factory: Optional ``callable(identity, claims) ->
                principal`` producing the application-defined principal.
        """
        self.session_engine = session_engine
        self.auth_manager = auth_manager
        self.session_bridge = SessionAuthBridge(session_engine) if session_engine is not None else None
        self.fault_engine = fault_engine
        self.require_auth = require_auth
        self.principal_factory = principal_factory
        self.logger = logger or logging.getLogger("aquilia.auth.middleware")

        _backends = backends if backends is not None else ["token", "session"]

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
        """Process request through the auth pipeline."""
        container = getattr(ctx, "container", None)

        # Phase 1: Resolve session if session engine is available
        session = None
        if self.session_engine is not None:
            session = await self.session_engine.resolve(request, container)
            request.state["session"] = session
            ctx.session = session

        auth_state = AuthState(session=session)

        auth_context = _RequestAuthContext(
            manager=self.auth_manager,
            request=request,
            session=session,
        )

        request.state["auth"] = auth_context
        ctx.auth = auth_context

        runtime_context = AuthRuntimeContext(
            request=request,
            session=session,
            auth=auth_context,
            container=container,
        )
        runtime_token = set_auth_runtime_context(runtime_context)

        try:
            # Phase 2: Optional authentication — never raises.
            credentials: dict[str, Any] = {}
            auth_header = request.header("authorization")
            token = None
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]
                credentials["token"] = token
            elif request.header("x-api-key"):
                credentials["api_key"] = request.header("x-api-key")
            elif auth_header and auth_header.startswith("ApiKey "):
                credentials["api_key"] = auth_header[7:]

            if session is not None:
                credentials["session"] = session

            for backend in self.backends:
                if not backend.accepts(credentials):
                    continue
                try:
                    result = await backend.authenticate(credentials)
                except Exception as e:
                    if hasattr(e, "code") and str(e.code).startswith("AUTH"):
                        # Record — do NOT raise. Enforcement (global flag or
                        # guard) decides whether this matters for the route;
                        # public/optional routes degrade to anonymous.
                        if auth_state.error is None:
                            auth_state.error = e
                        self.logger.debug(
                            "auth: strategy %s rejected credential (%s)",
                            backend.__class__.__name__,
                            getattr(e, "code", e),
                        )
                        continue
                    self.logger.warning(
                        "Backend %s failed authentication: %s", backend.__class__.__name__, e
                    )
                    continue

                if result is None:
                    continue

                # Unpack: Authentication (rich) or bare Identity (legacy).
                if isinstance(result, Authentication):
                    auth_state.identity = result.identity
                    auth_state.claims = result.claims
                    auth_state.principal = result.principal
                else:
                    auth_state.identity = result
                auth_state.strategy = backend.__class__.__name__

                # Sync identity to session if a token authenticated and a
                # session exists (legacy behavior preserved). Claims arrive
                # as a raw dict (token strategies) or a TokenClaims object —
                # normalize before the attribute-reading binder.
                if (
                    backend.__class__.__name__ in ("TokenBackend", "StatelessTokenBackend")
                    and session is not None
                    and token is not None
                ):
                    bind_identity(session, auth_state.identity)
                    try:
                        claims_obj = auth_state.claims
                        if isinstance(claims_obj, dict):
                            from aquilia.auth.core import TokenClaims

                            claims_obj = TokenClaims.from_dict(claims_obj)
                        elif claims_obj is None:
                            claims_obj = await self.auth_manager.verify_token(token)
                        if claims_obj is not None:
                            bind_token_claims(session, claims_obj)
                    except Exception as e:
                        # Session claims binding is best-effort; a malformed
                        # claims payload must not fail an authenticated request.
                        self.logger.debug("auth: session claims binding skipped (%s)", e)
                break

            # Phase 3: Application principal factory.
            if (
                auth_state.principal is None
                and self.principal_factory is not None
                and auth_state.identity is not None
            ):
                try:
                    auth_state.principal = self.principal_factory(auth_state.identity, auth_state.claims)
                except Exception as e:
                    self.logger.error("principal_factory raised; continuing without principal: %s", e)

            # Phase 4: Canonical state propagation (single write point for
            # every legacy mirror).
            initial_auth_state = session.is_authenticated if session is not None else False
            apply_auth_state_views(auth_state, request, ctx)
            runtime_context.identity = auth_state.identity

            if container is not None:
                if auth_state.identity is not None and not container.is_registered(Identity):
                    await container.register_instance(Identity, auth_state.identity, scope="request")
                principal = auth_state.principal
                if principal is not None:
                    principal_type = type(principal)
                    if not container.is_registered(principal_type):
                        await container.register_instance(principal_type, principal, scope="request")

            # Phase 5: Enforcement. Faults propagate to the ExceptionMiddleware,
            # which renders them through the configured error_renderer.
            is_public = route_is_public(request)
            if self.require_auth and not is_public and not auth_state.authenticated:
                denial = auth_state.error or AUTH_REQUIRED()
                # Commit the session before denying: rejected requests may
                # still have mutated session state (e.g. attempt counters,
                # the very first anonymous session's cookie) that must reach
                # the client. The rendered error response carries the
                # session headers via the fault's metadata.
                if self.session_engine is not None and session is not None:
                    try:
                        commit_target = Response(status=401)
                        privilege_changed = session.is_authenticated != initial_auth_state
                        await self.session_engine.commit(session, commit_target, privilege_changed=privilege_changed)
                        set_cookies = [v for k, v in commit_target.headers.items() if k.lower() == "set-cookie"]
                        if set_cookies:
                            existing = getattr(denial, "metadata", {}).get("headers", {})
                            existing.update({"Set-Cookie": ", ".join(set_cookies)})
                            denial.metadata["headers"] = existing
                    except Exception:
                        self.logger.debug("auth: session commit during denial failed", exc_info=True)
                raise denial

            # Phase 6: Execute handler
            try:
                response = await next(request, ctx)
            except Exception:
                # Let all exceptions propagate to ExceptionMiddleware
                # which properly maps Faults to HTTP status codes.
                raise

            runtime_context.response = response

            # Phase 7: Commit session
            if self.session_engine is not None and session is not None:
                privilege_changed = session.is_authenticated != initial_auth_state
                await self.session_engine.commit(session, response, privilege_changed=privilege_changed)

            return response
        finally:
            reset_auth_runtime_context(runtime_token)

    def _fault_to_response(self, fault_result: Any) -> Response:
        """Convert fault result to HTTP response."""

        # If the result is a Resolved with a response, use it
        if hasattr(fault_result, "value") and isinstance(fault_result.value, Response):
            return fault_result.value

        # If the result wraps a Fault, map to status code
        fault = getattr(fault_result, "fault", None) or getattr(fault_result, "original", None)
        if isinstance(fault, Fault):
            status_map = {
                FaultDomain.ROUTING: 404,
                FaultDomain.SECURITY: 401,  # Auth failures -> 401 (OWASP)
                FaultDomain.IO: 502,
                FaultDomain.EFFECT: 503,
            }
            status = status_map.get(fault.domain, 500)

            # Use public_message for client-facing response (never leak internals)
            message = getattr(fault, "public_message", None) or "Internal server error"
            return Response.json(
                {"error": {"code": fault.code, "message": message, "domain": fault.domain.value}},
                status=status,
            )

        # Fallback
        return Response.json(
            {"error": "Internal server error"},
            status=500,
        )


class _RequestAuthContext:
    """Request-scoped auth facade exposed via request.state and RequestCtx."""

    def __init__(self, manager: AuthManager, request: Request, session: Any | None):
        self._manager = manager
        self._request = request
        self._session = session

    async def sign_in(
        self,
        *,
        username: str,
        password: str,
        scopes: Any = None,
        session: str = "auto",
        client_metadata: dict[str, Any] | None = None,
    ) -> Any:
        return await self._manager.sign_in(
            username=username,
            password=password,
            scopes=scopes,
            session=session,
            client_metadata=client_metadata,
        )

    async def sign_out(
        self,
        *,
        scope: str = "session",
        identity_id: str | None = None,
        session_id: str | None = None,
    ) -> Any:
        return await self._manager.sign_out(
            scope=scope,
            identity_id=identity_id,
            session_id=session_id,
        )

    async def resume_identity(self, access_token: str | None = None) -> Any:
        return await self._manager.resume_identity(access_token=access_token)


# ============================================================================
# Optional Auth Middleware
# ============================================================================


class OptionalAuthMiddleware(AquilAuthMiddleware):
    """
    Auth middleware that does **not** require authentication.

    .. deprecated::
        Pass ``require_auth=False`` to :class:`AquilAuthMiddleware` directly,
        or use :class:`aquilia.auth.middleware.AuthMiddleware` for new code.
        This subclass will be removed in a future release.
    """

    def __init__(
        self,
        session_engine: SessionEngine | None,
        auth_manager: AuthManager,
        fault_engine: FaultEngine | None = None,
        backends: list[str] | None = None,
        logger: logging.Logger | None = None,
    ):
        import warnings

        warnings.warn(
            "OptionalAuthMiddleware is deprecated; use AquilAuthMiddleware(require_auth=False) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(
            session_engine=session_engine,
            auth_manager=auth_manager,
            fault_engine=fault_engine,
            require_auth=False,
            backends=backends,
            logger=logger,
        )


# ============================================================================
# Session-only Middleware
# ============================================================================


def _canonical_session_middleware() -> type[Middleware]:
    from aquilia.middleware.builtin.session import SessionMiddleware as _Builtin

    return _Builtin


class SessionMiddleware(_canonical_session_middleware()):  # type: ignore[misc, valid-type]
    """
    Session-only middleware without authentication.

    .. deprecated::
        This class was a fourth, weaker reimplementation of the session
        request lifecycle (no privilege-change tracking, sync DI
        registration) and was never mounted by the server. Use
        :class:`aquilia.middleware.builtin.session.SessionMiddleware` — the
        one canonical session middleware — instead. This alias is kept so
        existing imports keep working and will be removed in a future
        release.
    """

    def __init__(self, session_engine: SessionEngine | None = None, logger: logging.Logger | None = None):
        import warnings

        warnings.warn(
            "aquilia.auth.integration.middleware.SessionMiddleware is deprecated; "
            "use aquilia.middleware.builtin.session.SessionMiddleware instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(session_engine)
        if logger is not None:
            self.logger = logger

    @property
    def session_engine(self) -> SessionEngine | None:
        """Historical attribute name (the canonical one is ``engine``)."""
        return self.engine

    @session_engine.setter
    def session_engine(self, value: SessionEngine | None) -> None:
        self.engine = value


# ============================================================================
# Fault Handler Middleware
# ============================================================================


class FaultHandlerMiddleware(Middleware):
    """
    Middleware for handling faults with FaultEngine.

    Should be registered early in middleware stack.
    """

    def __init__(
        self,
        fault_engine: FaultEngine,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize fault handler middleware.

        Args:
            fault_engine: FaultEngine instance
            logger: Optional logger
        """
        self.fault_engine = fault_engine
        self.logger = logger or logging.getLogger("aquilia.faults.middleware")

    async def __call__(
        self,
        request: Request,
        ctx: RequestCtx,
        next: Handler,
    ) -> Response:
        """Process request with fault handling."""
        try:
            return await next(request, ctx)
        except Exception as e:
            # Process fault
            from aquilia.faults import Resolved

            result = await self.fault_engine.process(e)

            if isinstance(result, Resolved):
                # Fault was resolved, return response
                if hasattr(result, "response") and result.response:
                    return result.response

                # Create response from fault
                if hasattr(e, "error_code"):
                    # Structured fault — map domain to HTTP status
                    from aquilia.faults import FaultDomain

                    status_map = {
                        FaultDomain.ROUTING: 404,
                        FaultDomain.SECURITY: 401,
                        FaultDomain.IO: 502,
                        FaultDomain.EFFECT: 503,
                    }
                    fault_domain = getattr(e, "domain", None)
                    status = status_map.get(fault_domain, 500)
                    return Response.json(
                        {
                            "error": {
                                "code": e.error_code,
                                "message": e.public_message,
                                "retryable": e.retryable,
                            }
                        },
                        status=status,
                    )
                else:
                    # Unknown error
                    self.logger.error(f"Unhandled exception: {e}", exc_info=True)
                    return Response.json(
                        {"error": "Internal server error"},
                        status=500,
                    )
            else:
                # Fault not resolved, re-raise
                raise


# ============================================================================
# Request Scope Middleware (Enhanced)
# ============================================================================


class EnhancedRequestScopeMiddleware(Middleware):
    """
    Enhanced request scope middleware with better integration.

    Creates request-scoped DI container and provides access to:
    - Request object
    - Session (if SessionMiddleware is used)
    - Identity (if AuthMiddleware is used)
    """

    def __init__(
        self,
        app_container: Container,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize request scope middleware.

        Args:
            app_container: App-scoped DI container
            logger: Optional logger
        """
        self.app_container = app_container
        self.logger = logger or logging.getLogger("aquilia.di.middleware")

    async def __call__(
        self,
        request: Request,
        ctx: RequestCtx,
        next: Handler,
    ) -> Response:
        """Process request with request-scoped DI."""
        # Create request-scoped container
        request_container = self.app_container.create_request_scope()

        # Store in context
        ctx.container = request_container
        request.state["di_container"] = request_container

        # Register request in DI

        request_container.register(
            ValueProvider(
                value=request,
                token=Request,
                scope="request",
            )
        )

        try:
            # Execute handler
            response = await next(request, ctx)
        finally:
            # Cleanup request-scoped resources
            # Properly dispose of the request-scoped container to release
            # any held resources (DB connections, file handles, etc.)
            try:
                if hasattr(request_container, "shutdown"):
                    await request_container.shutdown()
                elif hasattr(request_container, "dispose"):
                    request_container.dispose()
            except Exception:
                pass

        return response


# ============================================================================
# Complete Middleware Stack Factory
# ============================================================================


def create_auth_middleware_stack(
    session_engine: SessionEngine | None,
    auth_manager: AuthManager,
    app_container: Container,
    fault_engine: FaultEngine | None = None,
    require_auth: bool = False,
    backends: list[str] | None = None,
) -> list[Middleware]:
    """
    Create complete middleware stack for authenticated app.

    Args:
        session_engine: Optional SessionEngine instance.
        auth_manager: AuthManager instance.
        app_container: App-scoped DI container.
        fault_engine: Optional FaultEngine.
        require_auth: Require auth for all routes.
        backends: Ordered list of active backends.

    Returns:
        List of middleware in correct order.
    """
    stack = []

    # 1. Request scope (creates DI container)
    stack.append(EnhancedRequestScopeMiddleware(app_container))

    # 2. Fault handler (catches errors)
    if fault_engine:
        stack.append(FaultHandlerMiddleware(fault_engine))

    # 3. Auth + Sessions (authentication)
    stack.append(
        AquilAuthMiddleware(
            session_engine=session_engine,
            auth_manager=auth_manager,
            fault_engine=fault_engine,
            require_auth=require_auth,
            backends=backends,
        )
    )

    return stack


# ============================================================================
# Exports
# ============================================================================


__all__ = [
    "AquilAuthMiddleware",
    "OptionalAuthMiddleware",
    "SessionMiddleware",
    "FaultHandlerMiddleware",
    "EnhancedRequestScopeMiddleware",
    "create_auth_middleware_stack",
]

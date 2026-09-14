"""
AquilAuth - Guard System

Single guard protocol and concrete implementations.

Design (inspired by NestJS ``CanActivate`` and DRF ``BasePermission``):
    * **Async-capable guards** — implement ``async def can_activate(ctx)
      -> bool`` (the NestJS ``CanActivate`` contract: return ``True`` to
      allow, ``False`` or raise to deny). Guards may perform real async
      work: JWT verification, permission-table lookups, policy services.
    * Legacy sync guards (``def check(ctx) -> None`` — raise on denial)
      remain fully supported and run through the same pipeline.
    * ``AuthGuard``, ``RoleGuard``, ``ScopeGuard``, ``PolicyGuard`` cover 95 % of use-cases.
    * Guards are composable: pass a list to any helper that accepts them.
    * All guards are first-class and can be used directly as class references
      in pipelines (e.g., ``pipeline = [AuthGuard]``) or as instances
      (e.g., ``pipeline = [AuthGuard()]``).
    * :class:`GuardPipeline` merges global (``global_guards`` / manifest),
      module (``AppManifest.guards``), class, and route (``@UseGuards``)
      guards and runs them with ``@Public()`` semantics.

Usage in a controller::

    from aquilia.auth.guards import AuthGuard, RoleGuard
    from aquilia.controller.decorators import UseGuards

    @UseGuards(AuthGuard, RoleGuard("admin"))
    @DELETE("/users/{id}")
    async def delete_user(self, ctx: RequestCtx) -> Response:
        ...
"""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from aquilia.faults.domains import DIResolutionFault

if TYPE_CHECKING:
    from aquilia.auth.core import Identity


# ============================================================================
# Protocol
# ============================================================================


@runtime_checkable
class Guard(Protocol):
    """
    Structural protocol for security guards.

    Two supported shapes:

    **Async (preferred — the NestJS ``CanActivate`` contract)::**

        class TenantGuard:
            async def can_activate(self, ctx: GuardContext) -> bool:
                return await self._load_tenants(ctx.identity)  # real async I/O

        Returning ``False`` denies with the guard's ``denial_fault``
        (default ``AUTHZ_RESOURCE_FORBIDDEN``); raising a specific fault
        denies with it.

    **Legacy sync**::

        def check(self, ctx) -> None:
            ...  # raise on denial

    Guards must be stateless so they can be instantiated once and reused
    across requests.
    """

    def check(self, ctx: Any) -> None:
        """
        Evaluate the guard condition (legacy synchronous contract).

        Args:
            ctx: Request context object.  Must expose ``identity`` as an
                 attribute or ``ctx["identity"]`` as a dict key.

        Raises:
            ``AUTH_REQUIRED``:          No authenticated identity.
            ``AUTHZ_INSUFFICIENT_ROLE``: Required role is absent.
            ``AUTHZ_INSUFFICIENT_SCOPE``: Required scope is absent.
            ``AUTHZ_POLICY_DENIED``:    Authorization policy denied access.
        """
        ...


# ============================================================================
# Guard Context — what a guard sees
# ============================================================================


class GuardContext:
    """
    The execution context handed to ``can_activate`` guards.

    Wraps the canonical :class:`~aquilia.auth.state.AuthState` (single source
    of truth) plus the request/DI surface guards legitimately need:

    * ``identity``  — the framework ``Identity`` or ``None``
    * ``principal`` — the application principal when configured
    * ``user``      — principal if present, else identity
    * ``claims``    — verified token claims (token strategies)
    * ``request`` / ``ctx`` — the raw request and ``RequestCtx``
    * ``container`` — request-scoped DI container (resolve services)
    * ``route_metadata`` / ``path_params`` — the matched route
    * ``await resolve_identity()`` — proactively authenticate from the
      request's Bearer token when no identity is set yet (the middleware
      already does this; the helper exists for standalone pipeline use)
    """

    __slots__ = (
        "request",
        "ctx",
        "container",
        "auth_state",
        "route_metadata",
        "path_params",
        "is_public",
        "_identity_resolved",
    )

    def __init__(
        self,
        request: Any = None,
        ctx: Any = None,
        auth_state: Any = None,
        route_metadata: Any = None,
        path_params: dict[str, Any] | None = None,
        is_public: bool = False,
    ) -> None:
        self.request = request
        self.ctx = ctx
        self.auth_state = auth_state
        self.route_metadata = route_metadata
        self.path_params = path_params or {}
        self.is_public = is_public
        self._identity_resolved = False

        container = getattr(ctx, "container", None) if ctx is not None else None
        if container is None and request is not None:
            state = getattr(request, "state", None)
            if state is not None:
                container = state.get("di_container") if hasattr(state, "get") else None
        self.container = container

    # ── Derived views over the canonical auth state ──────────────────────

    @property
    def auth_manager(self) -> Any | None:
        if self.container is not None:
            from aquilia.auth.manager import AuthManager

            try:
                if hasattr(self.container, "resolve"):
                    return self.container.resolve(AuthManager, optional=True)
            except Exception:
                return None
        return None

    def _state(self) -> Any:
        state = self.auth_state
        if state is not None:
            return state
        # Fall back to the request's canonical state when only request/ctx
        # were provided.
        for surface in (self.ctx, self.request):
            if surface is None:
                continue
            candidate = getattr(surface, "auth_state", None)
            if candidate is None and self.request is not None:
                rs = getattr(self.request, "state", None)
                if rs is not None and hasattr(rs, "get"):
                    candidate = rs.get("auth_state")
            if candidate is not None:
                return candidate
        return None

    @property
    def identity(self) -> Any | None:
        state = self._state()
        if state is not None:
            return state.identity
        ident = getattr(self.ctx, "identity", None) if self.ctx is not None else None
        if ident is None and self.request is not None:
            rs = getattr(self.request, "state", None)
            if rs is not None and hasattr(rs, "get"):
                ident = rs.get("identity")
        return ident

    @property
    def principal(self) -> Any | None:
        state = self._state()
        if state is not None:
            return state.principal
        if self.request is not None:
            rs = getattr(self.request, "state", None)
            if rs is not None and hasattr(rs, "get"):
                return rs.get("principal")
        return None

    @property
    def user(self) -> Any | None:
        return self.principal if self.principal is not None else self.identity

    @property
    def claims(self) -> dict[str, Any] | None:
        state = self._state()
        if state is not None:
            return state.claims
        if self.request is not None:
            rs = getattr(self.request, "state", None)
            if rs is not None and hasattr(rs, "get"):
                return rs.get("token_claims")
        return None

    @property
    def session(self) -> Any | None:
        state = self._state()
        if state is not None and getattr(state, "session", None) is not None:
            return state.session
        if self.ctx is not None:
            return getattr(self.ctx, "session", None)
        return None

    # ── Attribute/dict compatibility with legacy guards ─────────────────

    def get(self, key: str, default: Any = None) -> Any:
        if key == "identity":
            return self.identity
        if key == "session":
            return self.session
        if key == "container":
            return self.container
        if key == "request":
            return self.request
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        value = self.get(key)
        if value is None and key not in ("identity", "session", "container", "request"):
            raise KeyError(key)
        return value

    async def resolve_identity(self) -> Any | None:
        """
        Proactively authenticate from the request's Bearer token.

        Returns the resolved identity (registering it on the auth state) or
        ``None`` when no verifiable credential is present. Raises nothing —
        guards decide what an unauthenticated request means.
        """
        if self._identity_resolved:
            return self.identity
        self._identity_resolved = True

        if self.identity is not None:
            return self.identity

        request = self.request
        if request is None:
            return None
        auth_header = ""
        if hasattr(request, "header") and callable(request.header):
            auth_header = request.header("authorization", "") or ""
        else:
            headers = getattr(request, "headers", None)
            if headers and hasattr(headers, "get"):
                auth_header = headers.get("authorization", "") or ""

        if not auth_header.startswith("Bearer "):
            return None
        token = auth_header[7:]

        auth_manager = self.auth_manager
        if auth_manager is None:
            return None
        try:
            identity = await auth_manager.get_identity_from_token(token)
        except Exception:
            return None
        if identity is None:
            return None

        state = self._state()
        if state is not None:
            try:
                state.identity = identity
            except Exception:
                pass
        if self.ctx is not None:
            try:
                self.ctx.identity = identity
            except Exception:
                pass
        if request is not None:
            rs = getattr(request, "state", None)
            if rs is not None and hasattr(rs, "__setitem__"):
                rs["identity"] = identity
        return identity


# ============================================================================
# Guard execution — universal runner + pipeline
# ============================================================================


def is_authentication_guard(guard: Any) -> bool:
    """
    Whether a guard is an *authentication* guard (skipped on @Public routes).

    ``AuthGuard`` qualifies by default; any guard may opt in or out by
    setting ``authentication_guard = True`` / ``False`` on the class or
    instance — the explicit attribute always wins over the AuthGuard
    default (so an ``AuthGuard`` subclass can re-enable itself on public
    routes with ``authentication_guard = False``).
    """
    if isinstance(guard, type):
        return getattr(guard, "authentication_guard", False) is True

    declared = getattr(guard, "authentication_guard", None)
    if declared is not None:
        return declared is True

    from aquilia.auth.guards import AuthGuard

    return isinstance(guard, AuthGuard)


def _instantiate(guard: Any) -> Any:
    return guard() if inspect.isclass(guard) else guard


async def run_guard(guard: Any, ctx: Any) -> bool:
    """
    Run one guard against *ctx* (a :class:`GuardContext` or legacy context).

    Supports, in order:

    1. ``async def can_activate(ctx) -> bool`` — the async contract;
       ``False`` denies with the guard's ``denial_fault`` (or
       ``AUTHZ_RESOURCE_FORBIDDEN``). ``True`` and ``None`` allow (the
       NestJS ``CanActivate`` truthy contract — a guard with no opinion
       does not deny); raise to deny with a specific fault.
    2. ``def check(ctx) -> None`` — the legacy sync contract (raises on
       denial).
    3. Any callable — called with ctx; an awaitable result is awaited;
       ``False`` denies.

    Returns ``True`` when the guard allows the request.
    """
    from aquilia.auth.faults import AUTHZ_RESOURCE_FORBIDDEN

    guard_inst = _instantiate(guard)

    can_activate = getattr(guard_inst, "can_activate", None)
    if callable(can_activate):
        result = can_activate(ctx)
        if inspect.isawaitable(result):
            result = await result
        if result is False:
            denial = getattr(guard_inst, "denial_fault", None)
            if denial is not None:
                raise denial() if isinstance(denial, type) else denial
            raise AUTHZ_RESOURCE_FORBIDDEN()
        return True

    check = getattr(guard_inst, "check", None)
    if callable(check):
        result = check(ctx)
        if inspect.isawaitable(result):
            await result
        return True

    if callable(guard_inst):
        result = guard_inst(ctx)
        if inspect.isawaitable(result):
            result = await result
        if result is False:
            raise AUTHZ_RESOURCE_FORBIDDEN()
        return True

    return True


class GuardPipeline:
    """
    Merges and executes the guard chain for a route.

    Guard sources, executed in order:

    1. **Global guards** — ``AquilaConfig.Auth.global_guards`` (the NestJS
       ``APP_GUARD`` equivalent) and guards registered on this pipeline;
    2. **Module guards** — ``AppManifest.guards`` (stamped on the compiled
       route at load time);
    3. **Route guards** — ``@UseGuards(...)`` on the controller class or
       handler method.

    ``@Public()`` semantics: authentication guards are skipped on public
    routes; authorization guards (roles/scopes/policies) still run.
    """

    def __init__(self, global_guards: list[Any] | None = None) -> None:
        self.global_guards: list[Any] = list(global_guards or [])

    def add_global(self, *guards: Any) -> None:
        """Register additional global guards (idempotent per guard object)."""
        for g in guards:
            if g not in self.global_guards:
                self.global_guards.append(g)

    @staticmethod
    def collect_route_guards(route: Any, route_metadata: Any) -> list[Any]:
        """Guards declared on the compiled route / its metadata."""
        guards: list[Any] = []
        module_guards = getattr(route, "module_guards", None)
        if module_guards:
            guards.extend(module_guards)
        raw = getattr(route_metadata, "_raw_metadata", None) or {}
        route_level = raw.get("guards") if isinstance(raw, dict) else None
        if route_level:
            guards.extend(route_level)
        return guards

    async def run(
        self,
        route: Any = None,
        route_metadata: Any = None,
        request: Any = None,
        ctx: Any = None,
        auth_state: Any = None,
        is_public: bool | None = None,
    ) -> None:
        """
        Execute the full guard chain; raises the first denial fault.

        Returns silently when every guard allows the request (or when no
        guards apply at all).
        """
        from aquilia.auth.state import route_is_public

        if is_public is None:
            is_public = route_is_public(request)

        guards: list[Any] = list(self.global_guards)
        if route is not None or route_metadata is not None:
            guards.extend(self.collect_route_guards(route, route_metadata))

        if not guards:
            return

        gctx = GuardContext(
            request=request,
            ctx=ctx,
            auth_state=auth_state,
            route_metadata=route_metadata,
            path_params=getattr(request, "path_params", None) if request is not None else None,
            is_public=is_public,
        )

        for guard in guards:
            if is_public and is_authentication_guard(guard):
                continue
            await run_guard(guard, gctx)


# ============================================================================
# Helpers
# ============================================================================


def _get_identity(ctx: Any) -> Identity | None:
    """
    Extract ``Identity`` from request context using attribute or dict lookup.

    This is the single, canonical extraction path.  Controllers set
    ``ctx.identity`` (or ``request.state["identity"]``) via middleware; guards
    always read from the same location.
    """
    from unittest.mock import Mock

    if ctx is None:
        return None

    def get_from_session(c: Any) -> Any | None:
        session = getattr(c, "session", None)
        if session is None and isinstance(c, dict):
            session = c.get("session")
        if session is None and hasattr(c, "request"):
            req = c.request
            if req is not None and hasattr(req, "state"):
                state = req.state
                if state is not None and not isinstance(state, Mock):
                    if isinstance(state, dict) or hasattr(state, "get"):
                        session = state.get("session")
        if session is not None and not isinstance(session, Mock):
            if getattr(session, "is_authenticated", False) and session.principal is not None:
                return session.principal
        return None

    if isinstance(ctx, Mock):
        if hasattr(ctx, "identity"):
            ident = ctx.identity
            if ident is not None and not isinstance(ident, Mock):
                return ident
        ident = get_from_session(ctx)
        if ident is not None:
            return ident
        return None

    if hasattr(ctx, "identity"):
        ident = ctx.identity
        if ident is not None and not isinstance(ident, Mock):
            return ident
    if isinstance(ctx, dict):
        ident = ctx.get("identity")
        if ident is not None and not isinstance(ident, Mock):
            return ident

    ident = get_from_session(ctx)
    if ident is not None:
        return ident

    return None


# ============================================================================
# Concrete Guards
# ============================================================================


class AuthGuard:
    """
    Require an authenticated identity.

    When *optional* is ``True`` the guard passes even for unauthenticated
    requests; use this for endpoints that serve both authenticated and
    anonymous users.

    Can be used as a class reference ``AuthGuard`` or instance ``AuthGuard()``.

    Marks itself as an *authentication* guard (``authentication_guard =
    True``): the guard pipeline skips it on ``@Public()`` routes, and the
    protect-by-default middleware exempts public routes from it.

    Args:
        auth_manager: Optional authentication manager (resolved via DI if omitted).
        optional: When ``True``, allow unauthenticated requests through.
                  Defaults to ``False`` (strict authentication required).
    """

    #: Skipped by the guard pipeline on ``@Public()`` routes.
    authentication_guard = True

    def __init__(self, auth_manager: Any | None = None, *, optional: bool = False) -> None:
        self.auth_manager = auth_manager
        self.optional = optional

    def check(self, ctx: Any) -> None:
        """
        Assert that *ctx* has an authenticated identity.

        Raises:
            ``AUTH_REQUIRED``: No identity found and *optional* is ``False``.
        """
        identity = _get_identity(ctx)
        if identity is None and not self.optional:
            from aquilia.auth.faults import AUTH_REQUIRED

            raise AUTH_REQUIRED()

    async def can_activate(self, ctx: Any) -> bool:
        """
        Async contract: allow only authenticated requests.

        Accepts a :class:`GuardContext` (preferred — resolves identity
        proactively from the request's Bearer token when not yet set) or any
        legacy context shape. Raises ``AUTH_REQUIRED`` on denial — or the
        precise resolution error recorded by the auth middleware (invalid /
        expired / revoked token) when one exists, so protected routes keep
        their exact 401 reason codes.
        """
        identity = getattr(ctx, "identity", None) if not isinstance(ctx, dict) else ctx.get("identity")
        if identity is None and isinstance(ctx, GuardContext):
            identity = await ctx.resolve_identity()
        if identity is None:
            identity = _get_identity(ctx)
        if identity is None and not self.optional:
            state = getattr(ctx, "auth_state", None)
            error = getattr(state, "error", None)
            if error is not None:
                raise error
            from aquilia.auth.faults import AUTH_REQUIRED

            raise AUTH_REQUIRED()
        return True

    async def _proactive_authenticate(self, ctx: Any) -> None:
        """Proactively perform token-based authentication if identity is missing."""
        if _get_identity(ctx) is not None:
            return

        container = getattr(ctx, "container", None)
        if container is None and isinstance(ctx, dict):
            container = ctx.get("container")

        if container is None:
            if self.optional:
                return
            from aquilia.auth.faults import AUTH_REQUIRED

            raise AUTH_REQUIRED()

        from aquilia.auth.manager import AuthManager

        auth_manager = self.auth_manager
        if auth_manager is None:
            try:
                if hasattr(container, "resolve_async"):
                    auth_manager = await container.resolve_async(AuthManager, optional=True)
                elif hasattr(container, "resolve"):
                    maybe_resolved = container.resolve(AuthManager, optional=True)
                    if hasattr(maybe_resolved, "__await__"):
                        auth_manager = await maybe_resolved
                    else:
                        auth_manager = maybe_resolved
            except DIResolutionFault:
                raise
            except Exception as exc:
                raise DIResolutionFault(
                    provider="AuthGuard",
                    reason=f"Guard 'AuthGuard' failed resolving AuthManager: {exc}",
                ) from exc

        if auth_manager is None:
            raise DIResolutionFault(
                provider="AuthGuard",
                reason="Guard 'AuthGuard' requires AuthManager but no provider was found.",
            )

        request = getattr(ctx, "request", None)
        if request is None and isinstance(ctx, dict):
            request = ctx.get("request")

        if request is None:
            if self.optional:
                return
            from aquilia.auth.faults import AUTH_REQUIRED

            raise AUTH_REQUIRED()

        auth_header = ""
        if hasattr(request, "headers") and request.headers is not None:
            if hasattr(request.headers, "get"):
                auth_header = request.headers.get("authorization", "") or ""
        elif hasattr(request, "header") and callable(request.header):
            auth_header = request.header("authorization", "") or ""

        if not auth_header.startswith("Bearer "):
            if self.optional:
                return
            from aquilia.auth.faults import AUTH_REQUIRED

            raise AUTH_REQUIRED()

        token = auth_header[7:]

        from aquilia.auth.faults import AUTH_TOKEN_INVALID

        try:
            identity = await auth_manager.get_identity_from_token(token)
            if not identity:
                if self.optional:
                    return
                raise AUTH_TOKEN_INVALID()

            if hasattr(ctx, "identity"):
                ctx.identity = identity
            if isinstance(ctx, dict):
                ctx["identity"] = identity

            claims = await auth_manager.verify_token(token)
            if hasattr(ctx, "state") and isinstance(ctx.state, dict):
                ctx.state["token_claims"] = claims
            if isinstance(ctx, dict):
                ctx["token_claims"] = claims
        except Exception as e:
            if isinstance(e, AUTH_TOKEN_INVALID):
                raise
            if self.optional:
                return
            raise AUTH_TOKEN_INVALID() from e

    async def __call__(self, ctx: Any = None, *args: Any, **kwargs: Any) -> None:
        """
        Allow first-class pipeline execution when referenced as a class or instance.
        """
        resolved_ctx = None
        for candidate in (ctx,) + args + tuple(kwargs.values()):
            if candidate is not None and (
                hasattr(candidate, "identity")
                or hasattr(candidate, "session")
                or hasattr(candidate, "user")
                or hasattr(candidate, "container")
            ):
                resolved_ctx = candidate
                break

        if resolved_ctx is None:
            if ctx is not None:
                resolved_ctx = ctx
            elif len(args) > 0:
                resolved_ctx = args[0]

        await self._proactive_authenticate(resolved_ctx)
        self.check(resolved_ctx)


class RoleGuard:
    """
    Require that the authenticated identity holds all specified roles.

    Role check respects role inheritance defined in a ``PermissionEngine``.
    When no engine is provided the check is a direct membership test against
    ``identity.get_attribute("roles", [])``.

    Args:
        *roles:  One or more role names that the identity must hold.
        engine:  Optional ``PermissionEngine`` for inheritance-aware checks.
        require_all: When ``True`` (default) all roles must be present.
                     When ``False``, at least one role suffices.
    """

    def __init__(
        self,
        *roles: str,
        engine: Any | None = None,
        require_all: bool = True,
    ) -> None:
        self.roles = list(roles)
        self.engine = engine
        self.require_all = require_all

    def check(self, ctx: Any) -> None:
        """
        Assert that *ctx.identity* holds the required roles.

        Raises:
            ``AUTH_REQUIRED``:          No identity found.
            ``AUTHZ_INSUFFICIENT_ROLE``: Required role(s) are absent.
        """
        from aquilia.auth.faults import AUTH_REQUIRED

        identity = _get_identity(ctx)
        if identity is None:
            raise AUTH_REQUIRED()
        self._evaluate_roles(identity, ctx)

    async def can_activate(self, ctx: Any) -> bool:
        """
        Async contract — same evaluation as :meth:`check`, with proactive
        identity resolution when handed a :class:`GuardContext`.
        """
        from aquilia.auth.faults import AUTH_REQUIRED

        identity = None
        if isinstance(ctx, GuardContext):
            identity = ctx.identity
            if identity is None:
                identity = await ctx.resolve_identity()
        if identity is None:
            identity = _get_identity(ctx)
        if identity is None:
            raise AUTH_REQUIRED()
        self._evaluate_roles(identity, ctx)
        return True

    def _evaluate_roles(self, identity: Any, ctx: Any) -> None:
        from aquilia.auth.faults import AUTHZ_INSUFFICIENT_ROLE

        engine = self.engine
        if engine is None:
            container = getattr(ctx, "container", None)
            if container is None and isinstance(ctx, dict):
                container = ctx.get("container")
            if container is not None:
                from aquilia.auth.permissions import PermissionEngine

                try:
                    if hasattr(container, "resolve"):
                        engine = container.resolve(PermissionEngine, optional=True)
                except Exception:
                    pass

        if engine is not None:
            checks = [engine.has_role(identity, r) for r in self.roles]
        else:
            held = set(identity.get_attribute("roles", []))
            checks = [r in held for r in self.roles]

        if self.require_all:
            if not all(checks):
                missing = [r for r, ok in zip(self.roles, checks) if not ok]
                raise AUTHZ_INSUFFICIENT_ROLE(required_roles=missing)
        else:
            if not any(checks):
                raise AUTHZ_INSUFFICIENT_ROLE(required_roles=self.roles)

    async def __call__(self, ctx: Any = None, *args: Any, **kwargs: Any) -> None:
        """
        Allow first-class pipeline execution when referenced as a class or instance.
        """
        resolved_ctx = None
        for candidate in (ctx,) + args + tuple(kwargs.values()):
            if candidate is not None and (
                hasattr(candidate, "identity") or hasattr(candidate, "session") or hasattr(candidate, "user")
            ):
                resolved_ctx = candidate
                break

        if resolved_ctx is None:
            if ctx is not None:
                resolved_ctx = ctx
            elif len(args) > 0:
                resolved_ctx = args[0]

        self.check(resolved_ctx)


class ScopeGuard:
    """
    Require that the authenticated identity holds all specified scopes.

    The wildcard scope ``"*"`` is always sufficient.

    Args:
        *scopes:    One or more scope string required.
        require_all: When ``True`` (default) all scopes must be present.
                     When ``False``, at least one scope suffices.
    """

    def __init__(self, *scopes: str, require_all: bool = True) -> None:
        self.scopes = list(scopes)
        self.require_all = require_all

    def check(self, ctx: Any) -> None:
        """
        Assert that *ctx.identity* holds the required scopes.

        Raises:
            ``AUTH_REQUIRED``:            No identity found.
            ``AUTHZ_INSUFFICIENT_SCOPE``: Required scope(s) are absent.
        """
        from aquilia.auth.faults import AUTH_REQUIRED

        identity = _get_identity(ctx)
        if identity is None:
            raise AUTH_REQUIRED()
        self._evaluate_scopes(identity)

    async def can_activate(self, ctx: Any) -> bool:
        """Async contract — same evaluation as :meth:`check`."""
        from aquilia.auth.faults import AUTH_REQUIRED

        identity = None
        if isinstance(ctx, GuardContext):
            identity = ctx.identity
            if identity is None:
                identity = await ctx.resolve_identity()
        if identity is None:
            identity = _get_identity(ctx)
        if identity is None:
            raise AUTH_REQUIRED()
        self._evaluate_scopes(identity)
        return True

    def _evaluate_scopes(self, identity: Any) -> None:
        from aquilia.auth.faults import AUTHZ_INSUFFICIENT_SCOPE

        checks = [identity.has_scope(s) for s in self.scopes]

        if self.require_all:
            if not all(checks):
                missing = [s for s, ok in zip(self.scopes, checks) if not ok]
                raise AUTHZ_INSUFFICIENT_SCOPE(required_scopes=missing)
        else:
            if not any(checks):
                raise AUTHZ_INSUFFICIENT_SCOPE(required_scopes=self.scopes)

    async def __call__(self, ctx: Any = None, *args: Any, **kwargs: Any) -> None:
        """
        Allow first-class pipeline execution when referenced as a class or instance.
        """
        resolved_ctx = None
        for candidate in (ctx,) + args + tuple(kwargs.values()):
            if candidate is not None and (
                hasattr(candidate, "identity") or hasattr(candidate, "session") or hasattr(candidate, "user")
            ):
                resolved_ctx = candidate
                break

        if resolved_ctx is None:
            if ctx is not None:
                resolved_ctx = ctx
            elif len(args) > 0:
                resolved_ctx = args[0]

        self.check(resolved_ctx)


class PolicyGuard:
    """
    Enforce a named policy from a ``PermissionEngine``.

    Args:
        key:      Policy key registered in *engine*.
        engine:   ``PermissionEngine`` that owns the policy.
        resource: Optional resource to forward to the policy callable.
    """

    def __init__(self, key: str, engine: Any, resource: Any = None) -> None:
        self.key = key
        self.engine = engine
        self.resource = resource

    def check(self, ctx: Any) -> None:
        """
        Evaluate the named policy against *ctx.identity*.

        Raises:
            ``AUTH_REQUIRED``:       No identity found.
            ``AUTHZ_POLICY_DENIED``: Policy returned ``False``.
        """
        from aquilia.auth.faults import AUTH_REQUIRED

        identity = _get_identity(ctx)
        if identity is None:
            raise AUTH_REQUIRED()
        self._evaluate_policy(identity)

    async def can_activate(self, ctx: Any) -> bool:
        """Async contract — same evaluation as :meth:`check`."""
        from aquilia.auth.faults import AUTH_REQUIRED

        identity = None
        if isinstance(ctx, GuardContext):
            identity = ctx.identity
            if identity is None:
                identity = await ctx.resolve_identity()
        if identity is None:
            identity = _get_identity(ctx)
        if identity is None:
            raise AUTH_REQUIRED()
        self._evaluate_policy(identity)
        return True

    def _evaluate_policy(self, identity: Any) -> None:
        self.engine.check_policy(self.key, identity, self.resource)

    async def __call__(self, ctx: Any = None, *args: Any, **kwargs: Any) -> None:
        """
        Allow first-class pipeline execution when referenced as a class or instance.
        """
        resolved_ctx = None
        for candidate in (ctx,) + args + tuple(kwargs.values()):
            if candidate is not None and (
                hasattr(candidate, "identity") or hasattr(candidate, "session") or hasattr(candidate, "user")
            ):
                resolved_ctx = candidate
                break

        if resolved_ctx is None:
            if ctx is not None:
                resolved_ctx = ctx
            elif len(args) > 0:
                resolved_ctx = args[0]

        self.check(resolved_ctx)


# ============================================================================
# Composable helper
# ============================================================================


def requires(*guards: Any) -> Any:
    """
    Decorator that runs all *guards* before the decorated handler.

    Supports both guard instances and class references. Raises the first
    fault encountered. Guards are evaluated in order.

    Usage::

        @requires(AuthGuard, RoleGuard("admin"))
        async def admin_only(self, ctx: RequestCtx) -> Response:
            ...
    """
    import functools

    def decorator(func: Any) -> Any:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            ctx = None
            for arg in args:
                if hasattr(arg, "identity") or hasattr(arg, "user") or hasattr(arg, "session"):
                    ctx = arg
                    break
            if ctx is None and kwargs:
                ctx = next(iter(kwargs.values()), None)

            for guard in guards:
                if inspect.isclass(guard):
                    guard_inst = guard()
                else:
                    guard_inst = guard

                # Same dispatch order as run_guard: async can_activate →
                # legacy check → bare callable. Keeps @requires working with
                # new-style async-only guards.
                can_activate = getattr(guard_inst, "can_activate", None)
                if callable(can_activate):
                    res = can_activate(ctx)
                    if inspect.isawaitable(res):
                        res = await res
                    if res is False:
                        from aquilia.auth.faults import AUTHZ_RESOURCE_FORBIDDEN

                        raise AUTHZ_RESOURCE_FORBIDDEN()
                elif hasattr(guard_inst, "check"):
                    # Check if it needs proactive authentication (like AuthGuard)
                    if hasattr(guard_inst, "_proactive_authenticate"):
                        await guard_inst._proactive_authenticate(ctx)
                    guard_inst.check(ctx)
                elif callable(guard_inst):
                    res = guard_inst(ctx)
                    if inspect.isawaitable(res):
                        await res

            return await func(*args, **kwargs)

        wrapper.__guards__ = list(guards)
        return wrapper

    return decorator


__all__ = [
    "Guard",
    "GuardContext",
    "GuardPipeline",
    "AuthGuard",
    "RoleGuard",
    "ScopeGuard",
    "PolicyGuard",
    "requires",
    "run_guard",
    "is_authentication_guard",
]

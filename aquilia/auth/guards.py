"""
AquilAuth - Guard System

Single guard protocol and concrete implementations.

Design (inspired by NestJS ``CanActivate`` and DRF ``BasePermission``):
    * One ``Guard`` protocol — implement ``check(ctx)`` and raise a fault on
      denial; return ``None`` on success.
    * ``AuthGuard``, ``RoleGuard``, ``ScopeGuard``, ``PolicyGuard`` cover 95 % of use-cases.
    * Guards are composable: pass a list to any helper that accepts them.
    * All guards are first-class and can be used directly as class references
      in pipelines (e.g., ``pipeline = [AuthGuard]``) or as instances
      (e.g., ``pipeline = [AuthGuard()]``).

Usage in a controller::

    from aquilia.auth.guards import AuthGuard, RoleGuard

    @requires(AuthGuard, RoleGuard("admin"))
    async def delete_user(self, ctx: RequestCtx) -> Response:
        ...
"""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from .core import Identity


# ============================================================================
# Protocol
# ============================================================================


@runtime_checkable
class Guard(Protocol):
    """
    Structural protocol for security guards.

    A guard receives the request context (or a plain ``dict`` containing
    ``"identity"``) and either returns ``None`` to signal success or raises
    an auth fault to deny the request.

    Guards must be stateless so they can be instantiated once and reused
    across requests.
    """

    def check(self, ctx: Any) -> None:
        """
        Evaluate the guard condition.

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

    Args:
        auth_manager: Optional authentication manager (resolved via DI if omitted).
        optional: When ``True``, allow unauthenticated requests through.
                  Defaults to ``False`` (strict authentication required).
    """

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
            from .faults import AUTH_REQUIRED

            raise AUTH_REQUIRED()

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
            from .faults import AUTH_REQUIRED

            raise AUTH_REQUIRED()

        from ..faults.domains import DIResolutionFault
        from .manager import AuthManager

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
            from .faults import AUTH_REQUIRED

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
            from .faults import AUTH_REQUIRED

            raise AUTH_REQUIRED()

        token = auth_header[7:]

        from .faults import AUTH_TOKEN_INVALID

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
        from .faults import AUTH_REQUIRED, AUTHZ_INSUFFICIENT_ROLE

        identity = _get_identity(ctx)
        if identity is None:
            raise AUTH_REQUIRED()

        engine = self.engine
        if engine is None:
            container = getattr(ctx, "container", None)
            if container is None and isinstance(ctx, dict):
                container = ctx.get("container")
            if container is not None:
                from .permissions import PermissionEngine

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
        from .faults import AUTH_REQUIRED, AUTHZ_INSUFFICIENT_SCOPE

        identity = _get_identity(ctx)
        if identity is None:
            raise AUTH_REQUIRED()

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
        from .faults import AUTH_REQUIRED

        identity = _get_identity(ctx)
        if identity is None:
            raise AUTH_REQUIRED()

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

                if hasattr(guard_inst, "check"):
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
    "AuthGuard",
    "RoleGuard",
    "ScopeGuard",
    "PolicyGuard",
    "requires",
]

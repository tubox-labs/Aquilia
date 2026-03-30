"""
AquilAuth - Authentication Decorators and Guards.

Provides authentication and authorization decorators for protecting
controller endpoints and service methods.

Features:
- @authenticated - Require authenticated identity
- @require_identity - Require identity with specific attributes
- AuthGuard, AdminGuard, VerifiedEmailGuard - Session-aware guards
- requires() - Compose multiple guards

These decorators work with both session-based and token-based authentication,
extracting identity from RequestCtx, sessions, or request state.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from functools import wraps
from typing import TYPE_CHECKING, Any, TypeVar
from unittest.mock import Mock
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from aquilia.faults import Fault, FaultDomain

from .faults import AUTH_REQUIRED

if TYPE_CHECKING:
    from aquilia.auth.core import Identity
    from aquilia.sessions import Session

F = TypeVar("F", bound=Callable[..., Any])


# ============================================================================
# Faults
# ============================================================================


class AuthorizationRequiredFault(Fault):
    """Raised when authorization check fails."""

    def __init__(self, guard: str | None = None, reason: str | None = None):
        msg = reason or "Authorization required for this endpoint"
        super().__init__(
            code="AUTHORIZATION_REQUIRED",
            message=msg,
            domain=FaultDomain.SECURITY,
            metadata={"guard": guard} if guard else None,
        )


# ============================================================================
# Helper: Extract identity from args/kwargs
# ============================================================================


def _extract_identity(args: tuple, kwargs: dict) -> Identity | None:
    """
    Extract identity from function args/kwargs or RequestCtx.

    Resolution order:
    1. kwargs["identity"]
    2. arg.identity (for RequestCtx-like objects)
    3. arg.request.state["identity"]
    4. AuthRuntimeContext identity
    """
    identity = kwargs.get("identity")
    if _is_identity_like(identity):
        return identity

    # Support keyword-invoked handlers (e.g., handler(ctx=ctx)).
    for value in kwargs.values():
        if _is_identity_like(value):
            return value

        value_identity = getattr(value, "identity", None)
        if _is_identity_like(value_identity):
            return value_identity

        value_request = getattr(value, "request", None)
        if value_request is None:
            continue

        state = getattr(value_request, "state", None)
        if state is None:
            continue

        if isinstance(state, dict) or hasattr(state, "get"):
            state_identity = state.get("identity")
        else:
            state_identity = getattr(state, "identity", None)

        if _is_identity_like(state_identity):
            return state_identity

    for arg in args:
        arg_dict = getattr(arg, "__dict__", None)
        has_explicit_request = isinstance(arg_dict, dict) and "request" in arg_dict
        if not has_explicit_request and not hasattr(type(arg), "request"):
            continue

        # Only trust identity values on RequestCtx-like objects carrying request context.
        ctx_identity = getattr(arg, "identity", None)
        if _is_identity_like(ctx_identity):
            return ctx_identity

        request = getattr(arg, "request", None)
        if request is None:
            continue

        state = getattr(request, "state", None)
        if state is None:
            continue

        if isinstance(state, dict) or hasattr(state, "get"):
            state_identity = state.get("identity")
        else:
            state_identity = getattr(state, "identity", None)

        if _is_identity_like(state_identity):
            return state_identity

    # Fallback: try runtime context
    try:
        from aquilia.auth.integration.runtime_context import get_auth_runtime_context

        runtime_ctx = get_auth_runtime_context()
        if runtime_ctx is not None:
            session = runtime_ctx.session
            if session is not None and hasattr(session, "data"):
                identity_id = session.data.get("identity_id")
                if identity_id:
                    runtime_identity = getattr(runtime_ctx, "identity", None)
                    if _is_identity_like(runtime_identity):
                        return runtime_identity
    except Exception:
        pass

    return None


def _is_identity_like(value: Any) -> bool:
    """Return True only for values that look like real identity/principal objects."""
    if value is None:
        return False

    # Test doubles / placeholders should never satisfy authentication.
    if isinstance(value, Mock):
        return False

    # Primitive/container values are not valid identities.
    if isinstance(value, (bool, str, bytes, int, float, dict, list, tuple, set, frozenset)):
        return False

    # Accept common identity/principal shapes used across auth/session bridges.
    if hasattr(value, "id"):
        return True
    if hasattr(value, "identity_id"):
        return True
    if hasattr(value, "get_attribute") and callable(getattr(value, "get_attribute", None)):
        return True
    if hasattr(value, "attributes"):
        return True
    if hasattr(value, "has_role") and callable(getattr(value, "has_role", None)):
        return True

    return False


def _extract_session(args: tuple, kwargs: dict) -> Session | None:
    """
    Extract session from function args/kwargs or RequestCtx.

    Resolution order:
    1. kwargs["session"]
    2. arg.session (for RequestCtx-like objects)
    3. arg.request.state["session"]
    4. AuthRuntimeContext session
    """
    session = kwargs.get("session")
    if session is not None:
        return session

    # Support keyword-invoked handlers (e.g., handler(ctx=ctx)).
    for value in kwargs.values():
        value_session = getattr(value, "session", None)
        if value_session is not None:
            return value_session

        value_request = getattr(value, "request", None)
        if value_request is None:
            continue

        state = getattr(value_request, "state", None)
        if state is None:
            continue

        if isinstance(state, dict) or hasattr(state, "get"):
            state_session = state.get("session")
        else:
            state_session = getattr(state, "session", None)

        if state_session is not None:
            return state_session

    for arg in args:
        arg_dict = getattr(arg, "__dict__", None)
        has_explicit_request = isinstance(arg_dict, dict) and "request" in arg_dict
        if not has_explicit_request and not hasattr(type(arg), "request"):
            continue

        ctx_session = getattr(arg, "session", None)
        if ctx_session is not None:
            return ctx_session

        request = getattr(arg, "request", None)
        if request is None:
            continue

        state = getattr(request, "state", None)
        if state is None:
            continue

        if isinstance(state, dict) or hasattr(state, "get"):
            state_session = state.get("session")
        else:
            state_session = getattr(state, "session", None)

        if state_session is not None:
            return state_session

    # Fallback: try runtime context
    try:
        from aquilia.auth.integration.runtime_context import get_auth_runtime_context

        runtime_ctx = get_auth_runtime_context()
        if runtime_ctx is not None:
            return runtime_ctx.session
    except Exception:
        pass

    return None


def _extract_request(args: tuple, kwargs: dict) -> Any | None:
    """Extract request object from args/kwargs when available."""
    request = kwargs.get("request")
    if request is not None:
        return request

    # Support keyword-invoked handlers (e.g., handler(ctx=ctx)).
    for value in kwargs.values():
        value_request = getattr(value, "request", None)
        if value_request is not None:
            return value_request

    for arg in args:
        request = getattr(arg, "request", None)
        if request is not None:
            return request

    return None


def _request_accepts_html(request: Any | None) -> bool:
    """Return True when request should receive browser-style redirect challenge."""
    if request is None:
        return False

    accept = ""
    try:
        if hasattr(request, "header") and callable(getattr(request, "header", None)):
            accept = request.header("accept", "") or ""
        else:
            headers = getattr(request, "headers", None)
            if headers is not None and hasattr(headers, "get"):
                accept = headers.get("accept", "") or headers.get("Accept", "")
    except Exception:
        return False

    accept_l = str(accept).lower().strip()

    # Explicit JSON/CROUS API clients should keep fault behavior.
    if "application/json" in accept_l and "text/html" not in accept_l:
        return False
    if "application/x-crous" in accept_l and "text/html" not in accept_l:
        return False

    # Browser-style requests usually send text/html, */*, or no Accept header.
    if "text/html" in accept_l:
        return True
    if "*/*" in accept_l:
        return True
    if not accept_l:
        return True

    return False


def _resolve_login_url(args: tuple, kwargs: dict, configured_login_url: str | None) -> str | None:
    """Resolve login URL from decorator override, context state, or controller hints."""
    if configured_login_url:
        return configured_login_url

    request = _extract_request(args, kwargs)
    if request is not None:
        try:
            state = getattr(request, "state", None)
            if isinstance(state, dict):
                state_login_url = state.get("auth_login_url") or state.get("login_url")
                if isinstance(state_login_url, str) and state_login_url:
                    return state_login_url
        except Exception:
            pass

    # Optional controller-level convention: `auth_login_url = "/login"`
    if args:
        owner = args[0]
        owner_login_url = getattr(owner, "auth_login_url", None)
        if isinstance(owner_login_url, str) and owner_login_url:
            return owner_login_url

    return None


def _append_next_param(login_url: str, request: Any | None, next_param: str) -> str:
    """Append current request path/query to login URL as next parameter."""
    if request is None:
        return login_url

    try:
        path = getattr(request, "path", None)
        query_string = getattr(request, "query_string", "") or ""
        if not path:
            return login_url

        next_value = str(path)
        if query_string:
            next_value = f"{next_value}?{query_string}"

        split = urlsplit(login_url)
        query_items = parse_qsl(split.query, keep_blank_values=True)
        query_items = [(k, v) for k, v in query_items if k != next_param]
        query_items.append((next_param, next_value))
        rebuilt_query = urlencode(query_items, doseq=True)
        return urlunsplit((split.scheme, split.netloc, split.path, rebuilt_query, split.fragment))
    except Exception:
        return login_url


def _build_auth_challenge_response(
    args: tuple,
    kwargs: dict,
    *,
    login_url: str | None,
    redirect_if_html: bool,
    include_next: bool,
    next_param: str,
    redirect_status: int,
) -> Any | None:
    """Build redirect response for browser clients or return None to raise AUTH_REQUIRED."""
    # Aquilia convention: providing login_url implies browser redirect challenge.
    effective_redirect = redirect_if_html or bool(login_url)
    if not effective_redirect:
        return None

    request = _extract_request(args, kwargs)
    if not _request_accepts_html(request):
        return None

    resolved_login = _resolve_login_url(args, kwargs, login_url)
    if not resolved_login:
        return None

    if include_next:
        resolved_login = _append_next_param(resolved_login, request, next_param)

    from aquilia.response import Response

    return Response.redirect(resolved_login, status=redirect_status)


# ============================================================================
# @authenticated Decorator
# ============================================================================


def authenticated(
    func: F | None = None,
    *,
    login_url: str | None = None,
    redirect_if_html: bool = False,
    include_next: bool = True,
    next_param: str = "next",
    redirect_status: int = 303,
) -> F | Callable[[F], F]:
    """
    Decorator requiring authenticated identity.

    Works with both session-based and token-based authentication.
    Injects identity/user/principal into the function if parameter exists.

    Example:
        @authenticated
        async def profile(ctx, user: Identity):
            return {"user_id": user.id}

        @authenticated
        async def dashboard(ctx, principal: SessionPrincipal):
            return {"principal": principal.id}
    """

    def decorator(inner_func: F) -> F:
        @wraps(inner_func)
        async def wrapper(*args, **func_kwargs):
            # Try to get identity directly first
            identity = _extract_identity(args, func_kwargs)

            if identity is not None:
                sig = inspect.signature(inner_func)
                if "user" in sig.parameters:
                    func_kwargs["user"] = identity
                elif "identity" in sig.parameters:
                    func_kwargs["identity"] = identity
                elif "principal" in sig.parameters:
                    func_kwargs["principal"] = identity
                return await inner_func(*args, **func_kwargs)

            # Fall back to session-based authentication
            session = _extract_session(args, func_kwargs)

            if session is None or not getattr(session, "is_authenticated", False):
                redirect_response = _build_auth_challenge_response(
                    args,
                    func_kwargs,
                    login_url=login_url,
                    redirect_if_html=redirect_if_html,
                    include_next=include_next,
                    next_param=next_param,
                    redirect_status=redirect_status,
                )
                if redirect_response is not None:
                    return redirect_response
                raise AUTH_REQUIRED()

            # Inject principal/user/session based on signature
            sig = inspect.signature(inner_func)
            if "user" in sig.parameters:
                func_kwargs["user"] = session.principal
            elif "principal" in sig.parameters:
                func_kwargs["principal"] = session.principal
            elif "session" in sig.parameters:
                func_kwargs["session"] = session

            return await inner_func(*args, **func_kwargs)

        wrapper.__authenticated__ = True
        wrapper.__auth_challenge__ = {
            "login_url": login_url,
            "redirect_if_html": redirect_if_html,
            "include_next": include_next,
            "next_param": next_param,
            "redirect_status": redirect_status,
        }
        return wrapper

    if func is not None and callable(func):
        return decorator(func)
    return decorator


# ============================================================================
# @require_identity Decorator
# ============================================================================


def require_identity(
    *,
    roles: list[str] | None = None,
    scopes: list[str] | None = None,
    attributes: dict[str, Any] | None = None,
    require_all_roles: bool = False,
    require_all_scopes: bool = True,
    login_url: str | None = None,
    redirect_if_html: bool = False,
    include_next: bool = True,
    next_param: str = "next",
    redirect_status: int = 303,
) -> Callable[[F], F]:
    """
    Decorator requiring identity with specific attributes.

    Example:
        @require_identity(roles=["admin"])
        async def admin_panel(ctx, identity: Identity):
            ...

        @require_identity(scopes=["users:read", "users:write"])
        async def manage_users(ctx, identity: Identity):
            ...
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **func_kwargs):
            identity = _extract_identity(args, func_kwargs)

            if identity is None:
                session = _extract_session(args, func_kwargs)
                if session is not None and getattr(session, "is_authenticated", False):
                    identity = session.principal
                else:
                    redirect_response = _build_auth_challenge_response(
                        args,
                        func_kwargs,
                        login_url=login_url,
                        redirect_if_html=redirect_if_html,
                        include_next=include_next,
                        next_param=next_param,
                        redirect_status=redirect_status,
                    )
                    if redirect_response is not None:
                        return redirect_response
                    raise AUTH_REQUIRED()

            if identity is None:
                raise AUTH_REQUIRED()

            # Check roles
            if roles:
                identity_roles = set()
                if hasattr(identity, "roles"):
                    identity_roles = set(identity.roles)
                elif hasattr(identity, "get_attribute"):
                    identity_roles = set(identity.get_attribute("roles", []))
                elif hasattr(identity, "attributes"):
                    identity_roles = set(identity.attributes.get("roles", []))

                required_roles = set(roles)
                if require_all_roles:
                    if not required_roles.issubset(identity_roles):
                        from aquilia.auth.faults import AUTHZ_INSUFFICIENT_ROLE

                        raise AUTHZ_INSUFFICIENT_ROLE(
                            required_roles=roles,
                            available_roles=list(identity_roles),
                        )
                else:
                    if not required_roles.intersection(identity_roles):
                        from aquilia.auth.faults import AUTHZ_INSUFFICIENT_ROLE

                        raise AUTHZ_INSUFFICIENT_ROLE(
                            required_roles=roles,
                            available_roles=list(identity_roles),
                        )

            # Check scopes
            if scopes:
                identity_scopes = set()
                if hasattr(identity, "scopes"):
                    identity_scopes = set(identity.scopes)
                elif hasattr(identity, "get_attribute"):
                    identity_scopes = set(identity.get_attribute("scopes", []))
                elif hasattr(identity, "attributes"):
                    identity_scopes = set(identity.attributes.get("scopes", []))

                required_scopes = set(scopes)
                if require_all_scopes:
                    if not required_scopes.issubset(identity_scopes):
                        from aquilia.auth.faults import AUTHZ_INSUFFICIENT_SCOPE

                        raise AUTHZ_INSUFFICIENT_SCOPE(
                            required_scopes=scopes,
                            available_scopes=list(identity_scopes),
                        )
                else:
                    if not required_scopes.intersection(identity_scopes):
                        from aquilia.auth.faults import AUTHZ_INSUFFICIENT_SCOPE

                        raise AUTHZ_INSUFFICIENT_SCOPE(
                            required_scopes=scopes,
                            available_scopes=list(identity_scopes),
                        )

            # Check custom attributes
            if attributes:
                for key, expected_value in attributes.items():
                    actual_value = None
                    if hasattr(identity, "get_attribute"):
                        actual_value = identity.get_attribute(key)
                    elif hasattr(identity, "attributes"):
                        actual_value = identity.attributes.get(key)

                    if actual_value != expected_value:
                        raise AuthorizationRequiredFault(reason=f"Required attribute '{key}' not satisfied")

            # Inject identity
            sig = inspect.signature(func)
            if "identity" in sig.parameters:
                func_kwargs["identity"] = identity
            elif "user" in sig.parameters:
                func_kwargs["user"] = identity
            elif "principal" in sig.parameters:
                func_kwargs["principal"] = identity

            return await func(*args, **func_kwargs)

        wrapper.__require_identity__ = True
        wrapper.__required_roles__ = roles
        wrapper.__required_scopes__ = scopes
        return wrapper

    return decorator


# ============================================================================
# AuthGuard Base Class
# ============================================================================


class AuthGuard:
    """
    Base class for authentication/authorization guards.

    Guards can be used as decorators or composed with requires().

    Example:
        class PremiumGuard(AuthGuard):
            async def check(self, identity, session) -> bool:
                return identity.get_attribute("subscription") == "premium"

        @PremiumGuard()
        async def premium_feature(ctx):
            ...
    """

    async def check(self, identity: Identity | None, session: Session | None) -> bool:
        """
        Check if access should be granted.

        Override this method in subclasses.

        Args:
            identity: The authenticated identity (may be None)
            session: The current session (may be None)

        Returns:
            True if access granted, False otherwise
        """
        raise NotImplementedError("Subclasses must implement check()")

    def __call__(self, func: F) -> F:
        """Use guard as decorator."""

        @wraps(func)
        async def wrapper(*args, **kwargs):
            identity = _extract_identity(args, kwargs)
            session = _extract_session(args, kwargs)

            if not await self.check(identity, session):
                raise AuthorizationRequiredFault(
                    guard=self.__class__.__name__,
                    reason=f"Guard '{self.__class__.__name__}' denied access",
                )

            return await func(*args, **kwargs)

        wrapper.__guard__ = self.__class__.__name__
        return wrapper


# ============================================================================
# Built-in Guards
# ============================================================================


class AdminGuard(AuthGuard):
    """Guard that requires admin role."""

    async def check(self, identity: Identity | Session | None = None, session: Session | None = None) -> bool:
        if session is None and identity is not None and hasattr(identity, "is_authenticated"):
            session = identity
            identity = None

        # Check identity first
        if identity is not None:
            if hasattr(identity, "has_role"):
                return identity.has_role("admin")
            if hasattr(identity, "get_attribute"):
                roles = identity.get_attribute("roles", [])
                return "admin" in roles
            if hasattr(identity, "attributes"):
                return "admin" in identity.attributes.get("roles", [])

        # Fall back to session
        if session is None or not getattr(session, "is_authenticated", False):
            return False

        principal = session.principal
        if principal is None:
            return False

        if hasattr(principal, "role"):
            return principal.role == "admin"
        if hasattr(principal, "roles"):
            return "admin" in principal.roles
        if hasattr(principal, "get_attribute"):
            return principal.get_attribute("role") == "admin"

        return False


class VerifiedEmailGuard(AuthGuard):
    """Guard that requires verified email."""

    async def check(self, identity: Identity | Session | None = None, session: Session | None = None) -> bool:
        if session is None and identity is not None and hasattr(identity, "is_authenticated"):
            session = identity
            identity = None

        # Check identity first
        if identity is not None:
            if hasattr(identity, "get_attribute"):
                return identity.get_attribute("email_verified", False)
            if hasattr(identity, "attributes"):
                return identity.attributes.get("email_verified", False)

        # Fall back to session
        if session is None or not getattr(session, "is_authenticated", False):
            return False

        principal = session.principal
        if principal is None:
            return False

        if hasattr(principal, "email_verified"):
            return principal.email_verified
        if hasattr(principal, "get_attribute"):
            return principal.get_attribute("email_verified", False)

        return False


class RoleGuard(AuthGuard):
    """Guard that requires specific role(s)."""

    def __init__(self, *roles: str, require_all: bool = False):
        self.roles = set(roles)
        self.require_all = require_all

    async def check(self, identity: Identity | None, session: Session | None) -> bool:
        identity_roles: set[str] = set()

        # Get roles from identity
        if identity is not None:
            if hasattr(identity, "get_attribute"):
                identity_roles = set(identity.get_attribute("roles", []))
            elif hasattr(identity, "attributes"):
                identity_roles = set(identity.attributes.get("roles", []))
        elif session is not None and getattr(session, "is_authenticated", False):
            principal = session.principal
            if principal is not None:
                if hasattr(principal, "roles"):
                    identity_roles = set(principal.roles)
                elif hasattr(principal, "get_attribute"):
                    identity_roles = set(principal.get_attribute("roles", []))

        if self.require_all:
            return self.roles.issubset(identity_roles)
        return bool(self.roles.intersection(identity_roles))


class ScopeGuard(AuthGuard):
    """Guard that requires specific scope(s)."""

    def __init__(self, *scopes: str, require_all: bool = True):
        self.scopes = set(scopes)
        self.require_all = require_all

    async def check(self, identity: Identity | None, session: Session | None) -> bool:
        identity_scopes: set[str] = set()

        # Get scopes from identity
        if identity is not None:
            if hasattr(identity, "get_attribute"):
                identity_scopes = set(identity.get_attribute("scopes", []))
            elif hasattr(identity, "attributes"):
                identity_scopes = set(identity.attributes.get("scopes", []))
        elif session is not None and getattr(session, "is_authenticated", False):
            principal = session.principal
            if principal is not None:
                if hasattr(principal, "scopes"):
                    identity_scopes = set(principal.scopes)
                elif hasattr(principal, "get_attribute"):
                    identity_scopes = set(principal.get_attribute("scopes", []))

        if self.require_all:
            return self.scopes.issubset(identity_scopes)
        return bool(self.scopes.intersection(identity_scopes))


# ============================================================================
# requires() - Guard Composition
# ============================================================================


def requires(*guards: AuthGuard) -> Callable[[F], F]:
    """
    Decorator to require multiple guards.

    All guards must pass for access to be granted.

    Example:
        @requires(AdminGuard(), VerifiedEmailGuard())
        async def sensitive_operation(ctx):
            ...
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            identity = _extract_identity(args, kwargs)
            session = _extract_session(args, kwargs)

            for guard in guards:
                if not await guard.check(identity, session):
                    raise AuthorizationRequiredFault(
                        guard=guard.__class__.__name__,
                        reason=f"Guard '{guard.__class__.__name__}' denied access",
                    )

            return await func(*args, **kwargs)

        wrapper.__guards__ = [g.__class__.__name__ for g in guards]
        return wrapper

    return decorator


# ============================================================================
# Exports
# ============================================================================


__all__ = [
    # Faults
    "AuthorizationRequiredFault",
    # Decorators
    "authenticated",
    "require_identity",
    # Guards
    "AuthGuard",
    "AdminGuard",
    "VerifiedEmailGuard",
    "RoleGuard",
    "ScopeGuard",
    "requires",
    # Helpers (for internal use)
    "_extract_identity",
    "_extract_session",
]

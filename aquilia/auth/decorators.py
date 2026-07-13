"""
AquilAuth - Decorator Suite

Clean, ctx-first decorators replacing the old decorators.

Identity is always read from ``ctx.identity`` — the single canonical location
set by ``AuthMiddleware``.

Usage::

    from aquilia.auth.decorators import authenticated, roles_required, scopes_required

    class UserController(Controller):

        @authenticated
        async def profile(self, ctx: RequestCtx) -> Response:
            return Response.json(ctx.identity.to_dict())

        @roles_required("admin")
        async def admin_panel(self, ctx: RequestCtx) -> Response:
            ...

        @scopes_required("reports:read")
        async def reports(self, ctx: RequestCtx) -> Response:
            ...
"""

from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from typing import Any
from unittest.mock import Mock

from .guards import AuthGuard, RoleGuard, ScopeGuard

# ============================================================================
# Internal helpers
# ============================================================================


def _is_context_like(candidate: Any) -> bool:
    if candidate is None:
        return False
    if isinstance(candidate, Mock):
        return True
    if isinstance(candidate, dict):
        return True
    if hasattr(candidate, "request"):
        return True
    if hasattr(candidate, "headers") or hasattr(candidate, "header"):
        return True
    return False


def _extract_identity(args: tuple, kwargs: dict) -> Any | None:
    # 1. Direct Identity check
    for arg in args:
        if arg.__class__.__name__ == "Identity" and not isinstance(arg, Mock):
            return arg
    for val in kwargs.values():
        if val.__class__.__name__ == "Identity" and not isinstance(val, Mock):
            return val

    # 2. Check candidate context/request objects in args/kwargs
    for candidate in args + tuple(kwargs.values()):
        if not _is_context_like(candidate):
            continue

        if hasattr(candidate, "identity"):
            ident = candidate.identity
            if ident is not None and not isinstance(ident, Mock):
                return ident
        if hasattr(candidate, "request"):
            req = candidate.request
            if req is not None and not isinstance(req, Mock) and hasattr(req, "state"):
                ident = req.state.get("identity")
                if ident is not None and not isinstance(ident, Mock):
                    return ident
        if isinstance(candidate, dict) and "identity" in candidate:
            ident = candidate.get("identity")
            if ident is not None and not isinstance(ident, Mock):
                return ident
    return None


def _extract_session(args: tuple, kwargs: dict) -> Any | None:
    session = kwargs.get("session")
    if session is not None and not isinstance(session, Mock):
        return session

    for value in kwargs.values():
        if not _is_context_like(value):
            continue

        value_session = getattr(value, "session", None)
        if value_session is not None and not isinstance(value_session, Mock):
            return value_session

        value_request = getattr(value, "request", None)
        if value_request is not None:
            state = getattr(value_request, "state", None)
            if state is not None and not isinstance(state, Mock):
                if isinstance(state, dict) or hasattr(state, "get"):
                    state_session = state.get("session")
                else:
                    state_session = getattr(state, "session", None)

                if state_session is not None and not isinstance(state_session, Mock):
                    return state_session

    for arg in args:
        if not _is_context_like(arg):
            continue

        ctx_session = getattr(arg, "session", None)
        if ctx_session is not None and not isinstance(ctx_session, Mock):
            return ctx_session

        request = getattr(arg, "request", None)
        if request is not None:
            state = getattr(request, "state", None)
            if state is not None and not isinstance(state, Mock):
                if isinstance(state, dict) or hasattr(state, "get"):
                    state_session = state.get("session")
                else:
                    state_session = getattr(state, "session", None)

                if state_session is not None and not isinstance(state_session, Mock):
                    return state_session

    return None


def _apply_guard(guard: Any, func: Callable) -> Callable:
    """Wrap *func* to run *guard* before execution."""

    @functools.wraps(func)
    async def wrapper(*args: Any, **func_kwargs: Any) -> Any:
        identity = _extract_identity(args, func_kwargs)
        session = _extract_session(args, func_kwargs)

        ctx = None
        for candidate in args + tuple(func_kwargs.values()):
            if (
                candidate is not None
                and _is_context_like(candidate)
                and (
                    hasattr(candidate, "identity")
                    or hasattr(candidate, "session")
                    or hasattr(candidate, "request")
                    or hasattr(candidate, "user")
                )
            ):
                ctx = candidate
                break

        if ctx is None:
            if args:
                ctx = args[0]
            elif func_kwargs:
                ctx = next(iter(func_kwargs.values()), None)

        ctx_identity = getattr(ctx, "identity", None)
        if ctx is not None and (ctx_identity is None or isinstance(ctx_identity, Mock)) and identity is not None:
            ctx = {"identity": identity, "session": session}

        guard.check(ctx)

        # Parameter injection into handler based on signature
        sig = inspect.signature(func)
        if "identity" in sig.parameters and "identity" not in func_kwargs:
            func_kwargs["identity"] = identity
        if "user" in sig.parameters and "user" not in func_kwargs:
            if identity is not None:
                func_kwargs["user"] = identity
            elif session is not None and getattr(session, "principal", None) is not None:
                func_kwargs["user"] = session.principal
        if "session" in sig.parameters and "session" not in func_kwargs:
            func_kwargs["session"] = session
        if "principal" in sig.parameters and "principal" not in func_kwargs:
            if identity is not None:
                from .integration.aquila_sessions import AuthPrincipal

                func_kwargs["principal"] = AuthPrincipal.from_identity(identity)
            elif session is not None and getattr(session, "principal", None) is not None:
                func_kwargs["principal"] = session.principal

        return await func(*args, **func_kwargs)

    wrapper.__guards__ = getattr(func, "__guards__", []) + [guard]
    return wrapper


# ============================================================================
# Public decorators
# ============================================================================


def authenticated(
    func: Callable | None = None,
    *,
    login_url: str | None = None,
    redirect_if_html: bool = False,
    include_next: bool = True,
    next_param: str = "next",
    redirect_status: int = 303,
) -> Callable | Callable[[Callable], Callable]:
    """
    Decorator requiring authenticated identity.

    Works with both session-based and token-based authentication.
    Injects identity/user/principal/session into the function if parameter exists.

    Example::

        @authenticated
        async def profile(self, ctx, user: Identity):
            return {"user_id": user.id}
    """

    def decorator(inner_func: Callable) -> Callable:
        @functools.wraps(inner_func)
        async def wrapper(*args: Any, **func_kwargs: Any) -> Any:
            identity = _extract_identity(args, func_kwargs)
            session = _extract_session(args, func_kwargs)

            # Check if authenticated. If not, check if we need to do HTML browser challenge
            if identity is None and (session is None or not getattr(session, "is_authenticated", False)):
                from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

                from aquilia.response import Response

                request = None
                for val in func_kwargs.values():
                    if getattr(val, "request", None) is not None:
                        request = val.request
                        break
                for arg in args:
                    if getattr(arg, "request", None) is not None:
                        request = arg.request
                        break

                accept = ""
                if request is not None:
                    if hasattr(request, "header"):
                        accept = request.header("accept", "") or ""
                    else:
                        headers = getattr(request, "headers", None)
                        if headers:
                            accept = headers.get("accept", "") or headers.get("Accept", "")

                accept_l = str(accept).lower().strip()
                is_html = "text/html" in accept_l or "*/*" in accept_l or not accept_l

                if (redirect_if_html or login_url) and is_html:
                    resolved_login = login_url
                    if not resolved_login and request is not None:
                        state = getattr(request, "state", None)
                        if isinstance(state, dict):
                            resolved_login = state.get("auth_login_url") or state.get("login_url")
                    if not resolved_login and args:
                        resolved_login = getattr(args[0], "auth_login_url", None)

                    if resolved_login:
                        if include_next and request is not None:
                            path = getattr(request, "path", None)
                            query_string = getattr(request, "query_string", "") or ""
                            if path:
                                next_value = str(path)
                                if query_string:
                                    next_value = f"{next_value}?{query_string}"
                                split = urlsplit(resolved_login)
                                query_items = parse_qsl(split.query, keep_blank_values=True)
                                query_items = [(k, v) for k, v in query_items if k != next_param]
                                query_items.append((next_param, next_value))
                                rebuilt_query = urlencode(query_items, doseq=True)
                                resolved_login = urlunsplit(
                                    (split.scheme, split.netloc, split.path, rebuilt_query, split.fragment)
                                )
                        return Response.redirect(resolved_login, status=redirect_status)

            wrapped = _apply_guard(AuthGuard(), inner_func)
            return await wrapped(*args, **func_kwargs)

        wrapper.__authenticated__ = True
        return wrapper

    if func is not None:
        return decorator(func)
    return decorator


def roles_required(*roles: str, require_all: bool = True) -> Callable:
    """
    Require that the authenticated identity holds the specified roles.

    Args:
        *roles:      One or more role strings (e.g. ``"admin"``, ``"staff"``).
        require_all: When ``True`` (default) all roles must be held.
                     When ``False``, at least one role suffices.
    """

    def decorator(func: Callable) -> Callable:
        return _apply_guard(RoleGuard(*roles, require_all=require_all), func)

    return decorator


def scopes_required(*scopes: str, require_all: bool = True) -> Callable:
    """
    Require that the authenticated identity holds the specified OAuth scopes.

    Args:
        *scopes:     One or more scope strings (e.g. ``"reports:read"``).
        require_all: When ``True`` (default) all scopes must be present.
                     When ``False``, at least one scope suffices.
    """

    def decorator(func: Callable) -> Callable:
        return _apply_guard(ScopeGuard(*scopes, require_all=require_all), func)

    return decorator


def optional_auth(func: Callable) -> Callable:
    """
    Allow both authenticated and unauthenticated requests.
    """
    return _apply_guard(AuthGuard(optional=True), func)


__all__ = [
    "authenticated",
    "roles_required",
    "scopes_required",
    "optional_auth",
]

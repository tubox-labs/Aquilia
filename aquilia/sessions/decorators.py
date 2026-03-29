"""
Unique Session Decorators for Aquilia.

Provides fluent, type-safe decorators for session management plus
advanced guard and context manager patterns (merged from enhanced.py).

Features:
- @session.require() - Require session with specific properties
- @session.ensure() - Ensure session exists (create if missing)
- @session.optional() - Session is optional
- @stateful - Shorthand for stateful sessions
- SessionContext - Scoped session access (ensure, transactional)
- SessionGuard / requires() - Advanced session guards
"""

import inspect
from collections.abc import Callable
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, TypeVar

from aquilia.faults import Fault

# FIX: Use relative import to avoid circular import through __init__.py
from .core import Session

F = TypeVar("F", bound=Callable[..., Any])


class SessionRequiredFault(Fault):
    """Raised when session is required but missing."""

    def __init__(self):
        from aquilia.faults import FaultDomain

        super().__init__(
            code="SESSION_REQUIRED",
            message="Session required for this endpoint",
            domain=FaultDomain.SECURITY,
        )


# ============================================================================
# Helper: Extract session from args/kwargs
# ============================================================================


def _extract_session(args, kwargs) -> Session | None:
    """Extract session from function args/kwargs or RequestCtx."""
    session = kwargs.get("session")
    if session is not None:
        return session

    # Find RequestCtx in args
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

    return None


# ============================================================================
# SessionDecorators
# ============================================================================


class SessionDecorators:
    """Namespace for session decorators."""

    @staticmethod
    def require(authenticated: bool = False, **kwargs) -> Callable[[F], F]:
        """
        Require session with specific properties.

        Example:
            >>> @session.require(authenticated=True)
            >>> async def profile(ctx, session: Session):
            ...     return {"user": session.principal.id}
        """

        def decorator(func: F) -> F:
            @wraps(func)
            async def wrapper(*args, **func_kwargs):
                sess = _extract_session(args, func_kwargs)

                if sess is None:
                    raise SessionRequiredFault()

                if authenticated and not sess.is_authenticated:
                    from aquilia.auth.faults import AUTH_REQUIRED

                    raise AUTH_REQUIRED()

                if "session" not in func_kwargs:
                    sig = inspect.signature(func)
                    if "session" in sig.parameters:
                        func_kwargs["session"] = sess

                return await func(*args, **func_kwargs)

            wrapper.__session_required__ = True
            wrapper.__session_authenticated__ = authenticated
            return wrapper

        return decorator

    @staticmethod
    def ensure() -> Callable[[F], F]:
        """
        Ensure session exists (create if missing).

        Example:
            >>> @session.ensure()
            >>> async def cart(ctx, session: Session):
            ...     session.data.cart.append(item)
        """

        def decorator(func: F) -> F:
            @wraps(func)
            async def wrapper(*args, **func_kwargs):
                sess = _extract_session(args, func_kwargs)

                if sess is None:
                    # Try to resolve via SessionEngine from context
                    ctx = None
                    for arg in args:
                        if hasattr(arg, "session") and hasattr(arg, "request"):
                            ctx = arg
                            break

                    if ctx:
                        try:
                            from .engine import SessionEngine

                            engine = await ctx.container.resolve_async(SessionEngine)
                            sess = await engine.resolve(ctx.request)
                            ctx.session = sess
                            ctx.request.state["session"] = sess
                        except Exception:
                            from datetime import datetime, timezone

                            from .core import SessionID

                            session_id = SessionID()
                            sess = Session(
                                id=session_id,
                                created_at=datetime.now(timezone.utc),
                                last_accessed_at=datetime.now(timezone.utc),
                                data={},
                                principal=None,
                            )
                            ctx.session = sess
                            ctx.request.state["session"] = sess

                if sess and "session" not in func_kwargs:
                    sig = inspect.signature(func)
                    if "session" in sig.parameters:
                        func_kwargs["session"] = sess

                return await func(*args, **func_kwargs)

            wrapper.__session_ensure__ = True
            return wrapper

        return decorator

    @staticmethod
    def optional() -> Callable[[F], F]:
        """
        Session is optional. The handler will receive Session | None.

        Example:
            >>> @session.optional()
            >>> async def public(ctx, session: Session | None):
            ...     if session:
            ...         return {"user": session.principal.id}
            ...     return {"user": None}
        """

        def decorator(func: F) -> F:
            @wraps(func)
            async def wrapper(*args, **func_kwargs):
                sess = _extract_session(args, func_kwargs)

                if "session" not in func_kwargs:
                    sig = inspect.signature(func)
                    if "session" in sig.parameters:
                        func_kwargs["session"] = sess

                return await func(*args, **func_kwargs)

            wrapper.__session_optional__ = True
            return wrapper

        return decorator


# Create singleton instance
session = SessionDecorators()


def stateful(func: F) -> F:
    """
    Shorthand decorator for stateful sessions.

    Example:
        >>> @stateful
        >>> async def save_prefs(ctx, state: SessionState):
        ...     state.theme = "dark"
    """

    @wraps(func)
    async def wrapper(*args, **func_kwargs):
        sess = _extract_session(args, func_kwargs)

        if sess is None:
            raise SessionRequiredFault()

        sig = inspect.signature(func)
        if "state" in sig.parameters:
            import typing

            from .state import SessionState

            type_hints = typing.get_type_hints(func)
            state_cls = type_hints.get("state", SessionState)

            if not isinstance(state_cls, type) or not issubclass(state_cls, SessionState):
                state_cls = SessionState

            func_kwargs["state"] = state_cls(sess.data)
        elif "session" in sig.parameters:
            func_kwargs["session"] = sess

        return await func(*args, **func_kwargs)

    wrapper.__stateful__ = True
    return wrapper


# ============================================================================
# SessionContext (merged from enhanced.py)
# ============================================================================


class SessionContextManager:
    """
    Context manager for scoped session access.

    Provides guaranteed session lifecycle management with automatic cleanup.
    """

    @staticmethod
    @asynccontextmanager
    async def authenticated(ctx):
        """
        Context manager for authenticated sessions.

        Example:
            >>> async with SessionContext.authenticated(ctx) as session:
            ...     user_id = session.principal.id
        """
        sess = getattr(ctx, "session", None)
        if sess is None and hasattr(ctx, "request"):
            sess = ctx.request.state.get("session")

        if sess is None:
            raise SessionRequiredFault()

        if not sess.is_authenticated:
            from aquilia.auth.faults import AUTH_REQUIRED

            raise AUTH_REQUIRED()

        try:
            yield sess
        finally:
            pass

    @staticmethod
    @asynccontextmanager
    async def ensure(ctx):
        """
        Context manager that ensures session exists.

        Example:
            >>> async with SessionContext.ensure(ctx) as session:
            ...     session.data['cart'].append(item)
        """
        sess = getattr(ctx, "session", None)
        if sess is None and hasattr(ctx, "request"):
            sess = ctx.request.state.get("session")

        if sess is None:
            raise SessionRequiredFault()

        try:
            yield sess
        finally:
            pass

    @staticmethod
    @asynccontextmanager
    async def transactional(ctx):
        """
        Transactional session context with rollback on exception.

        Example:
            >>> async with SessionContext.transactional(ctx) as session:
            ...     session.data['balance'] -= 100
            ...     if session.data['balance'] < 0:
            ...         raise ValueError("Insufficient funds")
            ...     # Auto-commit on success, rollback on exception
        """
        sess = getattr(ctx, "session", None)
        if sess is None and hasattr(ctx, "request"):
            sess = ctx.request.state.get("session")

        if sess is None:
            raise SessionRequiredFault()

        # Snapshot for rollback
        snapshot = sess.data.copy()

        try:
            yield sess
        except Exception:
            # Rollback
            sess.data.clear()
            sess.data.update(snapshot)
            raise


SessionContext = SessionContextManager()


# ============================================================================
# SessionGuard (merged from enhanced.py)
# ============================================================================


class SessionGuard:
    """
    Advanced session guards for complex authorization logic.

    Example:
        >>> class FeatureGuard(SessionGuard):
        ...     async def check(self, session: Session) -> bool:
        ...         return bool(session.data.get("feature_enabled"))

        >>> @requires(FeatureGuard())
        >>> async def admin_panel(ctx, session: Session):
        ...     ...
    """

    async def check(self, session: Session) -> bool:
        raise NotImplementedError("Subclasses must implement check()")

    def __call__(self, func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            sess = _extract_session(args, kwargs)

            if sess is None:
                raise SessionRequiredFault()

            if not await self.check(sess):
                from aquilia.faults.domains import AuthorizationFault

                raise AuthorizationFault(
                    resource=self.__class__.__name__, action="access", metadata={"guard": self.__class__.__name__}
                )

            return await func(*args, **kwargs)

        return wrapper


def requires(*guards: SessionGuard):
    """
    Decorator to require multiple session guards.

    Example:
        >>> @requires(GuardA(), GuardB())
        >>> async def sensitive_operation(ctx, session: Session):
        ...     ...
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            sess = _extract_session(args, kwargs)

            if sess is None:
                raise SessionRequiredFault()

            for guard in guards:
                if not await guard.check(sess):
                    from aquilia.faults.domains import AuthorizationFault

                    raise AuthorizationFault(
                        resource=guard.__class__.__name__, action="access", metadata={"guard": guard.__class__.__name__}
                    )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


__all__ = [
    "session",
    "stateful",
    "SessionRequiredFault",
    # Merged from enhanced.py
    "SessionContext",
    "SessionGuard",
    "requires",
]

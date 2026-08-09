"""Registration-time validation.

Split from the registry so the checks are testable in isolation and so their
failure text lives next to the predicate that produced it. Each function
returns a *reason string* rather than raising — the registry decides whether a
reason becomes a fault or a warning.
"""

from __future__ import annotations

import inspect
from typing import Any

from aquilia.middleware.core.base import Middleware, implements_any_hook


def display_name(middleware: Any) -> str:
    """The name to use in diagnostics for *middleware*."""
    if inspect.isroutine(middleware):
        return getattr(middleware, "__name__", "<function>")
    return type(middleware).__name__


def validate(middleware: Any) -> str | None:
    """Check *middleware* is registrable. Returns a rejection reason, or ``None``.

    Enforces, in order:

    1. It subclasses ``Middleware`` or is a plain function.
    2. It is callable.
    3. Its entry point binds three positional parameters.
    4. Its entry point is ``async def``.

    All four are boot-time checks by design: a middleware with a sync
    ``__call__`` would otherwise fail on the first request in production.
    """
    is_routine = inspect.isroutine(middleware)

    if not isinstance(middleware, Middleware) and not is_routine:
        return f"Middleware of type '{type(middleware).__name__}' must inherit from the 'Middleware' base class."

    func = middleware if is_routine else getattr(middleware, "__call__", None)
    if func is None:
        return f"Middleware of type '{type(middleware).__name__}' must be callable."

    name = display_name(middleware)

    try:
        inspect.signature(func).bind(None, None, None)
    except TypeError as exc:
        return (
            f"Middleware '{name}' has an invalid signature: {exc}. "
            f"It must accept exactly three parameters: (request, ctx, next_handler)."
        )

    if not inspect.iscoroutinefunction(func):
        return f"Middleware '{name}' must be a coroutine function (async def)."

    return None


def validate_hooks(middleware: Any) -> str | None:
    """Check every overridden optional hook is async. Returns a reason, or ``None``.

    ``validate`` covers the entry point. This covers ``before``/``after``/
    ``should_run``/``setup``/``teardown``, which the chain awaits and which
    would therefore fail at runtime if declared ``def``.
    """
    if not isinstance(middleware, Middleware):
        return None

    name = display_name(middleware)
    for hook in ("before", "after", "handle", "should_run", "setup", "teardown"):
        func = getattr(middleware, hook, None)
        if func is None or not inspect.isroutine(func):
            continue
        if not inspect.iscoroutinefunction(func):
            return f"Middleware '{name}.{hook}' must be a coroutine function (async def)."
    return None


def is_noop(middleware: Any) -> bool:
    """True when a ``Middleware`` subclass overrides no request-path hook.

    Registering one has no effect, which is almost always a typo in the hook
    name. Worth a warning, not a rejection.
    """
    if not isinstance(middleware, Middleware):
        return False
    return not implements_any_hook(middleware)


__all__ = ["validate", "validate_hooks", "is_noop", "display_name"]

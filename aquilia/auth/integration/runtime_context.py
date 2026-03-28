"""
AquilAuth runtime context bridge.

Provides request-scoped context for auth operations so AuthManager can
bind to the active session without requiring explicit session plumbing
in every controller/service.
"""

from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class AuthRuntimeContext:
    """Request-scoped auth runtime state."""

    request: Any
    session: Any | None = None
    response: Any | None = None
    container: Any | None = None


_AUTH_RUNTIME_CONTEXT: ContextVar[AuthRuntimeContext | None] = ContextVar("aquilia_auth_runtime_context", default=None)


def set_auth_runtime_context(context: AuthRuntimeContext) -> Token:
    """Set auth runtime context for current async task execution."""
    return _AUTH_RUNTIME_CONTEXT.set(context)


def reset_auth_runtime_context(token: Token) -> None:
    """Reset auth runtime context to previous value."""
    _AUTH_RUNTIME_CONTEXT.reset(token)


def get_auth_runtime_context() -> AuthRuntimeContext | None:
    """Get current auth runtime context, if any."""
    return _AUTH_RUNTIME_CONTEXT.get()


__all__ = [
    "AuthRuntimeContext",
    "set_auth_runtime_context",
    "reset_auth_runtime_context",
    "get_auth_runtime_context",
]

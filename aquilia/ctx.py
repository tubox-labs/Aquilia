"""
Aquilia request context proxy.

Provides request-scoped access to request/session/identity/auth via contextvars.
"""

from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass
class _ContextData:
    request: Any | None = None
    session: Any | None = None
    identity: Any | None = None
    auth: Any | None = None
    container: Any | None = None
    extras: dict[str, Any] = field(default_factory=dict)


_context_var: ContextVar[_ContextData | None] = ContextVar("aquilia_context", default=None)


class _ContextProxy:
    @property
    def request(self) -> Any | None:
        data = _context_var.get()
        return data.request if data is not None else None

    @property
    def session(self) -> Any | None:
        data = _context_var.get()
        return data.session if data is not None else None

    @property
    def identity(self) -> Any | None:
        data = _context_var.get()
        return data.identity if data is not None else None

    @property
    def auth(self) -> Any | None:
        data = _context_var.get()
        return data.auth if data is not None else None

    @property
    def container(self) -> Any | None:
        data = _context_var.get()
        return data.container if data is not None else None

    @property
    def is_authenticated(self) -> bool:
        if self.identity is not None:
            return True
        session = self.session
        return bool(session is not None and getattr(session, "is_authenticated", False))

    def get(self, key: str, default: Any = None) -> Any:
        data = _context_var.get()
        if data is None:
            return default
        return data.extras.get(key, default)

    def set(self, key: str, value: Any) -> None:
        data = _context_var.get()
        if data is None:
            data = _ContextData()
            _context_var.set(data)
        data.extras[key] = value

    def resolve(self, token: type[T], *, optional: bool = False) -> T | None:
        container = self.container
        if container is None:
            if optional:
                return None
            raise RuntimeError("No DI container in context")
        return container.resolve(token, optional=optional)

    async def resolve_async(self, token: type[T], *, optional: bool = False) -> T | None:
        container = self.container
        if container is None:
            if optional:
                return None
            raise RuntimeError("No DI container in context")
        return await container.resolve_async(token, optional=optional)

    async def sign_in(self, **kwargs: Any) -> Any:
        auth = self.auth
        if auth is not None:
            return await auth.sign_in(**kwargs)

        from aquilia.auth.manager import AuthManager

        manager = await self.resolve_async(AuthManager, optional=True)
        if manager is None:
            raise RuntimeError("No AuthManager available in context")
        return await manager.sign_in(**kwargs)

    async def sign_out(self, **kwargs: Any) -> Any:
        auth = self.auth
        if auth is not None:
            return await auth.sign_out(**kwargs)

        from aquilia.auth.manager import AuthManager

        manager = await self.resolve_async(AuthManager, optional=True)
        if manager is None:
            raise RuntimeError("No AuthManager available in context")
        return await manager.sign_out(**kwargs)

    async def resume_identity(self, access_token: str | None = None) -> Any:
        auth = self.auth
        if auth is not None:
            return await auth.resume_identity(access_token=access_token)

        from aquilia.auth.manager import AuthManager

        manager = await self.resolve_async(AuthManager, optional=True)
        if manager is None:
            raise RuntimeError("No AuthManager available in context")
        return await manager.resume_identity(access_token=access_token)


ctx = _ContextProxy()


def set_context(
    *,
    request: Any | None = None,
    session: Any | None = None,
    identity: Any | None = None,
    auth: Any | None = None,
    container: Any | None = None,
) -> Token[_ContextData | None]:
    return _context_var.set(
        _ContextData(
            request=request,
            session=session,
            identity=identity,
            auth=auth,
            container=container,
        )
    )


def update_context(
    *,
    request: Any | None = None,
    session: Any | None = None,
    identity: Any | None = None,
    auth: Any | None = None,
    container: Any | None = None,
) -> None:
    data = _context_var.get()
    if data is None:
        data = _ContextData()
        _context_var.set(data)

    if request is not None:
        data.request = request
    if session is not None:
        data.session = session
    if identity is not None:
        data.identity = identity
    if auth is not None:
        data.auth = auth
    if container is not None:
        data.container = container


def reset_context(token: Token[_ContextData | None]) -> None:
    _context_var.reset(token)


def clear_context() -> None:
    _context_var.set(None)


__all__ = [
    "ctx",
    "set_context",
    "update_context",
    "reset_context",
    "clear_context",
]

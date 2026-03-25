from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Protocol, TypeAlias, TypeVar

T = TypeVar("T")

DIName: TypeAlias = object
DIOptionalFlag: TypeAlias = bool
DIResolvedValue: TypeAlias = object
CleanupCallback: TypeAlias = Callable[[], object | Awaitable[object]]


class SyncResolvableContainer(Protocol):
    def resolve(self, name: DIName, optional: DIOptionalFlag = False) -> DIResolvedValue: ...


class AsyncResolvableContainer(Protocol):
    async def resolve_async(self, name: DIName, optional: DIOptionalFlag = False) -> DIResolvedValue: ...


class StartupContainer(Protocol):
    async def startup(self) -> None: ...


class ShutdownContainer(Protocol):
    async def shutdown(self) -> None: ...


class RequestScopeFactory(Protocol):
    def create_request_scope(self) -> RequestContainer: ...


class RequestContainer(AsyncResolvableContainer, SyncResolvableContainer, ShutdownContainer, Protocol):
    pass


class AppContainer(
    AsyncResolvableContainer,
    SyncResolvableContainer,
    StartupContainer,
    ShutdownContainer,
    RequestScopeFactory,
    Protocol,
):
    pass

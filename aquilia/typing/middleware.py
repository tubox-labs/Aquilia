from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Protocol, TypeAlias

if TYPE_CHECKING:
    from aquilia.controller.base import RequestCtx
    from aquilia.request import Request
    from aquilia.response import Response

MiddlewareName: TypeAlias = str
MiddlewareScope: TypeAlias = str
MiddlewarePriority: TypeAlias = int

RequestHandler: TypeAlias = Callable[["Request", "RequestCtx"], Awaitable["Response"]]
MiddlewareCallable: TypeAlias = Callable[["Request", "RequestCtx", RequestHandler], Awaitable["Response"]]


class MiddlewareProtocol(Protocol):
    async def __call__(self, request: Request, ctx: RequestCtx, next_handler: RequestHandler) -> Response: ...

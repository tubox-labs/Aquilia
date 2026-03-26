from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable, Iterator, Mapping, Sequence
from typing import Any, Protocol, TypeAlias

from .common import JSONValue

ControllerName: TypeAlias = str
RoutePath: TypeAlias = str
HTTPMethod: TypeAlias = str
RouteParams: TypeAlias = dict[str, object]
RouteQuery: TypeAlias = dict[str, object]
ControllerPipeline: TypeAlias = list[object]

RouteMetadataDict: TypeAlias = dict[str, Any]


class ControllerRouteMatchLike(Protocol):
    route: object
    params: RouteParams
    query: RouteQuery


ControllerHandler: TypeAlias = Callable[..., Awaitable[object]]
ControllerStreamChunk: TypeAlias = bytes | str
ControllerStreamIterator: TypeAlias = AsyncIterator[ControllerStreamChunk] | Iterator[ControllerStreamChunk]
ControllerReturnValue: TypeAlias = (
    JSONValue | bytes | str | Mapping[str, Any] | Sequence[Any] | ControllerStreamIterator | Awaitable[Any]
)
ControllerStateMap: TypeAlias = dict[str, JSONValue]

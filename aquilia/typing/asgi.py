from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Literal, Protocol, TypedDict, TypeAlias

from .common import RawHeaderList

ASGIVersionInfo: TypeAlias = dict[str, str]
ASGIServerAddress: TypeAlias = tuple[str, int | None] | None
ASGIClientAddress: TypeAlias = tuple[str, int] | None


class HTTPScope(TypedDict, total=False):
    type: Literal["http"]
    asgi: ASGIVersionInfo
    http_version: str
    method: str
    scheme: str
    path: str
    raw_path: bytes
    root_path: str
    query_string: bytes
    headers: RawHeaderList
    client: ASGIClientAddress
    server: ASGIServerAddress
    state: dict[str, object]


class WebSocketScope(TypedDict, total=False):
    type: Literal["websocket"]
    asgi: ASGIVersionInfo
    http_version: str
    scheme: str
    path: str
    raw_path: bytes
    root_path: str
    query_string: bytes
    headers: RawHeaderList
    client: ASGIClientAddress
    server: ASGIServerAddress
    subprotocols: list[str]
    state: dict[str, object]


class LifespanScope(TypedDict, total=False):
    type: Literal["lifespan"]
    asgi: ASGIVersionInfo
    state: dict[str, object]


ASGIScope: TypeAlias = dict[str, Any]


class HTTPRequestEvent(TypedDict, total=False):
    type: Literal["http.request"]
    body: bytes
    more_body: bool


class HTTPDisconnectEvent(TypedDict):
    type: Literal["http.disconnect"]


class HTTPResponseStartEvent(TypedDict, total=False):
    type: Literal["http.response.start"]
    status: int
    headers: RawHeaderList
    trailers: bool


class HTTPResponseBodyEvent(TypedDict, total=False):
    type: Literal["http.response.body"]
    body: bytes
    more_body: bool


class HTTPResponseTrailersEvent(TypedDict, total=False):
    type: Literal["http.response.trailers"]
    headers: RawHeaderList
    more_trailers: bool


class WebSocketConnectEvent(TypedDict):
    type: Literal["websocket.connect"]


class WebSocketReceiveEvent(TypedDict, total=False):
    type: Literal["websocket.receive"]
    bytes: bytes
    text: str


class WebSocketDisconnectEvent(TypedDict, total=False):
    type: Literal["websocket.disconnect"]
    code: int
    reason: str


class WebSocketAcceptEvent(TypedDict, total=False):
    type: Literal["websocket.accept"]
    subprotocol: str
    headers: RawHeaderList


class WebSocketSendEvent(TypedDict, total=False):
    type: Literal["websocket.send"]
    bytes: bytes
    text: str


class WebSocketCloseEvent(TypedDict, total=False):
    type: Literal["websocket.close"]
    code: int
    reason: str


class LifespanStartupEvent(TypedDict):
    type: Literal["lifespan.startup"]


class LifespanShutdownEvent(TypedDict):
    type: Literal["lifespan.shutdown"]


class LifespanStartupCompleteEvent(TypedDict):
    type: Literal["lifespan.startup.complete"]


class LifespanStartupFailedEvent(TypedDict, total=False):
    type: Literal["lifespan.startup.failed"]
    message: str


class LifespanShutdownCompleteEvent(TypedDict):
    type: Literal["lifespan.shutdown.complete"]


class LifespanShutdownFailedEvent(TypedDict, total=False):
    type: Literal["lifespan.shutdown.failed"]
    message: str


ASGIReceiveEvent: TypeAlias = dict[str, Any]
ASGISendEvent: TypeAlias = dict[str, Any]

ASGIReceive: TypeAlias = Callable[[], Awaitable[ASGIReceiveEvent]]
ASGISend: TypeAlias = Callable[[ASGISendEvent], Awaitable[None]]


class ASGIApplication(Protocol):
    async def __call__(self, scope: ASGIScope, receive: ASGIReceive, send: ASGISend) -> None:
        ...

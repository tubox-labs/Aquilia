"""
SSEResponse — streaming HTTP response with text/event-stream content type.
Delegates to Response.sse() internally.
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator, AsyncIterable
from typing import Any

from aquilia.response import Response
from aquilia.response import ServerSentEvent as SSEEvent


class SSEResponse:
    """
    An ASGI-compatible SSE response builder.

    Returned directly from a controller method::

        @GET("/events")
        async def events(self, ctx):
            return SSEResponse(self._event_generator())

    Constructor overloads:

    ``SSEResponse(iterable)``
        Wrap an async iterable of SSEEvent objects.

    ``SSEResponse.text(generator)``
        Wrap an AsyncGenerator[str, None] — each string becomes a data event.

    ``SSEResponse.json(generator)``
        Wrap an AsyncGenerator[Any, None] — each value is JSON-encoded.
    """

    def __init__(
        self,
        source: AsyncGenerator[SSEEvent, None] | AsyncIterable[SSEEvent] | None = None,
        *,
        status: int = 200,
        event_name: str = "",
    ) -> None:
        self._source = source
        self._status = status
        self._event_name = event_name
        self._text_source: AsyncGenerator[str, None] | None = None
        self._json_source: AsyncGenerator[Any, None] | None = None

    @classmethod
    def text(
        cls,
        source: AsyncGenerator[str, None],
        *,
        status: int = 200,
        event_name: str = "",
    ) -> SSEResponse:
        """Wrap an async generator of plain text tokens (e.g. LLM output)."""
        instance = cls(status=status, event_name=event_name)
        instance._text_source = source
        return instance

    @classmethod
    def json(
        cls,
        source: AsyncGenerator[Any, None],
        *,
        status: int = 200,
        event_name: str = "",
    ) -> SSEResponse:
        """Wrap an async generator of JSON-serialisable values."""
        instance = cls(status=status, event_name=event_name)
        instance._json_source = source
        return instance

    def _resolve_source(self) -> AsyncGenerator[SSEEvent, None]:
        if self._text_source is not None:

            async def _text():
                async for token in self._text_source:  # type: ignore[union-attr]
                    yield SSEEvent(data=token, event=self._event_name)

            return _text()
        if self._json_source is not None:

            async def _json():
                async for value in self._json_source:  # type: ignore[union-attr]
                    yield SSEEvent(data=json.dumps(value, ensure_ascii=False), event=self._event_name)

            return _json()
        return self._source  # type: ignore[return-value]

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        response = Response.sse(self._resolve_source(), status=self._status)
        await response.send_asgi(send, None)

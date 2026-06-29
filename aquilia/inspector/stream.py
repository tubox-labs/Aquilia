import asyncio
from collections.abc import AsyncGenerator
from typing import Any

from .trace import RequestTrace


class SSEStreamManager:
    """Manages active SSE client streams and fans out trace events."""

    def __init__(self):
        self._queues = set()

    def register_client(self) -> asyncio.Queue:
        q = asyncio.Queue()
        self._queues.add(q)
        return q

    def unregister_client(self, q: asyncio.Queue) -> None:
        self._queues.discard(q)

    def publish_trace(self, trace: RequestTrace) -> None:
        # Fan out
        data = trace.to_dict()
        for q in list(self._queues):
            try:
                q.put_nowait(data)
            except asyncio.QueueFull:
                pass

    async def event_generator(self, q: asyncio.Queue) -> AsyncGenerator[Any, None]:
        try:
            while True:
                data = await q.get()
                yield data
                q.task_done()
        except asyncio.CancelledError:
            pass

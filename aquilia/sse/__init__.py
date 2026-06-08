"""
Aquilia SSE — Server-Sent Events support.

Quick start::

    from aquilia import Controller, GET, RequestCtx
    from aquilia.sse import SSEEvent, SSEResponse

    class StreamController(Controller):
        prefix = "/stream"

        @GET("/events")
        async def live_events(self, ctx: RequestCtx):
            return SSEResponse(self._generate_events())

        async def _generate_events(self):
            for i in range(100):
                yield SSEEvent(data=f"event {i}", event="update", id=str(i))
                await asyncio.sleep(0.5)

LLM token streaming::

    @GET("/chat")
    async def chat_stream(self, ctx: RequestCtx):
        prompt = ctx.query.get("q", "")
        return SSEResponse.text(self.llm.stream(prompt))
"""

from aquilia.response import ServerSentEvent

from ._core import SSEResponse
from ._faults import SSE_DOMAIN, SSEFault, SSESerializationFault, SSEStreamAbortedFault

SSEEvent = ServerSentEvent

__all__ = [
    "SSEEvent",
    "SSEResponse",
    "SSE_DOMAIN",
    "SSEFault",
    "SSEStreamAbortedFault",
    "SSESerializationFault",
]

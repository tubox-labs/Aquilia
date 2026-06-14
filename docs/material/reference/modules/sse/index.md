# SSE Module

> `aquilia.sse` — Server-Sent Events streaming

The SSE module provides lightweight, unidirectional real-time streaming via Server-Sent Events — ideal for live updates, LLM token streaming, and notification feeds.

## When to Use

Use the SSE module when you need:

- Streaming real-time updates to clients
- LLM token streaming (OpenAI, etc.)
- Progress indicators for long-running operations
- Live dashboards and notification feeds

## Key Classes

| Class | Purpose |
|---|---|
| `SSEEvent` | Typed SSE event with event name, data, ID, retry |
| `SSEResponse` | Response class for SSE streams |

## Quick Example

```python
from aquilia import Controller, GET, RequestCtx
from aquilia.sse import SSEEvent, SSEResponse
import asyncio

class StreamController(Controller):
    @GET("/stream")
    async def stream(self, ctx: RequestCtx):
        async def generate():
            for i in range(10):
                yield SSEEvent(event="update", data={"step": i})
                await asyncio.sleep(1)
            yield SSEEvent(event="done", data={"status": "complete"})
        
        return SSEResponse(generate())
```

## Import Path

```python
from aquilia.sse import SSEEvent, SSEResponse
```

## Related Modules

- [sockets](../sockets/index.md) — WebSocket for bidirectional real-time communication
- [core/response](../core/response.md) — `Response.sse()` factory method
- [core/flow](../core/flow.md) — SSE streaming in flow pipelines
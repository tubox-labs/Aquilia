# Server-Sent Events (SSE)

Aquilia provides first-class Server-Sent Events support through `SSEResponse` and `SSEEvent` classes, enabling real-time unidirectional data streaming from server to client.

## SSEEvent

```python
@dataclass
class ServerSentEvent:
    """Server-Sent Event data structure."""

    data: str
    id: str | None = None
    event: str | None = None
    retry: int | None = None

    def encode(self) -> bytes:
        """Encode SSE event according to spec."""
```

`SSEEvent` is an alias for `ServerSentEvent`:

```python
from aquilia.response import ServerSentEvent as SSEEvent
```

| Field | Type | Description |
|---|---|---|
| `data` | `str` | Event data (may contain newlines — encoded as multi-line `data:` fields) |
| `id` | `str \| None` | Event ID for reconnection tracking |
| `event` | `str \| None` | Named event type |
| `retry` | `int \| None` | Client reconnection time in milliseconds |

### Encoding

The `encode()` method produces SSE-spec-compliant bytes:

```
id: 42
event: update
retry: 3000
data: {"message": "hello"}
data: second line

```

- Empty `id`/`event` fields are omitted
- Multi-line data is split into separate `data:` prefix lines
- Each event ends with `\n\n` (double newline)

---

## SSEResponse

```python
class SSEResponse:
    """
    An ASGI-compatible SSE response builder.

    Returned directly from a controller method.
    """
```

### Constructor

```python
def __init__(
    self,
    source: AsyncGenerator[SSEEvent, None] | AsyncIterable[SSEEvent] | None = None,
    *,
    status: int = 200,
    event_name: str = "",
) -> None:
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `source` | `AsyncGenerator[SSEEvent, None] \| AsyncIterable[SSEEvent] \| None` | `None` | Async iterable of SSEEvent objects |
| `status` | `int` | `200` | HTTP status code |
| `event_name` | `str` | `""` | Default event name for `text()`/`json()` sources |

### Factory Methods

#### `SSEResponse.text()`

```python
@classmethod
def text(
    cls,
    source: AsyncGenerator[str, None],
    *,
    status: int = 200,
    event_name: str = "",
) -> SSEResponse:
```

Wraps an async generator of plain text tokens. Each yielded string becomes a `data:` event. Useful for LLM token streaming, log streaming, etc.

```python
@GET("/stream-text")
async def text_stream(self, ctx):
    async def generate():
        for line in some_large_file():
            yield line
            await asyncio.sleep(0.1)

    return SSEResponse.text(generate(), event_name="line")
```

#### `SSEResponse.json()`

```python
@classmethod
def json(
    cls,
    source: AsyncGenerator[Any, None],
    *,
    status: int = 200,
    event_name: str = "",
) -> SSEResponse:
```

Wraps an async generator of JSON-serializable values. Each value is `json.dumps()`-encoded.

```python
@GET("/stream-json")
async def json_stream(self, ctx):
    async def generate():
        for i in range(10):
            yield {"iteration": i, "timestamp": time.time()}
            await asyncio.sleep(1)

    return SSEResponse.json(generate(), event_name="progress")
```

### ASGI Integration

```python
async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
    """SSEResponse is itself ASGI-compatible."""
```

Internally delegates to `Response.sse()` which sets:
- `Content-Type: text/event-stream; charset=utf-8`
- `Cache-Control: no-cache`
- `Connection: keep-alive`
- `X-Accel-Buffering: no` (disables nginx buffering)

---

## Response.sse() Integration

SSEResponse uses `Response.sse()` under the hood:

```python
@classmethod
def sse(cls, event_iter: AsyncIterator[ServerSentEvent], status: int = 200, **kwargs) -> Response:
    """
    Create Server-Sent Events (SSE) response.

    Args:
        event_iter: Async iterator of ServerSentEvent objects
        status: HTTP status
    Returns:
        SSE streaming response
    """
```

---

## Usage Patterns

### Basic SSE Stream

```python
from aquilia import Controller, GET, RequestCtx
from aquilia.sse import SSEResponse, SSEEvent

class EventsController(Controller):
    prefix = "/events"

    @GET("/")
    async def stream_events(self, ctx: RequestCtx):
        async def event_generator():
            for i in range(100):
                yield SSEEvent(
                    data=f"Event {i}",
                    id=str(i),
                    event="counter",
                )
                await asyncio.sleep(0.5)

        return SSEResponse(event_generator())
```

### Named Events

```python
async def event_generator():
    yield SSEEvent(data=json.dumps({"type": "init"}), event="system")
    yield SSEEvent(data=json.dumps({"items": [...]}), event="update", id="1")
    yield SSEEvent(data=json.dumps({"item": {...}}), event="update", id="2")
```

### Reconnection Control

```python
# Initial connection — set reconnect interval
yield SSEEvent(data="connected", event="system", retry=3000)

# Client will retry every 3 seconds on disconnect
```

---

## SSE Faults

```python
class SSEFault(Fault):
    domain = "sse"
    severity = Severity.ERROR

class SSEStreamAbortedFault(SSEFault):
    code = "sse.stream_aborted"
    message = "SSE stream was aborted before completion"

class SSESerializationFault(SSEFault):
    code = "sse.serialization_error"
    message = "Failed to serialise SSE event data"
```
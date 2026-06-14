# Response

> `aquilia.response` — Production-grade HTTP response builder

`Response` is a comprehensive HTTP response builder with streaming support, content negotiation, cookie management, caching helpers, JSON serialization, file responses, and SSE streaming.

## Key Factory Methods

| Method | Returns | Purpose |
|---|---|---|
| `Response.json(obj, status=200)` | `Response` | JSON response (auto-serializes) |
| `Response.html(content, status=200)` | `Response` | HTML response |
| `Response.text(content, status=200)` | `Response` | Plain text response |
| `Response.redirect(url, status=307)` | `Response` | HTTP redirect |
| `Response.stream(iterator, status=200)` | `Response` | Streaming response |
| `Response.file(path, filename=None)` | `Response` | File download (sendfile-optimized) |
| `Response.sse(event_iter, status=200)` | `Response` | Server-Sent Events stream |
| `Response.surp(obj, status=200)` | `Response` | Binary SURP serialization |

## JSON Serialization

```python
from aquilia import Controller, GET, RequestCtx, Response

class ApiController(Controller):
    @GET("/data")
    async def get_data(self, ctx: RequestCtx):
        return Response.json({
            "items": [{"id": 1, "name": "Widget"}, {"id": 2, "name": "Gadget"}],
            "count": 2,
        })
```

Aquilia auto-detects the fastest JSON encoder: `orjson` > `ujson` > stdlib `json`.

## Streaming

```python
import asyncio

async def generate_events():
    for i in range(5):
        await asyncio.sleep(0.5)
        yield f"data: Event {i}\n\n"

return Response.stream(generate_events(), media_type="text/event-stream")
```

## File Responses

```python
# Serve a file for download
return Response.file(
    "/path/to/report.pdf",
    filename="quarterly-report.pdf",
    media_type="application/pdf",
)

# With range request support (206 Partial Content)
return Response.file("/path/to/video.mp4", media_type="video/mp4")
```

## Cookie Management

```python
response = Response.json({"ok": True})

# Set a signed cookie
response.set_cookie(
    "session_id", "abc123",
    max_age=3600,
    secure=True,
    httponly=True,
    samesite="lax",
)

# Delete a cookie
response.delete_cookie("session_id", path="/")
```

## Caching Helpers

```python
from datetime import datetime, timedelta, timezone

response = Response.json(data)

# ETag
response.set_etag("v1.0", weak=True)

# Last-Modified
response.set_last_modified(datetime.now(timezone.utc))

# Cache-Control
response.cache_control(
    max_age=3600,
    public=True,
    stale_while_revalidate=600,
)

# Conditional: returns 304 if client has fresh copy
await response.check_not_modified(request)
```

## Security Headers

```python
# Apply multiple security headers at once
response.secure_headers(
    hsts=True,
    csp="default-src 'self'",
    frame_options="DENY",
    content_type_nosniff=True,
    xss_protection=True,
)
```

## SSE (Server-Sent Events)

```python
import asyncio

async def event_stream():
    for i in range(10):
        yield {"event": "update", "data": {"step": i}}
        await asyncio.sleep(1)

return Response.sse(event_stream())
```

## Header Manipulation

```python
response = Response.json(data, status=201)

response.set_header("X-Custom", "value")
response.add_header("Set-Cookie", "a=b")  # Append (doesn't replace)
response.unset_header("X-Unwanted")
```

## Background Tasks

```python
response = Response.json({"status": "processing"})

response.background(lambda: logger.info("Cleanup after response sent"))
```

## Redirection

```python
# Temporary redirect (307)
return Response.redirect("/new-location")

# Permanent redirect (301)
return Response.redirect("/new-location", status=301)

# External URL
return Response.redirect("https://example.com", status=302)
```

## Related

- [Request](request.md) — Request parsing and body handling
- [SSE](../sse/index.md) — Server-Sent Events response pattern
- [Templates](../templates/index.md) — HTML template rendering
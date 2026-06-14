# HTTP Module

> `aquilia.http` — Async HTTP client with connection pooling

The HTTP module provides an async HTTP client with connection pooling, interceptors, middleware, retry logic, streaming responses, multipart uploads, and cookie management.

## When to Use

Use the HTTP module when you need:

- Making HTTP requests from services/controllers
- Connection pooling for performance
- Automatic retry with backoff
- Streaming large responses
- Multipart file uploads to external services

## Key Classes

| Class | Purpose |
|---|---|
| `AsyncHTTPClient` | Main async HTTP client |
| `HTTPSession` | Configurable HTTP session with cookies and auth |
| `ConnectionPool` | Connection pool with configurable limits |
| `Interceptor` | Request/response interception |
| `RetryPolicy` | Retry with exponential backoff |

## Quick Example

```python
from aquilia.http import AsyncHTTPClient

client = AsyncHTTPClient()

# Simple GET
response = await client.get("https://api.example.com/data")
data = await response.json()

# POST with JSON
response = await client.post(
    "https://api.example.com/users",
    json={"name": "Alice"},
    headers={"Authorization": "Bearer token"},
)

# Streaming response
async with client.stream("GET", "https://api.example.com/large") as resp:
    async for chunk in resp.iter_content(8192):
        process(chunk)

# Custom session with retry
session = HTTPSession(
    base_url="https://api.example.com",
    retry=RetryPolicy(max_retries=3, backoff=1.0),
    pool=ConnectionPool(max_connections=20),
)
response = await session.get("/data")
```

## Import Path

```python
from aquilia.http import (
    AsyncHTTPClient,
    HTTPSession,
    ConnectionPool,
)
```

## Related Modules

- [core/effects](../core/effects.md) — HTTPEffect for pipeline integration
- [integrations](../integrations/index.md) — HTTP client configuration
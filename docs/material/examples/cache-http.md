# Cache HTTP Edge

The Cache HTTP Edge example demonstrates a production cache-aside HTTP gateway
using Aquilia's cache primitives and a mock HTTP transport for deterministic
behavior without real network calls.

---

## What It Demonstrates

- `CacheService` with `MemoryBackend` for in-memory caching
- `AsyncHTTPClient` with `MockTransport` for deterministic responses
- Cache-aside pattern: check cache first, fetch on miss, populate cache
- Cache invalidation via explicit purge endpoints
- TTL (time-to-live) configuration for cache entries
- Service composition: `EdgeGatewayService` owns both cache and HTTP client

## Key Files

| File | Purpose |
| ---- | ------- |
| `workspace.py` | Configures `CacheIntegration` with memory backend and 300s TTL |
| `modules/edge/manifest.py` | Declares `EdgeController` and `EdgeGatewayService` |
| `modules/edge/controllers.py` | HTTP endpoints for proxied reads and cache purge |
| `modules/edge/services.py` | `EdgeGatewayService` implementing cache-aside logic |

## Workspace Configuration

```python
from aquilia.integrations import CacheIntegration, DiIntegration

workspace = (
    Workspace("cache-http-edge-app", version="1.0.0")
    .runtime(mode="dev", host="127.0.0.1", port=8062, reload=True)
    .module(Module("edge", version="1.0.0").route_prefix("/edge").tags("cache", "http"))
    .integrate(CacheIntegration(backend="memory", default_ttl=300))
    .integrate(DiIntegration(auto_wire=True))
)
```

## Cache-Aside Pattern

The `EdgeGatewayService` implements the standard cache-aside pattern:

```python
class EdgeGatewayService:
    def __init__(self):
        self._cache = CacheService(backend=MemoryBackend())
        self._http = AsyncHTTPClient(transport=MockTransport(self._origin_data))

    async def get_product(self, sku: str) -> dict:
        cached = await self._cache.get(f"product:{sku}")
        if cached is not None:
            return cached

        product = await self._http.get(f"https://origin.example.test/products/{sku}")
        await self._cache.set(f"product:{sku}", product, ttl=300)
        return product

    async def invalidate_product(self, sku: str) -> bool:
        return await self._cache.delete(f"product:{sku}")
```

The flow for each request:

1. Check cache for key `product:{sku}`
2. On hit: return cached value immediately
3. On miss: fetch from origin via HTTP client
4. Populate cache with origin response (TTL 300s)
5. Return the fresh value
6. On explicit purge: delete the cache key

## Controller Routes

```python
class EdgeController(Controller):
    prefix = "/"
    tags = ["edge"]

    @GET("/products/<sku:str>")
    async def get_product(self, ctx: RequestCtx, sku: str):
        return Response.json(await self.service.get_product(sku))

    @DELETE("/products/<sku:str>/cache")
    async def purge_cache(self, ctx: RequestCtx, sku: str):
        purged = await self.service.invalidate_product(sku)
        return Response.json({"purged": purged, "sku": sku})
```

## Running

```bash
cd examples/cache_http_edge_app
python -m uvicorn runtime:app --reload --port 8062
```

```bash
# First request hits origin and populates cache
curl http://127.0.0.1:8062/edge/products/AQ-STARTER

# Second request returns from cache (no origin call)
curl http://127.0.0.1:8062/edge/products/AQ-STARTER

# Purge the cache key
curl -X DELETE http://127.0.0.1:8062/edge/products/AQ-STARTER/cache

# Run tests
python -m pytest examples/cache_http_edge_app -q
```

## What You'll Learn

- How to configure `CacheIntegration` with `MemoryBackend`
- How to implement cache-aside reads with `CacheService`
- How to invalidate cache entries on data mutation
- How to use `MockTransport` for deterministic HTTP client tests
- How TTL-based expiration controls cache freshness
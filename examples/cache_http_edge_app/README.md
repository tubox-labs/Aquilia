# Cache HTTP Edge App

## Purpose

Shows a production cache-aside HTTP gateway without real network calls. It uses Aquilia cache primitives and the built-in HTTP `MockTransport`.

## Architecture

- `workspace.py` configures memory cache integration.
- `EdgeGatewayService` owns `CacheService`, `MemoryBackend`, and `AsyncHTTPClient`.
- `MockTransport` makes the example deterministic and CI-friendly.
- `AppManifest` exposes the edge service and controller.

## Setup

```bash
python -m pip install -e ".[dev]"
python -m pytest examples/cache_http_edge_app -q
```

## Run

```bash
cd examples/cache_http_edge_app
python -m uvicorn runtime:app --reload --port 8062
```

## Expected Behavior

Repeated reads for the same SKU hit the origin once until `DELETE /edge/products/<sku>/cache` purges the key.

## Common Pitfalls

- `CacheService` wraps backend entries, so app code should use the service API instead of reaching into backend internals.
- Use mock transport in examples and tests; replace with native transport for production egress.

## Extension Ideas

Add Redis or composite cache configuration, cache middleware, stale-while-revalidate, and origin error fallback.

## Related APIs

`CacheService`, `CacheConfig`, `MemoryBackend`, `AsyncHTTPClient`, `MockTransport`, `Integration.cache`.

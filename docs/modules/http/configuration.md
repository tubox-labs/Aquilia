# Http Configuration

Native async HTTP client, request/response builders, sessions, retry policies, auth interceptors, cookies, middleware, streaming, and transport.

This page distinguishes direct configuration APIs from indirect runtime wiring. All class names and source files below are extracted from the current source tree.

## Configuration Model

This module exposes config-oriented public classes. Use the table below to locate exact constructors and `to_dict()` behavior in `api-reference.md`.

## Source Inventory

| File | Lines | Public classes | Public functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/http/__init__.py` | 380 | 0 | 0 | AquilaHTTP — Async HTTP Client for Aquilia. |
| `aquilia/http/_transport.py` | 805 | 6 | 1 | HTTP Transport Layer |
| `aquilia/http/auth.py` | 533 | 8 | 0 | AquilaHTTP — Authentication Interceptors. |
| `aquilia/http/client.py` | 556 | 1 | 6 | AquilaHTTP — Async HTTP Client. |
| `aquilia/http/config.py` | 434 | 8 | 0 | AquilaHTTP — Configuration. |
| `aquilia/http/cookies.py` | 480 | 3 | 0 | AquilaHTTP — Cookie Jar. |
| `aquilia/http/faults.py` | 769 | 25 | 0 | AquilaHTTP — Fault Classes. |
| `aquilia/http/integration.py` | 340 | 2 | 2 | AquilaHTTP — Framework Integration. |
| `aquilia/http/interceptors.py` | 516 | 11 | 0 | AquilaHTTP — Interceptors. |
| `aquilia/http/middleware.py` | 485 | 11 | 1 | AquilaHTTP — Middleware. |
| `aquilia/http/multipart.py` | 484 | 3 | 0 | AquilaHTTP — Multipart Form Data. |
| `aquilia/http/pool.py` | 445 | 4 | 0 | AquilaHTTP — Connection Pool. |
| `aquilia/http/request.py` | 552 | 3 | 7 | AquilaHTTP — HTTP Client Request. |
| `aquilia/http/response.py` | 502 | 1 | 1 | AquilaHTTP — HTTP Client Response. |
| `aquilia/http/retry.py` | 390 | 8 | 1 | AquilaHTTP — Retry Strategies. |
| `aquilia/http/session.py` | 490 | 1 | 0 | AquilaHTTP — HTTP Session. |
| `aquilia/http/streaming.py` | 388 | 5 | 4 | AquilaHTTP — Streaming Support. |

## Detected Config-Oriented Classes

| Class | Source | Methods | Summary |
| --- | --- | --- | --- |
| `TimeoutConfig` | `aquilia/http/config.py` | `no_timeout`, `fast`, `slow` | HTTP request timeout configuration. |
| `PoolConfig` | `aquilia/http/config.py` |  | Connection pool configuration. |
| `RetryConfig` | `aquilia/http/config.py` | `no_retry`, `aggressive` | Retry configuration. |
| `ProxyConfig` | `aquilia/http/config.py` | `from_env` | Proxy configuration. |
| `TLSConfig` | `aquilia/http/config.py` |  | TLS/SSL configuration. |
| `HTTPClientConfig` | `aquilia/http/config.py` | `with_base_url`, `with_timeout`, `merge_headers`, `merge_params`, `to_dict`, `from_dict` | Complete HTTP client configuration. |
| `ConfigurationFault` | `aquilia/http/faults.py` |  | HTTP client configuration error. |
| `HTTPClientProvider` | `aquilia/http/integration.py` | `provides`, `scope`, `shutdown` | DI provider for AsyncHTTPClient. |
| `HTTPClientBuilder` | `aquilia/http/integration.py` | `base_url`, `timeout`, `pool`, `retry`, `proxy`, `tls`, `header`, `headers`, `follow_redirects`, `max_redirects`, `raise_for_status`, `user_agent`, `build`, `build_provider`, `to_dict` | Fluent builder for HTTP client configuration. |
| `HTTPClientMiddleware` | `aquilia/http/middleware.py` |  | Base class for HTTP client middleware. |
| `MiddlewareStack` | `aquilia/http/middleware.py` | `add`, `add_many`, `set_handler`, `build`, `execute` | Stack of middleware that processes requests. |
| `LoggingMiddleware` | `aquilia/http/middleware.py` |  | Logs requests and responses. |
| `HeadersMiddleware` | `aquilia/http/middleware.py` |  | Adds default headers to all requests. |
| `TimeoutMiddleware` | `aquilia/http/middleware.py` |  | Enforces timeout on requests. |
| `ErrorHandlingMiddleware` | `aquilia/http/middleware.py` |  | Handles errors and converts them to faults. |
| `RetryMiddleware` | `aquilia/http/middleware.py` |  | Retries failed requests. |
| `CompressionMiddleware` | `aquilia/http/middleware.py` |  | Handles request/response compression. |
| `CacheMiddleware` | `aquilia/http/middleware.py` |  | Caches GET responses. |
| `BaseURLMiddleware` | `aquilia/http/middleware.py` |  | Prepends base URL to relative URLs. |
| `CookieMiddleware` | `aquilia/http/middleware.py` | `jar` | Manages cookies automatically. |
| `RequestBuilder` | `aquilia/http/request.py` | `header`, `headers`, `param`, `params`, `body`, `json`, `form`, `multipart`, `cookie`, `cookies`, `auth_basic`, `auth_bearer`, `timeout`, `follow_redirects`, `extension`, `build` | Fluent builder for HTTP requests. |

## Runtime Wiring Paths

- `workspace.py` defines workspace-level structure with `Workspace`, `Module`, and `Integration` builders.
- `modules/<name>/manifest.py` defines module internals with `AppManifest`.
- `ConfigLoader.get(...)` resolves dotted configuration paths at runtime.
- `AquiliaServer` consumes resolved config during middleware and subsystem setup.
- Subsystems with optional providers only require optional dependencies when their backend/provider is configured.

## Verification Checklist

1. Run `aq validate` to verify manifests.
2. Run `aq inspect config` to inspect resolved configuration.
3. Run `aq doctor` for workspace and integration diagnostics.
4. For server-only wiring, start via `aq run` and check startup logs plus `GET /_health`.

## Related Pages

- `api-reference.md` for exact class fields, methods, constants, and signatures.
- `integration-guide.md` for the workspace/manifest wiring pattern.
- `edge-cases-and-limitations.md` for fallback and compatibility behavior.

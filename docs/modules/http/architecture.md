# Http Architecture

Native async HTTP client, request/response builders, sessions, retry policies, auth interceptors, cookies, middleware, streaming, and transport.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
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

## Internal Shape

`http` has 17 Python files, 100 public classes, 23 public module-level functions, and 12 constants or module flags detected by AST.

## Runtime Responsibilities

- No mounted `aq` command group maps directly to this module; it is used through Python APIs, manifests, workspace integrations, or server startup wiring.

## Internal Imports

| Import | Count |
| --- | ---: |
| `.request` | 15 |
| `.config` | 8 |
| `.response` | 8 |
| `.faults` | 6 |
| `.interceptors` | 4 |
| `._transport` | 3 |
| `.cookies` | 3 |
| `.middleware` | 3 |
| `.client` | 2 |
| `.multipart` | 2 |
| `.session` | 2 |
| `.auth` | 1 |
| `.integration` | 1 |
| `.pool` | 1 |
| `.retry` | 1 |
| `.streaming` | 1 |
| `aquilia.faults.core` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `__future__` | 16 |
| `typing` | 14 |
| `collections` | 11 |
| `dataclasses` | 11 |
| `logging` | 10 |
| `time` | 6 |
| `abc` | 5 |
| `asyncio` | 4 |
| `urllib` | 4 |
| `base64` | 2 |
| `enum` | 2 |
| `http` | 2 |
| `json` | 2 |
| `pathlib` | 2 |
| `ssl` | 2 |
| `datetime` | 1 |
| `gzip` | 1 |
| `hashlib` | 1 |
| `hmac` | 1 |
| `mimetypes` | 1 |
| `random` | 1 |
| `re` | 1 |
| `socket` | 1 |
| `uuid` | 1 |
| `zlib` | 1 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `HTTPTransport` | `aquilia/http/_transport.py` | Base transport interface. |
| `NativeTransport` | `aquilia/http/_transport.py` | Pure asyncio HTTP/1.1 transport. |
| `MockTransport` | `aquilia/http/_transport.py` | Mock transport for tests. Returns predefined responses. |
| `TimeoutConfig` | `aquilia/http/config.py` | HTTP request timeout configuration. |
| `PoolConfig` | `aquilia/http/config.py` | Connection pool configuration. |
| `RetryConfig` | `aquilia/http/config.py` | Retry configuration. |
| `ProxyConfig` | `aquilia/http/config.py` | Proxy configuration. |
| `TLSConfig` | `aquilia/http/config.py` | TLS/SSL configuration. |
| `HTTPClientConfig` | `aquilia/http/config.py` | Complete HTTP client configuration. |
| `TransportFault` | `aquilia/http/faults.py` | Low-level transport error. |
| `ConfigurationFault` | `aquilia/http/faults.py` | HTTP client configuration error. |
| `HTTPClientProvider` | `aquilia/http/integration.py` | DI provider for AsyncHTTPClient. |
| `HTTPClientMiddleware` | `aquilia/http/middleware.py` | Base class for HTTP client middleware. |
| `MiddlewareStack` | `aquilia/http/middleware.py` | Stack of middleware that processes requests. |
| `LoggingMiddleware` | `aquilia/http/middleware.py` | Logs requests and responses. |
| `HeadersMiddleware` | `aquilia/http/middleware.py` | Adds default headers to all requests. |
| `TimeoutMiddleware` | `aquilia/http/middleware.py` | Enforces timeout on requests. |
| `ErrorHandlingMiddleware` | `aquilia/http/middleware.py` | Handles errors and converts them to faults. |
| `RetryMiddleware` | `aquilia/http/middleware.py` | Retries failed requests. |
| `CompressionMiddleware` | `aquilia/http/middleware.py` | Handles request/response compression. |
| `CacheMiddleware` | `aquilia/http/middleware.py` | Caches GET responses. |
| `BaseURLMiddleware` | `aquilia/http/middleware.py` | Prepends base URL to relative URLs. |
| `CookieMiddleware` | `aquilia/http/middleware.py` | Manages cookies automatically. |
| `ConnectionPoolManager` | `aquilia/http/pool.py` | Manager for multiple connection pools. |

## Error Handling

Fault/error classes defined here:

`HTTPClientFault`, `ConnectionFault`, `ConnectionPoolExhaustedFault`, `ConnectionClosedFault`, `TimeoutFault`, `ConnectTimeoutFault`, `ReadTimeoutFault`, `WriteTimeoutFault`, `RequestTimeoutFault`, `TLSFault`, `CertificateVerifyFault`, `ResponseFault`, `InvalidResponseFault`, `DecodingFault`, `HTTPStatusFault`, `ClientErrorFault`, `ServerErrorFault`, `TooManyRedirectsFault`, `RequestBuildFault`, `InvalidURLFault`, `InvalidHeaderFault`, `TransportFault`, `ProxyFault`, `RetryExhaustedFault`, `ConfigurationFault`, `ErrorHandlingMiddleware`

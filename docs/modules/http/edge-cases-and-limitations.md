# HTTP Client Edge Cases And Limitations

## Fault And Error Types

The following error-oriented classes are present in the implementation and should guide defensive usage.

| Type | Source | Meaning |
| --- | --- | --- |
| `HTTPClientFault` | `aquilia/http/faults.py` | Base fault for the HTTP client subsystem. |
| `ConnectionFault` | `aquilia/http/faults.py` | Failed to establish connection to remote host. |
| `ConnectionPoolExhaustedFault` | `aquilia/http/faults.py` | Connection pool exhausted. |
| `ConnectionClosedFault` | `aquilia/http/faults.py` | Connection was unexpectedly closed. |
| `TimeoutFault` | `aquilia/http/faults.py` | Request timed out. |
| `ConnectTimeoutFault` | `aquilia/http/faults.py` | Connection timeout. |
| `ReadTimeoutFault` | `aquilia/http/faults.py` | Read timeout. |
| `WriteTimeoutFault` | `aquilia/http/faults.py` | Write timeout. |
| `RequestTimeoutFault` | `aquilia/http/faults.py` | Total request timeout. |
| `TLSFault` | `aquilia/http/faults.py` | TLS/SSL error. |
| `CertificateVerifyFault` | `aquilia/http/faults.py` | Certificate verification failed. |
| `ResponseFault` | `aquilia/http/faults.py` | Response processing error. |
| `InvalidResponseFault` | `aquilia/http/faults.py` | Invalid response received. |
| `DecodingFault` | `aquilia/http/faults.py` | Response body decoding error. |
| `HTTPStatusFault` | `aquilia/http/faults.py` | HTTP error status received. |
| `ClientErrorFault` | `aquilia/http/faults.py` | HTTP 4xx client error. |
| `ServerErrorFault` | `aquilia/http/faults.py` | HTTP 5xx server error. |
| `TooManyRedirectsFault` | `aquilia/http/faults.py` | Too many redirects. |
| `RequestBuildFault` | `aquilia/http/faults.py` | Request construction error. |
| `InvalidURLFault` | `aquilia/http/faults.py` | Invalid URL. |
| `InvalidHeaderFault` | `aquilia/http/faults.py` | Invalid header. |
| `TransportFault` | `aquilia/http/faults.py` | Low-level transport error. |
| `ProxyFault` | `aquilia/http/faults.py` | Proxy connection error. |
| `RetryExhaustedFault` | `aquilia/http/faults.py` | All retry attempts exhausted. |
| `ConfigurationFault` | `aquilia/http/faults.py` | HTTP client configuration error. |

## Common Edge Cases

- Optional dependencies may change behavior. Check imports and constructor docs before enabling production features.
- In-memory stores, queues, caches, adapters, and registries are usually process-local. Use durable backends when state must survive restarts or scale across workers.
- Request-scoped data must not be cached globally. Use request state, DI request scopes, or explicit parameters.
- Decorators in Aquilia generally attach metadata at import time. Runtime behavior happens later during compilation, routing, middleware execution, or service startup.
- Many subsystems intentionally convert invalid states into typed faults. Catch the specific fault type when application code can recover.

## Source-Level Limits To Review

Review these files before changing behavior:

- `aquilia/http/__init__.py`: AquilaHTTP - Async HTTP Client for Aquilia.
- `aquilia/http/_transport.py`: HTTP Transport Layer
- `aquilia/http/auth.py`: AquilaHTTP - Authentication Interceptors.
- `aquilia/http/client.py`: AquilaHTTP - Async HTTP Client.
- `aquilia/http/config.py`: AquilaHTTP - Configuration.
- `aquilia/http/cookies.py`: AquilaHTTP - Cookie Jar.
- `aquilia/http/faults.py`: AquilaHTTP - Fault Classes.
- `aquilia/http/integration.py`: AquilaHTTP - Framework Integration.
- `aquilia/http/interceptors.py`: AquilaHTTP - Interceptors.
- `aquilia/http/middleware.py`: AquilaHTTP - Middleware.
- `aquilia/http/multipart.py`: AquilaHTTP - Multipart Form Data.
- `aquilia/http/pool.py`: AquilaHTTP - Connection Pool.
- `aquilia/http/request.py`: AquilaHTTP - HTTP Client Request.
- `aquilia/http/response.py`: AquilaHTTP - HTTP Client Response.
- `aquilia/http/retry.py`: AquilaHTTP - Retry Strategies.
- `aquilia/http/session.py`: AquilaHTTP - HTTP Session.
- `aquilia/http/streaming.py`: AquilaHTTP - Streaming Support.

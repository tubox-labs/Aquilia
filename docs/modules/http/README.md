# http Module

## Purpose

Async HTTP client subsystem. Use this module for outbound HTTP requests, retry policy, auth schemes, cookies, middleware, interceptors, transport pooling, streaming, multipart, and typed HTTP faults.

## Source Coverage

- Python files: 17
- Public classes: 100
- Dataclasses: 19
- Enums: 3
- Public functions: 23

## How It Fits In Aquilia

1. Import the package from `aquilia.http` or its concrete submodules.
2. Configure it through workspace integrations, manifests, or direct service construction depending on the subsystem.
3. Keep business logic outside transport and framework glue so the subsystem stays testable.

## Practical Guidance

- Prefer typed configuration objects and framework helpers over ad hoc dictionaries when they exist.
- Use the tests in `tests/` as behavioral examples when changing this subsystem.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `RawResponse` | `aquilia/http/_transport.py` | Raw response before processing. |
| `ConnectionInfo` | `aquilia/http/_transport.py` | Tracks a pooled connection. |
| `ConnectionPool` | `aquilia/http/_transport.py` | Keep-alive connection pool. Reuses TCP connections per host. |
| `HTTPTransport` | `aquilia/http/_transport.py` | Base transport interface. |
| `NativeTransport` | `aquilia/http/_transport.py` | Pure asyncio HTTP/1.1 transport. |
| `MockTransport` | `aquilia/http/_transport.py` | Mock transport for tests. Returns predefined responses. |
| `AuthInterceptor` | `aquilia/http/auth.py` | Base class for authentication interceptors. |
| `BasicAuth` | `aquilia/http/auth.py` | HTTP Basic Authentication. |
| `BearerAuth` | `aquilia/http/auth.py` | Bearer Token Authentication. |
| `APIKeyAuth` | `aquilia/http/auth.py` | API Key Authentication. |
| `DigestAuth` | `aquilia/http/auth.py` | HTTP Digest Authentication. |
| `OAuth2Token` | `aquilia/http/auth.py` | OAuth 2.0 token. |
| `OAuth2Auth` | `aquilia/http/auth.py` | OAuth 2.0 Bearer Token Authentication. |
| `AWSSignatureV4Auth` | `aquilia/http/auth.py` | AWS Signature Version 4 Authentication. |
| `AsyncHTTPClient` | `aquilia/http/client.py` | Async HTTP client. |
| `HTTPVersion` | `aquilia/http/config.py` | Supported HTTP versions. |
| `CompressionAlgorithm` | `aquilia/http/config.py` | Supported compression algorithms for Accept-Encoding. |
| `TimeoutConfig` | `aquilia/http/config.py` | HTTP request timeout configuration. |
| `PoolConfig` | `aquilia/http/config.py` | Connection pool configuration. |
| `RetryConfig` | `aquilia/http/config.py` | Retry configuration. |
| `ProxyConfig` | `aquilia/http/config.py` | Proxy configuration. |
| `TLSConfig` | `aquilia/http/config.py` | TLS/SSL configuration. |
| `HTTPClientConfig` | `aquilia/http/config.py` | Complete HTTP client configuration. |
| `Cookie` | `aquilia/http/cookies.py` | HTTP Cookie representation. |
| `CookieJar` | `aquilia/http/cookies.py` | Thread-safe cookie storage. |
| `CookieInterceptor` | `aquilia/http/cookies.py` | Interceptor that manages cookies automatically. |
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
| `HTTPClientProvider` | `aquilia/http/integration.py` | DI provider for AsyncHTTPClient. |
| `HTTPClientBuilder` | `aquilia/http/integration.py` | Fluent builder for HTTP client configuration. |
| `HTTPInterceptor` | `aquilia/http/interceptors.py` | Base class for HTTP interceptors. |
| `InterceptorChain` | `aquilia/http/interceptors.py` | Chain of interceptors. |
| `LoggingInterceptor` | `aquilia/http/interceptors.py` | Logs request and response details. |
| `HeaderInterceptor` | `aquilia/http/interceptors.py` | Adds default headers to all requests. |
| `UserAgentInterceptor` | `aquilia/http/interceptors.py` | Sets User-Agent header. |
| `AcceptInterceptor` | `aquilia/http/interceptors.py` | Sets Accept header for content negotiation. |
| `RequestMetrics` | `aquilia/http/interceptors.py` | Metrics collected for a request. |
| `MetricsInterceptor` | `aquilia/http/interceptors.py` | Collects request metrics. |
| `TimeoutInterceptor` | `aquilia/http/interceptors.py` | Enforces timeout on requests. |
| `RedirectInterceptor` | `aquilia/http/interceptors.py` | Handles HTTP redirects. |
| `CacheInterceptor` | `aquilia/http/interceptors.py` | HTTP response caching interceptor. |
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
| `FormField` | `aquilia/http/multipart.py` | A form field in multipart data. |
| `FormFile` | `aquilia/http/multipart.py` | A file field in multipart data. |
| `MultipartFormData` | `aquilia/http/multipart.py` | Builder for multipart/form-data requests. |
| `ConnectionStats` | `aquilia/http/pool.py` | Connection pool statistics. |
| `PooledConnection` | `aquilia/http/pool.py` | Wrapper for a pooled connection. |

Only the first 80 classes are shown here. See the file inventory for the rest of the package.

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| `create_transport` | `aquilia/http/_transport.py` | Create native HTTP transport. |
| `request` | `aquilia/http/client.py` | Make a one-off HTTP request. |
| `get` | `aquilia/http/client.py` | Make a GET request. |
| `post` | `aquilia/http/client.py` | Make a POST request. |
| `put` | `aquilia/http/client.py` | Make a PUT request. |
| `patch` | `aquilia/http/client.py` | Make a PATCH request. |
| `delete` | `aquilia/http/client.py` | Make a DELETE request. |
| `http_client` | `aquilia/http/integration.py` | Create HTTP client integration builder. |
| `create_client_from_config` | `aquilia/http/integration.py` | Create HTTP client from configuration dictionary. |
| `create_middleware_stack` | `aquilia/http/middleware.py` | Create a standard middleware stack. |
| `get` | `aquilia/http/request.py` | Create a GET request builder. |
| `post` | `aquilia/http/request.py` | Create a POST request builder. |
| `put` | `aquilia/http/request.py` | Create a PUT request builder. |
| `patch` | `aquilia/http/request.py` | Create a PATCH request builder. |
| `delete` | `aquilia/http/request.py` | Create a DELETE request builder. |
| `head` | `aquilia/http/request.py` | Create a HEAD request builder. |
| `options` | `aquilia/http/request.py` | Create an OPTIONS request builder. |
| `create_response` | `aquilia/http/response.py` | Factory function to create HTTPClientResponse. |
| `create_retry_strategy` | `aquilia/http/retry.py` | Create a retry strategy from configuration. |
| `stream_file` | `aquilia/http/streaming.py` | Stream a file asynchronously. |
| `stream_bytes` | `aquilia/http/streaming.py` | Stream bytes in chunks. |
| `collect_stream` | `aquilia/http/streaming.py` | Collect all bytes from an async iterator. |
| `stream_with_limit` | `aquilia/http/streaming.py` | Stream with a byte limit. |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/http/__init__.py` | AquilaHTTP - Async HTTP Client for Aquilia. |
| `aquilia/http/_transport.py` | HTTP Transport Layer |
| `aquilia/http/auth.py` | AquilaHTTP - Authentication Interceptors. |
| `aquilia/http/client.py` | AquilaHTTP - Async HTTP Client. |
| `aquilia/http/config.py` | AquilaHTTP - Configuration. |
| `aquilia/http/cookies.py` | AquilaHTTP - Cookie Jar. |
| `aquilia/http/faults.py` | AquilaHTTP - Fault Classes. |
| `aquilia/http/integration.py` | AquilaHTTP - Framework Integration. |
| `aquilia/http/interceptors.py` | AquilaHTTP - Interceptors. |
| `aquilia/http/middleware.py` | AquilaHTTP - Middleware. |
| `aquilia/http/multipart.py` | AquilaHTTP - Multipart Form Data. |
| `aquilia/http/pool.py` | AquilaHTTP - Connection Pool. |
| `aquilia/http/request.py` | AquilaHTTP - HTTP Client Request. |
| `aquilia/http/response.py` | AquilaHTTP - HTTP Client Response. |
| `aquilia/http/retry.py` | AquilaHTTP - Retry Strategies. |
| `aquilia/http/session.py` | AquilaHTTP - HTTP Session. |
| `aquilia/http/streaming.py` | AquilaHTTP - Streaming Support. |

## Testing Pointers

Search `tests/` for `http` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.

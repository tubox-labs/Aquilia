# Http API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

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

## Public Exports

`APIKeyAuth`, `AWSSignatureV4Auth`, `AcceptInterceptor`, `AsyncHTTPClient`, `AuthInterceptor`, `BaseURLMiddleware`, `BasicAuth`, `BearerAuth`, `BufferedStream`, `CacheInterceptor`, `CacheMiddleware`, `CertificateVerifyFault`, `ChunkedDecoder`, `ChunkedEncoder`, `ClientErrorFault`, `CompositeRetryStrategy`, `CompressionAlgorithm`, `CompressionMiddleware`, `ConfigurationFault`, `ConnectTimeoutFault`, `ConnectionClosedFault`, `ConnectionFault`, `ConnectionPool`, `ConnectionPoolExhaustedFault`, `ConnectionPoolManager`, `ConnectionStats`, `ConstantBackoff`, `Cookie`, `CookieInterceptor`, `CookieJar`, `CookieMiddleware`, `DecodingFault`, `DigestAuth`, `ErrorHandlingMiddleware`, `ExponentialBackoff`, `FormField`, `FormFile`, `HTTPClientBuilder`, `HTTPClientConfig`, `HTTPClientFault`, `HTTPClientMiddleware`, `HTTPClientProvider`, `HTTPClientRequest`, `HTTPClientResponse`, `HTTPInterceptor`, `HTTPMethod`, `HTTPSession`, `HTTPStatusFault`, `HTTPTransport`, `HTTPVersion`, `HTTP_CLIENT_DOMAIN`, `HTTP_STATUS_REASONS`, `HeaderInterceptor`, `HeadersMiddleware`, `InterceptorChain`, `InvalidHeaderFault`, `InvalidResponseFault`, `InvalidURLFault`, `LoggingInterceptor`, `LoggingMiddleware`, `MetricsInterceptor`, `MiddlewareStack`, `MockTransport`, `MultipartFormData`, `NativeTransport`, `NoRetry`, `OAuth2Auth`, `OAuth2Token`, `PoolConfig`, `PooledConnection`, `ProxyConfig`, `ProxyFault`, `ReadTimeoutFault`, `RedirectInterceptor`, `RequestBuildFault`, `RequestBuilder`, `RequestMetrics`, `RequestTimeoutFault`, `ResponseFault`, `RetryAfterStrategy`, `RetryConfig`, `RetryExecutor`, `RetryExhaustedFault`, `RetryMiddleware`, `RetryState`, `RetryStrategy`, `ServerErrorFault`, `StreamProgress`, `StreamingBody`, `TLSConfig`, `TLSFault`, `TimeoutConfig`, `TimeoutFault`, `TimeoutInterceptor`, `TimeoutMiddleware`, `TooManyRedirectsFault`, `TransportFault`, `UserAgentInterceptor`, `WriteTimeoutFault`, `collect_stream`, `create_client_from_config`, `create_middleware_stack`, `create_response`, `create_retry_strategy`, `create_transport`, `delete`, `delete_request`, `get`, `get_request`, `head_request`, `http_client`, `options_request`, `patch`, `patch_request`, `post`, `post_request`, `put`, `put_request`, `request`, `stream_bytes`, `stream_file`, `stream_with_limit`

## Public Class Summary

| Class | Source | Bases | Summary |
| --- | --- | --- | --- |
| `RawResponse` | `aquilia/http/_transport.py` | object | Raw response before processing. |
| `ConnectionInfo` | `aquilia/http/_transport.py` | object | Tracks a pooled connection. |
| `ConnectionPool` | `aquilia/http/_transport.py` | object | Keep-alive connection pool. Reuses TCP connections per host. |
| `HTTPTransport` | `aquilia/http/_transport.py` | ABC | Base transport interface. |
| `NativeTransport` | `aquilia/http/_transport.py` | HTTPTransport | Pure asyncio HTTP/1.1 transport. |
| `MockTransport` | `aquilia/http/_transport.py` | HTTPTransport | Mock transport for tests. Returns predefined responses. |
| `AuthInterceptor` | `aquilia/http/auth.py` | HTTPInterceptor, ABC | Base class for authentication interceptors. |
| `BasicAuth` | `aquilia/http/auth.py` | AuthInterceptor | HTTP Basic Authentication. |
| `BearerAuth` | `aquilia/http/auth.py` | AuthInterceptor | Bearer Token Authentication. |
| `APIKeyAuth` | `aquilia/http/auth.py` | AuthInterceptor | API Key Authentication. |
| `DigestAuth` | `aquilia/http/auth.py` | AuthInterceptor | HTTP Digest Authentication. |
| `OAuth2Token` | `aquilia/http/auth.py` | object | OAuth 2.0 token. |
| `OAuth2Auth` | `aquilia/http/auth.py` | AuthInterceptor | OAuth 2.0 Bearer Token Authentication. |
| `AWSSignatureV4Auth` | `aquilia/http/auth.py` | AuthInterceptor | AWS Signature Version 4 Authentication. |
| `AsyncHTTPClient` | `aquilia/http/client.py` | object | Async HTTP client. |
| `HTTPVersion` | `aquilia/http/config.py` | str, Enum | Supported HTTP versions. |
| `CompressionAlgorithm` | `aquilia/http/config.py` | str, Enum | Supported compression algorithms for Accept-Encoding. |
| `TimeoutConfig` | `aquilia/http/config.py` | object | HTTP request timeout configuration. |
| `PoolConfig` | `aquilia/http/config.py` | object | Connection pool configuration. |
| `RetryConfig` | `aquilia/http/config.py` | object | Retry configuration. |
| `ProxyConfig` | `aquilia/http/config.py` | object | Proxy configuration. |
| `TLSConfig` | `aquilia/http/config.py` | object | TLS/SSL configuration. |
| `HTTPClientConfig` | `aquilia/http/config.py` | object | Complete HTTP client configuration. |
| `Cookie` | `aquilia/http/cookies.py` | object | HTTP Cookie representation. |
| `CookieJar` | `aquilia/http/cookies.py` | object | Thread-safe cookie storage. |
| `CookieInterceptor` | `aquilia/http/cookies.py` | object | Interceptor that manages cookies automatically. |
| `HTTPClientFault` | `aquilia/http/faults.py` | Fault | Base fault for the HTTP client subsystem. |
| `ConnectionFault` | `aquilia/http/faults.py` | HTTPClientFault | Failed to establish connection to remote host. |
| `ConnectionPoolExhaustedFault` | `aquilia/http/faults.py` | HTTPClientFault | Connection pool exhausted. |
| `ConnectionClosedFault` | `aquilia/http/faults.py` | HTTPClientFault | Connection was unexpectedly closed. |
| `TimeoutFault` | `aquilia/http/faults.py` | HTTPClientFault | Request timed out. |
| `ConnectTimeoutFault` | `aquilia/http/faults.py` | TimeoutFault | Connection timeout. |
| `ReadTimeoutFault` | `aquilia/http/faults.py` | TimeoutFault | Read timeout. |
| `WriteTimeoutFault` | `aquilia/http/faults.py` | TimeoutFault | Write timeout. |
| `RequestTimeoutFault` | `aquilia/http/faults.py` | TimeoutFault | Total request timeout. |
| `TLSFault` | `aquilia/http/faults.py` | HTTPClientFault | TLS/SSL error. |
| `CertificateVerifyFault` | `aquilia/http/faults.py` | TLSFault | Certificate verification failed. |
| `ResponseFault` | `aquilia/http/faults.py` | HTTPClientFault | Response processing error. |
| `InvalidResponseFault` | `aquilia/http/faults.py` | ResponseFault | Invalid response received. |
| `DecodingFault` | `aquilia/http/faults.py` | ResponseFault | Response body decoding error. |
| `HTTPStatusFault` | `aquilia/http/faults.py` | ResponseFault | HTTP error status received. |
| `ClientErrorFault` | `aquilia/http/faults.py` | HTTPStatusFault | HTTP 4xx client error. |
| `ServerErrorFault` | `aquilia/http/faults.py` | HTTPStatusFault | HTTP 5xx server error. |
| `TooManyRedirectsFault` | `aquilia/http/faults.py` | HTTPClientFault | Too many redirects. |
| `RequestBuildFault` | `aquilia/http/faults.py` | HTTPClientFault | Request construction error. |
| `InvalidURLFault` | `aquilia/http/faults.py` | RequestBuildFault | Invalid URL. |
| `InvalidHeaderFault` | `aquilia/http/faults.py` | RequestBuildFault | Invalid header. |
| `TransportFault` | `aquilia/http/faults.py` | HTTPClientFault | Low-level transport error. |
| `ProxyFault` | `aquilia/http/faults.py` | TransportFault | Proxy connection error. |
| `RetryExhaustedFault` | `aquilia/http/faults.py` | HTTPClientFault | All retry attempts exhausted. |
| `ConfigurationFault` | `aquilia/http/faults.py` | HTTPClientFault | HTTP client configuration error. |
| `HTTPClientProvider` | `aquilia/http/integration.py` | object | DI provider for AsyncHTTPClient. |
| `HTTPClientBuilder` | `aquilia/http/integration.py` | object | Fluent builder for HTTP client configuration. |
| `HTTPInterceptor` | `aquilia/http/interceptors.py` | ABC | Base class for HTTP interceptors. |
| `InterceptorChain` | `aquilia/http/interceptors.py` | object | Chain of interceptors. |
| `LoggingInterceptor` | `aquilia/http/interceptors.py` | HTTPInterceptor | Logs request and response details. |
| `HeaderInterceptor` | `aquilia/http/interceptors.py` | HTTPInterceptor | Adds default headers to all requests. |
| `UserAgentInterceptor` | `aquilia/http/interceptors.py` | HTTPInterceptor | Sets User-Agent header. |
| `AcceptInterceptor` | `aquilia/http/interceptors.py` | HTTPInterceptor | Sets Accept header for content negotiation. |
| `RequestMetrics` | `aquilia/http/interceptors.py` | object | Metrics collected for a request. |
| `MetricsInterceptor` | `aquilia/http/interceptors.py` | HTTPInterceptor | Collects request metrics. |
| `TimeoutInterceptor` | `aquilia/http/interceptors.py` | HTTPInterceptor | Enforces timeout on requests. |
| `RedirectInterceptor` | `aquilia/http/interceptors.py` | HTTPInterceptor | Handles HTTP redirects. |
| `CacheInterceptor` | `aquilia/http/interceptors.py` | HTTPInterceptor | HTTP response caching interceptor. |
| `HTTPClientMiddleware` | `aquilia/http/middleware.py` | ABC | Base class for HTTP client middleware. |
| `MiddlewareStack` | `aquilia/http/middleware.py` | object | Stack of middleware that processes requests. |
| `LoggingMiddleware` | `aquilia/http/middleware.py` | HTTPClientMiddleware | Logs requests and responses. |
| `HeadersMiddleware` | `aquilia/http/middleware.py` | HTTPClientMiddleware | Adds default headers to all requests. |
| `TimeoutMiddleware` | `aquilia/http/middleware.py` | HTTPClientMiddleware | Enforces timeout on requests. |
| `ErrorHandlingMiddleware` | `aquilia/http/middleware.py` | HTTPClientMiddleware | Handles errors and converts them to faults. |
| `RetryMiddleware` | `aquilia/http/middleware.py` | HTTPClientMiddleware | Retries failed requests. |
| `CompressionMiddleware` | `aquilia/http/middleware.py` | HTTPClientMiddleware | Handles request/response compression. |
| `CacheMiddleware` | `aquilia/http/middleware.py` | HTTPClientMiddleware | Caches GET responses. |
| `BaseURLMiddleware` | `aquilia/http/middleware.py` | HTTPClientMiddleware | Prepends base URL to relative URLs. |
| `CookieMiddleware` | `aquilia/http/middleware.py` | HTTPClientMiddleware | Manages cookies automatically. |
| `FormField` | `aquilia/http/multipart.py` | object | A form field in multipart data. |
| `FormFile` | `aquilia/http/multipart.py` | object | A file field in multipart data. |
| `MultipartFormData` | `aquilia/http/multipart.py` | object | Builder for multipart/form-data requests. |
| `ConnectionStats` | `aquilia/http/pool.py` | object | Connection pool statistics. |
| `PooledConnection` | `aquilia/http/pool.py` | object | Wrapper for a pooled connection. |
| `ConnectionPool` | `aquilia/http/pool.py` | object | Async connection pool. |
| `ConnectionPoolManager` | `aquilia/http/pool.py` | object | Manager for multiple connection pools. |
| `HTTPMethod` | `aquilia/http/request.py` | str, Enum | HTTP methods. |
| `HTTPClientRequest` | `aquilia/http/request.py` | object | HTTP request representation. |
| `RequestBuilder` | `aquilia/http/request.py` | object | Fluent builder for HTTP requests. |
| `HTTPClientResponse` | `aquilia/http/response.py` | object | HTTP response wrapper. |
| `RetryState` | `aquilia/http/retry.py` | object | State tracking for retry attempts. |
| `RetryStrategy` | `aquilia/http/retry.py` | ABC | Abstract retry strategy. |
| `ExponentialBackoff` | `aquilia/http/retry.py` | RetryStrategy | Exponential backoff retry strategy. |
| `ConstantBackoff` | `aquilia/http/retry.py` | RetryStrategy | Constant delay retry strategy. |
| `NoRetry` | `aquilia/http/retry.py` | RetryStrategy | No retry strategy - never retries. |
| `RetryAfterStrategy` | `aquilia/http/retry.py` | RetryStrategy | Strategy that respects Retry-After header. |
| `CompositeRetryStrategy` | `aquilia/http/retry.py` | RetryStrategy | Composite strategy combining multiple strategies. |
| `RetryExecutor` | `aquilia/http/retry.py` | object | Executes operations with retry logic. |
| `HTTPSession` | `aquilia/http/session.py` | object | Persistent HTTP session. |
| `StreamProgress` | `aquilia/http/streaming.py` | object | Progress information for streaming operations. |
| `StreamingBody` | `aquilia/http/streaming.py` | object | Streaming request body wrapper. |
| `BufferedStream` | `aquilia/http/streaming.py` | object | Buffered async stream reader. |
| `ChunkedEncoder` | `aquilia/http/streaming.py` | object | HTTP chunked transfer encoding encoder. |
| `ChunkedDecoder` | `aquilia/http/streaming.py` | object | HTTP chunked transfer encoding decoder. |

## Public Function Summary

| Function | Source | Signature | Summary |
| --- | --- | --- | --- |
| `create_transport` | `aquilia/http/_transport.py` | `def create_transport(config: HTTPClientConfig \| None=None)` | Create native HTTP transport. |
| `request` | `aquilia/http/client.py` | `async def request(method: str \| HTTPMethod, url: str, **kwargs: Any)` | Make a one-off HTTP request. |
| `get` | `aquilia/http/client.py` | `async def get(url: str, **kwargs: Any)` | Make a GET request. |
| `post` | `aquilia/http/client.py` | `async def post(url: str, **kwargs: Any)` | Make a POST request. |
| `put` | `aquilia/http/client.py` | `async def put(url: str, **kwargs: Any)` | Make a PUT request. |
| `patch` | `aquilia/http/client.py` | `async def patch(url: str, **kwargs: Any)` | Make a PATCH request. |
| `delete` | `aquilia/http/client.py` | `async def delete(url: str, **kwargs: Any)` | Make a DELETE request. |
| `http_client` | `aquilia/http/integration.py` | `def http_client()` | Create HTTP client integration builder. |
| `create_client_from_config` | `aquilia/http/integration.py` | `def create_client_from_config(config: dict[str, Any])` | Create HTTP client from configuration dictionary. |
| `create_middleware_stack` | `aquilia/http/middleware.py` | `def create_middleware_stack(*, base_url: str \| None=None, timeout: float \| None=None, headers: dict[str, str] \| None=None, enable_logging: bool=False, enable_retry: bool=False, enable_cache: bool=False, enable_cookies: bool=False, raise_for_status: bool=False)` | Create a standard middleware stack. |
| `get` | `aquilia/http/request.py` | `def get(url: str, **kwargs: Any)` | Create a GET request builder. |
| `post` | `aquilia/http/request.py` | `def post(url: str, **kwargs: Any)` | Create a POST request builder. |
| `put` | `aquilia/http/request.py` | `def put(url: str, **kwargs: Any)` | Create a PUT request builder. |
| `patch` | `aquilia/http/request.py` | `def patch(url: str, **kwargs: Any)` | Create a PATCH request builder. |
| `delete` | `aquilia/http/request.py` | `def delete(url: str, **kwargs: Any)` | Create a DELETE request builder. |
| `head` | `aquilia/http/request.py` | `def head(url: str, **kwargs: Any)` | Create a HEAD request builder. |
| `options` | `aquilia/http/request.py` | `def options(url: str, **kwargs: Any)` | Create an OPTIONS request builder. |
| `create_response` | `aquilia/http/response.py` | `def create_response(status_code: int, headers: dict[str, str] \| list[tuple[str, str]] \| None=None, *, body: bytes \| None=None, stream: AsyncIterator[bytes] \| None=None, url: str='', http_version: str='1.1', elapsed: float=0.0, request_url: str='', history: list[HTTPClientResponse] \| None=None, extensions: dict[str, Any] \| None=None)` | Factory function to create HTTPClientResponse. |
| `create_retry_strategy` | `aquilia/http/retry.py` | `def create_retry_strategy(config: RetryConfig \| None=None)` | Create a retry strategy from configuration. |
| `stream_file` | `aquilia/http/streaming.py` | `async def stream_file(path: Path \| str, *, chunk_size: int=65536)` | Stream a file asynchronously. |
| `stream_bytes` | `aquilia/http/streaming.py` | `async def stream_bytes(data: bytes, chunk_size: int=65536)` | Stream bytes in chunks. |
| `collect_stream` | `aquilia/http/streaming.py` | `async def collect_stream(stream: AsyncIterator[bytes])` | Collect all bytes from an async iterator. |
| `stream_with_limit` | `aquilia/http/streaming.py` | `async def stream_with_limit(stream: AsyncIterator[bytes], max_bytes: int)` | Stream with a byte limit. |

## Constants And Module Flags

| Name | Source | Value or Type |
| --- | --- | --- |
| `CRLF` | `aquilia/http/_transport.py` | `b'\r\n'` |
| `HTTP_VERSION` | `aquilia/http/_transport.py` | `b'HTTP/1.1'` |
| `DEFAULT_PORT_HTTP` | `aquilia/http/_transport.py` | `80` |
| `DEFAULT_PORT_HTTPS` | `aquilia/http/_transport.py` | `443` |
| `MAX_LINE_LENGTH` | `aquilia/http/_transport.py` | `65536` |
| `MAX_HEADERS` | `aquilia/http/_transport.py` | `100` |
| `CHUNK_SIZE` | `aquilia/http/_transport.py` | `65536` |
| `HTTP_CLIENT_DOMAIN` | `aquilia/http/faults.py` | `FaultDomain.custom('http_client', 'HTTP client faults')` |
| `SINGLE_VALUE_HEADERS` | `aquilia/http/request.py` | `frozenset({'content-type', 'content-length', 'host', 'authorization', 'user-agent', 'accept', 'connection', 'cache-control'})` |
| `HTTP_STATUS_REASONS` | `aquilia/http/response.py` | `{100: 'Continue', 101: 'Switching Protocols', 102: 'Processing', 103: 'Early Hints', 200: 'OK', 201: 'Created', 202: 'Accepted', 203: 'Non-Authoritative Information', 204: 'No Content', 205: 'Reset Content', 206: 'Partial Content', 207: 'Multi-Status', 208: 'Already Reported', 226: 'IM Used', 300: 'Multiple Choices', 301: 'Moved Permanently', 302: 'Found', 303: 'See Other', 304: 'Not Modified', 305: 'Use Proxy', 307: 'Temporary Redirect', 308: 'Permanent Redirect', 400: 'Bad Request', 401: 'Unauthorized', 402: 'Payment Required', 403: 'Forbidden', 404: 'Not Found', 405: 'Method Not Allowed', 406: 'Not Acceptable', 407: 'Proxy Authentication Required', 408: 'Request Timeout', 409: 'Conflict', 410: 'Gone', 411: 'Length Required', 412: 'Precondition Failed', 413: 'Payload Too Large', 414: 'URI Too Long', 415: 'Unsupported Media Type', 416: 'Range Not Satisfiable', 417: 'Expectation Failed', 418: "I'm a teapot", 421: 'Misdirected Request', 422: 'Unprocessable Entity', 423: 'Locked', 424: 'Failed Dependency', 425: 'Too Early', 426: 'Upgrade Required', 428: 'Precondition Required', 429: 'Too Many Requests', 431: 'Request Header Fields Too Large', 451: 'Unavailable For Legal Reasons', 500: 'Internal Server Error', 501: 'Not Implemented', 502: 'Bad Gateway', 503: 'Service Unavailable', 504: 'Gateway Timeout', 505: 'HTTP Version Not Supported', 506: 'Variant Also Negotiates', 507: 'Insufficient Storage', 508: 'Loop Detected', 510: 'Not Extended', 511: 'Network Authentication Required'}` |
| `T` | `aquilia/http/retry.py` | `TypeVar('T')` |

## Detailed Classes And Methods

### `RawResponse`

- Source: `aquilia/http/_transport.py`
- Bases: `object`
- Summary: Raw response before processing.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `http_version` | `str` | `` |
| `status_code` | `int` | `` |
| `reason` | `str` | `` |
| `headers` | `dict[str, str]` | `` |
| `body` | `bytes` | `b''` |
| `stream` | `AsyncIterator[bytes] \| None` | `None` |

### `ConnectionInfo`

- Source: `aquilia/http/_transport.py`
- Bases: `object`
- Summary: Tracks a pooled connection.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `host` | `str` | `` |
| `port` | `int` | `` |
| `ssl` | `bool` | `` |
| `reader` | `asyncio.StreamReader` | `` |
| `writer` | `asyncio.StreamWriter` | `` |
| `created_at` | `float` | `field(default_factory=time.monotonic)` |
| `last_used` | `float` | `field(default_factory=time.monotonic)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `age` | `def age(self)` |  |
| `is_alive` | `def is_alive(self)` |  |
| `close` | `async def close(self)` |  |

### `ConnectionPool`

- Source: `aquilia/http/_transport.py`
- Bases: `object`
- Summary: Keep-alive connection pool. Reuses TCP connections per host.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get_connection` | `async def get_connection(self, host: str, port: int, use_ssl: bool)` | Grab a live connection if one exists. |
| `put_connection` | `async def put_connection(self, conn: ConnectionInfo)` | Return connection to pool if we have room. |
| `close_all` | `async def close_all(self)` |  |
| `cleanup_expired` | `async def cleanup_expired(self)` | Prune dead/expired connections. |

### `HTTPTransport`

- Source: `aquilia/http/_transport.py`
- Bases: `ABC`
- Summary: Base transport interface.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `send` | `async def send(self, request: HTTPClientRequest)` |  |
| `close` | `async def close(self)` |  |

### `NativeTransport`

- Source: `aquilia/http/_transport.py`
- Bases: `HTTPTransport`
- Summary: Pure asyncio HTTP/1.1 transport.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `send` | `async def send(self, request: HTTPClientRequest)` |  |
| `close` | `async def close(self)` |  |

### `MockTransport`

- Source: `aquilia/http/_transport.py`
- Bases: `HTTPTransport`
- Summary: Mock transport for tests. Returns predefined responses.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `add_response` | `def add_response(self, method: str, url: str, response: HTTPClientResponse)` |  |
| `add_json_response` | `def add_json_response(self, method: str, url: str, data: dict[str, Any], status_code: int=200)` |  |
| `requests` | `def requests(self)` |  |
| `clear` | `def clear(self)` |  |
| `send` | `async def send(self, request: HTTPClientRequest)` |  |
| `close` | `async def close(self)` |  |

### `AuthInterceptor`

- Source: `aquilia/http/auth.py`
- Bases: `HTTPInterceptor, ABC`
- Summary: Base class for authentication interceptors.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get_auth_header` | `def get_auth_header(self, request: HTTPClientRequest)` | Generate authentication header. |
| `intercept` | `async def intercept(self, request: HTTPClientRequest, next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]])` | Apply authentication header to request. |

### `BasicAuth`

- Source: `aquilia/http/auth.py`
- Bases: `AuthInterceptor`
- Summary: HTTP Basic Authentication.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get_auth_header` | `def get_auth_header(self, request: HTTPClientRequest)` |  |

### `BearerAuth`

- Source: `aquilia/http/auth.py`
- Bases: `AuthInterceptor`
- Summary: Bearer Token Authentication.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get_auth_header` | `def get_auth_header(self, request: HTTPClientRequest)` |  |

### `APIKeyAuth`

- Source: `aquilia/http/auth.py`
- Bases: `AuthInterceptor`
- Summary: API Key Authentication.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get_auth_header` | `def get_auth_header(self, request: HTTPClientRequest)` |  |
| `intercept` | `async def intercept(self, request: HTTPClientRequest, next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]])` |  |

### `DigestAuth`

- Source: `aquilia/http/auth.py`
- Bases: `AuthInterceptor`
- Summary: HTTP Digest Authentication.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get_auth_header` | `def get_auth_header(self, request: HTTPClientRequest)` |  |
| `intercept` | `async def intercept(self, request: HTTPClientRequest, next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]])` |  |

### `OAuth2Token`

- Source: `aquilia/http/auth.py`
- Bases: `object`
- Summary: OAuth 2.0 token.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `access_token` | `str` | `` |
| `token_type` | `str` | `'Bearer'` |
| `expires_in` | `int \| None` | `None` |
| `refresh_token` | `str \| None` | `None` |
| `scope` | `str \| None` | `None` |
| `created_at` | `float` | `0.0` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_expired` | `def is_expired(self)` |  |

### `OAuth2Auth`

- Source: `aquilia/http/auth.py`
- Bases: `AuthInterceptor`
- Summary: OAuth 2.0 Bearer Token Authentication.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `token` | `def token(self)` |  |
| `set_token` | `def set_token(self, token: OAuth2Token)` |  |
| `get_auth_header` | `def get_auth_header(self, request: HTTPClientRequest)` |  |
| `intercept` | `async def intercept(self, request: HTTPClientRequest, next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]])` |  |

### `AWSSignatureV4Auth`

- Source: `aquilia/http/auth.py`
- Bases: `AuthInterceptor`
- Summary: AWS Signature Version 4 Authentication.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get_auth_header` | `def get_auth_header(self, request: HTTPClientRequest)` |  |
| `intercept` | `async def intercept(self, request: HTTPClientRequest, next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]])` |  |

### `AsyncHTTPClient`

- Source: `aquilia/http/client.py`
- Bases: `object`
- Summary: Async HTTP client.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `config` | `def config(self)` | Get client configuration. |
| `cookies` | `def cookies(self)` | Get cookie jar. |
| `base_url` | `def base_url(self)` | Get base URL. |
| `request` | `def request(self, method: str \| HTTPMethod, url: str, **kwargs: Any)` | Create a request builder. |
| `send` | `async def send(self, request: HTTPClientRequest)` | Send a pre-built request. |
| `get` | `async def get(self, url: str, *, params: dict[str, Any] \| None=None, headers: dict[str, str] \| None=None, timeout: float \| TimeoutConfig \| None=None, **kwargs: Any)` | Send a GET request. |
| `post` | `async def post(self, url: str, *, params: dict[str, Any] \| None=None, headers: dict[str, str] \| None=None, json: Any=None, data: dict[str, Any] \| str \| bytes \| None=None, files: MultipartFormData \| None=None, timeout: float \| TimeoutConfig \| None=None, **kwargs: Any)` | Send a POST request. |
| `put` | `async def put(self, url: str, *, params: dict[str, Any] \| None=None, headers: dict[str, str] \| None=None, json: Any=None, data: dict[str, Any] \| str \| bytes \| None=None, timeout: float \| TimeoutConfig \| None=None, **kwargs: Any)` | Send a PUT request. |
| `patch` | `async def patch(self, url: str, *, params: dict[str, Any] \| None=None, headers: dict[str, str] \| None=None, json: Any=None, data: dict[str, Any] \| str \| bytes \| None=None, timeout: float \| TimeoutConfig \| None=None, **kwargs: Any)` | Send a PATCH request. |
| `delete` | `async def delete(self, url: str, *, params: dict[str, Any] \| None=None, headers: dict[str, str] \| None=None, timeout: float \| TimeoutConfig \| None=None, **kwargs: Any)` | Send a DELETE request. |
| `head` | `async def head(self, url: str, *, params: dict[str, Any] \| None=None, headers: dict[str, str] \| None=None, timeout: float \| TimeoutConfig \| None=None, **kwargs: Any)` | Send a HEAD request. |
| `options` | `async def options(self, url: str, *, params: dict[str, Any] \| None=None, headers: dict[str, str] \| None=None, timeout: float \| TimeoutConfig \| None=None, **kwargs: Any)` | Send an OPTIONS request. |
| `stream` | `async def stream(self, method: str \| HTTPMethod, url: str, *, params: dict[str, Any] \| None=None, headers: dict[str, str] \| None=None, json: Any=None, data: dict[str, Any] \| str \| bytes \| None=None, chunk_size: int=65536, **kwargs: Any)` | Stream a response body. |
| `close` | `async def close(self)` | Close the client and release resources. |

### `HTTPVersion`

- Source: `aquilia/http/config.py`
- Bases: `str, Enum`
- Summary: Supported HTTP versions.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `HTTP_1_0` | `` | `'1.0'` |
| `HTTP_1_1` | `` | `'1.1'` |
| `HTTP_2` | `` | `'2'` |
| `AUTO` | `` | `'auto'` |

### `CompressionAlgorithm`

- Source: `aquilia/http/config.py`
- Bases: `str, Enum`
- Summary: Supported compression algorithms for Accept-Encoding.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `GZIP` | `` | `'gzip'` |
| `DEFLATE` | `` | `'deflate'` |
| `BR` | `` | `'br'` |
| `ZSTD` | `` | `'zstd'` |
| `IDENTITY` | `` | `'identity'` |

### `TimeoutConfig`

- Source: `aquilia/http/config.py`
- Bases: `object`
- Summary: HTTP request timeout configuration.
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `total` | `float \| None` | `30.0` |
| `connect` | `float \| None` | `10.0` |
| `read` | `float \| None` | `None` |
| `write` | `float \| None` | `None` |
| `pool` | `float \| None` | `5.0` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `no_timeout` | `def no_timeout(cls)` | Create a configuration with no timeouts (infinite wait). |
| `fast` | `def fast(cls)` | Create a fast timeout configuration for quick requests. |
| `slow` | `def slow(cls)` | Create a slow timeout configuration for long-running requests. |

### `PoolConfig`

- Source: `aquilia/http/config.py`
- Bases: `object`
- Summary: Connection pool configuration.
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `max_connections` | `int` | `100` |
| `max_connections_per_host` | `int` | `10` |
| `max_keepalive_connections` | `int` | `20` |
| `keepalive_expiry` | `float` | `60.0` |
| `enable_http2` | `bool` | `False` |

### `RetryConfig`

- Source: `aquilia/http/config.py`
- Bases: `object`
- Summary: Retry configuration.
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `max_attempts` | `int` | `3` |
| `backoff_base` | `float` | `1.0` |
| `backoff_multiplier` | `float` | `2.0` |
| `backoff_max` | `float` | `60.0` |
| `backoff_jitter` | `float` | `0.1` |
| `retry_on_status` | `frozenset[int]` | `field(default_factory=lambda: frozenset({429, 500, 502, 503, 504}))` |
| `retry_on_methods` | `frozenset[str]` | `field(default_factory=lambda: frozenset({'GET', 'HEAD', 'OPTIONS', 'PUT', 'DELETE'}))` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `no_retry` | `def no_retry(cls)` | Create a configuration with no retries. |
| `aggressive` | `def aggressive(cls)` | Create an aggressive retry configuration. |

### `ProxyConfig`

- Source: `aquilia/http/config.py`
- Bases: `object`
- Summary: Proxy configuration.
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `http_proxy` | `str \| None` | `None` |
| `https_proxy` | `str \| None` | `None` |
| `no_proxy` | `str \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `from_env` | `def from_env(cls)` | Create proxy config from environment variables. |

### `TLSConfig`

- Source: `aquilia/http/config.py`
- Bases: `object`
- Summary: TLS/SSL configuration.
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `verify` | `bool` | `True` |
| `cert_file` | `str \| None` | `None` |
| `key_file` | `str \| None` | `None` |
| `ca_bundle` | `str \| None` | `None` |
| `ssl_context` | `SSLContext \| None` | `None` |
| `minimum_version` | `str \| None` | `None` |

### `HTTPClientConfig`

- Source: `aquilia/http/config.py`
- Bases: `object`
- Summary: Complete HTTP client configuration.
- Decorators: `dataclass(slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `base_url` | `str \| None` | `None` |
| `timeout` | `TimeoutConfig` | `field(default_factory=TimeoutConfig)` |
| `pool` | `PoolConfig` | `field(default_factory=PoolConfig)` |
| `retry` | `RetryConfig` | `field(default_factory=RetryConfig)` |
| `proxy` | `ProxyConfig \| None` | `None` |
| `tls` | `TLSConfig` | `field(default_factory=TLSConfig)` |
| `http_version` | `HTTPVersion` | `HTTPVersion.AUTO` |
| `follow_redirects` | `bool` | `True` |
| `max_redirects` | `int` | `10` |
| `default_headers` | `dict[str, str]` | `field(default_factory=dict)` |
| `default_params` | `dict[str, str]` | `field(default_factory=dict)` |
| `compression` | `tuple[CompressionAlgorithm, ...]` | `(CompressionAlgorithm.GZIP, CompressionAlgorithm.DEFLATE)` |
| `trust_env` | `bool` | `True` |
| `raise_for_status` | `bool` | `False` |
| `user_agent` | `str` | `'Aquilia-HTTP/1.0'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `with_base_url` | `def with_base_url(self, url: str)` | Return a copy with a different base URL. |
| `with_timeout` | `def with_timeout(self, **kwargs: Any)` | Return a copy with modified timeout settings. |
| `merge_headers` | `def merge_headers(self, headers: dict[str, str] \| None)` | Merge default headers with request-specific headers. |
| `merge_params` | `def merge_params(self, params: dict[str, str] \| None)` | Merge default params with request-specific params. |
| `to_dict` | `def to_dict(self)` | Convert to dictionary for serialization. |
| `from_dict` | `def from_dict(cls, data: dict[str, Any])` | Create from dictionary. |

### `Cookie`

- Source: `aquilia/http/cookies.py`
- Bases: `object`
- Summary: HTTP Cookie representation.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `value` | `str` | `` |
| `domain` | `str` | `''` |
| `path` | `str` | `'/'` |
| `expires` | `float \| None` | `None` |
| `max_age` | `int \| None` | `None` |
| `secure` | `bool` | `False` |
| `http_only` | `bool` | `False` |
| `same_site` | `str` | `''` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_expired` | `def is_expired(self)` | Check if cookie has expired. |
| `is_session` | `def is_session(self)` | Check if this is a session cookie (no expiry). |
| `matches_domain` | `def matches_domain(self, request_domain: str)` | Check if cookie matches the request domain. |
| `matches_path` | `def matches_path(self, request_path: str)` | Check if cookie matches the request path. |
| `matches` | `def matches(self, url: str)` | Check if cookie matches the URL. |
| `to_header_value` | `def to_header_value(self)` | Format as cookie header value (name=value). |
| `to_set_cookie` | `def to_set_cookie(self)` | Format as Set-Cookie header value. |
| `from_set_cookie` | `def from_set_cookie(cls, header: str, request_url: str='')` | Parse a Set-Cookie header. |

### `CookieJar`

- Source: `aquilia/http/cookies.py`
- Bases: `object`
- Summary: Thread-safe cookie storage.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `set` | `def set(self, cookie: Cookie)` | Add or update a cookie. |
| `set_from_response` | `def set_from_response(self, headers: dict[str, str] \| list[tuple[str, str]], request_url: str)` | Extract and store cookies from response headers. |
| `get` | `def get(self, name: str, domain: str='', path: str='/')` | Get a specific cookie. |
| `get_for_url` | `def get_for_url(self, url: str)` | Get all cookies that match a URL. |
| `get_header` | `def get_header(self, url: str)` | Get Cookie header value for a URL. |
| `delete` | `def delete(self, name: str, domain: str='', path: str='/')` | Delete a cookie. |
| `clear` | `def clear(self, domain: str='')` | Clear cookies. |
| `cleanup_expired` | `def cleanup_expired(self)` | Remove expired cookies. |
| `all` | `def all(self)` | Get all non-expired cookies. |
| `to_dict` | `def to_dict(self)` | Export cookies as simple dict. |

### `CookieInterceptor`

- Source: `aquilia/http/cookies.py`
- Bases: `object`
- Summary: Interceptor that manages cookies automatically.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `jar` | `def jar(self)` |  |
| `intercept` | `async def intercept(self, request: Any, next_handler: Any)` |  |

### `HTTPClientFault`

- Source: `aquilia/http/faults.py`
- Bases: `Fault`
- Summary: Base fault for the HTTP client subsystem.

### `ConnectionFault`

- Source: `aquilia/http/faults.py`
- Bases: `HTTPClientFault`
- Summary: Failed to establish connection to remote host.

### `ConnectionPoolExhaustedFault`

- Source: `aquilia/http/faults.py`
- Bases: `HTTPClientFault`
- Summary: Connection pool exhausted.

### `ConnectionClosedFault`

- Source: `aquilia/http/faults.py`
- Bases: `HTTPClientFault`
- Summary: Connection was unexpectedly closed.

### `TimeoutFault`

- Source: `aquilia/http/faults.py`
- Bases: `HTTPClientFault`
- Summary: Request timed out.

### `ConnectTimeoutFault`

- Source: `aquilia/http/faults.py`
- Bases: `TimeoutFault`
- Summary: Connection timeout.

### `ReadTimeoutFault`

- Source: `aquilia/http/faults.py`
- Bases: `TimeoutFault`
- Summary: Read timeout.

### `WriteTimeoutFault`

- Source: `aquilia/http/faults.py`
- Bases: `TimeoutFault`
- Summary: Write timeout.

### `RequestTimeoutFault`

- Source: `aquilia/http/faults.py`
- Bases: `TimeoutFault`
- Summary: Total request timeout.

### `TLSFault`

- Source: `aquilia/http/faults.py`
- Bases: `HTTPClientFault`
- Summary: TLS/SSL error.

### `CertificateVerifyFault`

- Source: `aquilia/http/faults.py`
- Bases: `TLSFault`
- Summary: Certificate verification failed.

### `ResponseFault`

- Source: `aquilia/http/faults.py`
- Bases: `HTTPClientFault`
- Summary: Response processing error.

### `InvalidResponseFault`

- Source: `aquilia/http/faults.py`
- Bases: `ResponseFault`
- Summary: Invalid response received.

### `DecodingFault`

- Source: `aquilia/http/faults.py`
- Bases: `ResponseFault`
- Summary: Response body decoding error.

### `HTTPStatusFault`

- Source: `aquilia/http/faults.py`
- Bases: `ResponseFault`
- Summary: HTTP error status received.

### `ClientErrorFault`

- Source: `aquilia/http/faults.py`
- Bases: `HTTPStatusFault`
- Summary: HTTP 4xx client error.

### `ServerErrorFault`

- Source: `aquilia/http/faults.py`
- Bases: `HTTPStatusFault`
- Summary: HTTP 5xx server error.

### `TooManyRedirectsFault`

- Source: `aquilia/http/faults.py`
- Bases: `HTTPClientFault`
- Summary: Too many redirects.

### `RequestBuildFault`

- Source: `aquilia/http/faults.py`
- Bases: `HTTPClientFault`
- Summary: Request construction error.

### `InvalidURLFault`

- Source: `aquilia/http/faults.py`
- Bases: `RequestBuildFault`
- Summary: Invalid URL.

### `InvalidHeaderFault`

- Source: `aquilia/http/faults.py`
- Bases: `RequestBuildFault`
- Summary: Invalid header.

### `TransportFault`

- Source: `aquilia/http/faults.py`
- Bases: `HTTPClientFault`
- Summary: Low-level transport error.

### `ProxyFault`

- Source: `aquilia/http/faults.py`
- Bases: `TransportFault`
- Summary: Proxy connection error.

### `RetryExhaustedFault`

- Source: `aquilia/http/faults.py`
- Bases: `HTTPClientFault`
- Summary: All retry attempts exhausted.

### `ConfigurationFault`

- Source: `aquilia/http/faults.py`
- Bases: `HTTPClientFault`
- Summary: HTTP client configuration error.

### `HTTPClientProvider`

- Source: `aquilia/http/integration.py`
- Bases: `object`
- Summary: DI provider for AsyncHTTPClient.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `provides` | `def provides(self)` | Type this provider provides. |
| `scope` | `def scope(self)` | DI scope. |
| `shutdown` | `async def shutdown(self)` | Shutdown the provider. |

### `HTTPClientBuilder`

- Source: `aquilia/http/integration.py`
- Bases: `object`
- Summary: Fluent builder for HTTP client configuration.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `base_url` | `def base_url(self, url: str)` | Set base URL. |
| `timeout` | `def timeout(self, total: float \| None=30.0, connect: float \| None=10.0, read: float \| None=None, write: float \| None=None)` | Set timeout configuration. |
| `pool` | `def pool(self, max_connections: int=100, max_connections_per_host: int=10, keepalive_expiry: float=60.0)` | Set connection pool configuration. |
| `retry` | `def retry(self, max_attempts: int=3, backoff_base: float=1.0, backoff_multiplier: float=2.0, backoff_max: float=60.0)` | Set retry configuration. |
| `proxy` | `def proxy(self, http_proxy: str \| None=None, https_proxy: str \| None=None, no_proxy: str \| None=None)` | Set proxy configuration. |
| `tls` | `def tls(self, verify: bool=True, cert_file: str \| None=None, key_file: str \| None=None, ca_bundle: str \| None=None)` | Set TLS configuration. |
| `header` | `def header(self, name: str, value: str)` | Add a default header. |
| `headers` | `def headers(self, headers: dict[str, str])` | Set default headers. |
| `follow_redirects` | `def follow_redirects(self, follow: bool=True)` | Set redirect following behavior. |
| `max_redirects` | `def max_redirects(self, max_redirects: int)` | Set maximum redirects. |
| `raise_for_status` | `def raise_for_status(self, raise_errors: bool=True)` | Set raise_for_status behavior. |
| `user_agent` | `def user_agent(self, user_agent: str)` | Set User-Agent header. |
| `build` | `def build(self)` | Build the configuration. |
| `build_provider` | `def build_provider(self, scope: str='singleton')` | Build a DI provider. |
| `to_dict` | `def to_dict(self)` | Convert to dictionary for serialization. |

### `HTTPInterceptor`

- Source: `aquilia/http/interceptors.py`
- Bases: `ABC`
- Summary: Base class for HTTP interceptors.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `intercept` | `async def intercept(self, request: HTTPClientRequest, next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]])` | Intercept and optionally modify request/response. |

### `InterceptorChain`

- Source: `aquilia/http/interceptors.py`
- Bases: `object`
- Summary: Chain of interceptors.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `add` | `def add(self, interceptor: HTTPInterceptor)` | Add an interceptor to the chain. |
| `set_handler` | `def set_handler(self, handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]])` | Set the final handler. |
| `execute` | `async def execute(self, request: HTTPClientRequest)` | Execute the interceptor chain. |

### `LoggingInterceptor`

- Source: `aquilia/http/interceptors.py`
- Bases: `HTTPInterceptor`
- Summary: Logs request and response details.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `intercept` | `async def intercept(self, request: HTTPClientRequest, next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]])` |  |

### `HeaderInterceptor`

- Source: `aquilia/http/interceptors.py`
- Bases: `HTTPInterceptor`
- Summary: Adds default headers to all requests.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `intercept` | `async def intercept(self, request: HTTPClientRequest, next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]])` |  |

### `UserAgentInterceptor`

- Source: `aquilia/http/interceptors.py`
- Bases: `HTTPInterceptor`
- Summary: Sets User-Agent header.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `intercept` | `async def intercept(self, request: HTTPClientRequest, next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]])` |  |

### `AcceptInterceptor`

- Source: `aquilia/http/interceptors.py`
- Bases: `HTTPInterceptor`
- Summary: Sets Accept header for content negotiation.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `intercept` | `async def intercept(self, request: HTTPClientRequest, next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]])` |  |

### `RequestMetrics`

- Source: `aquilia/http/interceptors.py`
- Bases: `object`
- Summary: Metrics collected for a request.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `method` | `str` | `` |
| `url` | `str` | `` |
| `status_code` | `int` | `` |
| `elapsed` | `float` | `` |
| `request_size` | `int` | `` |
| `response_size` | `int \| None` | `` |
| `error` | `str \| None` | `None` |

### `MetricsInterceptor`

- Source: `aquilia/http/interceptors.py`
- Bases: `HTTPInterceptor`
- Summary: Collects request metrics.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `intercept` | `async def intercept(self, request: HTTPClientRequest, next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]])` |  |

### `TimeoutInterceptor`

- Source: `aquilia/http/interceptors.py`
- Bases: `HTTPInterceptor`
- Summary: Enforces timeout on requests.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `intercept` | `async def intercept(self, request: HTTPClientRequest, next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]])` |  |

### `RedirectInterceptor`

- Source: `aquilia/http/interceptors.py`
- Bases: `HTTPInterceptor`
- Summary: Handles HTTP redirects.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `intercept` | `async def intercept(self, request: HTTPClientRequest, next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]])` |  |

### `CacheInterceptor`

- Source: `aquilia/http/interceptors.py`
- Bases: `HTTPInterceptor`
- Summary: HTTP response caching interceptor.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `intercept` | `async def intercept(self, request: HTTPClientRequest, next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]])` |  |

### `HTTPClientMiddleware`

- Source: `aquilia/http/middleware.py`
- Bases: `ABC`
- Summary: Base class for HTTP client middleware.

### `MiddlewareStack`

- Source: `aquilia/http/middleware.py`
- Bases: `object`
- Summary: Stack of middleware that processes requests.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `add` | `def add(self, middleware: HTTPClientMiddleware)` | Add middleware to the stack. |
| `add_many` | `def add_many(self, middleware: list[HTTPClientMiddleware])` | Add multiple middleware to the stack. |
| `set_handler` | `def set_handler(self, handler: MiddlewareHandler)` | Set the final request handler. |
| `build` | `def build(self)` | Build the middleware chain. |
| `execute` | `async def execute(self, request: HTTPClientRequest)` | Execute the middleware chain. |

### `LoggingMiddleware`

- Source: `aquilia/http/middleware.py`
- Bases: `HTTPClientMiddleware`
- Summary: Logs requests and responses.

### `HeadersMiddleware`

- Source: `aquilia/http/middleware.py`
- Bases: `HTTPClientMiddleware`
- Summary: Adds default headers to all requests.

### `TimeoutMiddleware`

- Source: `aquilia/http/middleware.py`
- Bases: `HTTPClientMiddleware`
- Summary: Enforces timeout on requests.

### `ErrorHandlingMiddleware`

- Source: `aquilia/http/middleware.py`
- Bases: `HTTPClientMiddleware`
- Summary: Handles errors and converts them to faults.

### `RetryMiddleware`

- Source: `aquilia/http/middleware.py`
- Bases: `HTTPClientMiddleware`
- Summary: Retries failed requests.

### `CompressionMiddleware`

- Source: `aquilia/http/middleware.py`
- Bases: `HTTPClientMiddleware`
- Summary: Handles request/response compression.

### `CacheMiddleware`

- Source: `aquilia/http/middleware.py`
- Bases: `HTTPClientMiddleware`
- Summary: Caches GET responses.

### `BaseURLMiddleware`

- Source: `aquilia/http/middleware.py`
- Bases: `HTTPClientMiddleware`
- Summary: Prepends base URL to relative URLs.

### `CookieMiddleware`

- Source: `aquilia/http/middleware.py`
- Bases: `HTTPClientMiddleware`
- Summary: Manages cookies automatically.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `jar` | `def jar(self)` |  |

### `FormField`

- Source: `aquilia/http/multipart.py`
- Bases: `object`
- Summary: A form field in multipart data.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `value` | `str \| bytes` | `` |
| `content_type` | `str \| None` | `None` |
| `filename` | `str \| None` | `None` |

### `FormFile`

- Source: `aquilia/http/multipart.py`
- Bases: `object`
- Summary: A file field in multipart data.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `filename` | `str` | `` |
| `content` | `bytes \| BinaryIO \| AsyncIterator[bytes] \| Path` | `` |
| `content_type` | `str \| None` | `None` |
| `content_length` | `int \| None` | `None` |

### `MultipartFormData`

- Source: `aquilia/http/multipart.py`
- Bases: `object`
- Summary: Builder for multipart/form-data requests.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `boundary` | `def boundary(self)` | Get the multipart boundary. |
| `content_type` | `def content_type(self)` | Get the Content-Type header value. |
| `field` | `def field(self, name: str, value: str \| bytes, content_type: str \| None=None)` | Add a form field. |
| `file` | `def file(self, name: str, filename: str, content: bytes \| BinaryIO \| AsyncIterator[bytes], content_type: str \| None=None)` | Add a file field. |
| `file_from_path` | `def file_from_path(self, name: str, path: Path \| str, content_type: str \| None=None, filename: str \| None=None)` | Add a file field from a path. |
| `file_from_bytes` | `def file_from_bytes(self, name: str, filename: str, data: bytes, content_type: str \| None=None)` | Add a file field from bytes. |
| `encode` | `async def encode(self)` | Encode all fields and files to multipart body. |
| `encode_sync` | `def encode_sync(self)` | Synchronously encode fields and files. |
| `stream` | `async def stream(self, chunk_size: int=65536)` | Stream the multipart body in chunks. |
| `content_length` | `def content_length(self)` | Calculate total content length if possible. |

### `ConnectionStats`

- Source: `aquilia/http/pool.py`
- Bases: `object`
- Summary: Connection pool statistics.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `total_created` | `int` | `0` |
| `total_closed` | `int` | `0` |
| `total_reused` | `int` | `0` |
| `active_connections` | `int` | `0` |
| `idle_connections` | `int` | `0` |
| `failed_acquisitions` | `int` | `0` |
| `pool_exhausted_count` | `int` | `0` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `PooledConnection`

- Source: `aquilia/http/pool.py`
- Bases: `object`
- Summary: Wrapper for a pooled connection.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `host` | `str` | `` |
| `port` | `int` | `` |
| `scheme` | `str` | `` |
| `connection` | `Any` | `` |
| `created_at` | `float` | `field(default_factory=time.monotonic)` |
| `last_used_at` | `float` | `field(default_factory=time.monotonic)` |
| `requests_count` | `int` | `0` |
| `is_available` | `bool` | `True` |
| `is_http2` | `bool` | `False` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `age` | `def age(self)` | Seconds since connection was created. |
| `idle_time` | `def idle_time(self)` | Seconds since connection was last used. |
| `key` | `def key(self)` | Connection pool key. |
| `mark_used` | `def mark_used(self)` | Mark connection as in use. |
| `mark_available` | `def mark_available(self)` | Mark connection as available for reuse. |
| `is_expired` | `def is_expired(self, max_age: float)` | Check if connection has exceeded keepalive timeout. |

### `ConnectionPool`

- Source: `aquilia/http/pool.py`
- Bases: `object`
- Summary: Async connection pool.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `stats` | `def stats(self)` | Get pool statistics. |
| `config` | `def config(self)` | Get pool configuration. |
| `acquire` | `async def acquire(self, url: str, *, timeout: float \| None=None)` | Acquire a connection from the pool. |
| `add` | `async def add(self, url: str, connection: Any, *, is_http2: bool=False)` | Add a new connection to the pool. |
| `release` | `async def release(self, conn: PooledConnection, *, reusable: bool=True)` | Release a connection back to the pool. |
| `remove` | `async def remove(self, conn: PooledConnection)` | Remove and close a connection. |
| `cleanup` | `async def cleanup(self)` | Clean up expired connections. |
| `start_cleanup_task` | `def start_cleanup_task(self)` | Start background cleanup task. |
| `close` | `async def close(self)` | Close all connections and shutdown pool. |

### `ConnectionPoolManager`

- Source: `aquilia/http/pool.py`
- Bases: `object`
- Summary: Manager for multiple connection pools.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get_pool` | `async def get_pool(self, name: str='default', config: PoolConfig \| None=None)` | Get or create a named pool. |
| `close_all` | `async def close_all(self)` | Close all managed pools. |

### `HTTPMethod`

- Source: `aquilia/http/request.py`
- Bases: `str, Enum`
- Summary: HTTP methods.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `GET` | `` | `'GET'` |
| `POST` | `` | `'POST'` |
| `PUT` | `` | `'PUT'` |
| `PATCH` | `` | `'PATCH'` |
| `DELETE` | `` | `'DELETE'` |
| `HEAD` | `` | `'HEAD'` |
| `OPTIONS` | `` | `'OPTIONS'` |
| `TRACE` | `` | `'TRACE'` |
| `CONNECT` | `` | `'CONNECT'` |

### `HTTPClientRequest`

- Source: `aquilia/http/request.py`
- Bases: `object`
- Summary: HTTP request representation.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `method` | `HTTPMethod` | `` |
| `url` | `str` | `` |
| `headers` | `dict[str, str]` | `field(default_factory=dict)` |
| `body` | `bytes \| AsyncIterator[bytes] \| None` | `None` |
| `timeout` | `TimeoutConfig \| None` | `None` |
| `follow_redirects` | `bool \| None` | `None` |
| `auth` | `tuple[str, str] \| None` | `None` |
| `extensions` | `dict[str, Any]` | `field(default_factory=dict)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `host` | `def host(self)` | Extract host from URL. |
| `path` | `def path(self)` | Extract path from URL. |
| `scheme` | `def scheme(self)` | Extract scheme from URL. |
| `query_string` | `def query_string(self)` | Extract query string from URL. |
| `content_type` | `def content_type(self)` | Get Content-Type header. |
| `content_length` | `def content_length(self)` | Get Content-Length header as int. |
| `has_body` | `def has_body(self)` | Check if request has a body. |
| `is_streaming` | `def is_streaming(self)` | Check if body is a stream. |
| `copy` | `def copy(self, **changes: Any)` | Create a copy with optional changes. |
| `to_dict` | `def to_dict(self)` | Serialize to dictionary (for logging/debugging). |

### `RequestBuilder`

- Source: `aquilia/http/request.py`
- Bases: `object`
- Summary: Fluent builder for HTTP requests.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `header` | `def header(self, name: str, value: str)` | Add a header. |
| `headers` | `def headers(self, headers: HeadersType)` | Add multiple headers. |
| `param` | `def param(self, name: str, value: str \| int \| float \| bool \| None)` | Add a query parameter. |
| `params` | `def params(self, params: ParamsType)` | Add multiple query parameters. |
| `body` | `def body(self, content: bytes \| AsyncIterator[bytes])` | Set raw body content. |
| `json` | `def json(self, data: JsonType)` | Set JSON body (automatically sets Content-Type). |
| `form` | `def form(self, data: Mapping[str, Any] \| str)` | Set form-urlencoded body (automatically sets Content-Type). |
| `multipart` | `def multipart(self, fields: dict[str, str \| tuple[str, bytes \| BinaryIO, str \| None]] \| None=None, files: list[tuple[str, tuple[str, bytes \| BinaryIO, str \| None]]] \| None=None)` | Set multipart form data with optional files. |
| `cookie` | `def cookie(self, name: str, value: str)` | Add a cookie. |
| `cookies` | `def cookies(self, cookies: CookiesType)` | Add multiple cookies. |
| `auth_basic` | `def auth_basic(self, username: str, password: str)` | Set Basic authentication. |
| `auth_bearer` | `def auth_bearer(self, token: str)` | Set Bearer token authentication. |
| `timeout` | `def timeout(self, total: float \| None=None, connect: float \| None=None, read: float \| None=None, write: float \| None=None, pool: float \| None=None)` | Set request-specific timeouts. |
| `follow_redirects` | `def follow_redirects(self, follow: bool=True)` | Set redirect following behavior. |
| `extension` | `def extension(self, key: str, value: Any)` | Add an extension for interceptors. |
| `build` | `def build(self)` | Build the final HTTPClientRequest. |

### `HTTPClientResponse`

- Source: `aquilia/http/response.py`
- Bases: `object`
- Summary: HTTP response wrapper.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `status_code` | `int` | `` |
| `headers` | `dict[str, str]` | `` |
| `url` | `str` | `` |
| `http_version` | `str` | `'1.1'` |
| `elapsed` | `float` | `0.0` |
| `request_url` | `str` | `''` |
| `history` | `list[HTTPClientResponse]` | `field(default_factory=list)` |
| `extensions` | `dict[str, Any]` | `field(default_factory=dict)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `reason` | `def reason(self)` | HTTP status reason phrase. |
| `is_informational` | `def is_informational(self)` | Check if status is 1xx. |
| `is_success` | `def is_success(self)` | Check if status is 2xx. |
| `is_redirect` | `def is_redirect(self)` | Check if status is 3xx redirect. |
| `is_client_error` | `def is_client_error(self)` | Check if status is 4xx. |
| `is_server_error` | `def is_server_error(self)` | Check if status is 5xx. |
| `is_error` | `def is_error(self)` | Check if status is 4xx or 5xx. |
| `ok` | `def ok(self)` | Check if status indicates success (2xx). |
| `content_type` | `def content_type(self)` | Get Content-Type header. |
| `content_length` | `def content_length(self)` | Get Content-Length header as int. |
| `encoding` | `def encoding(self)` | Detect encoding from Content-Type header. |
| `etag` | `def etag(self)` | Get ETag header. |
| `last_modified` | `def last_modified(self)` | Parse Last-Modified header. |
| `location` | `def location(self)` | Get Location header (for redirects). |
| `cookies` | `def cookies(self)` | Parse Set-Cookie headers into dict. |
| `get_header` | `def get_header(self, name: str, default: str \| None=None)` | Get header by name (case-insensitive). |
| `get_headers` | `def get_headers(self, name: str)` | Get all values for a header (for multi-value headers). |
| `read` | `async def read(self)` | Read entire response body as bytes. |
| `text` | `async def text(self, encoding: str \| None=None)` | Read response body as text. |
| `json` | `async def json(self)` | Parse response body as JSON. |
| `iter_bytes` | `async def iter_bytes(self, chunk_size: int=65536)` | Stream response body in chunks. |
| `iter_text` | `async def iter_text(self, chunk_size: int=65536, encoding: str \| None=None)` | Stream response body as text chunks. |
| `iter_lines` | `async def iter_lines(self, encoding: str \| None=None, delimiter: str='\n')` | Stream response body line by line. |
| `raise_for_status` | `def raise_for_status(self)` | Raise HTTPStatusFault if status is 4xx or 5xx. |
| `close` | `async def close(self)` | Close the response and release resources. |
| `to_dict` | `def to_dict(self)` | Serialize to dictionary (for logging/debugging). |

### `RetryState`

- Source: `aquilia/http/retry.py`
- Bases: `object`
- Summary: State tracking for retry attempts.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `attempt` | `int` | `0` |
| `last_error` | `Exception \| None` | `None` |
| `last_response` | `HTTPClientResponse \| None` | `None` |
| `total_delay` | `float` | `0.0` |
| `start_time` | `float` | `0.0` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `elapsed` | `def elapsed(self)` | Total elapsed time since first attempt. |

### `RetryStrategy`

- Source: `aquilia/http/retry.py`
- Bases: `ABC`
- Summary: Abstract retry strategy.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `should_retry` | `def should_retry(self, state: RetryState, request: HTTPClientRequest, response: HTTPClientResponse \| None, error: Exception \| None)` | Determine if request should be retried. |
| `get_delay` | `def get_delay(self, state: RetryState)` | Calculate delay before next retry. |

### `ExponentialBackoff`

- Source: `aquilia/http/retry.py`
- Bases: `RetryStrategy`
- Summary: Exponential backoff retry strategy.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `config` | `def config(self)` |  |
| `should_retry` | `def should_retry(self, state: RetryState, request: HTTPClientRequest, response: HTTPClientResponse \| None, error: Exception \| None)` | Check if retry should be attempted. |
| `get_delay` | `def get_delay(self, state: RetryState)` | Calculate exponential backoff delay. |

### `ConstantBackoff`

- Source: `aquilia/http/retry.py`
- Bases: `RetryStrategy`
- Summary: Constant delay retry strategy.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `should_retry` | `def should_retry(self, state: RetryState, request: HTTPClientRequest, response: HTTPClientResponse \| None, error: Exception \| None)` |  |
| `get_delay` | `def get_delay(self, state: RetryState)` |  |

### `NoRetry`

- Source: `aquilia/http/retry.py`
- Bases: `RetryStrategy`
- Summary: No retry strategy - never retries.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `should_retry` | `def should_retry(self, state: RetryState, request: HTTPClientRequest, response: HTTPClientResponse \| None, error: Exception \| None)` |  |
| `get_delay` | `def get_delay(self, state: RetryState)` |  |

### `RetryAfterStrategy`

- Source: `aquilia/http/retry.py`
- Bases: `RetryStrategy`
- Summary: Strategy that respects Retry-After header.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `should_retry` | `def should_retry(self, state: RetryState, request: HTTPClientRequest, response: HTTPClientResponse \| None, error: Exception \| None)` |  |
| `get_delay` | `def get_delay(self, state: RetryState)` |  |

### `CompositeRetryStrategy`

- Source: `aquilia/http/retry.py`
- Bases: `RetryStrategy`
- Summary: Composite strategy combining multiple strategies.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `should_retry` | `def should_retry(self, state: RetryState, request: HTTPClientRequest, response: HTTPClientResponse \| None, error: Exception \| None)` |  |
| `get_delay` | `def get_delay(self, state: RetryState)` |  |

### `RetryExecutor`

- Source: `aquilia/http/retry.py`
- Bases: `object`
- Summary: Executes operations with retry logic.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `execute` | `async def execute(self, operation: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]], request: HTTPClientRequest)` | Execute operation with retries. |

### `HTTPSession`

- Source: `aquilia/http/session.py`
- Bases: `object`
- Summary: Persistent HTTP session.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `config` | `def config(self)` | Get session configuration. |
| `cookies` | `def cookies(self)` | Get session cookie jar. |
| `base_url` | `def base_url(self)` | Get base URL. |
| `send` | `async def send(self, request: HTTPClientRequest)` | Send an HTTP request. |
| `request` | `def request(self, method: str \| HTTPMethod, url: str, **kwargs: Any)` | Create a request builder. |
| `get` | `async def get(self, url: str, *, params: dict[str, Any] \| None=None, headers: dict[str, str] \| None=None, timeout: float \| TimeoutConfig \| None=None, **kwargs: Any)` | Send a GET request. |
| `post` | `async def post(self, url: str, *, params: dict[str, Any] \| None=None, headers: dict[str, str] \| None=None, json: Any=None, data: dict[str, Any] \| str \| bytes \| None=None, timeout: float \| TimeoutConfig \| None=None, **kwargs: Any)` | Send a POST request. |
| `put` | `async def put(self, url: str, *, params: dict[str, Any] \| None=None, headers: dict[str, str] \| None=None, json: Any=None, data: dict[str, Any] \| str \| bytes \| None=None, timeout: float \| TimeoutConfig \| None=None, **kwargs: Any)` | Send a PUT request. |
| `patch` | `async def patch(self, url: str, *, params: dict[str, Any] \| None=None, headers: dict[str, str] \| None=None, json: Any=None, data: dict[str, Any] \| str \| bytes \| None=None, timeout: float \| TimeoutConfig \| None=None, **kwargs: Any)` | Send a PATCH request. |
| `delete` | `async def delete(self, url: str, *, params: dict[str, Any] \| None=None, headers: dict[str, str] \| None=None, timeout: float \| TimeoutConfig \| None=None, **kwargs: Any)` | Send a DELETE request. |
| `head` | `async def head(self, url: str, *, params: dict[str, Any] \| None=None, headers: dict[str, str] \| None=None, timeout: float \| TimeoutConfig \| None=None, **kwargs: Any)` | Send a HEAD request. |
| `options` | `async def options(self, url: str, *, params: dict[str, Any] \| None=None, headers: dict[str, str] \| None=None, timeout: float \| TimeoutConfig \| None=None, **kwargs: Any)` | Send an OPTIONS request. |
| `close` | `async def close(self)` | Close the session. |

### `StreamProgress`

- Source: `aquilia/http/streaming.py`
- Bases: `object`
- Summary: Progress information for streaming operations.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `bytes_transferred` | `int` | `` |
| `total_bytes` | `int \| None` | `` |
| `elapsed` | `float` | `` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `percentage` | `def percentage(self)` | Calculate progress percentage (0-100). |
| `bytes_per_second` | `def bytes_per_second(self)` | Calculate transfer rate. |
| `eta_seconds` | `def eta_seconds(self)` | Estimate remaining time in seconds. |

### `StreamingBody`

- Source: `aquilia/http/streaming.py`
- Bases: `object`
- Summary: Streaming request body wrapper.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `content_length` | `def content_length(self)` | Get content length if known. |

### `BufferedStream`

- Source: `aquilia/http/streaming.py`
- Bases: `object`
- Summary: Buffered async stream reader.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `readline` | `async def readline(self)` | Read a single line. |
| `readlines` | `async def readlines(self)` | Read all lines. |
| `read` | `async def read(self, n: int=-1)` | Read up to n bytes (or all if n=-1). |

### `ChunkedEncoder`

- Source: `aquilia/http/streaming.py`
- Bases: `object`
- Summary: HTTP chunked transfer encoding encoder.

### `ChunkedDecoder`

- Source: `aquilia/http/streaming.py`
- Bases: `object`
- Summary: HTTP chunked transfer encoding decoder.

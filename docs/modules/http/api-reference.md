# HTTP Client API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
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

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `create_transport` | `aquilia/http/_transport.py` | `def create_transport(config: HTTPClientConfig &#124; None = None) -> HTTPTransport` | Create native HTTP transport. |
| `request` | `aquilia/http/client.py` | `async def request(method: str &#124; HTTPMethod, url: str, **kwargs: Any) -> HTTPClientResponse` | Make a one-off HTTP request. |
| `get` | `aquilia/http/client.py` | `async def get(url: str, **kwargs: Any) -> HTTPClientResponse` | Make a GET request. |
| `post` | `aquilia/http/client.py` | `async def post(url: str, **kwargs: Any) -> HTTPClientResponse` | Make a POST request. |
| `put` | `aquilia/http/client.py` | `async def put(url: str, **kwargs: Any) -> HTTPClientResponse` | Make a PUT request. |
| `patch` | `aquilia/http/client.py` | `async def patch(url: str, **kwargs: Any) -> HTTPClientResponse` | Make a PATCH request. |
| `delete` | `aquilia/http/client.py` | `async def delete(url: str, **kwargs: Any) -> HTTPClientResponse` | Make a DELETE request. |
| `http_client` | `aquilia/http/integration.py` | `def http_client() -> HTTPClientBuilder` | Create HTTP client integration builder. |
| `create_client_from_config` | `aquilia/http/integration.py` | `def create_client_from_config(config: dict[str, Any]) -> AsyncHTTPClient` | Create HTTP client from configuration dictionary. |
| `create_middleware_stack` | `aquilia/http/middleware.py` | `def create_middleware_stack(*, base_url: str &#124; None = None, timeout: float &#124; None = None, headers: dict[str, str] &#124; None = None, enable_logging: bool = False, enable_retry: bool = False, enable_cache: bool = False, enable_cookies: bool = False, raise_for_status: bool = False) -> list[HTTPClientMiddleware]` | Create a standard middleware stack. |
| `get` | `aquilia/http/request.py` | `def get(url: str, **kwargs: Any) -> RequestBuilder` | Create a GET request builder. |
| `post` | `aquilia/http/request.py` | `def post(url: str, **kwargs: Any) -> RequestBuilder` | Create a POST request builder. |
| `put` | `aquilia/http/request.py` | `def put(url: str, **kwargs: Any) -> RequestBuilder` | Create a PUT request builder. |
| `patch` | `aquilia/http/request.py` | `def patch(url: str, **kwargs: Any) -> RequestBuilder` | Create a PATCH request builder. |
| `delete` | `aquilia/http/request.py` | `def delete(url: str, **kwargs: Any) -> RequestBuilder` | Create a DELETE request builder. |
| `head` | `aquilia/http/request.py` | `def head(url: str, **kwargs: Any) -> RequestBuilder` | Create a HEAD request builder. |
| `options` | `aquilia/http/request.py` | `def options(url: str, **kwargs: Any) -> RequestBuilder` | Create an OPTIONS request builder. |
| `create_response` | `aquilia/http/response.py` | `def create_response(status_code: int, headers: dict[str, str] &#124; list[tuple[str, str]] &#124; None = None, *, body: bytes &#124; None = None, stream: AsyncIterator[bytes] &#124; None = None, url: str = '', http_version: str = '1.1', elapsed: float = 0.0, request_url: str = '', history: list[HTTPClientResponse] &#124; None = None, extensions: dict[str, Any] &#124; None = None) -> HTTPClientResponse` | Factory function to create HTTPClientResponse. |
| `create_retry_strategy` | `aquilia/http/retry.py` | `def create_retry_strategy(config: RetryConfig &#124; None = None) -> RetryStrategy` | Create a retry strategy from configuration. |
| `stream_file` | `aquilia/http/streaming.py` | `async def stream_file(path: Path &#124; str, *, chunk_size: int = 65536) -> AsyncIterator[bytes]` | Stream a file asynchronously. |
| `stream_bytes` | `aquilia/http/streaming.py` | `async def stream_bytes(data: bytes, chunk_size: int = 65536) -> AsyncIterator[bytes]` | Stream bytes in chunks. |
| `collect_stream` | `aquilia/http/streaming.py` | `async def collect_stream(stream: AsyncIterator[bytes]) -> bytes` | Collect all bytes from an async iterator. |
| `stream_with_limit` | `aquilia/http/streaming.py` | `async def stream_with_limit(stream: AsyncIterator[bytes], max_bytes: int) -> AsyncIterator[bytes]` | Stream with a byte limit. |

## Constants

| Name | Source | Value or type |
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
| `HTTP_STATUS_REASONS` | `aquilia/http/response.py` | `{100: 'Continue', 101: 'Switching Protocols', 102: 'Processing', 103: 'Early Hints', 200: 'OK', 201: 'Created', 202: 'Accepted', 203: 'Non-Authoritative Informa` |
| `T` | `aquilia/http/retry.py` | `TypeVar('T')` |

## Detailed Classes And Methods

### Class: `RawResponse`

- Source: `aquilia/http/_transport.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Raw response before processing.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `http_version` | `str` |  |
| `status_code` | `int` |  |
| `reason` | `str` |  |
| `headers` | `dict[str, str]` |  |
| `body` | `bytes` | `b''` |
| `stream` | `AsyncIterator[bytes] &#124; None` | `None` |

### Class: `ConnectionInfo`

- Source: `aquilia/http/_transport.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Tracks a pooled connection.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `host` | `str` |  |
| `port` | `int` |  |
| `ssl` | `bool` |  |
| `reader` | `asyncio.StreamReader` |  |
| `writer` | `asyncio.StreamWriter` |  |
| `created_at` | `float` | `field(default_factory=time.monotonic)` |
| `last_used` | `float` | `field(default_factory=time.monotonic)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `age` | `def age(self) -> float` | property | Method. |
| `is_alive` | `def is_alive(self) -> bool` |  | Method. |
| `close` | `async def close(self) -> None` |  | Method. |

### Class: `ConnectionPool`

- Source: `aquilia/http/_transport.py`
- Bases: `object`
- Summary: Keep-alive connection pool. Reuses TCP connections per host.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_connection` | `async def get_connection(self, host: str, port: int, use_ssl: bool) -> ConnectionInfo &#124; None` |  | Grab a live connection if one exists. |
| `put_connection` | `async def put_connection(self, conn: ConnectionInfo) -> bool` |  | Return connection to pool if we have room. |
| `close_all` | `async def close_all(self) -> None` |  | Method. |
| `cleanup_expired` | `async def cleanup_expired(self) -> int` |  | Prune dead/expired connections. |

### Class: `HTTPTransport`

- Source: `aquilia/http/_transport.py`
- Bases: `ABC`
- Summary: Base transport interface.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `send` | `async def send(self, request: HTTPClientRequest) -> HTTPClientResponse` | abstractmethod | Method. |
| `close` | `async def close(self) -> None` | abstractmethod | Method. |

### Class: `NativeTransport`

- Source: `aquilia/http/_transport.py`
- Bases: `HTTPTransport`
- Summary: Pure asyncio HTTP/1.1 transport.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `send` | `async def send(self, request: HTTPClientRequest) -> HTTPClientResponse` |  | Method. |
| `close` | `async def close(self) -> None` |  | Method. |

### Class: `MockTransport`

- Source: `aquilia/http/_transport.py`
- Bases: `HTTPTransport`
- Summary: Mock transport for tests. Returns predefined responses.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `add_response` | `def add_response(self, method: str, url: str, response: HTTPClientResponse) -> None` |  | Method. |
| `add_json_response` | `def add_json_response(self, method: str, url: str, data: dict[str, Any], status_code: int = 200) -> None` |  | Method. |
| `requests` | `def requests(self) -> list[HTTPClientRequest]` | property | Method. |
| `clear` | `def clear(self) -> None` |  | Method. |
| `send` | `async def send(self, request: HTTPClientRequest) -> HTTPClientResponse` |  | Method. |
| `close` | `async def close(self) -> None` |  | Method. |

### Class: `AuthInterceptor`

- Source: `aquilia/http/auth.py`
- Bases: `HTTPInterceptor, ABC`
- Summary: Base class for authentication interceptors.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_auth_header` | `def get_auth_header(self, request: HTTPClientRequest) -> tuple[str, str] &#124; None` | abstractmethod | Generate authentication header. |
| `intercept` | `async def intercept(self, request: HTTPClientRequest, next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]]) -> HTTPClientResponse` |  | Apply authentication header to request. |

### Class: `BasicAuth`

- Source: `aquilia/http/auth.py`
- Bases: `AuthInterceptor`
- Summary: HTTP Basic Authentication.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_auth_header` | `def get_auth_header(self, request: HTTPClientRequest) -> tuple[str, str]` |  | Method. |

### Class: `BearerAuth`

- Source: `aquilia/http/auth.py`
- Bases: `AuthInterceptor`
- Summary: Bearer Token Authentication.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_auth_header` | `def get_auth_header(self, request: HTTPClientRequest) -> tuple[str, str]` |  | Method. |

### Class: `APIKeyAuth`

- Source: `aquilia/http/auth.py`
- Bases: `AuthInterceptor`
- Summary: API Key Authentication.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_auth_header` | `def get_auth_header(self, request: HTTPClientRequest) -> tuple[str, str] &#124; None` |  | Method. |
| `intercept` | `async def intercept(self, request: HTTPClientRequest, next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]]) -> HTTPClientResponse` |  | Method. |

### Class: `DigestAuth`

- Source: `aquilia/http/auth.py`
- Bases: `AuthInterceptor`
- Summary: HTTP Digest Authentication.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_auth_header` | `def get_auth_header(self, request: HTTPClientRequest) -> tuple[str, str] &#124; None` |  | Method. |
| `intercept` | `async def intercept(self, request: HTTPClientRequest, next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]]) -> HTTPClientResponse` |  | Method. |

### Class: `OAuth2Token`

- Source: `aquilia/http/auth.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: OAuth 2.0 token.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `access_token` | `str` |  |
| `token_type` | `str` | `'Bearer'` |
| `expires_in` | `int &#124; None` | `None` |
| `refresh_token` | `str &#124; None` | `None` |
| `scope` | `str &#124; None` | `None` |
| `created_at` | `float` | `0.0` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_expired` | `def is_expired(self) -> bool` | property | Method. |

### Class: `OAuth2Auth`

- Source: `aquilia/http/auth.py`
- Bases: `AuthInterceptor`
- Summary: OAuth 2.0 Bearer Token Authentication.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `token` | `def token(self) -> OAuth2Token` | property | Method. |
| `set_token` | `def set_token(self, token: OAuth2Token) -> None` |  | Method. |
| `get_auth_header` | `def get_auth_header(self, request: HTTPClientRequest) -> tuple[str, str]` |  | Method. |
| `intercept` | `async def intercept(self, request: HTTPClientRequest, next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]]) -> HTTPClientResponse` |  | Method. |

### Class: `AWSSignatureV4Auth`

- Source: `aquilia/http/auth.py`
- Bases: `AuthInterceptor`
- Summary: AWS Signature Version 4 Authentication.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_auth_header` | `def get_auth_header(self, request: HTTPClientRequest) -> tuple[str, str] &#124; None` |  | Method. |
| `intercept` | `async def intercept(self, request: HTTPClientRequest, next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]]) -> HTTPClientResponse` |  | Method. |

### Class: `AsyncHTTPClient`

- Source: `aquilia/http/client.py`
- Bases: `object`
- Summary: Async HTTP client.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `config` | `def config(self) -> HTTPClientConfig` | property | Get client configuration. |
| `cookies` | `def cookies(self) -> CookieJar` | property | Get cookie jar. |
| `base_url` | `def base_url(self) -> str &#124; None` | property | Get base URL. |
| `request` | `def request(self, method: str &#124; HTTPMethod, url: str, **kwargs: Any) -> RequestBuilder` |  | Create a request builder. |
| `send` | `async def send(self, request: HTTPClientRequest) -> HTTPClientResponse` |  | Send a pre-built request. |
| `get` | `async def get(self, url: str, *, params: dict[str, Any] &#124; None = None, headers: dict[str, str] &#124; None = None, timeout: float &#124; TimeoutConfig &#124; None = None, **kwargs: Any) -> HTTPClientResponse` |  | Send a GET request. |
| `post` | `async def post(self, url: str, *, params: dict[str, Any] &#124; None = None, headers: dict[str, str] &#124; None = None, json: Any = None, data: dict[str, Any] &#124; str &#124; bytes &#124; None = None, files: MultipartFormData &#124; None = None, timeout: float &#124; TimeoutConfig &#124; None = None, **kwargs: Any) -> HTTPClientResponse` |  | Send a POST request. |
| `put` | `async def put(self, url: str, *, params: dict[str, Any] &#124; None = None, headers: dict[str, str] &#124; None = None, json: Any = None, data: dict[str, Any] &#124; str &#124; bytes &#124; None = None, timeout: float &#124; TimeoutConfig &#124; None = None, **kwargs: Any) -> HTTPClientResponse` |  | Send a PUT request. |
| `patch` | `async def patch(self, url: str, *, params: dict[str, Any] &#124; None = None, headers: dict[str, str] &#124; None = None, json: Any = None, data: dict[str, Any] &#124; str &#124; bytes &#124; None = None, timeout: float &#124; TimeoutConfig &#124; None = None, **kwargs: Any) -> HTTPClientResponse` |  | Send a PATCH request. |
| `delete` | `async def delete(self, url: str, *, params: dict[str, Any] &#124; None = None, headers: dict[str, str] &#124; None = None, timeout: float &#124; TimeoutConfig &#124; None = None, **kwargs: Any) -> HTTPClientResponse` |  | Send a DELETE request. |
| `head` | `async def head(self, url: str, *, params: dict[str, Any] &#124; None = None, headers: dict[str, str] &#124; None = None, timeout: float &#124; TimeoutConfig &#124; None = None, **kwargs: Any) -> HTTPClientResponse` |  | Send a HEAD request. |
| `options` | `async def options(self, url: str, *, params: dict[str, Any] &#124; None = None, headers: dict[str, str] &#124; None = None, timeout: float &#124; TimeoutConfig &#124; None = None, **kwargs: Any) -> HTTPClientResponse` |  | Send an OPTIONS request. |
| `stream` | `async def stream(self, method: str &#124; HTTPMethod, url: str, *, params: dict[str, Any] &#124; None = None, headers: dict[str, str] &#124; None = None, json: Any = None, data: dict[str, Any] &#124; str &#124; bytes &#124; None = None, chunk_size: int = 65536, **kwargs: Any) -> AsyncIterator[bytes]` |  | Stream a response body. |
| `close` | `async def close(self) -> None` |  | Close the client and release resources. |

### Class: `HTTPVersion`

- Source: `aquilia/http/config.py`
- Bases: `str, Enum`
- Summary: Supported HTTP versions.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `HTTP_1_0` |  | `'1.0'` |
| `HTTP_1_1` |  | `'1.1'` |
| `HTTP_2` |  | `'2'` |
| `AUTO` |  | `'auto'` |

### Class: `CompressionAlgorithm`

- Source: `aquilia/http/config.py`
- Bases: `str, Enum`
- Summary: Supported compression algorithms for Accept-Encoding.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `GZIP` |  | `'gzip'` |
| `DEFLATE` |  | `'deflate'` |
| `BR` |  | `'br'` |
| `ZSTD` |  | `'zstd'` |
| `IDENTITY` |  | `'identity'` |

### Class: `TimeoutConfig`

- Source: `aquilia/http/config.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: HTTP request timeout configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `total` | `float &#124; None` | `30.0` |
| `connect` | `float &#124; None` | `10.0` |
| `read` | `float &#124; None` | `None` |
| `write` | `float &#124; None` | `None` |
| `pool` | `float &#124; None` | `5.0` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `no_timeout` | `def no_timeout(cls) -> TimeoutConfig` | classmethod | Create a configuration with no timeouts (infinite wait). |
| `fast` | `def fast(cls) -> TimeoutConfig` | classmethod | Create a fast timeout configuration for quick requests. |
| `slow` | `def slow(cls) -> TimeoutConfig` | classmethod | Create a slow timeout configuration for long-running requests. |

### Class: `PoolConfig`

- Source: `aquilia/http/config.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Connection pool configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `max_connections` | `int` | `100` |
| `max_connections_per_host` | `int` | `10` |
| `max_keepalive_connections` | `int` | `20` |
| `keepalive_expiry` | `float` | `60.0` |
| `enable_http2` | `bool` | `False` |

### Class: `RetryConfig`

- Source: `aquilia/http/config.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Retry configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `max_attempts` | `int` | `3` |
| `backoff_base` | `float` | `1.0` |
| `backoff_multiplier` | `float` | `2.0` |
| `backoff_max` | `float` | `60.0` |
| `backoff_jitter` | `float` | `0.1` |
| `retry_on_status` | `frozenset[int]` | `field(default_factory=lambda: frozenset({429, 500, 502, 503, 504}))` |
| `retry_on_methods` | `frozenset[str]` | `field(default_factory=lambda: frozenset({'GET', 'HEAD', 'OPTIONS', 'PUT', 'DELETE'}))` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `no_retry` | `def no_retry(cls) -> RetryConfig` | classmethod | Create a configuration with no retries. |
| `aggressive` | `def aggressive(cls) -> RetryConfig` | classmethod | Create an aggressive retry configuration. |

### Class: `ProxyConfig`

- Source: `aquilia/http/config.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Proxy configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `http_proxy` | `str &#124; None` | `None` |
| `https_proxy` | `str &#124; None` | `None` |
| `no_proxy` | `str &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `from_env` | `def from_env(cls) -> ProxyConfig` | classmethod | Create proxy config from environment variables. |

### Class: `TLSConfig`

- Source: `aquilia/http/config.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: TLS/SSL configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `verify` | `bool` | `True` |
| `cert_file` | `str &#124; None` | `None` |
| `key_file` | `str &#124; None` | `None` |
| `ca_bundle` | `str &#124; None` | `None` |
| `ssl_context` | `SSLContext &#124; None` | `None` |
| `minimum_version` | `str &#124; None` | `None` |

### Class: `HTTPClientConfig`

- Source: `aquilia/http/config.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Complete HTTP client configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `base_url` | `str &#124; None` | `None` |
| `timeout` | `TimeoutConfig` | `field(default_factory=TimeoutConfig)` |
| `pool` | `PoolConfig` | `field(default_factory=PoolConfig)` |
| `retry` | `RetryConfig` | `field(default_factory=RetryConfig)` |
| `proxy` | `ProxyConfig &#124; None` | `None` |
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

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `with_base_url` | `def with_base_url(self, url: str) -> HTTPClientConfig` |  | Return a copy with a different base URL. |
| `with_timeout` | `def with_timeout(self, **kwargs: Any) -> HTTPClientConfig` |  | Return a copy with modified timeout settings. |
| `merge_headers` | `def merge_headers(self, headers: dict[str, str] &#124; None) -> dict[str, str]` |  | Merge default headers with request-specific headers. |
| `merge_params` | `def merge_params(self, params: dict[str, str] &#124; None) -> dict[str, str]` |  | Merge default params with request-specific params. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Convert to dictionary for serialization. |
| `from_dict` | `def from_dict(cls, data: dict[str, Any]) -> HTTPClientConfig` | classmethod | Create from dictionary. |

### Class: `Cookie`

- Source: `aquilia/http/cookies.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: HTTP Cookie representation.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `value` | `str` |  |
| `domain` | `str` | `''` |
| `path` | `str` | `'/'` |
| `expires` | `float &#124; None` | `None` |
| `max_age` | `int &#124; None` | `None` |
| `secure` | `bool` | `False` |
| `http_only` | `bool` | `False` |
| `same_site` | `str` | `''` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_expired` | `def is_expired(self) -> bool` | property | Check if cookie has expired. |
| `is_session` | `def is_session(self) -> bool` | property | Check if this is a session cookie (no expiry). |
| `matches_domain` | `def matches_domain(self, request_domain: str) -> bool` |  | Check if cookie matches the request domain. |
| `matches_path` | `def matches_path(self, request_path: str) -> bool` |  | Check if cookie matches the request path. |
| `matches` | `def matches(self, url: str) -> bool` |  | Check if cookie matches the URL. |
| `to_header_value` | `def to_header_value(self) -> str` |  | Format as cookie header value (name=value). |
| `to_set_cookie` | `def to_set_cookie(self) -> str` |  | Format as Set-Cookie header value. |
| `from_set_cookie` | `def from_set_cookie(cls, header: str, request_url: str = '') -> Cookie` | classmethod | Parse a Set-Cookie header. |

### Class: `CookieJar`

- Source: `aquilia/http/cookies.py`
- Bases: `object`
- Summary: Thread-safe cookie storage.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `set` | `def set(self, cookie: Cookie) -> None` |  | Add or update a cookie. |
| `set_from_response` | `def set_from_response(self, headers: dict[str, str] &#124; list[tuple[str, str]], request_url: str) -> list[Cookie]` |  | Extract and store cookies from response headers. |
| `get` | `def get(self, name: str, domain: str = '', path: str = '/') -> Cookie &#124; None` |  | Get a specific cookie. |
| `get_for_url` | `def get_for_url(self, url: str) -> list[Cookie]` |  | Get all cookies that match a URL. |
| `get_header` | `def get_header(self, url: str) -> str &#124; None` |  | Get Cookie header value for a URL. |
| `delete` | `def delete(self, name: str, domain: str = '', path: str = '/') -> bool` |  | Delete a cookie. |
| `clear` | `def clear(self, domain: str = '') -> int` |  | Clear cookies. |
| `cleanup_expired` | `def cleanup_expired(self) -> int` |  | Remove expired cookies. |
| `all` | `def all(self) -> list[Cookie]` |  | Get all non-expired cookies. |
| `to_dict` | `def to_dict(self) -> dict[str, str]` |  | Export cookies as simple dict. |

### Class: `CookieInterceptor`

- Source: `aquilia/http/cookies.py`
- Bases: `object`
- Summary: Interceptor that manages cookies automatically.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `jar` | `def jar(self) -> CookieJar` | property | Method. |
| `intercept` | `async def intercept(self, request: Any, next_handler: Any) -> Any` |  | Method. |

### Class: `HTTPClientFault`

- Source: `aquilia/http/faults.py`
- Bases: `Fault`
- Summary: Base fault for the HTTP client subsystem.

### Class: `ConnectionFault`

- Source: `aquilia/http/faults.py`
- Bases: `HTTPClientFault`
- Summary: Failed to establish connection to remote host.

### Class: `ConnectionPoolExhaustedFault`

- Source: `aquilia/http/faults.py`
- Bases: `HTTPClientFault`
- Summary: Connection pool exhausted.

### Class: `ConnectionClosedFault`

- Source: `aquilia/http/faults.py`
- Bases: `HTTPClientFault`
- Summary: Connection was unexpectedly closed.

### Class: `TimeoutFault`

- Source: `aquilia/http/faults.py`
- Bases: `HTTPClientFault`
- Summary: Request timed out.

### Class: `ConnectTimeoutFault`

- Source: `aquilia/http/faults.py`
- Bases: `TimeoutFault`
- Summary: Connection timeout.

### Class: `ReadTimeoutFault`

- Source: `aquilia/http/faults.py`
- Bases: `TimeoutFault`
- Summary: Read timeout.

### Class: `WriteTimeoutFault`

- Source: `aquilia/http/faults.py`
- Bases: `TimeoutFault`
- Summary: Write timeout.

### Class: `RequestTimeoutFault`

- Source: `aquilia/http/faults.py`
- Bases: `TimeoutFault`
- Summary: Total request timeout.

### Class: `TLSFault`

- Source: `aquilia/http/faults.py`
- Bases: `HTTPClientFault`
- Summary: TLS/SSL error.

### Class: `CertificateVerifyFault`

- Source: `aquilia/http/faults.py`
- Bases: `TLSFault`
- Summary: Certificate verification failed.

### Class: `ResponseFault`

- Source: `aquilia/http/faults.py`
- Bases: `HTTPClientFault`
- Summary: Response processing error.

### Class: `InvalidResponseFault`

- Source: `aquilia/http/faults.py`
- Bases: `ResponseFault`
- Summary: Invalid response received.

### Class: `DecodingFault`

- Source: `aquilia/http/faults.py`
- Bases: `ResponseFault`
- Summary: Response body decoding error.

### Class: `HTTPStatusFault`

- Source: `aquilia/http/faults.py`
- Bases: `ResponseFault`
- Summary: HTTP error status received.

### Class: `ClientErrorFault`

- Source: `aquilia/http/faults.py`
- Bases: `HTTPStatusFault`
- Summary: HTTP 4xx client error.

### Class: `ServerErrorFault`

- Source: `aquilia/http/faults.py`
- Bases: `HTTPStatusFault`
- Summary: HTTP 5xx server error.

### Class: `TooManyRedirectsFault`

- Source: `aquilia/http/faults.py`
- Bases: `HTTPClientFault`
- Summary: Too many redirects.

### Class: `RequestBuildFault`

- Source: `aquilia/http/faults.py`
- Bases: `HTTPClientFault`
- Summary: Request construction error.

### Class: `InvalidURLFault`

- Source: `aquilia/http/faults.py`
- Bases: `RequestBuildFault`
- Summary: Invalid URL.

### Class: `InvalidHeaderFault`

- Source: `aquilia/http/faults.py`
- Bases: `RequestBuildFault`
- Summary: Invalid header.

### Class: `TransportFault`

- Source: `aquilia/http/faults.py`
- Bases: `HTTPClientFault`
- Summary: Low-level transport error.

### Class: `ProxyFault`

- Source: `aquilia/http/faults.py`
- Bases: `TransportFault`
- Summary: Proxy connection error.

### Class: `RetryExhaustedFault`

- Source: `aquilia/http/faults.py`
- Bases: `HTTPClientFault`
- Summary: All retry attempts exhausted.

### Class: `ConfigurationFault`

- Source: `aquilia/http/faults.py`
- Bases: `HTTPClientFault`
- Summary: HTTP client configuration error.

### Class: `HTTPClientProvider`

- Source: `aquilia/http/integration.py`
- Bases: `object`
- Summary: DI provider for AsyncHTTPClient.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `provides` | `def provides(self) -> type` | property | Type this provider provides. |
| `scope` | `def scope(self) -> str` | property | DI scope. |
| `shutdown` | `async def shutdown(self) -> None` |  | Shutdown the provider. |

### Class: `HTTPClientBuilder`

- Source: `aquilia/http/integration.py`
- Bases: `object`
- Summary: Fluent builder for HTTP client configuration.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `base_url` | `def base_url(self, url: str) -> HTTPClientBuilder` |  | Set base URL. |
| `timeout` | `def timeout(self, total: float &#124; None = 30.0, connect: float &#124; None = 10.0, read: float &#124; None = None, write: float &#124; None = None) -> HTTPClientBuilder` |  | Set timeout configuration. |
| `pool` | `def pool(self, max_connections: int = 100, max_connections_per_host: int = 10, keepalive_expiry: float = 60.0) -> HTTPClientBuilder` |  | Set connection pool configuration. |
| `retry` | `def retry(self, max_attempts: int = 3, backoff_base: float = 1.0, backoff_multiplier: float = 2.0, backoff_max: float = 60.0) -> HTTPClientBuilder` |  | Set retry configuration. |
| `proxy` | `def proxy(self, http_proxy: str &#124; None = None, https_proxy: str &#124; None = None, no_proxy: str &#124; None = None) -> HTTPClientBuilder` |  | Set proxy configuration. |
| `tls` | `def tls(self, verify: bool = True, cert_file: str &#124; None = None, key_file: str &#124; None = None, ca_bundle: str &#124; None = None) -> HTTPClientBuilder` |  | Set TLS configuration. |
| `header` | `def header(self, name: str, value: str) -> HTTPClientBuilder` |  | Add a default header. |
| `headers` | `def headers(self, headers: dict[str, str]) -> HTTPClientBuilder` |  | Set default headers. |
| `follow_redirects` | `def follow_redirects(self, follow: bool = True) -> HTTPClientBuilder` |  | Set redirect following behavior. |
| `max_redirects` | `def max_redirects(self, max_redirects: int) -> HTTPClientBuilder` |  | Set maximum redirects. |
| `raise_for_status` | `def raise_for_status(self, raise_errors: bool = True) -> HTTPClientBuilder` |  | Set raise_for_status behavior. |
| `user_agent` | `def user_agent(self, user_agent: str) -> HTTPClientBuilder` |  | Set User-Agent header. |
| `build` | `def build(self) -> HTTPClientConfig` |  | Build the configuration. |
| `build_provider` | `def build_provider(self, scope: str = 'singleton') -> HTTPClientProvider` |  | Build a DI provider. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Convert to dictionary for serialization. |

### Class: `HTTPInterceptor`

- Source: `aquilia/http/interceptors.py`
- Bases: `ABC`
- Summary: Base class for HTTP interceptors.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `intercept` | `async def intercept(self, request: HTTPClientRequest, next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]]) -> HTTPClientResponse` | abstractmethod | Intercept and optionally modify request/response. |

### Class: `InterceptorChain`

- Source: `aquilia/http/interceptors.py`
- Bases: `object`
- Summary: Chain of interceptors.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `add` | `def add(self, interceptor: HTTPInterceptor) -> InterceptorChain` |  | Add an interceptor to the chain. |
| `set_handler` | `def set_handler(self, handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]]) -> InterceptorChain` |  | Set the final handler. |
| `execute` | `async def execute(self, request: HTTPClientRequest) -> HTTPClientResponse` |  | Execute the interceptor chain. |

### Class: `LoggingInterceptor`

- Source: `aquilia/http/interceptors.py`
- Bases: `HTTPInterceptor`
- Summary: Logs request and response details.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `intercept` | `async def intercept(self, request: HTTPClientRequest, next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]]) -> HTTPClientResponse` |  | Method. |

### Class: `HeaderInterceptor`

- Source: `aquilia/http/interceptors.py`
- Bases: `HTTPInterceptor`
- Summary: Adds default headers to all requests.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `intercept` | `async def intercept(self, request: HTTPClientRequest, next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]]) -> HTTPClientResponse` |  | Method. |

### Class: `UserAgentInterceptor`

- Source: `aquilia/http/interceptors.py`
- Bases: `HTTPInterceptor`
- Summary: Sets User-Agent header.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `intercept` | `async def intercept(self, request: HTTPClientRequest, next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]]) -> HTTPClientResponse` |  | Method. |

### Class: `AcceptInterceptor`

- Source: `aquilia/http/interceptors.py`
- Bases: `HTTPInterceptor`
- Summary: Sets Accept header for content negotiation.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `intercept` | `async def intercept(self, request: HTTPClientRequest, next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]]) -> HTTPClientResponse` |  | Method. |

### Class: `RequestMetrics`

- Source: `aquilia/http/interceptors.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Metrics collected for a request.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `method` | `str` |  |
| `url` | `str` |  |
| `status_code` | `int` |  |
| `elapsed` | `float` |  |
| `request_size` | `int` |  |
| `response_size` | `int &#124; None` |  |
| `error` | `str &#124; None` | `None` |

### Class: `MetricsInterceptor`

- Source: `aquilia/http/interceptors.py`
- Bases: `HTTPInterceptor`
- Summary: Collects request metrics.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `intercept` | `async def intercept(self, request: HTTPClientRequest, next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]]) -> HTTPClientResponse` |  | Method. |

### Class: `TimeoutInterceptor`

- Source: `aquilia/http/interceptors.py`
- Bases: `HTTPInterceptor`
- Summary: Enforces timeout on requests.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `intercept` | `async def intercept(self, request: HTTPClientRequest, next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]]) -> HTTPClientResponse` |  | Method. |

### Class: `RedirectInterceptor`

- Source: `aquilia/http/interceptors.py`
- Bases: `HTTPInterceptor`
- Summary: Handles HTTP redirects.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `intercept` | `async def intercept(self, request: HTTPClientRequest, next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]]) -> HTTPClientResponse` |  | Method. |

### Class: `CacheInterceptor`

- Source: `aquilia/http/interceptors.py`
- Bases: `HTTPInterceptor`
- Summary: HTTP response caching interceptor.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `intercept` | `async def intercept(self, request: HTTPClientRequest, next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]]) -> HTTPClientResponse` |  | Method. |

### Class: `HTTPClientMiddleware`

- Source: `aquilia/http/middleware.py`
- Bases: `ABC`
- Summary: Base class for HTTP client middleware.

### Class: `MiddlewareStack`

- Source: `aquilia/http/middleware.py`
- Bases: `object`
- Summary: Stack of middleware that processes requests.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `add` | `def add(self, middleware: HTTPClientMiddleware) -> MiddlewareStack` |  | Add middleware to the stack. |
| `add_many` | `def add_many(self, middleware: list[HTTPClientMiddleware]) -> MiddlewareStack` |  | Add multiple middleware to the stack. |
| `set_handler` | `def set_handler(self, handler: MiddlewareHandler) -> MiddlewareStack` |  | Set the final request handler. |
| `build` | `def build(self) -> MiddlewareHandler` |  | Build the middleware chain. |
| `execute` | `async def execute(self, request: HTTPClientRequest) -> HTTPClientResponse` |  | Execute the middleware chain. |

### Class: `LoggingMiddleware`

- Source: `aquilia/http/middleware.py`
- Bases: `HTTPClientMiddleware`
- Summary: Logs requests and responses.

### Class: `HeadersMiddleware`

- Source: `aquilia/http/middleware.py`
- Bases: `HTTPClientMiddleware`
- Summary: Adds default headers to all requests.

### Class: `TimeoutMiddleware`

- Source: `aquilia/http/middleware.py`
- Bases: `HTTPClientMiddleware`
- Summary: Enforces timeout on requests.

### Class: `ErrorHandlingMiddleware`

- Source: `aquilia/http/middleware.py`
- Bases: `HTTPClientMiddleware`
- Summary: Handles errors and converts them to faults.

### Class: `RetryMiddleware`

- Source: `aquilia/http/middleware.py`
- Bases: `HTTPClientMiddleware`
- Summary: Retries failed requests.

### Class: `CompressionMiddleware`

- Source: `aquilia/http/middleware.py`
- Bases: `HTTPClientMiddleware`
- Summary: Handles request/response compression.

### Class: `CacheMiddleware`

- Source: `aquilia/http/middleware.py`
- Bases: `HTTPClientMiddleware`
- Summary: Caches GET responses.

### Class: `BaseURLMiddleware`

- Source: `aquilia/http/middleware.py`
- Bases: `HTTPClientMiddleware`
- Summary: Prepends base URL to relative URLs.

### Class: `CookieMiddleware`

- Source: `aquilia/http/middleware.py`
- Bases: `HTTPClientMiddleware`
- Summary: Manages cookies automatically.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `jar` | `def jar(self) -> Any` | property | Method. |

### Class: `FormField`

- Source: `aquilia/http/multipart.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A form field in multipart data.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `value` | `str &#124; bytes` |  |
| `content_type` | `str &#124; None` | `None` |
| `filename` | `str &#124; None` | `None` |

### Class: `FormFile`

- Source: `aquilia/http/multipart.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A file field in multipart data.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `filename` | `str` |  |
| `content` | `bytes &#124; BinaryIO &#124; AsyncIterator[bytes] &#124; Path` |  |
| `content_type` | `str &#124; None` | `None` |
| `content_length` | `int &#124; None` | `None` |

### Class: `MultipartFormData`

- Source: `aquilia/http/multipart.py`
- Bases: `object`
- Summary: Builder for multipart/form-data requests.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `boundary` | `def boundary(self) -> str` | property | Get the multipart boundary. |
| `content_type` | `def content_type(self) -> str` | property | Get the Content-Type header value. |
| `field` | `def field(self, name: str, value: str &#124; bytes, content_type: str &#124; None = None) -> MultipartFormData` |  | Add a form field. |
| `file` | `def file(self, name: str, filename: str, content: bytes &#124; BinaryIO &#124; AsyncIterator[bytes], content_type: str &#124; None = None) -> MultipartFormData` |  | Add a file field. |
| `file_from_path` | `def file_from_path(self, name: str, path: Path &#124; str, content_type: str &#124; None = None, filename: str &#124; None = None) -> MultipartFormData` |  | Add a file field from a path. |
| `file_from_bytes` | `def file_from_bytes(self, name: str, filename: str, data: bytes, content_type: str &#124; None = None) -> MultipartFormData` |  | Add a file field from bytes. |
| `encode` | `async def encode(self) -> bytes` |  | Encode all fields and files to multipart body. |
| `encode_sync` | `def encode_sync(self) -> bytes` |  | Synchronously encode fields and files. |
| `stream` | `async def stream(self, chunk_size: int = 65536) -> AsyncIterator[bytes]` |  | Stream the multipart body in chunks. |
| `content_length` | `def content_length(self) -> int &#124; None` |  | Calculate total content length if possible. |

### Class: `ConnectionStats`

- Source: `aquilia/http/pool.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Connection pool statistics.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `total_created` | `int` | `0` |
| `total_closed` | `int` | `0` |
| `total_reused` | `int` | `0` |
| `active_connections` | `int` | `0` |
| `idle_connections` | `int` | `0` |
| `failed_acquisitions` | `int` | `0` |
| `pool_exhausted_count` | `int` | `0` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, int]` |  | Method. |

### Class: `PooledConnection`

- Source: `aquilia/http/pool.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Wrapper for a pooled connection.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `host` | `str` |  |
| `port` | `int` |  |
| `scheme` | `str` |  |
| `connection` | `Any` |  |
| `created_at` | `float` | `field(default_factory=time.monotonic)` |
| `last_used_at` | `float` | `field(default_factory=time.monotonic)` |
| `requests_count` | `int` | `0` |
| `is_available` | `bool` | `True` |
| `is_http2` | `bool` | `False` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `age` | `def age(self) -> float` | property | Seconds since connection was created. |
| `idle_time` | `def idle_time(self) -> float` | property | Seconds since connection was last used. |
| `key` | `def key(self) -> str` | property | Connection pool key. |
| `mark_used` | `def mark_used(self) -> None` |  | Mark connection as in use. |
| `mark_available` | `def mark_available(self) -> None` |  | Mark connection as available for reuse. |
| `is_expired` | `def is_expired(self, max_age: float) -> bool` |  | Check if connection has exceeded keepalive timeout. |

### Class: `ConnectionPool`

- Source: `aquilia/http/pool.py`
- Bases: `object`
- Summary: Async connection pool.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `stats` | `def stats(self) -> ConnectionStats` | property | Get pool statistics. |
| `config` | `def config(self) -> PoolConfig` | property | Get pool configuration. |
| `acquire` | `async def acquire(self, url: str, *, timeout: float &#124; None = None) -> PooledConnection &#124; None` |  | Acquire a connection from the pool. |
| `add` | `async def add(self, url: str, connection: Any, *, is_http2: bool = False) -> PooledConnection` |  | Add a new connection to the pool. |
| `release` | `async def release(self, conn: PooledConnection, *, reusable: bool = True) -> None` |  | Release a connection back to the pool. |
| `remove` | `async def remove(self, conn: PooledConnection) -> None` |  | Remove and close a connection. |
| `cleanup` | `async def cleanup(self) -> int` |  | Clean up expired connections. |
| `start_cleanup_task` | `def start_cleanup_task(self) -> None` |  | Start background cleanup task. |
| `close` | `async def close(self) -> None` |  | Close all connections and shutdown pool. |

### Class: `ConnectionPoolManager`

- Source: `aquilia/http/pool.py`
- Bases: `object`
- Summary: Manager for multiple connection pools.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_pool` | `async def get_pool(self, name: str = 'default', config: PoolConfig &#124; None = None) -> ConnectionPool` |  | Get or create a named pool. |
| `close_all` | `async def close_all(self) -> None` |  | Close all managed pools. |

### Class: `HTTPMethod`

- Source: `aquilia/http/request.py`
- Bases: `str, Enum`
- Summary: HTTP methods.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `GET` |  | `'GET'` |
| `POST` |  | `'POST'` |
| `PUT` |  | `'PUT'` |
| `PATCH` |  | `'PATCH'` |
| `DELETE` |  | `'DELETE'` |
| `HEAD` |  | `'HEAD'` |
| `OPTIONS` |  | `'OPTIONS'` |
| `TRACE` |  | `'TRACE'` |
| `CONNECT` |  | `'CONNECT'` |

### Class: `HTTPClientRequest`

- Source: `aquilia/http/request.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: HTTP request representation.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `method` | `HTTPMethod` |  |
| `url` | `str` |  |
| `headers` | `dict[str, str]` | `field(default_factory=dict)` |
| `body` | `bytes &#124; AsyncIterator[bytes] &#124; None` | `None` |
| `timeout` | `TimeoutConfig &#124; None` | `None` |
| `follow_redirects` | `bool &#124; None` | `None` |
| `auth` | `tuple[str, str] &#124; None` | `None` |
| `extensions` | `dict[str, Any]` | `field(default_factory=dict)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `host` | `def host(self) -> str` | property | Extract host from URL. |
| `path` | `def path(self) -> str` | property | Extract path from URL. |
| `scheme` | `def scheme(self) -> str` | property | Extract scheme from URL. |
| `query_string` | `def query_string(self) -> str` | property | Extract query string from URL. |
| `content_type` | `def content_type(self) -> str &#124; None` | property | Get Content-Type header. |
| `content_length` | `def content_length(self) -> int &#124; None` | property | Get Content-Length header as int. |
| `has_body` | `def has_body(self) -> bool` |  | Check if request has a body. |
| `is_streaming` | `def is_streaming(self) -> bool` |  | Check if body is a stream. |
| `copy` | `def copy(self, **changes: Any) -> HTTPClientRequest` |  | Create a copy with optional changes. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize to dictionary (for logging/debugging). |

### Class: `RequestBuilder`

- Source: `aquilia/http/request.py`
- Bases: `object`
- Summary: Fluent builder for HTTP requests.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `header` | `def header(self, name: str, value: str) -> RequestBuilder` |  | Add a header. |
| `headers` | `def headers(self, headers: HeadersType) -> RequestBuilder` |  | Add multiple headers. |
| `param` | `def param(self, name: str, value: str &#124; int &#124; float &#124; bool &#124; None) -> RequestBuilder` |  | Add a query parameter. |
| `params` | `def params(self, params: ParamsType) -> RequestBuilder` |  | Add multiple query parameters. |
| `body` | `def body(self, content: bytes &#124; AsyncIterator[bytes]) -> RequestBuilder` |  | Set raw body content. |
| `json` | `def json(self, data: JsonType) -> RequestBuilder` |  | Set JSON body (automatically sets Content-Type). |
| `form` | `def form(self, data: Mapping[str, Any] &#124; str) -> RequestBuilder` |  | Set form-urlencoded body (automatically sets Content-Type). |
| `multipart` | `def multipart(self, fields: dict[str, str &#124; tuple[str, bytes &#124; BinaryIO, str &#124; None]] &#124; None = None, files: list[tuple[str, tuple[str, bytes &#124; BinaryIO, str &#124; None]]] &#124; None = None) -> RequestBuilder` |  | Set multipart form data with optional files. |
| `cookie` | `def cookie(self, name: str, value: str) -> RequestBuilder` |  | Add a cookie. |
| `cookies` | `def cookies(self, cookies: CookiesType) -> RequestBuilder` |  | Add multiple cookies. |
| `auth_basic` | `def auth_basic(self, username: str, password: str) -> RequestBuilder` |  | Set Basic authentication. |
| `auth_bearer` | `def auth_bearer(self, token: str) -> RequestBuilder` |  | Set Bearer token authentication. |
| `timeout` | `def timeout(self, total: float &#124; None = None, connect: float &#124; None = None, read: float &#124; None = None, write: float &#124; None = None, pool: float &#124; None = None) -> RequestBuilder` |  | Set request-specific timeouts. |
| `follow_redirects` | `def follow_redirects(self, follow: bool = True) -> RequestBuilder` |  | Set redirect following behavior. |
| `extension` | `def extension(self, key: str, value: Any) -> RequestBuilder` |  | Add an extension for interceptors. |
| `build` | `def build(self) -> HTTPClientRequest` |  | Build the final HTTPClientRequest. |

### Class: `HTTPClientResponse`

- Source: `aquilia/http/response.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: HTTP response wrapper.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `status_code` | `int` |  |
| `headers` | `dict[str, str]` |  |
| `url` | `str` |  |
| `http_version` | `str` | `'1.1'` |
| `elapsed` | `float` | `0.0` |
| `request_url` | `str` | `''` |
| `history` | `list[HTTPClientResponse]` | `field(default_factory=list)` |
| `extensions` | `dict[str, Any]` | `field(default_factory=dict)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `reason` | `def reason(self) -> str` | property | HTTP status reason phrase. |
| `is_informational` | `def is_informational(self) -> bool` | property | Check if status is 1xx. |
| `is_success` | `def is_success(self) -> bool` | property | Check if status is 2xx. |
| `is_redirect` | `def is_redirect(self) -> bool` | property | Check if status is 3xx redirect. |
| `is_client_error` | `def is_client_error(self) -> bool` | property | Check if status is 4xx. |
| `is_server_error` | `def is_server_error(self) -> bool` | property | Check if status is 5xx. |
| `is_error` | `def is_error(self) -> bool` | property | Check if status is 4xx or 5xx. |
| `ok` | `def ok(self) -> bool` | property | Check if status indicates success (2xx). |
| `content_type` | `def content_type(self) -> str` | property | Get Content-Type header. |
| `content_length` | `def content_length(self) -> int &#124; None` | property | Get Content-Length header as int. |
| `encoding` | `def encoding(self) -> str` | property | Detect encoding from Content-Type header. |
| `etag` | `def etag(self) -> str &#124; None` | property | Get ETag header. |
| `last_modified` | `def last_modified(self) -> datetime &#124; None` | property | Parse Last-Modified header. |
| `location` | `def location(self) -> str &#124; None` | property | Get Location header (for redirects). |
| `cookies` | `def cookies(self) -> dict[str, str]` | property | Parse Set-Cookie headers into dict. |
| `get_header` | `def get_header(self, name: str, default: str &#124; None = None) -> str &#124; None` |  | Get header by name (case-insensitive). |
| `get_headers` | `def get_headers(self, name: str) -> list[str]` |  | Get all values for a header (for multi-value headers). |
| `read` | `async def read(self) -> bytes` |  | Read entire response body as bytes. |
| `text` | `async def text(self, encoding: str &#124; None = None) -> str` |  | Read response body as text. |
| `json` | `async def json(self) -> Any` |  | Parse response body as JSON. |
| `iter_bytes` | `async def iter_bytes(self, chunk_size: int = 65536) -> AsyncIterator[bytes]` |  | Stream response body in chunks. |
| `iter_text` | `async def iter_text(self, chunk_size: int = 65536, encoding: str &#124; None = None) -> AsyncIterator[str]` |  | Stream response body as text chunks. |
| `iter_lines` | `async def iter_lines(self, encoding: str &#124; None = None, delimiter: str = '\n') -> AsyncIterator[str]` |  | Stream response body line by line. |
| `raise_for_status` | `def raise_for_status(self) -> None` |  | Raise HTTPStatusFault if status is 4xx or 5xx. |
| `close` | `async def close(self) -> None` |  | Close the response and release resources. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize to dictionary (for logging/debugging). |

### Class: `RetryState`

- Source: `aquilia/http/retry.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: State tracking for retry attempts.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `attempt` | `int` | `0` |
| `last_error` | `Exception &#124; None` | `None` |
| `last_response` | `HTTPClientResponse &#124; None` | `None` |
| `total_delay` | `float` | `0.0` |
| `start_time` | `float` | `0.0` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `elapsed` | `def elapsed(self) -> float` | property | Total elapsed time since first attempt. |

### Class: `RetryStrategy`

- Source: `aquilia/http/retry.py`
- Bases: `ABC`
- Summary: Abstract retry strategy.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `should_retry` | `def should_retry(self, state: RetryState, request: HTTPClientRequest, response: HTTPClientResponse &#124; None, error: Exception &#124; None) -> bool` | abstractmethod | Determine if request should be retried. |
| `get_delay` | `def get_delay(self, state: RetryState) -> float` | abstractmethod | Calculate delay before next retry. |

### Class: `ExponentialBackoff`

- Source: `aquilia/http/retry.py`
- Bases: `RetryStrategy`
- Summary: Exponential backoff retry strategy.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `config` | `def config(self) -> RetryConfig` | property | Method. |
| `should_retry` | `def should_retry(self, state: RetryState, request: HTTPClientRequest, response: HTTPClientResponse &#124; None, error: Exception &#124; None) -> bool` |  | Check if retry should be attempted. |
| `get_delay` | `def get_delay(self, state: RetryState) -> float` |  | Calculate exponential backoff delay. |

### Class: `ConstantBackoff`

- Source: `aquilia/http/retry.py`
- Bases: `RetryStrategy`
- Summary: Constant delay retry strategy.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `should_retry` | `def should_retry(self, state: RetryState, request: HTTPClientRequest, response: HTTPClientResponse &#124; None, error: Exception &#124; None) -> bool` |  | Method. |
| `get_delay` | `def get_delay(self, state: RetryState) -> float` |  | Method. |

### Class: `NoRetry`

- Source: `aquilia/http/retry.py`
- Bases: `RetryStrategy`
- Summary: No retry strategy - never retries.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `should_retry` | `def should_retry(self, state: RetryState, request: HTTPClientRequest, response: HTTPClientResponse &#124; None, error: Exception &#124; None) -> bool` |  | Method. |
| `get_delay` | `def get_delay(self, state: RetryState) -> float` |  | Method. |

### Class: `RetryAfterStrategy`

- Source: `aquilia/http/retry.py`
- Bases: `RetryStrategy`
- Summary: Strategy that respects Retry-After header.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `should_retry` | `def should_retry(self, state: RetryState, request: HTTPClientRequest, response: HTTPClientResponse &#124; None, error: Exception &#124; None) -> bool` |  | Method. |
| `get_delay` | `def get_delay(self, state: RetryState) -> float` |  | Method. |

### Class: `CompositeRetryStrategy`

- Source: `aquilia/http/retry.py`
- Bases: `RetryStrategy`
- Summary: Composite strategy combining multiple strategies.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `should_retry` | `def should_retry(self, state: RetryState, request: HTTPClientRequest, response: HTTPClientResponse &#124; None, error: Exception &#124; None) -> bool` |  | Method. |
| `get_delay` | `def get_delay(self, state: RetryState) -> float` |  | Method. |

### Class: `RetryExecutor`

- Source: `aquilia/http/retry.py`
- Bases: `object`
- Summary: Executes operations with retry logic.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `execute` | `async def execute(self, operation: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]], request: HTTPClientRequest) -> HTTPClientResponse` |  | Execute operation with retries. |

### Class: `HTTPSession`

- Source: `aquilia/http/session.py`
- Bases: `object`
- Summary: Persistent HTTP session.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `config` | `def config(self) -> HTTPClientConfig` | property | Get session configuration. |
| `cookies` | `def cookies(self) -> CookieJar` | property | Get session cookie jar. |
| `base_url` | `def base_url(self) -> str &#124; None` | property | Get base URL. |
| `send` | `async def send(self, request: HTTPClientRequest) -> HTTPClientResponse` |  | Send an HTTP request. |
| `request` | `def request(self, method: str &#124; HTTPMethod, url: str, **kwargs: Any) -> RequestBuilder` |  | Create a request builder. |
| `get` | `async def get(self, url: str, *, params: dict[str, Any] &#124; None = None, headers: dict[str, str] &#124; None = None, timeout: float &#124; TimeoutConfig &#124; None = None, **kwargs: Any) -> HTTPClientResponse` |  | Send a GET request. |
| `post` | `async def post(self, url: str, *, params: dict[str, Any] &#124; None = None, headers: dict[str, str] &#124; None = None, json: Any = None, data: dict[str, Any] &#124; str &#124; bytes &#124; None = None, timeout: float &#124; TimeoutConfig &#124; None = None, **kwargs: Any) -> HTTPClientResponse` |  | Send a POST request. |
| `put` | `async def put(self, url: str, *, params: dict[str, Any] &#124; None = None, headers: dict[str, str] &#124; None = None, json: Any = None, data: dict[str, Any] &#124; str &#124; bytes &#124; None = None, timeout: float &#124; TimeoutConfig &#124; None = None, **kwargs: Any) -> HTTPClientResponse` |  | Send a PUT request. |
| `patch` | `async def patch(self, url: str, *, params: dict[str, Any] &#124; None = None, headers: dict[str, str] &#124; None = None, json: Any = None, data: dict[str, Any] &#124; str &#124; bytes &#124; None = None, timeout: float &#124; TimeoutConfig &#124; None = None, **kwargs: Any) -> HTTPClientResponse` |  | Send a PATCH request. |
| `delete` | `async def delete(self, url: str, *, params: dict[str, Any] &#124; None = None, headers: dict[str, str] &#124; None = None, timeout: float &#124; TimeoutConfig &#124; None = None, **kwargs: Any) -> HTTPClientResponse` |  | Send a DELETE request. |
| `head` | `async def head(self, url: str, *, params: dict[str, Any] &#124; None = None, headers: dict[str, str] &#124; None = None, timeout: float &#124; TimeoutConfig &#124; None = None, **kwargs: Any) -> HTTPClientResponse` |  | Send a HEAD request. |
| `options` | `async def options(self, url: str, *, params: dict[str, Any] &#124; None = None, headers: dict[str, str] &#124; None = None, timeout: float &#124; TimeoutConfig &#124; None = None, **kwargs: Any) -> HTTPClientResponse` |  | Send an OPTIONS request. |
| `close` | `async def close(self) -> None` |  | Close the session. |

### Class: `StreamProgress`

- Source: `aquilia/http/streaming.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Progress information for streaming operations.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `bytes_transferred` | `int` |  |
| `total_bytes` | `int &#124; None` |  |
| `elapsed` | `float` |  |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `percentage` | `def percentage(self) -> float &#124; None` | property | Calculate progress percentage (0-100). |
| `bytes_per_second` | `def bytes_per_second(self) -> float` | property | Calculate transfer rate. |
| `eta_seconds` | `def eta_seconds(self) -> float &#124; None` | property | Estimate remaining time in seconds. |

### Class: `StreamingBody`

- Source: `aquilia/http/streaming.py`
- Bases: `object`
- Summary: Streaming request body wrapper.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `content_length` | `def content_length(self) -> int &#124; None` | property | Get content length if known. |

### Class: `BufferedStream`

- Source: `aquilia/http/streaming.py`
- Bases: `object`
- Summary: Buffered async stream reader.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `readline` | `async def readline(self) -> str` |  | Read a single line. |
| `readlines` | `async def readlines(self) -> list[str]` |  | Read all lines. |
| `read` | `async def read(self, n: int = -1) -> bytes` |  | Read up to n bytes (or all if n=-1). |

### Class: `ChunkedEncoder`

- Source: `aquilia/http/streaming.py`
- Bases: `object`
- Summary: HTTP chunked transfer encoding encoder.

### Class: `ChunkedDecoder`

- Source: `aquilia/http/streaming.py`
- Bases: `object`
- Summary: HTTP chunked transfer encoding decoder.

## Functions

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `create_transport` | `aquilia/http/_transport.py` | `def create_transport(config: HTTPClientConfig &#124; None = None) -> HTTPTransport` | Create native HTTP transport. |
| `request` | `aquilia/http/client.py` | `async def request(method: str &#124; HTTPMethod, url: str, **kwargs: Any) -> HTTPClientResponse` | Make a one-off HTTP request. |
| `get` | `aquilia/http/client.py` | `async def get(url: str, **kwargs: Any) -> HTTPClientResponse` | Make a GET request. |
| `post` | `aquilia/http/client.py` | `async def post(url: str, **kwargs: Any) -> HTTPClientResponse` | Make a POST request. |
| `put` | `aquilia/http/client.py` | `async def put(url: str, **kwargs: Any) -> HTTPClientResponse` | Make a PUT request. |
| `patch` | `aquilia/http/client.py` | `async def patch(url: str, **kwargs: Any) -> HTTPClientResponse` | Make a PATCH request. |
| `delete` | `aquilia/http/client.py` | `async def delete(url: str, **kwargs: Any) -> HTTPClientResponse` | Make a DELETE request. |
| `http_client` | `aquilia/http/integration.py` | `def http_client() -> HTTPClientBuilder` | Create HTTP client integration builder. |
| `create_client_from_config` | `aquilia/http/integration.py` | `def create_client_from_config(config: dict[str, Any]) -> AsyncHTTPClient` | Create HTTP client from configuration dictionary. |
| `create_middleware_stack` | `aquilia/http/middleware.py` | `def create_middleware_stack(*, base_url: str &#124; None = None, timeout: float &#124; None = None, headers: dict[str, str] &#124; None = None, enable_logging: bool = False, enable_retry: bool = False, enable_cache: bool = False, enable_cookies: bool = False, raise_for_status: bool = False) -> list[HTTPClientMiddleware]` | Create a standard middleware stack. |
| `get` | `aquilia/http/request.py` | `def get(url: str, **kwargs: Any) -> RequestBuilder` | Create a GET request builder. |
| `post` | `aquilia/http/request.py` | `def post(url: str, **kwargs: Any) -> RequestBuilder` | Create a POST request builder. |
| `put` | `aquilia/http/request.py` | `def put(url: str, **kwargs: Any) -> RequestBuilder` | Create a PUT request builder. |
| `patch` | `aquilia/http/request.py` | `def patch(url: str, **kwargs: Any) -> RequestBuilder` | Create a PATCH request builder. |
| `delete` | `aquilia/http/request.py` | `def delete(url: str, **kwargs: Any) -> RequestBuilder` | Create a DELETE request builder. |
| `head` | `aquilia/http/request.py` | `def head(url: str, **kwargs: Any) -> RequestBuilder` | Create a HEAD request builder. |
| `options` | `aquilia/http/request.py` | `def options(url: str, **kwargs: Any) -> RequestBuilder` | Create an OPTIONS request builder. |
| `create_response` | `aquilia/http/response.py` | `def create_response(status_code: int, headers: dict[str, str] &#124; list[tuple[str, str]] &#124; None = None, *, body: bytes &#124; None = None, stream: AsyncIterator[bytes] &#124; None = None, url: str = '', http_version: str = '1.1', elapsed: float = 0.0, request_url: str = '', history: list[HTTPClientResponse] &#124; None = None, extensions: dict[str, Any] &#124; None = None) -> HTTPClientResponse` | Factory function to create HTTPClientResponse. |
| `create_retry_strategy` | `aquilia/http/retry.py` | `def create_retry_strategy(config: RetryConfig &#124; None = None) -> RetryStrategy` | Create a retry strategy from configuration. |
| `stream_file` | `aquilia/http/streaming.py` | `async def stream_file(path: Path &#124; str, *, chunk_size: int = 65536) -> AsyncIterator[bytes]` | Stream a file asynchronously. |
| `stream_bytes` | `aquilia/http/streaming.py` | `async def stream_bytes(data: bytes, chunk_size: int = 65536) -> AsyncIterator[bytes]` | Stream bytes in chunks. |
| `collect_stream` | `aquilia/http/streaming.py` | `async def collect_stream(stream: AsyncIterator[bytes]) -> bytes` | Collect all bytes from an async iterator. |
| `stream_with_limit` | `aquilia/http/streaming.py` | `async def stream_with_limit(stream: AsyncIterator[bytes], max_bytes: int) -> AsyncIterator[bytes]` | Stream with a byte limit. |

## Constants

| Name | Source | Value or type |
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
| `HTTP_STATUS_REASONS` | `aquilia/http/response.py` | `{100: 'Continue', 101: 'Switching Protocols', 102: 'Processing', 103: 'Early Hints', 200: 'OK', 201: 'Created', 202: 'Accepted', 203: 'Non-Authoritative Informa` |
| `T` | `aquilia/http/retry.py` | `TypeVar('T')` |

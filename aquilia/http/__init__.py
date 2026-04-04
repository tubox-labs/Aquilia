"""
AquilaHTTP — Async HTTP Client for Aquilia.

A fully asynchronous, modern HTTP client library deeply integrated
with the Aquilia framework.

Features:
- Async-native request/response handling
- Connection pooling with per-host limits
- Automatic cookie management
- Request/response interceptors
- Composable middleware
- Retry strategies with exponential backoff
- Streaming request/response bodies
- Multipart form data with file uploads
- Multiple authentication schemes
- TLS/SSL configuration
- Full timeout control
- DI integration

Example:
    ```python
    from aquilia.http import AsyncHTTPClient

    async with AsyncHTTPClient() as client:
        # Simple GET
        response = await client.get("https://api.example.com/users")
        users = await response.json()

        # POST with JSON
        response = await client.post(
            "https://api.example.com/users",
            json={"name": "John", "email": "john@example.com"},
        )

        # With authentication
        response = await client.get(
            "https://api.example.com/me",
            headers={"Authorization": "Bearer token"},
        )

        # Streaming
        async for chunk in client.stream("GET", "https://example.com/large-file"):
            process(chunk)
    ```
"""

# Core client
# Transport (internal, but exported for testing)
from ._transport import (
    AIOHTTP_AVAILABLE,
    AIOHTTPTransport,
    HTTPTransport,
    MockTransport,
    NativeTransport,
    create_transport,
)

# Authentication
from .auth import (
    APIKeyAuth,
    AuthInterceptor,
    AWSSignatureV4Auth,
    BasicAuth,
    BearerAuth,
    DigestAuth,
    OAuth2Auth,
    OAuth2Token,
)
from .client import (
    AsyncHTTPClient,
    delete,
    get,
    patch,
    post,
    put,
    request,
)

# Configuration
from .config import (
    CompressionAlgorithm,
    HTTPClientConfig,
    HTTPVersion,
    PoolConfig,
    ProxyConfig,
    RetryConfig,
    TimeoutConfig,
    TLSConfig,
)

# Cookies
from .cookies import (
    Cookie,
    CookieInterceptor,
    CookieJar,
)

# Faults
from .faults import (
    HTTP_CLIENT_DOMAIN,
    CertificateVerifyFault,
    ClientErrorFault,
    ConfigurationFault,
    ConnectionClosedFault,
    ConnectionFault,
    ConnectionPoolExhaustedFault,
    ConnectTimeoutFault,
    DecodingFault,
    HTTPClientFault,
    HTTPStatusFault,
    InvalidHeaderFault,
    InvalidResponseFault,
    InvalidURLFault,
    ProxyFault,
    ReadTimeoutFault,
    RequestBuildFault,
    RequestTimeoutFault,
    ResponseFault,
    RetryExhaustedFault,
    ServerErrorFault,
    TimeoutFault,
    TLSFault,
    TooManyRedirectsFault,
    TransportFault,
    WriteTimeoutFault,
)

# Integration
from .integration import (
    HTTPClientBuilder,
    HTTPClientProvider,
    create_client_from_config,
    http_client,
)

# Interceptors
from .interceptors import (
    AcceptInterceptor,
    CacheInterceptor,
    HeaderInterceptor,
    HTTPInterceptor,
    InterceptorChain,
    LoggingInterceptor,
    MetricsInterceptor,
    RedirectInterceptor,
    RequestMetrics,
    TimeoutInterceptor,
    UserAgentInterceptor,
)

# Middleware
from .middleware import (
    BaseURLMiddleware,
    CacheMiddleware,
    CompressionMiddleware,
    CookieMiddleware,
    ErrorHandlingMiddleware,
    HeadersMiddleware,
    HTTPClientMiddleware,
    LoggingMiddleware,
    MiddlewareStack,
    RetryMiddleware,
    TimeoutMiddleware,
    create_middleware_stack,
)

# Multipart
from .multipart import (
    FormField,
    FormFile,
    MultipartFormData,
)

# Connection pool
from .pool import (
    ConnectionPool,
    ConnectionPoolManager,
    ConnectionStats,
    PooledConnection,
)

# Request/Response
from .request import (
    HTTPClientRequest,
    HTTPMethod,
    RequestBuilder,
)
from .request import (
    delete as delete_request,
)
from .request import (
    get as get_request,
)
from .request import (
    head as head_request,
)
from .request import (
    options as options_request,
)
from .request import (
    patch as patch_request,
)
from .request import (
    post as post_request,
)
from .request import (
    put as put_request,
)
from .response import (
    HTTP_STATUS_REASONS,
    HTTPClientResponse,
    create_response,
)

# Retry
from .retry import (
    CompositeRetryStrategy,
    ConstantBackoff,
    ExponentialBackoff,
    NoRetry,
    RetryAfterStrategy,
    RetryExecutor,
    RetryState,
    RetryStrategy,
    create_retry_strategy,
)

# Session
from .session import HTTPSession

# Streaming
from .streaming import (
    BufferedStream,
    ChunkedDecoder,
    ChunkedEncoder,
    StreamingBody,
    StreamProgress,
    collect_stream,
    stream_bytes,
    stream_file,
    stream_with_limit,
)

__all__ = [
    # Client
    "AsyncHTTPClient",
    "HTTPSession",
    "request",
    "get",
    "post",
    "put",
    "patch",
    "delete",
    # Config
    "HTTPClientConfig",
    "TimeoutConfig",
    "PoolConfig",
    "RetryConfig",
    "ProxyConfig",
    "TLSConfig",
    "HTTPVersion",
    "CompressionAlgorithm",
    # Request/Response
    "HTTPClientRequest",
    "HTTPClientResponse",
    "HTTPMethod",
    "RequestBuilder",
    "create_response",
    "HTTP_STATUS_REASONS",
    # Convenience request builders
    "get_request",
    "post_request",
    "put_request",
    "patch_request",
    "delete_request",
    "head_request",
    "options_request",
    # Cookies
    "Cookie",
    "CookieJar",
    "CookieInterceptor",
    # Faults
    "HTTP_CLIENT_DOMAIN",
    "HTTPClientFault",
    "ConnectionFault",
    "ConnectionPoolExhaustedFault",
    "ConnectionClosedFault",
    "TimeoutFault",
    "ConnectTimeoutFault",
    "ReadTimeoutFault",
    "WriteTimeoutFault",
    "RequestTimeoutFault",
    "TLSFault",
    "CertificateVerifyFault",
    "ResponseFault",
    "InvalidResponseFault",
    "DecodingFault",
    "HTTPStatusFault",
    "ClientErrorFault",
    "ServerErrorFault",
    "TooManyRedirectsFault",
    "RequestBuildFault",
    "InvalidURLFault",
    "InvalidHeaderFault",
    "TransportFault",
    "ProxyFault",
    "RetryExhaustedFault",
    "ConfigurationFault",
    # Interceptors
    "HTTPInterceptor",
    "InterceptorChain",
    "LoggingInterceptor",
    "HeaderInterceptor",
    "UserAgentInterceptor",
    "AcceptInterceptor",
    "MetricsInterceptor",
    "RequestMetrics",
    "TimeoutInterceptor",
    "RedirectInterceptor",
    "CacheInterceptor",
    # Middleware
    "HTTPClientMiddleware",
    "MiddlewareStack",
    "LoggingMiddleware",
    "HeadersMiddleware",
    "TimeoutMiddleware",
    "ErrorHandlingMiddleware",
    "RetryMiddleware",
    "CompressionMiddleware",
    "CacheMiddleware",
    "BaseURLMiddleware",
    "CookieMiddleware",
    "create_middleware_stack",
    # Multipart
    "MultipartFormData",
    "FormField",
    "FormFile",
    # Retry
    "RetryStrategy",
    "RetryState",
    "ExponentialBackoff",
    "ConstantBackoff",
    "NoRetry",
    "RetryAfterStrategy",
    "CompositeRetryStrategy",
    "RetryExecutor",
    "create_retry_strategy",
    # Streaming
    "StreamingBody",
    "StreamProgress",
    "BufferedStream",
    "ChunkedEncoder",
    "ChunkedDecoder",
    "stream_file",
    "stream_bytes",
    "collect_stream",
    "stream_with_limit",
    # Authentication
    "AuthInterceptor",
    "BasicAuth",
    "BearerAuth",
    "APIKeyAuth",
    "DigestAuth",
    "OAuth2Auth",
    "OAuth2Token",
    "AWSSignatureV4Auth",
    # Pool
    "ConnectionPool",
    "ConnectionPoolManager",
    "PooledConnection",
    "ConnectionStats",
    # Integration
    "HTTPClientProvider",
    "HTTPClientBuilder",
    "http_client",
    "create_client_from_config",
    # Transport
    "HTTPTransport",
    "NativeTransport",
    "AIOHTTPTransport",
    "MockTransport",
    "create_transport",
    "AIOHTTP_AVAILABLE",
]

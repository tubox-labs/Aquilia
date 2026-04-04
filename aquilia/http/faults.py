"""
AquilaHTTP — Fault Classes.

Typed, structured fault classes for the async HTTP client system.
Replaces raw exceptions with first-class Aquilia Fault objects.

Domains:
    HTTP_CLIENT — HTTP client request/response, connection, and transport faults.
"""

from __future__ import annotations

from typing import Any

from aquilia.faults.core import Fault, FaultDomain, Severity

# ============================================================================
# Domain
# ============================================================================

HTTP_CLIENT_DOMAIN = FaultDomain.custom("http_client", "HTTP client faults")


# ============================================================================
# Base
# ============================================================================


class HTTPClientFault(Fault):
    """Base fault for the HTTP client subsystem."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        severity: Severity = Severity.ERROR,
        retryable: bool = False,
        public: bool = False,
        metadata: dict[str, Any] | None = None,
    ):
        super().__init__(
            code=code,
            message=message,
            domain=HTTP_CLIENT_DOMAIN,
            severity=severity,
            retryable=retryable,
            public=public,
            metadata=metadata,
        )


# ============================================================================
# Connection Faults
# ============================================================================


class ConnectionFault(HTTPClientFault):
    """
    Failed to establish connection to remote host.

    Raised when the client cannot connect to the target server,
    including DNS resolution failures, connection refused, network unreachable.
    """

    def __init__(
        self,
        message: str,
        *,
        url: str = "",
        host: str = "",
        port: int | None = None,
        cause: str = "",
        **kwargs,
    ):
        metadata = {
            "url": url,
            "host": host,
            "port": port,
            "cause": cause,
            **kwargs.get("metadata", {}),
        }
        super().__init__(
            code="HTTP_CONNECTION_FAILED",
            message=message,
            severity=Severity.ERROR,
            retryable=True,
            metadata=metadata,
        )


class ConnectionPoolExhaustedFault(HTTPClientFault):
    """
    Connection pool exhausted.

    Raised when the connection pool has no available connections
    and the maximum pool size has been reached.
    """

    def __init__(
        self,
        message: str = "Connection pool exhausted",
        *,
        pool_size: int = 0,
        active_connections: int = 0,
        **kwargs,
    ):
        metadata = {
            "pool_size": pool_size,
            "active_connections": active_connections,
            **kwargs.get("metadata", {}),
        }
        super().__init__(
            code="HTTP_POOL_EXHAUSTED",
            message=message,
            severity=Severity.WARN,
            retryable=True,
            metadata=metadata,
        )


class ConnectionClosedFault(HTTPClientFault):
    """
    Connection was unexpectedly closed.

    Raised when the server closes the connection during a request,
    or when a keepalive connection becomes stale.
    """

    def __init__(
        self,
        message: str = "Connection closed unexpectedly",
        *,
        url: str = "",
        **kwargs,
    ):
        metadata = {"url": url, **kwargs.get("metadata", {})}
        super().__init__(
            code="HTTP_CONNECTION_CLOSED",
            message=message,
            severity=Severity.WARN,
            retryable=True,
            metadata=metadata,
        )


# ============================================================================
# Timeout Faults
# ============================================================================


class TimeoutFault(HTTPClientFault):
    """
    Request timed out.

    Base class for all timeout-related faults.
    """

    def __init__(
        self,
        code: str,
        message: str,
        *,
        timeout: float = 0.0,
        url: str = "",
        **kwargs,
    ):
        metadata = {
            "timeout": timeout,
            "url": url,
            **kwargs.get("metadata", {}),
        }
        super().__init__(
            code=code,
            message=message,
            severity=Severity.WARN,
            retryable=True,
            metadata=metadata,
        )


class ConnectTimeoutFault(TimeoutFault):
    """
    Connection timeout.

    Raised when the client cannot establish a connection
    within the configured connect timeout.
    """

    def __init__(
        self,
        message: str = "Connection timed out",
        *,
        timeout: float = 0.0,
        url: str = "",
        **kwargs,
    ):
        super().__init__(
            code="HTTP_CONNECT_TIMEOUT",
            message=message,
            timeout=timeout,
            url=url,
            **kwargs,
        )


class ReadTimeoutFault(TimeoutFault):
    """
    Read timeout.

    Raised when the client does not receive data from the server
    within the configured read timeout.
    """

    def __init__(
        self,
        message: str = "Read timed out",
        *,
        timeout: float = 0.0,
        url: str = "",
        **kwargs,
    ):
        super().__init__(
            code="HTTP_READ_TIMEOUT",
            message=message,
            timeout=timeout,
            url=url,
            **kwargs,
        )


class WriteTimeoutFault(TimeoutFault):
    """
    Write timeout.

    Raised when the client cannot send data to the server
    within the configured write timeout.
    """

    def __init__(
        self,
        message: str = "Write timed out",
        *,
        timeout: float = 0.0,
        url: str = "",
        **kwargs,
    ):
        super().__init__(
            code="HTTP_WRITE_TIMEOUT",
            message=message,
            timeout=timeout,
            url=url,
            **kwargs,
        )


class RequestTimeoutFault(TimeoutFault):
    """
    Total request timeout.

    Raised when the entire request (connect + send + receive)
    exceeds the configured total timeout.
    """

    def __init__(
        self,
        message: str = "Request timed out",
        *,
        timeout: float = 0.0,
        url: str = "",
        **kwargs,
    ):
        super().__init__(
            code="HTTP_REQUEST_TIMEOUT",
            message=message,
            timeout=timeout,
            url=url,
            **kwargs,
        )


# ============================================================================
# TLS/SSL Faults
# ============================================================================


class TLSFault(HTTPClientFault):
    """
    TLS/SSL error.

    Raised on TLS handshake failures, certificate validation errors,
    or other SSL-related issues.
    """

    def __init__(
        self,
        message: str,
        *,
        url: str = "",
        reason: str = "",
        **kwargs,
    ):
        metadata = {
            "url": url,
            "reason": reason,
            **kwargs.get("metadata", {}),
        }
        super().__init__(
            code="HTTP_TLS_ERROR",
            message=message,
            severity=Severity.ERROR,
            retryable=False,
            metadata=metadata,
        )


class CertificateVerifyFault(TLSFault):
    """
    Certificate verification failed.

    Raised when the server's SSL certificate cannot be verified
    against the trust store.
    """

    def __init__(
        self,
        message: str = "Certificate verification failed",
        *,
        url: str = "",
        reason: str = "",
        **kwargs,
    ):
        super().__init__(
            message=message,
            url=url,
            reason=reason,
            **kwargs,
        )
        self.code = "HTTP_CERTIFICATE_VERIFY_FAILED"


# ============================================================================
# Response Faults
# ============================================================================


class ResponseFault(HTTPClientFault):
    """
    Response processing error.

    Base class for response-related faults.
    """

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = 0,
        url: str = "",
        **kwargs,
    ):
        metadata = {
            "status_code": status_code,
            "url": url,
            **kwargs.get("metadata", {}),
        }
        super().__init__(
            code=code,
            message=message,
            severity=Severity.ERROR,
            retryable=False,
            metadata=metadata,
        )


class InvalidResponseFault(ResponseFault):
    """
    Invalid response received.

    Raised when the response cannot be parsed or is malformed.
    """

    def __init__(
        self,
        message: str = "Invalid response",
        *,
        status_code: int = 0,
        url: str = "",
        reason: str = "",
        **kwargs,
    ):
        super().__init__(
            code="HTTP_INVALID_RESPONSE",
            message=message,
            status_code=status_code,
            url=url,
            **kwargs,
        )
        self.metadata["reason"] = reason


class DecodingFault(ResponseFault):
    """
    Response body decoding error.

    Raised when the response body cannot be decoded
    (e.g., invalid JSON, wrong charset).
    """

    def __init__(
        self,
        message: str = "Failed to decode response body",
        *,
        status_code: int = 0,
        url: str = "",
        content_type: str = "",
        encoding: str = "",
        **kwargs,
    ):
        super().__init__(
            code="HTTP_DECODING_ERROR",
            message=message,
            status_code=status_code,
            url=url,
            **kwargs,
        )
        self.metadata["content_type"] = content_type
        self.metadata["encoding"] = encoding


class HTTPStatusFault(ResponseFault):
    """
    HTTP error status received.

    Raised when the server returns a 4xx or 5xx status code.
    Can be subclassed for specific status ranges.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        url: str = "",
        reason: str = "",
        body: str = "",
        **kwargs,
    ):
        # Determine retryability based on status code
        # 5xx errors are generally retryable, 4xx are not
        retryable = status_code >= 500 and status_code < 600
        if status_code == 429:  # Too Many Requests
            retryable = True

        super().__init__(
            code=f"HTTP_{status_code}",
            message=message,
            status_code=status_code,
            url=url,
            **kwargs,
        )
        self.metadata["reason"] = reason
        self.metadata["body"] = body[:1000] if body else ""  # Truncate for safety
        self.retryable = retryable


class ClientErrorFault(HTTPStatusFault):
    """
    HTTP 4xx client error.

    Raised for 4xx status codes indicating client-side issues.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        url: str = "",
        reason: str = "",
        body: str = "",
        **kwargs,
    ):
        if not (400 <= status_code < 500):
            status_code = 400
        super().__init__(
            message=message,
            status_code=status_code,
            url=url,
            reason=reason,
            body=body,
            **kwargs,
        )
        self.severity = Severity.WARN
        self.retryable = False


class ServerErrorFault(HTTPStatusFault):
    """
    HTTP 5xx server error.

    Raised for 5xx status codes indicating server-side issues.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        url: str = "",
        reason: str = "",
        body: str = "",
        **kwargs,
    ):
        if not (500 <= status_code < 600):
            status_code = 500
        super().__init__(
            message=message,
            status_code=status_code,
            url=url,
            reason=reason,
            body=body,
            **kwargs,
        )
        self.severity = Severity.ERROR
        self.retryable = True


class TooManyRedirectsFault(HTTPClientFault):
    """
    Too many redirects.

    Raised when the maximum number of redirects is exceeded.
    """

    def __init__(
        self,
        message: str = "Too many redirects",
        *,
        max_redirects: int = 0,
        url: str = "",
        redirect_chain: list[str] | None = None,
        **kwargs,
    ):
        metadata = {
            "max_redirects": max_redirects,
            "url": url,
            "redirect_chain": redirect_chain or [],
            **kwargs.get("metadata", {}),
        }
        super().__init__(
            code="HTTP_TOO_MANY_REDIRECTS",
            message=message,
            severity=Severity.WARN,
            retryable=False,
            metadata=metadata,
        )


# ============================================================================
# Request Faults
# ============================================================================


class RequestBuildFault(HTTPClientFault):
    """
    Request construction error.

    Raised when the request cannot be built due to invalid parameters.
    """

    def __init__(
        self,
        message: str,
        *,
        field: str = "",
        value: Any = None,
        **kwargs,
    ):
        metadata = {
            "field": field,
            "value": str(value) if value is not None else None,
            **kwargs.get("metadata", {}),
        }
        super().__init__(
            code="HTTP_REQUEST_BUILD_ERROR",
            message=message,
            severity=Severity.ERROR,
            retryable=False,
            metadata=metadata,
        )


class InvalidURLFault(RequestBuildFault):
    """
    Invalid URL.

    Raised when the URL is malformed or contains invalid characters.
    """

    def __init__(
        self,
        message: str = "Invalid URL",
        *,
        url: str = "",
        **kwargs,
    ):
        super().__init__(
            message=message,
            field="url",
            value=url,
            **kwargs,
        )
        self.code = "HTTP_INVALID_URL"


class InvalidHeaderFault(RequestBuildFault):
    """
    Invalid header.

    Raised when a header name or value is invalid.
    """

    def __init__(
        self,
        message: str = "Invalid header",
        *,
        header_name: str = "",
        header_value: str = "",
        **kwargs,
    ):
        super().__init__(
            message=message,
            field="header",
            value=f"{header_name}: {header_value}",
            **kwargs,
        )
        self.code = "HTTP_INVALID_HEADER"
        self.metadata["header_name"] = header_name


# ============================================================================
# Transport Faults
# ============================================================================


class TransportFault(HTTPClientFault):
    """
    Low-level transport error.

    Raised for transport-layer issues not covered by other faults.
    """

    def __init__(
        self,
        message: str,
        *,
        url: str = "",
        cause: str = "",
        **kwargs,
    ):
        metadata = {
            "url": url,
            "cause": cause,
            **kwargs.get("metadata", {}),
        }
        super().__init__(
            code="HTTP_TRANSPORT_ERROR",
            message=message,
            severity=Severity.ERROR,
            retryable=True,
            metadata=metadata,
        )


class ProxyFault(TransportFault):
    """
    Proxy connection error.

    Raised when connecting through a proxy fails.
    """

    def __init__(
        self,
        message: str = "Proxy connection failed",
        *,
        proxy_url: str = "",
        url: str = "",
        **kwargs,
    ):
        super().__init__(
            message=message,
            url=url,
            **kwargs,
        )
        self.code = "HTTP_PROXY_ERROR"
        self.metadata["proxy_url"] = proxy_url


# ============================================================================
# Retry Faults
# ============================================================================


class RetryExhaustedFault(HTTPClientFault):
    """
    All retry attempts exhausted.

    Raised when all configured retry attempts have been used
    without success.
    """

    def __init__(
        self,
        message: str = "All retry attempts exhausted",
        *,
        attempts: int = 0,
        last_error: str = "",
        url: str = "",
        **kwargs,
    ):
        metadata = {
            "attempts": attempts,
            "last_error": last_error,
            "url": url,
            **kwargs.get("metadata", {}),
        }
        super().__init__(
            code="HTTP_RETRY_EXHAUSTED",
            message=message,
            severity=Severity.ERROR,
            retryable=False,
            metadata=metadata,
        )


# ============================================================================
# Configuration Faults
# ============================================================================


class ConfigurationFault(HTTPClientFault):
    """
    HTTP client configuration error.

    Raised when the client is misconfigured.
    """

    def __init__(
        self,
        message: str,
        *,
        setting: str = "",
        value: Any = None,
        **kwargs,
    ):
        metadata = {
            "setting": setting,
            "value": str(value) if value is not None else None,
            **kwargs.get("metadata", {}),
        }
        super().__init__(
            code="HTTP_CONFIG_ERROR",
            message=message,
            severity=Severity.FATAL,
            retryable=False,
            metadata=metadata,
        )

"""
AquilaHTTP — Configuration.

Dataclass-based configuration for the HTTP client with sensible defaults.
Integrates with Aquilia's config system (AquilaConfig, pyconfig).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from ssl import SSLContext
from typing import Any


class HTTPVersion(str, Enum):
    """Supported HTTP versions."""

    HTTP_1_0 = "1.0"
    HTTP_1_1 = "1.1"
    HTTP_2 = "2"
    AUTO = "auto"


class CompressionAlgorithm(str, Enum):
    """Supported compression algorithms for Accept-Encoding."""

    GZIP = "gzip"
    DEFLATE = "deflate"
    BR = "br"
    ZSTD = "zstd"
    IDENTITY = "identity"


@dataclass(frozen=True, slots=True)
class TimeoutConfig:
    """
    HTTP request timeout configuration.

    All values are in seconds. Set to 0 or None to disable.

    Attributes:
        total: Total timeout for the entire request lifecycle.
        connect: Timeout for establishing a connection.
        read: Timeout for reading response data.
        write: Timeout for writing request data.
        pool: Timeout for acquiring a connection from the pool.
    """

    total: float | None = 30.0
    connect: float | None = 10.0
    read: float | None = None  # Inherit from total if None
    write: float | None = None  # Inherit from total if None
    pool: float | None = 5.0

    def __post_init__(self) -> None:
        # Validate non-negative
        for name in ("total", "connect", "read", "write", "pool"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"Timeout {name} cannot be negative: {value}")

    @classmethod
    def no_timeout(cls) -> TimeoutConfig:
        """Create a configuration with no timeouts (infinite wait)."""
        return cls(total=None, connect=None, read=None, write=None, pool=None)

    @classmethod
    def fast(cls) -> TimeoutConfig:
        """Create a fast timeout configuration for quick requests."""
        return cls(total=5.0, connect=2.0, read=5.0, write=5.0, pool=2.0)

    @classmethod
    def slow(cls) -> TimeoutConfig:
        """Create a slow timeout configuration for long-running requests."""
        return cls(total=300.0, connect=30.0, read=300.0, write=300.0, pool=30.0)


@dataclass(frozen=True, slots=True)
class PoolConfig:
    """
    Connection pool configuration.

    Attributes:
        max_connections: Maximum total connections across all hosts.
        max_connections_per_host: Maximum connections per host.
        max_keepalive_connections: Maximum idle keepalive connections.
        keepalive_expiry: Seconds to keep idle connections alive.
        enable_http2: Whether to enable HTTP/2 support.
    """

    max_connections: int = 100
    max_connections_per_host: int = 10
    max_keepalive_connections: int = 20
    keepalive_expiry: float = 60.0
    enable_http2: bool = False

    def __post_init__(self) -> None:
        if self.max_connections < 1:
            raise ValueError(f"max_connections must be >= 1: {self.max_connections}")
        if self.max_connections_per_host < 1:
            raise ValueError(f"max_connections_per_host must be >= 1: {self.max_connections_per_host}")
        if self.keepalive_expiry < 0:
            raise ValueError(f"keepalive_expiry cannot be negative: {self.keepalive_expiry}")


@dataclass(frozen=True, slots=True)
class RetryConfig:
    """
    Retry configuration.

    Attributes:
        max_attempts: Maximum number of retry attempts (0 = no retries).
        backoff_base: Base delay between retries (seconds).
        backoff_multiplier: Multiplier applied to backoff for each retry.
        backoff_max: Maximum backoff delay (seconds).
        backoff_jitter: Random jitter factor (0-1) added to backoff.
        retry_on_status: Status codes that trigger a retry.
        retry_on_methods: HTTP methods that are safe to retry.
    """

    max_attempts: int = 3
    backoff_base: float = 1.0
    backoff_multiplier: float = 2.0
    backoff_max: float = 60.0
    backoff_jitter: float = 0.1
    retry_on_status: frozenset[int] = field(default_factory=lambda: frozenset({429, 500, 502, 503, 504}))
    retry_on_methods: frozenset[str] = field(
        default_factory=lambda: frozenset({"GET", "HEAD", "OPTIONS", "PUT", "DELETE"})
    )

    def __post_init__(self) -> None:
        if self.max_attempts < 0:
            raise ValueError(f"max_attempts cannot be negative: {self.max_attempts}")
        if self.backoff_base < 0:
            raise ValueError(f"backoff_base cannot be negative: {self.backoff_base}")
        if self.backoff_multiplier < 1:
            raise ValueError(f"backoff_multiplier must be >= 1: {self.backoff_multiplier}")
        if self.backoff_max < 0:
            raise ValueError(f"backoff_max cannot be negative: {self.backoff_max}")
        if not 0 <= self.backoff_jitter <= 1:
            raise ValueError(f"backoff_jitter must be between 0 and 1: {self.backoff_jitter}")

    @classmethod
    def no_retry(cls) -> RetryConfig:
        """Create a configuration with no retries."""
        return cls(max_attempts=0)

    @classmethod
    def aggressive(cls) -> RetryConfig:
        """Create an aggressive retry configuration."""
        return cls(
            max_attempts=5,
            backoff_base=0.5,
            backoff_multiplier=2.0,
            backoff_max=30.0,
            backoff_jitter=0.2,
        )


@dataclass(frozen=True, slots=True)
class ProxyConfig:
    """
    Proxy configuration.

    Attributes:
        http_proxy: Proxy URL for HTTP requests.
        https_proxy: Proxy URL for HTTPS requests.
        no_proxy: Comma-separated list of hosts to bypass proxy.
    """

    http_proxy: str | None = None
    https_proxy: str | None = None
    no_proxy: str | None = None

    @classmethod
    def from_env(cls) -> ProxyConfig:
        """Create proxy config from environment variables."""
        import os

        return cls(
            http_proxy=os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy"),
            https_proxy=os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy"),
            no_proxy=os.environ.get("NO_PROXY") or os.environ.get("no_proxy"),
        )


@dataclass(frozen=True, slots=True)
class TLSConfig:
    """
    TLS/SSL configuration.

    Attributes:
        verify: Whether to verify SSL certificates.
        cert_file: Path to client certificate file.
        key_file: Path to client key file.
        ca_bundle: Path to CA bundle file.
        ssl_context: Custom SSL context (overrides other settings).
        minimum_version: Minimum TLS version (e.g., TLSv1.2).
    """

    verify: bool = True
    cert_file: str | None = None
    key_file: str | None = None
    ca_bundle: str | None = None
    ssl_context: SSLContext | None = None
    minimum_version: str | None = None  # e.g., "TLSv1.2", "TLSv1.3"


@dataclass(slots=True)
class HTTPClientConfig:
    """
    Complete HTTP client configuration.

    Combines all configuration aspects into a single dataclass.

    Attributes:
        base_url: Base URL prepended to all requests.
        timeout: Timeout configuration.
        pool: Connection pool configuration.
        retry: Retry configuration.
        proxy: Proxy configuration.
        tls: TLS/SSL configuration.
        http_version: HTTP version to use.
        follow_redirects: Whether to follow redirects.
        max_redirects: Maximum number of redirects to follow.
        default_headers: Default headers for all requests.
        default_params: Default query parameters for all requests.
        compression: Accepted compression algorithms.
        trust_env: Whether to read proxy settings from environment.
        raise_for_status: Raise HTTPStatusFault for 4xx/5xx responses.
        user_agent: User-Agent header value.
    """

    base_url: str | None = None
    timeout: TimeoutConfig = field(default_factory=TimeoutConfig)
    pool: PoolConfig = field(default_factory=PoolConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    proxy: ProxyConfig | None = None
    tls: TLSConfig = field(default_factory=TLSConfig)
    http_version: HTTPVersion = HTTPVersion.AUTO
    follow_redirects: bool = True
    max_redirects: int = 10
    default_headers: dict[str, str] = field(default_factory=dict)
    default_params: dict[str, str] = field(default_factory=dict)
    compression: tuple[CompressionAlgorithm, ...] = (
        CompressionAlgorithm.GZIP,
        CompressionAlgorithm.DEFLATE,
    )
    trust_env: bool = True
    raise_for_status: bool = False
    user_agent: str = "Aquilia-HTTP/1.0"

    def __post_init__(self) -> None:
        # Validate max_redirects
        if self.max_redirects < 0:
            raise ValueError(f"max_redirects cannot be negative: {self.max_redirects}")

        # Auto-load proxy from env if enabled and not set
        if self.trust_env and self.proxy is None:
            self.proxy = ProxyConfig.from_env()

    def with_base_url(self, url: str) -> HTTPClientConfig:
        """Return a copy with a different base URL."""
        return HTTPClientConfig(
            base_url=url,
            timeout=self.timeout,
            pool=self.pool,
            retry=self.retry,
            proxy=self.proxy,
            tls=self.tls,
            http_version=self.http_version,
            follow_redirects=self.follow_redirects,
            max_redirects=self.max_redirects,
            default_headers=dict(self.default_headers),
            default_params=dict(self.default_params),
            compression=self.compression,
            trust_env=self.trust_env,
            raise_for_status=self.raise_for_status,
            user_agent=self.user_agent,
        )

    def with_timeout(self, **kwargs: Any) -> HTTPClientConfig:
        """Return a copy with modified timeout settings."""
        current = {
            "total": self.timeout.total,
            "connect": self.timeout.connect,
            "read": self.timeout.read,
            "write": self.timeout.write,
            "pool": self.timeout.pool,
        }
        current.update(kwargs)
        return HTTPClientConfig(
            base_url=self.base_url,
            timeout=TimeoutConfig(**current),
            pool=self.pool,
            retry=self.retry,
            proxy=self.proxy,
            tls=self.tls,
            http_version=self.http_version,
            follow_redirects=self.follow_redirects,
            max_redirects=self.max_redirects,
            default_headers=dict(self.default_headers),
            default_params=dict(self.default_params),
            compression=self.compression,
            trust_env=self.trust_env,
            raise_for_status=self.raise_for_status,
            user_agent=self.user_agent,
        )

    def merge_headers(self, headers: dict[str, str] | None) -> dict[str, str]:
        """Merge default headers with request-specific headers."""
        result = dict(self.default_headers)
        if headers:
            result.update(headers)
        return result

    def merge_params(self, params: dict[str, str] | None) -> dict[str, str]:
        """Merge default params with request-specific params."""
        result = dict(self.default_params)
        if params:
            result.update(params)
        return result

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "base_url": self.base_url,
            "timeout": {
                "total": self.timeout.total,
                "connect": self.timeout.connect,
                "read": self.timeout.read,
                "write": self.timeout.write,
                "pool": self.timeout.pool,
            },
            "pool": {
                "max_connections": self.pool.max_connections,
                "max_connections_per_host": self.pool.max_connections_per_host,
                "max_keepalive_connections": self.pool.max_keepalive_connections,
                "keepalive_expiry": self.pool.keepalive_expiry,
                "enable_http2": self.pool.enable_http2,
            },
            "retry": {
                "max_attempts": self.retry.max_attempts,
                "backoff_base": self.retry.backoff_base,
                "backoff_multiplier": self.retry.backoff_multiplier,
                "backoff_max": self.retry.backoff_max,
                "backoff_jitter": self.retry.backoff_jitter,
                "retry_on_status": list(self.retry.retry_on_status),
                "retry_on_methods": list(self.retry.retry_on_methods),
            },
            "proxy": {
                "http_proxy": self.proxy.http_proxy if self.proxy else None,
                "https_proxy": self.proxy.https_proxy if self.proxy else None,
                "no_proxy": self.proxy.no_proxy if self.proxy else None,
            },
            "tls": {
                "verify": self.tls.verify,
                "cert_file": self.tls.cert_file,
                "key_file": self.tls.key_file,
                "ca_bundle": self.tls.ca_bundle,
                "minimum_version": self.tls.minimum_version,
            },
            "http_version": self.http_version.value,
            "follow_redirects": self.follow_redirects,
            "max_redirects": self.max_redirects,
            "default_headers": dict(self.default_headers),
            "default_params": dict(self.default_params),
            "compression": [c.value for c in self.compression],
            "trust_env": self.trust_env,
            "raise_for_status": self.raise_for_status,
            "user_agent": self.user_agent,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HTTPClientConfig:
        """Create from dictionary."""
        timeout_data = data.get("timeout", {})
        pool_data = data.get("pool", {})
        retry_data = data.get("retry", {})
        proxy_data = data.get("proxy", {})
        tls_data = data.get("tls", {})

        return cls(
            base_url=data.get("base_url"),
            timeout=TimeoutConfig(
                total=timeout_data.get("total", 30.0),
                connect=timeout_data.get("connect", 10.0),
                read=timeout_data.get("read"),
                write=timeout_data.get("write"),
                pool=timeout_data.get("pool", 5.0),
            ),
            pool=PoolConfig(
                max_connections=pool_data.get("max_connections", 100),
                max_connections_per_host=pool_data.get("max_connections_per_host", 10),
                max_keepalive_connections=pool_data.get("max_keepalive_connections", 20),
                keepalive_expiry=pool_data.get("keepalive_expiry", 60.0),
                enable_http2=pool_data.get("enable_http2", False),
            ),
            retry=RetryConfig(
                max_attempts=retry_data.get("max_attempts", 3),
                backoff_base=retry_data.get("backoff_base", 1.0),
                backoff_multiplier=retry_data.get("backoff_multiplier", 2.0),
                backoff_max=retry_data.get("backoff_max", 60.0),
                backoff_jitter=retry_data.get("backoff_jitter", 0.1),
                retry_on_status=frozenset(retry_data.get("retry_on_status", [429, 500, 502, 503, 504])),
                retry_on_methods=frozenset(
                    retry_data.get("retry_on_methods", ["GET", "HEAD", "OPTIONS", "PUT", "DELETE"])
                ),
            ),
            proxy=ProxyConfig(
                http_proxy=proxy_data.get("http_proxy"),
                https_proxy=proxy_data.get("https_proxy"),
                no_proxy=proxy_data.get("no_proxy"),
            )
            if any(proxy_data.values())
            else None,
            tls=TLSConfig(
                verify=tls_data.get("verify", True),
                cert_file=tls_data.get("cert_file"),
                key_file=tls_data.get("key_file"),
                ca_bundle=tls_data.get("ca_bundle"),
                minimum_version=tls_data.get("minimum_version"),
            ),
            http_version=HTTPVersion(data.get("http_version", "auto")),
            follow_redirects=data.get("follow_redirects", True),
            max_redirects=data.get("max_redirects", 10),
            default_headers=data.get("default_headers", {}),
            default_params=data.get("default_params", {}),
            compression=tuple(CompressionAlgorithm(c) for c in data.get("compression", ["gzip", "deflate"])),
            trust_env=data.get("trust_env", True),
            raise_for_status=data.get("raise_for_status", False),
            user_agent=data.get("user_agent", "Aquilia-HTTP/1.0"),
        )

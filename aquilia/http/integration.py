"""
AquilaHTTP — Framework Integration.

Integration with Aquilia's DI system, config builders,
and subsystem lifecycle.
"""

from __future__ import annotations

import logging
from typing import Any

from .client import AsyncHTTPClient
from .config import (
    HTTPClientConfig,
    PoolConfig,
    ProxyConfig,
    RetryConfig,
    TimeoutConfig,
    TLSConfig,
)

logger = logging.getLogger("aquilia.http.integration")


class HTTPClientProvider:
    """
    DI provider for AsyncHTTPClient.

    Provides HTTP client instances to the DI container with
    configurable scope (singleton, app, request).

    Example:
        ```python
        # In manifest.py
        manifest = AppManifest(
            providers=[
                HTTPClientProvider(
                    base_url="https://api.example.com",
                    timeout=30.0,
                )
            ],
        )

        # In controller
        class UsersController(Controller):
            def __init__(self, http: AsyncHTTPClient):
                self.http = http

            @GET("/users")
            async def list_users(self, ctx: RequestCtx):
                response = await self.http.get("/users")
                return await response.json()
        ```
    """

    __slots__ = ("_config", "_scope", "_client")

    def __init__(
        self,
        base_url: str | None = None,
        *,
        config: HTTPClientConfig | None = None,
        timeout: float | None = None,
        headers: dict[str, str] | None = None,
        scope: str = "singleton",
    ):
        """
        Initialize provider.

        Args:
            base_url: Base URL for all requests.
            config: Full HTTP client configuration.
            timeout: Default request timeout.
            headers: Default headers.
            scope: DI scope ("singleton", "app", or "request").
        """
        if config is None:
            config = HTTPClientConfig(
                base_url=base_url,
                default_headers=headers or {},
            )
            if timeout is not None:
                config = config.with_timeout(total=timeout)

        self._config = config
        self._scope = scope
        self._client: AsyncHTTPClient | None = None

    @property
    def provides(self) -> type:
        """Type this provider provides."""
        return AsyncHTTPClient

    @property
    def scope(self) -> str:
        """DI scope."""
        return self._scope

    async def __call__(self) -> AsyncHTTPClient:
        """Create or return HTTP client."""
        if self._scope == "singleton":
            if self._client is None:
                self._client = AsyncHTTPClient(config=self._config)
            return self._client

        # For app/request scope, create new client
        return AsyncHTTPClient(config=self._config)

    async def shutdown(self) -> None:
        """Shutdown the provider."""
        if self._client:
            await self._client.close()
            self._client = None


class HTTPClientBuilder:
    """
    Fluent builder for HTTP client configuration.

    Used with Aquilia's config builder pattern.

    Example:
        ```python
        workspace = (
            Workspace("myapp")
            .integrate(
                Integration.http_client()
                .base_url("https://api.example.com")
                .timeout(30.0)
                .retry(max_attempts=3)
                .header("X-API-Key", "${API_KEY}")
            )
        )
        ```
    """

    __slots__ = (
        "_base_url",
        "_timeout",
        "_pool",
        "_retry",
        "_proxy",
        "_tls",
        "_headers",
        "_follow_redirects",
        "_max_redirects",
        "_raise_for_status",
        "_user_agent",
    )

    def __init__(self):
        self._base_url: str | None = None
        self._timeout: TimeoutConfig | None = None
        self._pool: PoolConfig | None = None
        self._retry: RetryConfig | None = None
        self._proxy: ProxyConfig | None = None
        self._tls: TLSConfig | None = None
        self._headers: dict[str, str] = {}
        self._follow_redirects: bool = True
        self._max_redirects: int = 10
        self._raise_for_status: bool = False
        self._user_agent: str = "Aquilia-HTTP/1.0"

    def base_url(self, url: str) -> HTTPClientBuilder:
        """Set base URL."""
        self._base_url = url
        return self

    def timeout(
        self,
        total: float | None = 30.0,
        connect: float | None = 10.0,
        read: float | None = None,
        write: float | None = None,
    ) -> HTTPClientBuilder:
        """Set timeout configuration."""
        self._timeout = TimeoutConfig(
            total=total,
            connect=connect,
            read=read,
            write=write,
        )
        return self

    def pool(
        self,
        max_connections: int = 100,
        max_connections_per_host: int = 10,
        keepalive_expiry: float = 60.0,
    ) -> HTTPClientBuilder:
        """Set connection pool configuration."""
        self._pool = PoolConfig(
            max_connections=max_connections,
            max_connections_per_host=max_connections_per_host,
            keepalive_expiry=keepalive_expiry,
        )
        return self

    def retry(
        self,
        max_attempts: int = 3,
        backoff_base: float = 1.0,
        backoff_multiplier: float = 2.0,
        backoff_max: float = 60.0,
    ) -> HTTPClientBuilder:
        """Set retry configuration."""
        self._retry = RetryConfig(
            max_attempts=max_attempts,
            backoff_base=backoff_base,
            backoff_multiplier=backoff_multiplier,
            backoff_max=backoff_max,
        )
        return self

    def proxy(
        self,
        http_proxy: str | None = None,
        https_proxy: str | None = None,
        no_proxy: str | None = None,
    ) -> HTTPClientBuilder:
        """Set proxy configuration."""
        self._proxy = ProxyConfig(
            http_proxy=http_proxy,
            https_proxy=https_proxy,
            no_proxy=no_proxy,
        )
        return self

    def tls(
        self,
        verify: bool = True,
        cert_file: str | None = None,
        key_file: str | None = None,
        ca_bundle: str | None = None,
    ) -> HTTPClientBuilder:
        """Set TLS configuration."""
        self._tls = TLSConfig(
            verify=verify,
            cert_file=cert_file,
            key_file=key_file,
            ca_bundle=ca_bundle,
        )
        return self

    def header(self, name: str, value: str) -> HTTPClientBuilder:
        """Add a default header."""
        self._headers[name] = value
        return self

    def headers(self, headers: dict[str, str]) -> HTTPClientBuilder:
        """Set default headers."""
        self._headers.update(headers)
        return self

    def follow_redirects(self, follow: bool = True) -> HTTPClientBuilder:
        """Set redirect following behavior."""
        self._follow_redirects = follow
        return self

    def max_redirects(self, max_redirects: int) -> HTTPClientBuilder:
        """Set maximum redirects."""
        self._max_redirects = max_redirects
        return self

    def raise_for_status(self, raise_errors: bool = True) -> HTTPClientBuilder:
        """Set raise_for_status behavior."""
        self._raise_for_status = raise_errors
        return self

    def user_agent(self, user_agent: str) -> HTTPClientBuilder:
        """Set User-Agent header."""
        self._user_agent = user_agent
        return self

    def build(self) -> HTTPClientConfig:
        """Build the configuration."""
        return HTTPClientConfig(
            base_url=self._base_url,
            timeout=self._timeout or TimeoutConfig(),
            pool=self._pool or PoolConfig(),
            retry=self._retry or RetryConfig(),
            proxy=self._proxy,
            tls=self._tls or TLSConfig(),
            default_headers=self._headers,
            follow_redirects=self._follow_redirects,
            max_redirects=self._max_redirects,
            raise_for_status=self._raise_for_status,
            user_agent=self._user_agent,
        )

    def build_provider(self, scope: str = "singleton") -> HTTPClientProvider:
        """Build a DI provider."""
        config = self.build()
        return HTTPClientProvider(config=config, scope=scope)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "type": "http_client",
            "config": self.build().to_dict(),
        }


# Integration point for Aquilia's Integration class
def http_client() -> HTTPClientBuilder:
    """
    Create HTTP client integration builder.

    Example:
        ```python
        workspace = (
            Workspace("myapp")
            .integrate(
                Integration.http_client()
                .base_url("https://api.example.com")
                .timeout(30.0)
            )
        )
        ```

    Returns:
        HTTPClientBuilder for fluent configuration.
    """
    return HTTPClientBuilder()


# Factory function for creating clients from config dict
def create_client_from_config(config: dict[str, Any]) -> AsyncHTTPClient:
    """
    Create HTTP client from configuration dictionary.

    Args:
        config: Configuration dictionary.

    Returns:
        Configured AsyncHTTPClient.
    """
    http_config = HTTPClientConfig.from_dict(config)
    return AsyncHTTPClient(config=http_config)

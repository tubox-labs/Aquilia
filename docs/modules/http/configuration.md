# HTTP Client Configuration

## Configuration Entry Points

The implementation exposes the following configuration-like classes, policies, integrations, or dataclasses.

| Type | Source | Fields | Purpose |
| --- | --- | --- | --- |
| `RawResponse` | `aquilia/http/_transport.py` | http_version: str, status_code: int, reason: str, headers: dict[str, str], body: bytes, stream: AsyncIterator[bytes] &#124; None | Raw response before processing. |
| `ConnectionInfo` | `aquilia/http/_transport.py` | host: str, port: int, ssl: bool, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, created_at: float, last_used: float | Tracks a pooled connection. |
| `OAuth2Token` | `aquilia/http/auth.py` | access_token: str, token_type: str, expires_in: int &#124; None, refresh_token: str &#124; None, scope: str &#124; None, created_at: float | OAuth 2.0 token. |
| `TimeoutConfig` | `aquilia/http/config.py` | total: float &#124; None, connect: float &#124; None, read: float &#124; None, write: float &#124; None, pool: float &#124; None | HTTP request timeout configuration. |
| `PoolConfig` | `aquilia/http/config.py` | max_connections: int, max_connections_per_host: int, max_keepalive_connections: int, keepalive_expiry: float, enable_http2: bool | Connection pool configuration. |
| `RetryConfig` | `aquilia/http/config.py` | max_attempts: int, backoff_base: float, backoff_multiplier: float, backoff_max: float, backoff_jitter: float, retry_on_status: frozenset[int], retry_on_methods: frozenset[str] | Retry configuration. |
| `ProxyConfig` | `aquilia/http/config.py` | http_proxy: str &#124; None, https_proxy: str &#124; None, no_proxy: str &#124; None | Proxy configuration. |
| `TLSConfig` | `aquilia/http/config.py` | verify: bool, cert_file: str &#124; None, key_file: str &#124; None, ca_bundle: str &#124; None, ssl_context: SSLContext &#124; None, minimum_version: str &#124; None | TLS/SSL configuration. |
| `HTTPClientConfig` | `aquilia/http/config.py` | base_url: str &#124; None, timeout: TimeoutConfig, pool: PoolConfig, retry: RetryConfig, proxy: ProxyConfig &#124; None, tls: TLSConfig, http_version: HTTPVersion, follow_redirects: bool, max_redirects: int, default_headers: dict[str, str], default_params: dict[str, str], compression: tuple[CompressionAlgorithm, ...], ... | Complete HTTP client configuration. |
| `Cookie` | `aquilia/http/cookies.py` | name: str, value: str, domain: str, path: str, expires: float &#124; None, max_age: int &#124; None, secure: bool, http_only: bool, same_site: str | HTTP Cookie representation. |
| `RequestMetrics` | `aquilia/http/interceptors.py` | method: str, url: str, status_code: int, elapsed: float, request_size: int, response_size: int &#124; None, error: str &#124; None | Metrics collected for a request. |
| `FormField` | `aquilia/http/multipart.py` | name: str, value: str &#124; bytes, content_type: str &#124; None, filename: str &#124; None | A form field in multipart data. |
| `FormFile` | `aquilia/http/multipart.py` | name: str, filename: str, content: bytes &#124; BinaryIO &#124; AsyncIterator[bytes] &#124; Path, content_type: str &#124; None, content_length: int &#124; None | A file field in multipart data. |
| `ConnectionStats` | `aquilia/http/pool.py` | total_created: int, total_closed: int, total_reused: int, active_connections: int, idle_connections: int, failed_acquisitions: int, pool_exhausted_count: int | Connection pool statistics. |
| `PooledConnection` | `aquilia/http/pool.py` | host: str, port: int, scheme: str, connection: Any, created_at: float, last_used_at: float, requests_count: int, is_available: bool, is_http2: bool | Wrapper for a pooled connection. |
| `HTTPClientRequest` | `aquilia/http/request.py` | method: HTTPMethod, url: str, headers: dict[str, str], body: bytes &#124; AsyncIterator[bytes] &#124; None, timeout: TimeoutConfig &#124; None, follow_redirects: bool &#124; None, auth: tuple[str, str] &#124; None, extensions: dict[str, Any] | HTTP request representation. |
| `HTTPClientResponse` | `aquilia/http/response.py` | status_code: int, headers: dict[str, str], url: str, http_version: str, elapsed: float, request_url: str, history: list[HTTPClientResponse], extensions: dict[str, Any] | HTTP response wrapper. |
| `RetryState` | `aquilia/http/retry.py` | attempt: int, last_error: Exception &#124; None, last_response: HTTPClientResponse &#124; None, total_delay: float, start_time: float | State tracking for retry attempts. |
| `StreamProgress` | `aquilia/http/streaming.py` | bytes_transferred: int, total_bytes: int &#124; None, elapsed: float | Progress information for streaming operations. |

## Common Entry Points

- No dedicated workspace integration was detected from module naming. Configure this module through direct constructors, manifests, or the subsystem that owns it.

## Precedence Model

Aquilia generally resolves configuration in this order:

1. Explicit constructor arguments or typed integration dataclass values.
2. `Workspace` builder methods and `Workspace.integrate(...)` output.
3. `ConfigLoader` defaults and environment overlays.
4. Runtime defaults inside the subsystem service or provider constructor.

When this module is registered through an `AppManifest`, keep component declarations inside `modules/<name>/manifest.py` and keep cross-cutting integration settings in `workspace.py`.

## Datatype Guidance

- Prefer typed dataclasses, policy objects, and config objects listed above when they exist.
- Keep secret values in environment-backed config, not literal strings in committed workspace files.
- Keep runtime-only state in services, stores, providers, or request state rather than static configuration.
- Use `to_dict()` on integration dataclasses when you need to inspect exactly what enters `ConfigLoader`.

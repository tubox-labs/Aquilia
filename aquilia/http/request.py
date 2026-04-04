"""
AquilaHTTP — HTTP Client Request.

Request builder for constructing HTTP requests with a fluent API.
Supports headers, query params, body, cookies, auth, and more.
"""

from __future__ import annotations

import json as stdlib_json
from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, BinaryIO
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

from .config import TimeoutConfig
from .faults import InvalidHeaderFault, InvalidURLFault, RequestBuildFault


class HTTPMethod(str, Enum):
    """HTTP methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    TRACE = "TRACE"
    CONNECT = "CONNECT"


# Type aliases
HeadersType = Mapping[str, str] | list[tuple[str, str]] | None
ParamsType = Mapping[str, str | int | float | bool | None] | list[tuple[str, str]] | None
CookiesType = Mapping[str, str] | None
DataType = Mapping[str, Any] | str | bytes | None
JsonType = Any
ContentType = str | bytes | AsyncIterator[bytes] | BinaryIO | None

# Headers that should not be duplicated
SINGLE_VALUE_HEADERS = frozenset(
    {
        "content-type",
        "content-length",
        "host",
        "authorization",
        "user-agent",
        "accept",
        "connection",
        "cache-control",
    }
)


def _normalize_header_name(name: str) -> str:
    """Normalize header name to Title-Case."""
    return "-".join(word.capitalize() for word in name.split("-"))


def _validate_header_name(name: str) -> None:
    """Validate header name per RFC 7230."""
    if not name:
        raise InvalidHeaderFault("Header name cannot be empty")

    # Must be ASCII printable, no whitespace, no delimiters
    for char in name:
        if ord(char) < 33 or ord(char) > 126 or char in '()/<>@,;:\\"{} \t':
            raise InvalidHeaderFault(
                f"Invalid character in header name: {char!r}",
                header_name=name,
            )


def _validate_header_value(value: str, name: str = "") -> None:
    """Validate header value per RFC 7230."""
    # Allow empty values
    if not value:
        return

    # Must be printable ASCII or horizontal whitespace
    for char in value:
        code = ord(char)
        if code < 32 and char not in "\t":
            raise InvalidHeaderFault(
                f"Invalid character in header value: {char!r}",
                header_name=name,
                header_value=value[:50],
            )
        if code > 126 and code < 256:
            # Allow UTF-8 in header values (modern practice)
            pass


@dataclass
class HTTPClientRequest:
    """
    HTTP request representation.

    Immutable request object used internally by the HTTP client.
    Use the RequestBuilder for construction.

    Attributes:
        method: HTTP method.
        url: Full URL including scheme, host, path, and query.
        headers: Request headers.
        body: Request body (bytes, stream, or None).
        timeout: Request-specific timeout override.
        follow_redirects: Whether to follow redirects.
        auth: Authentication tuple (username, password) for Basic auth.
        extensions: Additional metadata for interceptors.
    """

    method: HTTPMethod
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes | AsyncIterator[bytes] | None = None
    timeout: TimeoutConfig | None = None
    follow_redirects: bool | None = None
    auth: tuple[str, str] | None = None
    extensions: dict[str, Any] = field(default_factory=dict)

    @property
    def host(self) -> str:
        """Extract host from URL."""
        parsed = urlparse(self.url)
        return parsed.netloc or ""

    @property
    def path(self) -> str:
        """Extract path from URL."""
        parsed = urlparse(self.url)
        return parsed.path or "/"

    @property
    def scheme(self) -> str:
        """Extract scheme from URL."""
        parsed = urlparse(self.url)
        return parsed.scheme or "https"

    @property
    def query_string(self) -> str:
        """Extract query string from URL."""
        parsed = urlparse(self.url)
        return parsed.query or ""

    @property
    def content_type(self) -> str | None:
        """Get Content-Type header."""
        return self.headers.get("Content-Type")

    @property
    def content_length(self) -> int | None:
        """Get Content-Length header as int."""
        value = self.headers.get("Content-Length")
        if value:
            try:
                return int(value)
            except ValueError:
                return None
        return None

    def has_body(self) -> bool:
        """Check if request has a body."""
        return self.body is not None

    def is_streaming(self) -> bool:
        """Check if body is a stream."""
        return hasattr(self.body, "__aiter__")

    def copy(self, **changes: Any) -> HTTPClientRequest:
        """Create a copy with optional changes."""
        return HTTPClientRequest(
            method=changes.get("method", self.method),
            url=changes.get("url", self.url),
            headers=changes.get("headers", dict(self.headers)),
            body=changes.get("body", self.body),
            timeout=changes.get("timeout", self.timeout),
            follow_redirects=changes.get("follow_redirects", self.follow_redirects),
            auth=changes.get("auth", self.auth),
            extensions=changes.get("extensions", dict(self.extensions)),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary (for logging/debugging)."""
        return {
            "method": self.method.value,
            "url": self.url,
            "headers": dict(self.headers),
            "has_body": self.has_body(),
            "is_streaming": self.is_streaming(),
            "content_type": self.content_type,
            "content_length": self.content_length,
        }


class RequestBuilder:
    """
    Fluent builder for HTTP requests.

    Example:
        ```python
        request = (
            RequestBuilder("GET", "https://api.example.com/users")
            .header("Authorization", "Bearer token")
            .param("page", 1)
            .timeout(total=30.0)
            .build()
        )
        ```
    """

    __slots__ = (
        "_method",
        "_url",
        "_headers",
        "_params",
        "_body",
        "_json",
        "_data",
        "_files",
        "_cookies",
        "_timeout",
        "_follow_redirects",
        "_auth",
        "_extensions",
        "_base_url",
    )

    def __init__(
        self,
        method: str | HTTPMethod,
        url: str,
        *,
        base_url: str | None = None,
    ):
        """
        Initialize request builder.

        Args:
            method: HTTP method.
            url: Request URL (can be relative if base_url is provided).
            base_url: Base URL to prepend to relative URLs.
        """
        self._method = HTTPMethod(method.upper()) if isinstance(method, str) else method
        self._base_url = base_url
        self._url = url
        self._headers: dict[str, str] = {}
        self._params: list[tuple[str, str]] = []
        self._body: bytes | AsyncIterator[bytes] | None = None
        self._json: Any = None
        self._data: dict[str, Any] | str | None = None
        self._files: list[tuple[str, tuple[str, bytes | BinaryIO, str | None]]] | None = None
        self._cookies: dict[str, str] = {}
        self._timeout: TimeoutConfig | None = None
        self._follow_redirects: bool | None = None
        self._auth: tuple[str, str] | None = None
        self._extensions: dict[str, Any] = {}

    def header(self, name: str, value: str) -> RequestBuilder:
        """Add a header."""
        _validate_header_name(name)
        _validate_header_value(value, name)
        normalized = _normalize_header_name(name)
        self._headers[normalized] = value
        return self

    def headers(self, headers: HeadersType) -> RequestBuilder:
        """Add multiple headers."""
        if headers is None:
            return self

        items = headers.items() if isinstance(headers, Mapping) else headers
        for name, value in items:
            self.header(name, value)
        return self

    def param(self, name: str, value: str | int | float | bool | None) -> RequestBuilder:
        """Add a query parameter."""
        if value is None:
            return self

        if isinstance(value, bool):
            value = "true" if value else "false"
        self._params.append((name, str(value)))
        return self

    def params(self, params: ParamsType) -> RequestBuilder:
        """Add multiple query parameters."""
        if params is None:
            return self

        items = params.items() if isinstance(params, Mapping) else params
        for name, value in items:
            self.param(name, value)
        return self

    def body(self, content: bytes | AsyncIterator[bytes]) -> RequestBuilder:
        """Set raw body content."""
        self._body = content
        return self

    def json(self, data: JsonType) -> RequestBuilder:
        """Set JSON body (automatically sets Content-Type)."""
        self._json = data
        return self

    def form(self, data: Mapping[str, Any] | str) -> RequestBuilder:
        """Set form-urlencoded body (automatically sets Content-Type)."""
        self._data = dict(data) if isinstance(data, Mapping) else data
        return self

    def multipart(
        self,
        fields: dict[str, str | tuple[str, bytes | BinaryIO, str | None]] | None = None,
        files: list[tuple[str, tuple[str, bytes | BinaryIO, str | None]]] | None = None,
    ) -> RequestBuilder:
        """Set multipart form data with optional files."""
        if fields:
            for name, value in fields.items():
                if isinstance(value, str):
                    self.param(name, value)
                else:
                    if self._files is None:
                        self._files = []
                    self._files.append((name, value))

        if files:
            if self._files is None:
                self._files = []
            self._files.extend(files)

        return self

    def cookie(self, name: str, value: str) -> RequestBuilder:
        """Add a cookie."""
        self._cookies[name] = value
        return self

    def cookies(self, cookies: CookiesType) -> RequestBuilder:
        """Add multiple cookies."""
        if cookies:
            self._cookies.update(cookies)
        return self

    def auth_basic(self, username: str, password: str) -> RequestBuilder:
        """Set Basic authentication."""
        self._auth = (username, password)
        return self

    def auth_bearer(self, token: str) -> RequestBuilder:
        """Set Bearer token authentication."""
        return self.header("Authorization", f"Bearer {token}")

    def timeout(
        self,
        total: float | None = None,
        connect: float | None = None,
        read: float | None = None,
        write: float | None = None,
        pool: float | None = None,
    ) -> RequestBuilder:
        """Set request-specific timeouts."""
        self._timeout = TimeoutConfig(
            total=total,
            connect=connect,
            read=read,
            write=write,
            pool=pool,
        )
        return self

    def follow_redirects(self, follow: bool = True) -> RequestBuilder:
        """Set redirect following behavior."""
        self._follow_redirects = follow
        return self

    def extension(self, key: str, value: Any) -> RequestBuilder:
        """Add an extension for interceptors."""
        self._extensions[key] = value
        return self

    def _build_url(self) -> str:
        """Build the final URL with base URL and query params."""
        url = self._url

        # Join with base URL if provided
        if self._base_url:
            url = urljoin(self._base_url.rstrip("/") + "/", url.lstrip("/"))

        # Validate URL
        parsed = urlparse(url)
        if not parsed.scheme:
            raise InvalidURLFault(
                f"URL must include scheme (http/https): {url}",
                url=url,
            )
        if not parsed.netloc:
            raise InvalidURLFault(
                f"URL must include host: {url}",
                url=url,
            )

        # Append query params
        if self._params:
            existing_params = parse_qsl(parsed.query, keep_blank_values=True)
            all_params = existing_params + self._params
            new_query = urlencode(all_params)
            url = urlunparse(
                (
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    new_query,
                    parsed.fragment,
                )
            )

        return url

    def _build_body(self) -> tuple[bytes | AsyncIterator[bytes] | None, dict[str, str]]:
        """Build body and additional headers."""
        extra_headers: dict[str, str] = {}

        # Priority: raw body > json > form data
        if self._body is not None:
            return self._body, extra_headers

        if self._json is not None:
            try:
                body = stdlib_json.dumps(self._json).encode("utf-8")
            except (TypeError, ValueError) as e:
                raise RequestBuildFault(
                    f"Failed to serialize JSON body: {e}",
                    field="json",
                ) from e
            extra_headers["Content-Type"] = "application/json; charset=utf-8"
            extra_headers["Content-Length"] = str(len(body))
            return body, extra_headers

        if self._data is not None:
            if isinstance(self._data, str):
                body = self._data.encode("utf-8")
            else:
                body = urlencode(self._data).encode("utf-8")
            extra_headers["Content-Type"] = "application/x-www-form-urlencoded"
            extra_headers["Content-Length"] = str(len(body))
            return body, extra_headers

        if self._files:
            # Multipart form data - handled separately
            # Return None here, client will handle multipart encoding
            self._extensions["_multipart_files"] = self._files
            extra_headers["Content-Type"] = "multipart/form-data"
            return None, extra_headers

        return None, extra_headers

    def _build_cookies(self) -> str | None:
        """Build Cookie header value."""
        if not self._cookies:
            return None
        return "; ".join(f"{k}={v}" for k, v in self._cookies.items())

    def _build_auth_header(self) -> str | None:
        """Build Authorization header for Basic auth."""
        if not self._auth:
            return None

        import base64

        username, password = self._auth
        credentials = f"{username}:{password}".encode()
        encoded = base64.b64encode(credentials).decode("ascii")
        return f"Basic {encoded}"

    def build(self) -> HTTPClientRequest:
        """Build the final HTTPClientRequest."""
        url = self._build_url()
        body, extra_headers = self._build_body()

        # Merge headers
        headers = dict(self._headers)

        # Add extra headers from body building
        for name, value in extra_headers.items():
            if name not in headers:
                headers[name] = value

        # Add cookies
        cookie_header = self._build_cookies()
        if cookie_header:
            existing = headers.get("Cookie", "")
            if existing:
                headers["Cookie"] = f"{existing}; {cookie_header}"
            else:
                headers["Cookie"] = cookie_header

        # Add basic auth header
        auth_header = self._build_auth_header()
        if auth_header and "Authorization" not in headers:
            headers["Authorization"] = auth_header

        return HTTPClientRequest(
            method=self._method,
            url=url,
            headers=headers,
            body=body,
            timeout=self._timeout,
            follow_redirects=self._follow_redirects,
            auth=self._auth,
            extensions=dict(self._extensions),
        )


# Convenience factory functions
def get(url: str, **kwargs: Any) -> RequestBuilder:
    """Create a GET request builder."""
    return RequestBuilder("GET", url, **kwargs)


def post(url: str, **kwargs: Any) -> RequestBuilder:
    """Create a POST request builder."""
    return RequestBuilder("POST", url, **kwargs)


def put(url: str, **kwargs: Any) -> RequestBuilder:
    """Create a PUT request builder."""
    return RequestBuilder("PUT", url, **kwargs)


def patch(url: str, **kwargs: Any) -> RequestBuilder:
    """Create a PATCH request builder."""
    return RequestBuilder("PATCH", url, **kwargs)


def delete(url: str, **kwargs: Any) -> RequestBuilder:
    """Create a DELETE request builder."""
    return RequestBuilder("DELETE", url, **kwargs)


def head(url: str, **kwargs: Any) -> RequestBuilder:
    """Create a HEAD request builder."""
    return RequestBuilder("HEAD", url, **kwargs)


def options(url: str, **kwargs: Any) -> RequestBuilder:
    """Create an OPTIONS request builder."""
    return RequestBuilder("OPTIONS", url, **kwargs)

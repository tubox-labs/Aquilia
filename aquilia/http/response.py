"""
AquilaHTTP — HTTP Client Response.

Response wrapper for HTTP responses with streaming support,
JSON/text parsing, and header access.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from http.cookies import SimpleCookie
from typing import Any

from aquilia.http.faults import ClientErrorFault, DecodingFault, ServerErrorFault, StreamConsumedFault
from aquilia.json import loads as _json_loads

# HTTP status code reasons
HTTP_STATUS_REASONS = {
    100: "Continue",
    101: "Switching Protocols",
    102: "Processing",
    103: "Early Hints",
    200: "OK",
    201: "Created",
    202: "Accepted",
    203: "Non-Authoritative Information",
    204: "No Content",
    205: "Reset Content",
    206: "Partial Content",
    207: "Multi-Status",
    208: "Already Reported",
    226: "IM Used",
    300: "Multiple Choices",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    305: "Use Proxy",
    307: "Temporary Redirect",
    308: "Permanent Redirect",
    400: "Bad Request",
    401: "Unauthorized",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    407: "Proxy Authentication Required",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    411: "Length Required",
    412: "Precondition Failed",
    413: "Payload Too Large",
    414: "URI Too Long",
    415: "Unsupported Media Type",
    416: "Range Not Satisfiable",
    417: "Expectation Failed",
    418: "I'm a teapot",
    421: "Misdirected Request",
    422: "Unprocessable Entity",
    423: "Locked",
    424: "Failed Dependency",
    425: "Too Early",
    426: "Upgrade Required",
    428: "Precondition Required",
    429: "Too Many Requests",
    431: "Request Header Fields Too Large",
    451: "Unavailable For Legal Reasons",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
    505: "HTTP Version Not Supported",
    506: "Variant Also Negotiates",
    507: "Insufficient Storage",
    508: "Loop Detected",
    510: "Not Extended",
    511: "Network Authentication Required",
}


@dataclass
class HTTPClientResponse:
    """
    HTTP response wrapper.

    Provides convenient access to status, headers, and body
    with streaming support for large responses.

    Attributes:
        status_code: HTTP status code (e.g., 200, 404).
        headers: Response headers.
        url: Final URL after redirects.
        http_version: HTTP version (e.g., "1.1", "2").
        elapsed: Request duration in seconds.
        request_url: Original request URL.
        history: List of redirect responses.
        extensions: Additional metadata.
    """

    status_code: int
    headers: dict[str, str]
    url: str
    http_version: str = "1.1"
    elapsed: float = 0.0
    request_url: str = ""
    history: list[HTTPClientResponse] = field(default_factory=list)
    extensions: dict[str, Any] = field(default_factory=dict)

    # Internal state
    _body: bytes | None = field(default=None, repr=False)
    _stream: AsyncIterator[bytes] | None = field(default=None, repr=False)
    _body_consumed: bool = field(default=False, repr=False)
    # Set when the stream was consumed through ``iter_bytes`` (which does
    # not cache): a later ``read()`` is a caller bug, not an empty body.
    _stream_iterated: bool = field(default=False, repr=False)
    # Raw field lines in arrival order. ``headers`` above collapses
    # duplicates into one comma-joined entry for convenience, which is
    # lossy for the fields that must not be combined (``Set-Cookie``);
    # ``get_headers()`` and ``cookies`` read from this list instead.
    _raw_headers: list[tuple[str, str]] = field(default_factory=list, repr=False)

    @property
    def reason(self) -> str:
        """HTTP status reason phrase."""
        return HTTP_STATUS_REASONS.get(self.status_code, "Unknown")

    @property
    def is_informational(self) -> bool:
        """Check if status is 1xx."""
        return 100 <= self.status_code < 200

    @property
    def is_success(self) -> bool:
        """Check if status is 2xx."""
        return 200 <= self.status_code < 300

    @property
    def is_redirect(self) -> bool:
        """Check if status is 3xx redirect."""
        return self.status_code in (301, 302, 303, 307, 308)

    @property
    def is_client_error(self) -> bool:
        """Check if status is 4xx."""
        return 400 <= self.status_code < 500

    @property
    def is_server_error(self) -> bool:
        """Check if status is 5xx."""
        return 500 <= self.status_code < 600

    @property
    def is_error(self) -> bool:
        """Check if status is 4xx or 5xx."""
        return self.status_code >= 400

    @property
    def ok(self) -> bool:
        """Check if status indicates success (2xx)."""
        return self.is_success

    @property
    def content_type(self) -> str:
        """Get Content-Type header."""
        return self.headers.get("Content-Type", "")

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

    @property
    def encoding(self) -> str:
        """Detect encoding from Content-Type header."""
        content_type = self.content_type.lower()

        # Extract charset from Content-Type
        if "charset=" in content_type:
            for part in content_type.split(";"):
                part = part.strip()
                if part.startswith("charset="):
                    charset = part[8:].strip("'\"")
                    return charset

        # Default to UTF-8 for JSON
        if "application/json" in content_type or "+json" in content_type:
            return "utf-8"

        # Default to ISO-8859-1 for text/* per HTTP/1.1 spec
        if content_type.startswith("text/"):
            return "iso-8859-1"

        return "utf-8"

    @property
    def etag(self) -> str | None:
        """Get ETag header."""
        return self.headers.get("ETag")

    @property
    def last_modified(self) -> datetime | None:
        """Parse Last-Modified header."""
        value = self.headers.get("Last-Modified")
        if not value:
            return None
        try:
            from email.utils import parsedate_to_datetime

            return parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None

    @property
    def location(self) -> str | None:
        """Get Location header (for redirects)."""
        return self.headers.get("Location")

    @property
    def cookies(self) -> dict[str, str]:
        """Parse Set-Cookie headers into dict.

        Every ``Set-Cookie`` field line is parsed -- a response that sets
        several cookies (a session plus a CSRF token, say) yields all of
        them, not only the last one to arrive.
        """
        result: dict[str, str] = {}
        for _, value in self._header_lines("set-cookie"):
            cookie: SimpleCookie[str] = SimpleCookie()
            cookie.load(value)
            for morsel in cookie.values():
                result[morsel.key] = morsel.value
        return result

    @property
    def raw_headers(self) -> list[tuple[str, str]]:
        """Raw response field lines in arrival order.

        Duplicates are preserved as separate entries -- unlike
        ``headers``, which combines them. ``Set-Cookie`` above all must
        be read from here (RFC 9110 §5.2: it must not be combined).
        """
        if self._raw_headers:
            return list(self._raw_headers)
        return list(self.headers.items())

    def _header_lines(self, name: str) -> list[tuple[str, str]]:
        """Return the raw ``(name, value)`` lines whose name matches *name* (case-insensitive)."""
        name_lower = name.lower()
        if self._raw_headers:
            return [(k, v) for k, v in self._raw_headers if k.lower() == name_lower]
        # Responses built directly with a plain dict (no raw list) fall back
        # to the collapsed view.
        return [(k, v) for k, v in self.headers.items() if k.lower() == name_lower]

    def get_header(self, name: str, default: str | None = None) -> str | None:
        """Get header by name (case-insensitive)."""
        lines = self._header_lines(name)
        if lines:
            return lines[0][1]
        return default

    def get_headers(self, name: str) -> list[str]:
        """Get every value received for a header, in arrival order.

        Multi-value headers are preserved verbatim -- no comma-joining, no
        loss of the values a collapsed dict cannot hold (``Set-Cookie``
        above all).
        """
        return [value for _, value in self._header_lines(name)]

    async def read(self) -> bytes:
        """Read entire response body as bytes."""
        if self._body is not None:
            return self._body

        if self._stream_iterated:
            # The body was already handed out through iter_bytes() and
            # not cached: a second read cannot reproduce it. Failing
            # silently would look like an empty body.
            raise StreamConsumedFault(
                "Response body was already consumed via iter_bytes(); read() cannot return it again",
                url=self.url or self.request_url,
            )

        if self._stream is None:
            return b""

        if self._body_consumed:
            return b""

        chunks: list[bytes] = []
        async for chunk in self._stream:
            chunks.append(chunk)

        self._body = b"".join(chunks)
        self._body_consumed = True
        self._stream = None

        return self._body

    async def text(self, encoding: str | None = None) -> str:
        """Read response body as text."""
        body = await self.read()
        enc = encoding or self.encoding

        try:
            return body.decode(enc)
        except (UnicodeDecodeError, LookupError) as e:
            raise DecodingFault(
                f"Failed to decode response as {enc}: {e}",
                status_code=self.status_code,
                url=self.url,
                encoding=enc,
            ) from e

    async def json(self) -> Any:
        """Parse response body as JSON."""
        body = await self.read()

        if not body:
            raise DecodingFault(
                "Response body is empty",
                status_code=self.status_code,
                url=self.url,
                content_type=self.content_type,
            )

        try:
            return _json_loads(body)
        except (ValueError, TypeError) as e:
            raise DecodingFault(
                f"Failed to parse JSON: {e}",
                status_code=self.status_code,
                url=self.url,
                content_type=self.content_type,
            ) from e

    async def iter_bytes(self, chunk_size: int = 65536) -> AsyncIterator[bytes]:
        """Stream response body in chunks."""
        if self._body is not None:
            # Already read - yield from cached body
            for i in range(0, len(self._body), chunk_size):
                yield self._body[i : i + chunk_size]
            return

        if self._stream is None or self._body_consumed:
            return

        # Re-slice: a transport chunk larger than the caller's chunk_size
        # is split, but small chunks are yielded as-is -- buffering to
        # fill chunk_size would delay incremental delivery, and callers
        # must tolerate short chunks anyway.
        async for chunk in self._stream:
            if len(chunk) <= chunk_size:
                yield chunk
            else:
                for i in range(0, len(chunk), chunk_size):
                    yield chunk[i : i + chunk_size]

        self._body_consumed = True
        # Not cached: a subsequent read() is a caller bug, not b"".
        self._stream_iterated = True
        self._stream = None

    async def iter_text(
        self,
        chunk_size: int = 65536,
        encoding: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream response body as text chunks."""
        enc = encoding or self.encoding
        async for chunk in self.iter_bytes(chunk_size):
            try:
                yield chunk.decode(enc)
            except (UnicodeDecodeError, LookupError) as e:
                raise DecodingFault(
                    f"Failed to decode chunk as {enc}: {e}",
                    status_code=self.status_code,
                    url=self.url,
                    encoding=enc,
                ) from e

    async def iter_lines(
        self,
        encoding: str | None = None,
        delimiter: str = "\n",
    ) -> AsyncIterator[str]:
        """Stream response body line by line."""
        buffer = ""
        enc = encoding or self.encoding

        async for chunk in self.iter_bytes():
            try:
                buffer += chunk.decode(enc)
            except (UnicodeDecodeError, LookupError) as e:
                raise DecodingFault(
                    f"Failed to decode chunk as {enc}: {e}",
                    status_code=self.status_code,
                    url=self.url,
                    encoding=enc,
                ) from e

            while delimiter in buffer:
                line, buffer = buffer.split(delimiter, 1)
                yield line

        # Yield remaining buffer
        if buffer:
            yield buffer

    def raise_for_status(self) -> None:
        """Raise HTTPStatusFault if status is 4xx or 5xx."""
        if self.is_client_error:
            raise ClientErrorFault(
                f"HTTP {self.status_code} {self.reason}",
                status_code=self.status_code,
                url=self.url,
                reason=self.reason,
            )

        if self.is_server_error:
            raise ServerErrorFault(
                f"HTTP {self.status_code} {self.reason}",
                status_code=self.status_code,
                url=self.url,
                reason=self.reason,
            )

    async def close(self) -> None:
        """Close the response and release resources.

        The stream is aborted, not drained: a body the caller chose not
        to read is discarded and its connection closed, never returned
        to the pool half-read.
        """
        stream = self._stream
        self._stream = None
        if stream is not None:
            aclose = getattr(stream, "aclose", None)
            if aclose is not None:
                await aclose()
        self._body_consumed = True

    async def __aenter__(self) -> HTTPClientResponse:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *exc: Any) -> None:
        """Async context manager exit."""
        await self.close()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary (for logging/debugging)."""
        return {
            "status_code": self.status_code,
            "reason": self.reason,
            "url": self.url,
            "http_version": self.http_version,
            "elapsed": self.elapsed,
            "headers": dict(self.headers),
            "content_type": self.content_type,
            "content_length": self.content_length,
            "is_success": self.is_success,
            "is_error": self.is_error,
        }

    def __repr__(self) -> str:
        return f"<HTTPClientResponse [{self.status_code} {self.reason}]>"


def create_response(
    status_code: int,
    headers: dict[str, str] | list[tuple[str, str]] | None = None,
    *,
    body: bytes | None = None,
    stream: AsyncIterator[bytes] | None = None,
    url: str = "",
    http_version: str = "1.1",
    elapsed: float = 0.0,
    request_url: str = "",
    history: list[HTTPClientResponse] | None = None,
    extensions: dict[str, Any] | None = None,
) -> HTTPClientResponse:
    """
    Factory function to create HTTPClientResponse.

    Args:
        status_code: HTTP status code.
        headers: Response headers (dict or list of tuples).
        body: Response body bytes (for buffered responses).
        stream: Response body stream (for streaming responses).
        url: Final URL after redirects.
        http_version: HTTP version string.
        elapsed: Request duration in seconds.
        request_url: Original request URL.
        history: List of redirect responses.
        extensions: Additional metadata.

    Returns:
        HTTPClientResponse instance.

    Note:
        A list of raw field lines preserves every duplicate as its own
        entry in ``_raw_headers`` (what ``get_headers()`` returns), while
        the convenience ``headers`` dict joins duplicates with ``", "``
        (RFC 9110 field-line combining). ``Set-Cookie`` is the documented
        exception that must not be combined -- use ``get_headers()`` or the
        ``cookies`` property for it.
    """
    # Normalize headers to dict
    if headers is None:
        headers_dict: dict[str, str] = {}
        raw_lines: list[tuple[str, str]] = []
    elif isinstance(headers, list):
        headers_dict = {}
        for name, value in headers:
            # Handle multiple values for same header
            if name in headers_dict:
                headers_dict[name] = f"{headers_dict[name]}, {value}"
            else:
                headers_dict[name] = value
        raw_lines = list(headers)
    else:
        headers_dict = dict(headers)
        raw_lines = list(headers_dict.items())

    return HTTPClientResponse(
        status_code=status_code,
        headers=headers_dict,
        url=url,
        http_version=http_version,
        elapsed=elapsed,
        request_url=request_url,
        history=history or [],
        extensions=extensions if extensions is not None else {},
        _body=body,
        _stream=stream,
        _body_consumed=body is not None,
        _raw_headers=raw_lines,
    )

"""
Response - Production-grade HTTP response builder with streaming support.

Provides:
- ASGI 3 compliant response sending with robust streaming
- Support for bytes, str, dict/list (JSON), async iterables, sync iterables, coroutines
- Content negotiation & safe charset handling
- RFC-compliant headers & cookies with signing support
- Server-Sent Events (SSE) support
- File streaming with optional sendfile optimization
- Range request support (206 Partial Content)
- Caching helpers (ETag, Last-Modified, Cache-Control, 304 responses)
- Background task scheduling
- Header validation & security helpers
- Compression support (gzip, brotli)
- Integration with TemplateEngine, FaultEngine, and tracing/metrics
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import hmac
import inspect
import logging
import mimetypes
from base64 import urlsafe_b64decode, urlsafe_b64encode
from collections.abc import AsyncIterator, Awaitable, Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import formatdate, parsedate_to_datetime
from pathlib import Path
from typing import (
    Any,
    Protocol,
)
from urllib.parse import quote

# Optional fast JSON
try:
    import orjson

    JSON_ENCODER = "orjson"
except ImportError:
    try:
        import ujson as orjson_fallback

        orjson = orjson_fallback
        JSON_ENCODER = "ujson"
    except ImportError:
        import json as orjson_fallback

        orjson = orjson_fallback
        JSON_ENCODER = "stdlib"

# Optional compression
try:
    import brotli  # noqa: F401

    BROTLI_AVAILABLE = True
except ImportError:
    BROTLI_AVAILABLE = False

# Native async file I/O
from .filesystem import stream_read as _fs_stream_read

# Import Crous binary serializer
try:
    import crous as _crous_mod

    _HAS_CROUS = True
except ImportError:
    _crous_mod = None  # type: ignore[assignment]
    _HAS_CROUS = False

# Import Aquilia components
from .faults import Fault, FaultDomain, Severity

# CROUS media type constants
CROUS_MEDIA_TYPE = "application/x-crous"
CROUS_MAGIC = b"CROUSv1"


def has_crous() -> bool:
    """Return ``True`` if the ``crous`` library is importable."""
    return _HAS_CROUS


logger = logging.getLogger("aquilia.response")

# Type aliases
PathLike = str | Path


def _json_default_serializer(o):
    """Default JSON serializer for non-standard types."""
    if isinstance(o, (set, tuple)):
        return list(o)
    if hasattr(o, "isoformat"):
        return o.isoformat()
    return str(o)


# ============================================================================
# Helper Classes & Protocols
# ============================================================================


class BackgroundTask(Protocol):
    """Protocol for background tasks executed after response is sent."""

    async def run(self) -> None:
        """Execute the background task."""
        ...


@dataclass
class CallableBackgroundTask:
    """Simple callable-based background task."""

    func: Callable[[], Awaitable[None]]
    run_on_disconnect: bool = False

    async def run(self) -> None:
        await self.func()


@dataclass
class ServerSentEvent:
    """Server-Sent Event data structure."""

    data: str
    id: str | None = None
    event: str | None = None
    retry: int | None = None

    def encode(self) -> bytes:
        """Encode SSE event according to spec."""
        lines = []

        if self.id:
            lines.append(f"id: {self.id}")

        if self.event:
            lines.append(f"event: {self.event}")

        if self.retry is not None:
            lines.append(f"retry: {self.retry}")

        # Multi-line data support
        for line in self.data.splitlines():
            lines.append(f"data: {line}")

        # SSE spec: event ends with double newline
        return ("\n".join(lines) + "\n\n").encode("utf-8")


@dataclass(frozen=True, slots=True)
class MediaChunk:
    """Type-safe media chunk container for streaming payloads."""

    data: bytes | str
    content_type: str | None = None
    is_final: bool = False

    def encode(self, encoding: str = "utf-8") -> bytes:
        if isinstance(self.data, bytes):
            return self.data
        return self.data.encode(encoding)


@dataclass(frozen=True, slots=True)
class HLSSegment:
    """Single media segment entry in an HLS media playlist."""

    uri: str
    duration: float
    title: str | None = None
    byte_range: str | None = None
    discontinuity: bool = False

    def render(self) -> list[str]:
        lines: list[str] = []
        if self.discontinuity:
            lines.append("#EXT-X-DISCONTINUITY")
        if self.byte_range:
            lines.append(f"#EXT-X-BYTERANGE:{self.byte_range}")
        title = self.title or ""
        lines.append(f"#EXTINF:{self.duration:.3f},{title}")
        lines.append(self.uri)
        return lines


@dataclass(frozen=True, slots=True)
class HLSVariant:
    """Variant stream descriptor for an HLS master playlist."""

    uri: str
    bandwidth: int
    resolution: str | None = None
    codecs: str | None = None
    frame_rate: float | None = None
    audio: str | None = None

    def render(self) -> list[str]:
        attrs = [f"BANDWIDTH={self.bandwidth}"]
        if self.resolution:
            attrs.append(f"RESOLUTION={self.resolution}")
        if self.codecs:
            attrs.append(f'CODECS="{self.codecs}"')
        if self.frame_rate is not None:
            attrs.append(f"FRAME-RATE={self.frame_rate:.3f}")
        if self.audio:
            attrs.append(f'AUDIO="{self.audio}"')
        return [f"#EXT-X-STREAM-INF:{','.join(attrs)}", self.uri]


class CookieSigner:
    """
    Cookie signer with HMAC-based signing and key rotation support.

    Uses urlsafe base64 encoding for signed values.
    """

    def __init__(self, secret_key: str | bytes, algorithm: str = "sha256"):
        """
        Initialize cookie signer.

        Args:
            secret_key: Secret key for signing (rotatable keyring supported)
            algorithm: Hash algorithm (sha256, sha384, sha512)
        """
        if isinstance(secret_key, str):
            secret_key = secret_key.encode("utf-8")

        self.secret_key = secret_key
        self.algorithm = algorithm
        self._hash_func = getattr(hashlib, algorithm)

    def sign(self, value: str) -> str:
        """
        Sign a cookie value.

        Returns: base64-encoded signature.value
        """
        value_bytes = value.encode("utf-8")
        signature = hmac.new(self.secret_key, value_bytes, self._hash_func).digest()

        # Format: signature.value (both base64)
        sig_b64 = urlsafe_b64encode(signature).decode("ascii").rstrip("=")
        val_b64 = urlsafe_b64encode(value_bytes).decode("ascii").rstrip("=")

        return f"{sig_b64}.{val_b64}"

    def unsign(self, signed_value: str) -> str | None:
        """
        Verify and unsign a cookie value.

        Returns: Original value if signature valid, None otherwise
        """
        try:
            sig_b64, val_b64 = signed_value.split(".", 1)

            # Add padding back
            sig_b64 += "=" * (4 - len(sig_b64) % 4)
            val_b64 += "=" * (4 - len(val_b64) % 4)

            signature = urlsafe_b64decode(sig_b64)
            value_bytes = urlsafe_b64decode(val_b64)

            # Verify signature
            expected_sig = hmac.new(self.secret_key, value_bytes, self._hash_func).digest()

            if not hmac.compare_digest(signature, expected_sig):
                return None

            return value_bytes.decode("utf-8")

        except (ValueError, KeyError):
            return None


# ============================================================================
# Response Faults
# ============================================================================

FaultDomain.RESPONSE = FaultDomain("response", "HTTP response errors")


class ResponseStreamError(Fault):
    """Error during response streaming."""

    code = "RESPONSE_STREAM_ERROR"
    domain = FaultDomain.RESPONSE
    severity = Severity.ERROR


class TemplateRenderError(Fault):
    """Template rendering error during response."""

    code = "TEMPLATE_RENDER_ERROR"
    domain = FaultDomain.RESPONSE
    severity = Severity.ERROR
    message = "Template rendering failed"

    def __init__(self, message: str | None = None, **kwargs):
        super().__init__(message=message or self.message, **kwargs)


class InvalidHeaderError(Fault):
    """Invalid header name or value (injection attempt)."""

    code = "INVALID_HEADER"
    domain = FaultDomain.SECURITY
    severity = Severity.WARN


class ClientDisconnectError(Fault):
    """Client disconnected during response send."""

    code = "CLIENT_DISCONNECT"
    domain = FaultDomain.IO
    severity = Severity.INFO


class RangeNotSatisfiableError(Fault):
    """Invalid Range header (416 response)."""

    code = "RANGE_NOT_SATISFIABLE"
    domain = FaultDomain.RESPONSE
    severity = Severity.WARN


class HLSManifestError(Fault):
    """Invalid HLS manifest payload or helper usage."""

    code = "HLS_MANIFEST_ERROR"
    domain = FaultDomain.RESPONSE
    severity = Severity.ERROR


# ============================================================================
# Main Response Class
# ============================================================================
class Response:
    """
    Production-grade HTTP response with ASGI 3 streaming support.

    Features:
    - Multiple content types: bytes, str, dict/list, async/sync iterables, coroutines
    - Streaming-first with proper chunking and backpressure
    - RFC-compliant headers & cookies
    - Server-Sent Events (SSE)
    - File streaming with Range support
    - Background task scheduling
    - Security & caching helpers
    """

    def __init__(
        self,
        content: bytes | str | Mapping | Sequence | AsyncIterator[bytes] | Iterator[bytes] | Awaitable[Any] = b"",
        status: int = 200,
        headers: Mapping[str, str | Sequence[str]] | None = None,
        media_type: str | None = None,
        *,
        background: BackgroundTask | list[BackgroundTask] | None = None,
        encoding: str = "utf-8",
        validate_headers: bool = True,
    ):
        """
        Initialize Response.

        Args:
            content: Response body (bytes, str, dict, iterable, coroutine)
            status: HTTP status code
            headers: Response headers (supports multi-value)
            media_type: Content-Type override
            background: Background task(s) to run after send
            encoding: Text encoding (default utf-8)
            validate_headers: Validate headers against injection attacks
        """
        self.status = status
        self._content = content
        self.encoding = encoding
        self.validate_headers = validate_headers

        # Initialize headers dict (handle multi-value)
        self._headers: dict[str, str | list[str]] = {}
        if headers:
            for key, value in headers.items():
                if isinstance(value, (list, tuple)):
                    self._headers[key.lower()] = list(value)
                else:
                    self._headers[key.lower()] = value

        # Set content-type
        if media_type:
            self._headers["content-type"] = media_type
        elif "content-type" not in self._headers:
            # Auto-detect media type
            self._headers["content-type"] = self._detect_media_type(content)

        # Background tasks -- avoid list allocation when empty (common case)
        if background is None:
            self._background_tasks: list[BackgroundTask] = []
        elif isinstance(background, list):
            self._background_tasks = background
        else:
            self._background_tasks = [background]

        # Metrics
        self._bytes_sent = 0

    @property
    def headers(self) -> dict[str, str | list[str]]:
        """Get response headers."""
        return self._headers

    def _detect_media_type(self, content: Any) -> str:
        """Auto-detect media type from content."""
        if isinstance(content, bytes):
            # Detect CROUS binary by magic header
            if len(content) >= 7 and content[:7] == CROUS_MAGIC:
                return CROUS_MEDIA_TYPE
            return "application/octet-stream"
        elif isinstance(content, (dict, list)):
            return "application/json; charset=utf-8"
        elif isinstance(content, str):
            return "text/plain; charset=utf-8"
        elif hasattr(content, "__aiter__") or hasattr(content, "__iter__"):
            return "application/octet-stream"
        elif inspect.iscoroutine(content) or inspect.isawaitable(content):
            return "text/html; charset=utf-8"  # Assume template
        else:
            return "application/octet-stream"

    # ========================================================================
    # Factory Methods
    # ========================================================================

    @classmethod
    def json(
        cls,
        obj: Any,
        status: int = 200,
        *,
        encoder: Callable[[Any], str] | None = None,
        headers: Mapping[str, str] | None = None,
        **kwargs,
    ) -> Response:
        """
        Create JSON response.

        Args:
            obj: Object to serialize
            status: HTTP status
            encoder: Custom JSON encoder
            headers: Additional headers
            **kwargs: Passed to json encoder

        Returns:
            Response with JSON content
        """
        if encoder:
            content = encoder(obj)
        elif JSON_ENCODER == "orjson":
            # Fast path: when kwargs is empty (common case), avoid **kwargs overhead.
            if kwargs:
                content = orjson.dumps(obj, default=_json_default_serializer, **kwargs)
            else:
                content = orjson.dumps(obj, default=_json_default_serializer)
        else:
            try:
                if kwargs:
                    content = orjson.dumps(obj, default=_json_default_serializer, **kwargs)
                else:
                    content = orjson.dumps(obj, default=_json_default_serializer)
            except Exception:
                import json

                content = json.dumps(obj, default=_json_default_serializer)

        return cls(content=content, status=status, headers=headers, media_type="application/json; charset=utf-8")

    @classmethod
    def html(cls, content: str, status: int = 200, **kwargs) -> Response:
        """Create HTML response."""
        return cls(content=content, status=status, media_type="text/html; charset=utf-8", **kwargs)

    @classmethod
    def text(cls, content: str, status: int = 200, **kwargs) -> Response:
        """Create plain text response."""
        return cls(content=content, status=status, media_type="text/plain; charset=utf-8", **kwargs)

    @classmethod
    def redirect(cls, url: str, status: int = 307, *, headers: dict[str, str] | None = None) -> Response:
        """
        Create redirect response.

        Args:
            url: Redirect URL
            status: HTTP status (default 307 Temporary Redirect)
            headers: Additional headers

        Returns:
            Redirect response
        """
        redirect_headers = {"location": url}
        if headers:
            redirect_headers.update(headers)

        return cls(content=b"", status=status, headers=redirect_headers)

    @classmethod
    def stream(
        cls,
        iterator: AsyncIterator[bytes] | Iterator[bytes],
        status: int = 200,
        media_type: str = "application/octet-stream",
        **kwargs,
    ) -> Response:
        """
        Create streaming response.

        Args:
            iterator: Async or sync iterator yielding bytes
            status: HTTP status
            media_type: Content type

        Returns:
            Streaming response
        """
        return cls(content=iterator, status=status, media_type=media_type, **kwargs)

    @classmethod
    def media_stream(
        cls,
        chunks: AsyncIterator[MediaChunk] | Iterator[MediaChunk],
        status: int = 200,
        media_type: str = "application/octet-stream",
        **kwargs,
    ) -> Response:
        """Create a type-safe media chunk streaming response."""

        if hasattr(chunks, "__aiter__"):

            async def _media_aiter() -> AsyncIterator[bytes]:
                async for chunk in chunks:  # type: ignore[misc]
                    yield chunk.encode()

            return cls(content=_media_aiter(), status=status, media_type=media_type, **kwargs)

        def _media_iter() -> Iterator[bytes]:
            for chunk in chunks:  # type: ignore[misc]
                yield chunk.encode()

        return cls(content=_media_iter(), status=status, media_type=media_type, **kwargs)

    @classmethod
    def sse(cls, event_iter: AsyncIterator[ServerSentEvent], status: int = 200, **kwargs) -> Response:
        """
        Create Server-Sent Events (SSE) response.

        Args:
            event_iter: Async iterator of ServerSentEvent objects
            status: HTTP status

        Returns:
            SSE streaming response
        """

        async def _sse_stream() -> AsyncIterator[bytes]:
            async for event in event_iter:
                yield event.encode()

        headers = {
            "cache-control": "no-cache",
            "connection": "keep-alive",
            "x-accel-buffering": "no",  # Disable nginx buffering
        }
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))

        return cls(
            content=_sse_stream(),
            status=status,
            media_type="text/event-stream; charset=utf-8",
            headers=headers,
            **kwargs,
        )

    @classmethod
    def crous(
        cls,
        obj: Any,
        status: int = 200,
        *,
        headers: Mapping[str, str] | None = None,
        compression: str | None = None,
        dedup: bool = True,
        **kwargs,
    ) -> Response:
        """
        Create a CROUS binary response.

        Serialises ``obj`` into Crous wire format (``CROUSv1`` header,
        XXH64-checksummed blocks) and returns a ``Response`` with
        ``Content-Type: application/x-crous``.

        Falls back to JSON automatically when the ``crous`` library
        is not installed.

        Args:
            obj: Python object to serialise (dict, list, str, int, …)
            status: HTTP status code.
            headers: Additional response headers.
            compression: Optional block compression
                         (``"lz4"``, ``"zstd"``, ``"snappy"``
                         or ``None`` for no compression).
            dedup: Enable string deduplication (default ``True``).
            **kwargs: Forwarded to ``Response.__init__``.

        Returns:
            Response with CROUS binary body.

        Example::

            @GET("/users")
            async def list_users(self, ctx):
                return Response.crous({"users": users})
        """
        if not _HAS_CROUS:
            # Graceful degradation — fall back to JSON
            return cls.json(obj, status=status, headers=headers, **kwargs)

        try:
            # Use Encoder for fine-grained control when compression
            # or dedup is requested.
            if compression or dedup:
                from crous.encoder import Encoder

                enc = Encoder()
                if dedup:
                    enc.enable_dedup()
                if compression:
                    from crous.wire import CompressionType

                    comp_map = {
                        "zstd": CompressionType.ZSTD,
                        "snappy": CompressionType.SNAPPY,
                        "none": CompressionType.NONE,
                    }
                    # Also support LZ4 if available in the
                    # installed version of the crous library.
                    if hasattr(CompressionType, "LZ4"):
                        comp_map["lz4"] = CompressionType.LZ4

                    comp = comp_map.get(compression.lower())
                    if comp is not None:
                        enc.set_compression(comp)

                from crous.value import Value

                enc.encode_value(Value.from_python(obj))
                content = enc.finish()
            else:
                content = _crous_mod.encode(obj)
        except Exception as exc:
            logger.warning("CROUS encode failed (%s); falling back to JSON", exc)
            return cls.json(obj, status=status, headers=headers, **kwargs)

        merged_headers: dict[str, str] = dict(headers or {})
        merged_headers.setdefault("content-length", str(len(content)))
        # Signal the wire format version for proxies / CDNs
        merged_headers.setdefault("x-crous-version", "1")

        return cls(
            content=content,
            status=status,
            headers=merged_headers,
            media_type=CROUS_MEDIA_TYPE,
            **kwargs,
        )

    @classmethod
    def negotiated(
        cls,
        obj: Any,
        request: Any,
        status: int = 200,
        *,
        headers: Mapping[str, str] | None = None,
        **kwargs,
    ) -> Response:
        """Create a response with automatic content negotiation.

        Inspects the ``Accept`` header on *request* and returns
        either a CROUS or JSON response.

        Resolution order:
        1. If the handler is decorated with ``@requires_crous`` and
           the client accepts CROUS → CROUS.
        2. If ``request.prefers_crous()`` → CROUS.
        3. Otherwise → JSON.

        Args:
            obj: Python object to serialise.
            request: The incoming :class:`~aquilia.request.Request`.
            status: HTTP status code.
            headers: Additional response headers.
            **kwargs: Forwarded to the underlying factory.

        Returns:
            Response in the negotiated format.

        Example::

            @GET("/users")
            async def list_users(self, ctx):
                return Response.negotiated(users, ctx.request)
        """
        use_crous = False

        if _HAS_CROUS:
            # Check handler-level preference (stored in state by router)
            handler = None
            if hasattr(request, "state") and isinstance(request.state, dict):
                handler = request.state.get("matched_handler")
            if handler and getattr(handler, "__crous_response__", False):
                if hasattr(request, "accepts_crous") and request.accepts_crous():
                    use_crous = True

            # Check client preference
            if not use_crous and hasattr(request, "prefers_crous"):
                use_crous = request.prefers_crous()

        if use_crous:
            return cls.crous(obj, status=status, headers=headers, **kwargs)
        return cls.json(obj, status=status, headers=headers, **kwargs)

    @classmethod
    def file(
        cls,
        path: PathLike,
        *,
        filename: str | None = None,
        media_type: str | None = None,
        status: int = 200,
        use_sendfile: bool = True,
        chunk_size: int = 64 * 1024,
        **kwargs,
    ) -> Response:
        """
        Create file download response.

        Args:
            path: File path
            filename: Download filename (Content-Disposition)
            media_type: Content type (auto-detected if None)
            status: HTTP status
            use_sendfile: Use sendfile optimization (TODO: Phase 2)
            chunk_size: Streaming chunk size

        Returns:
            File streaming response
        """
        path = Path(path)

        if not path.exists():
            from .faults.domains import FilesystemFault

            raise FilesystemFault(
                path=str(path),
                operation="read",
                reason="File not found",
            )

        if not path.is_file():
            from .faults.domains import IOFault

            raise IOFault(code="NOT_A_FILE", message=f"Not a file: {path}")

        # Detect media type
        if media_type is None:
            media_type, _ = mimetypes.guess_type(str(path))
            if media_type is None:
                media_type = "application/octet-stream"

        # File size
        file_size = path.stat().st_size

        # Headers
        headers = kwargs.pop("headers", {})
        headers["content-length"] = str(file_size)
        headers["accept-ranges"] = "bytes"

        # Content-Disposition
        if filename:
            disposition = f'attachment; filename="{quote(filename)}"'
            headers["content-disposition"] = disposition

        # Create streaming iterator
        async def _file_stream() -> AsyncIterator[bytes]:
            async for chunk in _fs_stream_read(path, chunk_size=chunk_size):
                yield chunk

        response = cls(content=_file_stream(), status=status, media_type=media_type, headers=headers, **kwargs)

        # Store file metadata for Range support
        response._file_path = path
        response._file_size = file_size

        return response

    @classmethod
    def hls_playlist(
        cls,
        segments: Sequence[HLSSegment],
        *,
        target_duration: int | None = None,
        media_sequence: int = 0,
        version: int = 3,
        endlist: bool = True,
        status: int = 200,
        headers: Mapping[str, str] | None = None,
    ) -> Response:
        """Create an HLS media playlist (.m3u8) response."""
        if target_duration is None:
            max_duration = max((seg.duration for seg in segments), default=1.0)
            target_duration = max(1, int(max_duration) + (0 if float(max_duration).is_integer() else 1))
        if target_duration < 1:
            raise HLSManifestError(message="target_duration must be >= 1")

        lines = [
            "#EXTM3U",
            f"#EXT-X-VERSION:{version}",
            f"#EXT-X-TARGETDURATION:{target_duration}",
            f"#EXT-X-MEDIA-SEQUENCE:{media_sequence}",
        ]
        for segment in segments:
            lines.extend(segment.render())
        if endlist:
            lines.append("#EXT-X-ENDLIST")

        playlist = "\n".join(lines) + "\n"
        merged_headers = dict(headers or {})
        merged_headers.setdefault("cache-control", "no-cache")
        return cls(
            content=playlist,
            status=status,
            headers=merged_headers,
            media_type="application/vnd.apple.mpegurl; charset=utf-8",
        )

    @classmethod
    def hls_master_playlist(
        cls,
        variants: Sequence[HLSVariant],
        *,
        version: int = 3,
        status: int = 200,
        headers: Mapping[str, str] | None = None,
    ) -> Response:
        """Create an HLS master playlist response."""
        if not variants:
            raise HLSManifestError(message="master playlist requires at least one variant")

        lines = ["#EXTM3U", f"#EXT-X-VERSION:{version}"]
        for variant in variants:
            lines.extend(variant.render())
        playlist = "\n".join(lines) + "\n"
        merged_headers = dict(headers or {})
        merged_headers.setdefault("cache-control", "no-cache")
        return cls(
            content=playlist,
            status=status,
            headers=merged_headers,
            media_type="application/vnd.apple.mpegurl; charset=utf-8",
        )

    @classmethod
    def hls_segment(
        cls,
        path: PathLike,
        *,
        status: int = 200,
        chunk_size: int = 64 * 1024,
        headers: Mapping[str, str] | None = None,
    ) -> Response:
        """Create an HLS segment file response with media-aware defaults."""
        suffix = Path(path).suffix.lower()
        if suffix == ".ts":
            media_type = "video/mp2t"
        elif suffix in {".m4s", ".cmfa"}:
            media_type = "video/iso.segment"
        elif suffix in {".aac"}:
            media_type = "audio/aac"
        else:
            media_type = "application/octet-stream"
        return cls.file(
            path,
            status=status,
            media_type=media_type,
            chunk_size=chunk_size,
            headers=dict(headers or {}),
        )

    @classmethod
    async def render(
        cls,
        template_name: str,
        context: Mapping[str, Any] | None = None,
        *,
        request: Any | None = None,
        request_ctx: Any | None = None,
        engine: Any | None = None,
        status: int = 200,
        headers: Mapping | None = None,
        **response_kwargs,
    ) -> Response:
        """
        Render template with automatic context injection.

        Automatically injects from request (if provided):
        - request: Request object
        - identity: Authenticated identity
        - session: Session object
        - authenticated: Boolean authentication status
        - All values from request.template_context

        Args:
            template_name: Template name
            context: Additional template variables
            request: Request object for auto-injection
            engine: TemplateEngine instance (resolved from DI if None)
            status: HTTP status code
            headers: Response headers
            **response_kwargs: Additional Response constructor kwargs

        Returns:
            Response with rendered HTML

        Example:
            # Minimal usage (identity/session auto-injected from request)
            return await Response.render("profile.html", request=request)

            # With additional context
            return await Response.render(
                "profile.html",
                {"extra_data": "value"},
                request=request,
            )
        """
        # Merge contexts
        final_context = dict(context or {})

        # Extract request from context if available
        if request_ctx and request is None:
            request = getattr(request_ctx, "request", None)

        # Auto-inject from request
        if request:
            # Get request's template context (already has identity, session, etc.)
            final_context.update(request.template_context)

            # Resolve engine from DI if not provided
            if engine is None:
                if hasattr(request, "resolve"):
                    try:
                        # Try to resolve TemplateEngine from DI
                        from aquilia.templates.engine import TemplateEngine

                        engine = await request.resolve(TemplateEngine, optional=True)
                    except Exception:
                        pass

                # Fallback: try from state
                if engine is None:
                    engine = request.state.get("template_engine")

        if engine is None:
            raise TemplateRenderError(
                "No TemplateEngine available. Ensure TemplateMiddleware is installed or pass engine parameter."
            )

        # Render template
        try:
            html = await engine.render(template_name, final_context)
        except Exception as e:
            raise TemplateRenderError(f"Template rendering failed: {e}")

        return cls(
            content=html, status=status, headers=headers, media_type="text/html; charset=utf-8", **response_kwargs
        )

    # ========================================================================
    # Session Integration
    # ========================================================================

    async def commit_session(self, request: Any) -> None:
        """
        Commit session changes after response.

        This is typically called automatically by SessionMiddleware,
        but can be called manually if needed.

        Args:
            request: Request object with session
        """
        if not hasattr(request, "session") or not request.session:
            return

        session = request.session

        # Try to get SessionEngine from DI
        session_engine = None
        if hasattr(request, "resolve"):
            try:
                from aquilia.sessions.engine import SessionEngine

                session_engine = await request.resolve(SessionEngine, optional=True)
            except Exception:
                pass

        # Fallback: try from state
        if session_engine is None:
            session_engine = request.state.get("session_engine")

        if session_engine and hasattr(session_engine, "commit"):
            await session_engine.commit(session, self)

    # ========================================================================
    # Lifecycle Hooks Integration
    # ========================================================================

    async def execute_before_send_hooks(self, request: Any) -> None:
        """
        Execute before-response callbacks registered on request.

        Args:
            request: Request object with callbacks
        """
        if not hasattr(request, "state"):
            return

        callbacks = request.state.get("before_response_callbacks", [])
        for callback in callbacks:
            try:
                if inspect.iscoroutinefunction(callback):
                    await callback(self)
                else:
                    callback(self)
            except Exception as e:
                logger.warning(f"Before-send hook failed: {e}")

    async def execute_after_send_hooks(self, request: Any) -> None:
        """
        Execute after-response callbacks registered on request.

        Args:
            request: Request object with callbacks
        """
        if not hasattr(request, "state"):
            return

        callbacks = request.state.get("after_response_callbacks", [])
        for callback in callbacks:
            try:
                if inspect.iscoroutinefunction(callback):
                    await callback(self)
                else:
                    callback(self)
            except Exception as e:
                logger.warning(f"After-send hook failed: {e}")

    # ========================================================================
    # Metrics Integration
    # ========================================================================

    def record_response_metrics(self, request: Any, duration_ms: float) -> None:
        """
        Record response metrics.

        Args:
            request: Request object with metrics collector
            duration_ms: Request duration in milliseconds
        """
        if not hasattr(request, "record_metric"):
            return

        try:
            request.record_metric("http_response_time_ms", duration_ms, status=self.status)

            # Calculate approximate response size
            response_size = sum(len(v) if isinstance(v, str) else 0 for v in self._headers.values())
            request.record_metric("http_response_size_bytes", response_size, status=self.status)
        except Exception as e:
            logger.warning(f"Failed to record response metrics: {e}")

    # ========================================================================
    # Enhanced Error Responses with Fault Integration
    # ========================================================================

    @classmethod
    def from_fault(
        cls,
        fault: Fault,
        *,
        include_details: bool = False,
        request: Any | None = None,
    ) -> Response:
        """
        Create Response from Fault with appropriate status code.

        Args:
            fault: Fault object
            include_details: Include fault details in response
            request: Request for context

        Returns:
            JSON response with fault information
        """
        # Map fault codes to HTTP status
        status_map = {
            "AUTH_REQUIRED": 401,
            "AUTH_TOKEN_INVALID": 401,
            "AUTH_TOKEN_EXPIRED": 401,
            "AUTHZ_INSUFFICIENT_SCOPE": 403,
            "AUTHZ_FORBIDDEN": 403,
            "SESSION_EXPIRED": 401,
            "SESSION_INVALID": 400,
            "BAD_REQUEST": 400,
            "PAYLOAD_TOO_LARGE": 413,
            "UNSUPPORTED_MEDIA_TYPE": 415,
            "NOT_FOUND": 404,
            "METHOD_NOT_ALLOWED": 405,
            "CONFLICT": 409,
            "RATE_LIMIT_EXCEEDED": 429,
        }

        status = status_map.get(fault.code, 500)

        # Build response body
        body = {
            "error": fault.code,
            "message": fault.message,
        }

        if include_details and hasattr(fault, "metadata"):
            body["details"] = fault.metadata

        if request and hasattr(request, "request_id"):
            body["request_id"] = request.request_id

        return cls.json(body, status=status)

    # ========================================================================
    # Cookie Helpers
    # ========================================================================

    def set_cookie(
        self,
        name: str,
        value: str,
        *,
        max_age: int | None = None,
        expires: datetime | None = None,
        path: str = "/",
        domain: str | None = None,
        secure: bool = True,
        httponly: bool = True,
        samesite: str | None = "Lax",
        same_site_policy: str | None = None,  # Alias
        signed: bool = False,
        signer: CookieSigner | None = None,
    ) -> None:
        """
        Set a cookie.

        Args:
            name: Cookie name
            value: Cookie value
            max_age: Max age in seconds
            expires: Expiration datetime
            path: Cookie path
            domain: Cookie domain
            secure: Secure flag
            httponly: HttpOnly flag
            samesite: SameSite policy (Strict, Lax, None)
            same_site_policy: Alias for samesite
            signed: Sign cookie value
            signer: CookieSigner instance (required if signed=True)
        """
        if signed:
            if signer is None:
                from .faults.domains import ConfigInvalidFault

                raise ConfigInvalidFault(
                    key="cookie_signer",
                    reason="signer is required when signed=True; pass a CookieSigner instance",
                )
            value = signer.sign(value)

        cookie_parts = [f"{name}={value}"]

        if max_age is not None:
            cookie_parts.append(f"Max-Age={max_age}")

        if expires:
            # Format as HTTP date
            expires_str = formatdate(expires.timestamp(), usegmt=True)
            cookie_parts.append(f"Expires={expires_str}")

        cookie_parts.append(f"Path={path}")

        if domain:
            cookie_parts.append(f"Domain={domain}")

        if secure:
            cookie_parts.append("Secure")

        if httponly:
            cookie_parts.append("HttpOnly")

        # SameSite
        samesite_val = same_site_policy or samesite
        if samesite_val:
            cookie_parts.append(f"SameSite={samesite_val}")

        cookie_str = "; ".join(cookie_parts)

        # Support multiple Set-Cookie headers
        self.add_header("set-cookie", cookie_str)

    def delete_cookie(self, name: str, path: str = "/", domain: str | None = None) -> None:
        """
        Delete a cookie by setting Max-Age=0.

        Args:
            name: Cookie name
            path: Cookie path
            domain: Cookie domain
        """
        self.set_cookie(
            name,
            "",
            max_age=0,
            expires=datetime.fromtimestamp(0, tz=timezone.utc),
            path=path,
            domain=domain,
            secure=False,
            httponly=False,
            samesite=None,
        )

    # ========================================================================
    # Header Helpers
    # ========================================================================

    def set_header(self, name: str, value: str) -> None:
        """
        Set header (replaces existing).

        Args:
            name: Header name
            value: Header value
        """
        if self.validate_headers:
            self._validate_header(name, value)

        self._headers[name.lower()] = value

    def add_header(self, name: str, value: str) -> None:
        """
        Add header (supports multiple values).

        Args:
            name: Header name
            value: Header value
        """
        if self.validate_headers:
            self._validate_header(name, value)

        name_lower = name.lower()

        if name_lower in self._headers:
            existing = self._headers[name_lower]
            if isinstance(existing, list):
                existing.append(value)
            else:
                self._headers[name_lower] = [existing, value]
        else:
            self._headers[name_lower] = value

    def unset_header(self, name: str) -> None:
        """Remove header."""
        self._headers.pop(name.lower(), None)

    def _validate_header(self, name: str, value: str) -> None:
        """
        Validate header name and value against injection attacks.

        Raises InvalidHeaderError if header contains control characters.
        """
        # Check for control characters and newlines
        for char in name:
            if ord(char) < 32 or char in ("\r", "\n"):
                raise InvalidHeaderError(message=f"Invalid header name: {name!r}", details={"header_name": name})

        for char in value:
            if char in ("\r", "\n"):
                raise InvalidHeaderError(
                    message=f"Invalid header value: {value!r}", details={"header_name": name, "header_value": value}
                )

    # ========================================================================
    # Caching Helpers
    # ========================================================================

    def set_etag(self, etag: str, weak: bool = False) -> None:
        """
        Set ETag header.

        Args:
            etag: ETag value (without quotes)
            weak: Use weak validator (W/ prefix)
        """
        etag_header = f'W/"{etag}"' if weak else f'"{etag}"'

        self.set_header("etag", etag_header)

    def set_last_modified(self, dt: datetime) -> None:
        """
        Set Last-Modified header.

        Args:
            dt: Last modified datetime
        """
        http_date = formatdate(dt.timestamp(), usegmt=True)
        self.set_header("last-modified", http_date)

    def cache_control(self, **directives) -> None:
        """
        Set Cache-Control header.

        Args:
            **directives: Cache directives (e.g., max_age=3600, no_cache=True)

        Example:
            response.cache_control(max_age=3600, public=True)
            response.cache_control(no_cache=True, no_store=True)
        """
        parts = []

        for key, value in directives.items():
            # Convert snake_case to kebab-case
            directive = key.replace("_", "-")

            if value is True:
                parts.append(directive)
            elif value is False:
                continue
            else:
                parts.append(f"{directive}={value}")

        if parts:
            self.set_header("cache-control", ", ".join(parts))

    def secure_headers(
        self,
        *,
        hsts: bool = True,
        hsts_max_age: int = 31536000,
        csp: str | None = None,
        frame_options: str = "DENY",
        content_type_options: bool = True,
        xss_protection: bool = True,
        referrer_policy: str = "strict-origin-when-cross-origin",
    ) -> None:
        """
        Set recommended security headers.

        Args:
            hsts: Enable HSTS
            hsts_max_age: HSTS max-age in seconds
            csp: Content-Security-Policy value
            frame_options: X-Frame-Options value
            content_type_options: Enable X-Content-Type-Options: nosniff
            xss_protection: Enable X-XSS-Protection
            referrer_policy: Referrer-Policy value
        """
        if hsts:
            self.set_header("strict-transport-security", f"max-age={hsts_max_age}; includeSubDomains")

        if csp:
            self.set_header("content-security-policy", csp)

        if frame_options:
            self.set_header("x-frame-options", frame_options)

        if content_type_options:
            self.set_header("x-content-type-options", "nosniff")

        if xss_protection:
            self.set_header("x-xss-protection", "1; mode=block")

        if referrer_policy:
            self.set_header("referrer-policy", referrer_policy)

    # ========================================================================
    # ASGI Send
    # ========================================================================

    async def send_asgi(self, send: Callable[[dict], Awaitable[None]], request: Any | None = None) -> None:
        """
        Send response via ASGI.

        Performance (v2):
        - Skip range-request logic when no _file_path attribute exists.
        - Pre-encode simple bodies (bytes) to avoid branching in _send_body.
        - Minimize time.time() calls for metrics.
        """
        try:
            # Range request handling -- only for file responses
            if request is not None and hasattr(self, "_file_path") and hasattr(self, "_file_size"):
                self._handle_range_request(request)

            # Pre-compute content-length for simple bodies before preparing headers
            content = self._content
            if isinstance(content, bytes):
                if "content-length" not in self._headers:
                    self._headers["content-length"] = str(len(content))
            elif isinstance(content, str):
                # Will be encoded later, but pre-compute length
                content_bytes = content.encode(self.encoding)
                self._content = content_bytes
                if "content-length" not in self._headers:
                    self._headers["content-length"] = str(len(content_bytes))

            # Prepare headers for ASGI
            headers_list = self._prepare_headers()

            # Send http.response.start
            await send(
                {
                    "type": "http.response.start",
                    "status": self.status,
                    "headers": headers_list,
                }
            )

            # Send body based on content type
            await self._send_body(send, request)

            # Run background tasks
            if self._background_tasks:
                await self._run_background_tasks()

        except asyncio.CancelledError:
            await self._aclose_if_possible(self._content)
            raise ClientDisconnectError(
                message="Client disconnected",
                details={"bytes_sent": self._bytes_sent},
            )
        except ResponseStreamError:
            raise
        except Exception as e:
            raise ResponseStreamError(
                message=f"Response stream error: {e}",
                details={"error": str(e), "bytes_sent": self._bytes_sent},
            )

    def _handle_range_request(self, request: Any) -> None:
        """Handle Range header for file responses (moved out of hot path)."""
        range_header = None
        if hasattr(request, "headers"):
            h = request.headers
            if hasattr(h, "get"):
                range_header = h.get("range")
            elif isinstance(h, dict):
                range_header = h.get("range") or h.get("Range")

        if not range_header or not range_header.startswith("bytes="):
            return

        try:
            range_spec = range_header[6:]
            file_size = self._file_size

            if range_spec.startswith("-"):
                suffix_len = int(range_spec[1:])
                range_start = max(0, file_size - suffix_len)
                range_end = file_size - 1
            elif range_spec.endswith("-"):
                range_start = int(range_spec[:-1])
                range_end = file_size - 1
            else:
                parts = range_spec.split("-", 1)
                range_start = int(parts[0])
                range_end = int(parts[1])

            if range_start < 0 or range_start >= file_size or range_end < range_start:
                raise RangeNotSatisfiableError(
                    message=f"Range not satisfiable: {range_header} (size={file_size})",
                    details={"file_size": file_size},
                )

            range_end = min(range_end, file_size - 1)
            content_length = range_end - range_start + 1

            self.status = 206
            self._headers["content-range"] = f"bytes {range_start}-{range_end}/{file_size}"
            self._headers["content-length"] = str(content_length)

            self._content = self._create_range_stream(
                self._file_path,
                range_start,
                range_end,
            )
        except (ValueError, IndexError):
            pass  # Malformed range -- send full response

    @staticmethod
    def _create_range_stream(
        file_path: Path, start: int, end: int, chunk_size: int = 64 * 1024
    ) -> AsyncIterator[bytes]:
        """Create an async iterator that streams a byte range of a file.

        Args:
            file_path: Path to the file
            start: Start byte offset (inclusive)
            end: End byte offset (inclusive)
            chunk_size: Size of each chunk to read

        Yields:
            Chunks of bytes from the specified range
        """

        async def _range_stream():
            async for chunk in _fs_stream_read(
                file_path,
                chunk_size=chunk_size,
                offset=start,
                end=end + 1,
            ):
                yield chunk

        return _range_stream()

    def _prepare_headers(self) -> list[tuple]:
        """Prepare headers for ASGI (convert to list of byte tuples).

        Uses local variable binding for encode method to reduce
        attribute lookups in the loop.
        """
        headers_list = []
        _append = headers_list.append
        _str_encode = str.encode

        for name, value in self._headers.items():
            name_bytes = _str_encode(name, "latin1")

            if isinstance(value, list):
                # Multiple values (e.g., Set-Cookie)
                for v in value:
                    _append((name_bytes, _str_encode(v, "latin1")))
            else:
                _append((name_bytes, _str_encode(value, "latin1")))

        return headers_list

    def _is_sse_response(self) -> bool:
        """Return True when this response is an SSE stream."""
        content_type = self._headers.get("content-type")
        if isinstance(content_type, list):
            content_type = content_type[0] if content_type else ""
        return isinstance(content_type, str) and content_type.lower().startswith("text/event-stream")

    async def _emit_sse_error_frame(self, send: Callable[[dict], Awaitable[None]], exc: Exception) -> None:
        """Best-effort SSE error frame emission for mid-stream failures."""
        event = ServerSentEvent(event="error", data=f"stream_error: {type(exc).__name__}")
        payload = event.encode()
        self._bytes_sent += len(payload)
        await send(
            {
                "type": "http.response.body",
                "body": payload,
                "more_body": True,
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": b"",
                "more_body": False,
            }
        )

    async def _aclose_if_possible(self, stream: Any) -> None:
        """Close async generators/streams when available."""
        close = getattr(stream, "aclose", None)
        if close is None:
            return
        with contextlib.suppress(Exception):
            await close()

    def _close_if_possible(self, stream: Any) -> None:
        """Close sync iterators/generators when available."""
        close = getattr(stream, "close", None)
        if close is None:
            return
        with contextlib.suppress(Exception):
            close()

    async def _send_body(self, send: Callable[[dict], Awaitable[None]], request: Any | None) -> None:
        """Send response body based on content type.

        Performance (v2):
        - Checks bytes first (most common fast path for JSON/HTML).
        - Avoids isinstance checks for streaming when content is bytes.
        """
        content = self._content

        # ── Fast path: bytes (pre-encoded JSON, HTML, binary) ──
        if isinstance(content, bytes):
            self._bytes_sent = len(content)
            await send(
                {
                    "type": "http.response.body",
                    "body": content,
                    "more_body": False,
                }
            )
            return

        # ── Fast path: str ──
        if isinstance(content, str):
            body_bytes = content.encode(self.encoding)
            self._bytes_sent = len(body_bytes)
            await send(
                {
                    "type": "http.response.body",
                    "body": body_bytes,
                    "more_body": False,
                }
            )
            return

        # ── Fast path: dict/list (JSON) ──
        if isinstance(content, (dict, list)):
            body_bytes = self._encode_body(content)
            if "content-length" not in self._headers:
                self._headers["content-length"] = str(len(body_bytes))
            self._bytes_sent = len(body_bytes)
            await send(
                {
                    "type": "http.response.body",
                    "body": body_bytes,
                    "more_body": False,
                }
            )
            return

        # ── Async iterator (streaming) ──
        if hasattr(content, "__aiter__"):
            stream = content
            try:
                async for chunk in stream:
                    chunk_bytes = self._ensure_bytes(chunk)
                    self._bytes_sent += len(chunk_bytes)
                    await send(
                        {
                            "type": "http.response.body",
                            "body": chunk_bytes,
                            "more_body": True,
                        }
                    )
            except Exception as exc:
                if self._is_sse_response():
                    await self._emit_sse_error_frame(send, exc)
                    return
                raise ResponseStreamError(
                    message=f"Async stream failed: {exc}",
                    details={"error": str(exc), "bytes_sent": self._bytes_sent},
                )
            finally:
                await self._aclose_if_possible(stream)
            await send(
                {
                    "type": "http.response.body",
                    "body": b"",
                    "more_body": False,
                }
            )
            return

        # ── Sync iterator ──
        if hasattr(content, "__iter__"):
            loop = asyncio.get_running_loop()

            def _get_next_chunk(iterator):
                try:
                    return next(iterator), True
                except StopIteration:
                    return None, False

            iterator = iter(content)
            try:
                while True:
                    chunk, has_more = await loop.run_in_executor(None, _get_next_chunk, iterator)
                    if not has_more:
                        break
                    chunk_bytes = self._ensure_bytes(chunk)
                    self._bytes_sent += len(chunk_bytes)
                    await send(
                        {
                            "type": "http.response.body",
                            "body": chunk_bytes,
                            "more_body": True,
                        }
                    )
            except Exception as exc:
                raise ResponseStreamError(
                    message=f"Sync stream failed: {exc}",
                    details={"error": str(exc), "bytes_sent": self._bytes_sent},
                )
            finally:
                self._close_if_possible(iterator)
            await send(
                {
                    "type": "http.response.body",
                    "body": b"",
                    "more_body": False,
                }
            )
            return

        # ── Coroutine/awaitable (template render) ──
        if inspect.iscoroutine(content) or inspect.isawaitable(content):
            try:
                rendered = await content
                body_bytes = self._encode_body(rendered)
                self._bytes_sent += len(body_bytes)
                await send(
                    {
                        "type": "http.response.body",
                        "body": body_bytes,
                        "more_body": False,
                    }
                )
            except Exception as e:
                raise TemplateRenderError(
                    message=f"Template rendering failed: {e}",
                    details={"error": str(e), "error_type": type(e).__name__},
                )
            return

        # ── Fallback ──
        body_bytes = self._encode_body(content)
        self._bytes_sent += len(body_bytes)
        if "content-length" not in self._headers:
            self._headers["content-length"] = str(len(body_bytes))
        await send(
            {
                "type": "http.response.body",
                "body": body_bytes,
                "more_body": False,
            }
        )

    def _ensure_bytes(self, chunk: Any) -> bytes:
        """Ensure chunk is bytes."""
        if isinstance(chunk, bytes):
            return chunk
        elif isinstance(chunk, str):
            return chunk.encode(self.encoding)
        else:
            return str(chunk).encode(self.encoding)

    def _encode_body(self, content: Any) -> bytes:
        """Encode content to bytes."""
        if isinstance(content, bytes):
            return content

        elif isinstance(content, str):
            return content.encode(self.encoding)

        elif isinstance(content, (dict, list)):
            # JSON encode
            if JSON_ENCODER == "orjson":
                return orjson.dumps(content)
            elif JSON_ENCODER == "ujson":
                return orjson.dumps(content).encode(self.encoding)
            else:
                return orjson.dumps(content).encode(self.encoding)

        else:
            # Fallback: str() then encode
            return str(content).encode(self.encoding)

    async def _run_background_tasks(self) -> None:
        """Execute background tasks after response sent."""
        for task in self._background_tasks:
            try:
                await task.run()
            except Exception as e:
                logger.error(f"Background task error: {e}", exc_info=True)


# ============================================================================
# Convenience Response Factories
# ============================================================================


def Ok(content: Any = None, **kwargs) -> Response:
    """200 OK response."""
    if content is None:
        content = {"status": "ok"}
    return Response.json(content, status=200, **kwargs)


def Created(content: Any = None, location: str | None = None, **kwargs) -> Response:
    """201 Created response."""
    if content is None:
        content = {"status": "created"}

    headers = kwargs.pop("headers", {})
    if location:
        headers["location"] = location

    return Response.json(content, status=201, headers=headers, **kwargs)


def NoContent() -> Response:
    """204 No Content response."""
    return Response(b"", status=204)


def BadRequest(message: str = "Bad Request", **kwargs) -> Response:
    """400 Bad Request response."""
    return Response.json({"error": message}, status=400, **kwargs)


def Unauthorized(message: str = "Unauthorized", **kwargs) -> Response:
    """401 Unauthorized response."""
    return Response.json({"error": message}, status=401, **kwargs)


def Forbidden(message: str = "Forbidden", **kwargs) -> Response:
    """403 Forbidden response."""
    return Response.json({"error": message}, status=403, **kwargs)


def NotFound(message: str = "Not Found", **kwargs) -> Response:
    """404 Not Found response."""
    return Response.json({"error": message}, status=404, **kwargs)


def InternalError(message: str = "Internal Server Error", **kwargs) -> Response:
    """500 Internal Server Error response."""
    return Response.json({"error": message}, status=500, **kwargs)


# ============================================================================
# Utility Functions
# ============================================================================


def generate_etag(content: bytes, weak: bool = False) -> str:
    """
    Generate ETag from content.

    Args:
        content: Response body bytes
        weak: Generate weak ETag

    Returns:
        ETag value (without quotes)
    """
    hash_value = hashlib.sha256(content).hexdigest()[:32]
    return hash_value


def generate_etag_from_file(path: PathLike, weak: bool = True) -> str:
    """
    Generate ETag from file metadata.

    Uses mtime and size for weak ETag (fast).

    Args:
        path: File path
        weak: Generate weak ETag (default True for files)

    Returns:
        ETag value
    """
    path = Path(path)
    stat = path.stat()

    # Use mtime + size for weak ETag
    etag_input = f"{stat.st_mtime}:{stat.st_size}".encode()
    hash_value = hashlib.sha256(etag_input).hexdigest()[:16]

    return hash_value


def check_not_modified(request: Any, etag: str | None = None, last_modified: datetime | None = None) -> bool:
    """
    Check if response should be 304 Not Modified.

    Args:
        request: Request object with headers
        etag: Response ETag (without quotes)
        last_modified: Response last modified datetime

    Returns:
        True if 304 should be sent
    """
    # Check If-None-Match (ETag)
    if etag and hasattr(request, "headers"):
        if_none_match = request.headers.get("if-none-match")
        if if_none_match:
            # Handle multiple ETags
            request_etags = [tag.strip(' "W/') for tag in if_none_match.split(",")]
            if etag in request_etags or "*" in request_etags:
                return True

    # Check If-Modified-Since
    if last_modified and hasattr(request, "headers"):
        if_modified_since = request.headers.get("if-modified-since")
        if if_modified_since:
            try:
                ims_dt = parsedate_to_datetime(if_modified_since)
                # Compare timestamps (ignore microseconds)
                if last_modified.timestamp() <= ims_dt.timestamp():
                    return True
            except (ValueError, TypeError):
                pass

    return False


def not_modified_response(etag: str | None = None) -> Response:
    """
    Create 304 Not Modified response.

    Args:
        etag: ETag to include in response

    Returns:
        304 response with ETag if provided
    """
    response = Response(b"", status=304)

    if etag:
        response.set_etag(etag)

    return response


# ============================================================================
# CROUS Decorator
# ============================================================================


def requires_crous(func: Callable) -> Callable:
    """Mark a handler as preferring CROUS binary responses.

    When combined with :meth:`Response.negotiated`, responses will be
    encoded as CROUS when the client includes a CROUS media type in
    its ``Accept`` header.

    The decorator simply sets ``func.__crous_response__ = True`` — it
    does **not** alter control flow or enforce CROUS.  If the client
    does not accept CROUS (or the library is unavailable), JSON is
    returned transparently.

    Example::

        @requires_crous
        @GET("/metrics")
        async def metrics(self, ctx):
            return Response.negotiated(data, ctx.request)
    """
    func.__crous_response__ = True  # type: ignore[attr-defined]
    return func


__all__ = [
    "Response",
    "BackgroundTask",
    "CallableBackgroundTask",
    "ServerSentEvent",
    "MediaChunk",
    "HLSSegment",
    "HLSVariant",
    "CookieSigner",
    "ResponseStreamError",
    "TemplateRenderError",
    "InvalidHeaderError",
    "ClientDisconnectError",
    "RangeNotSatisfiableError",
    "HLSManifestError",
    "Ok",
    "Created",
    "NoContent",
    "BadRequest",
    "Unauthorized",
    "Forbidden",
    "NotFound",
    "InternalError",
    "generate_etag",
    "generate_etag_from_file",
    "check_not_modified",
    "not_modified_response",
    # CROUS support
    "CROUS_MEDIA_TYPE",
    "CROUS_MAGIC",
    "has_crous",
    "requires_crous",
]

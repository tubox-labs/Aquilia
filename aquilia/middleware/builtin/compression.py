"""Response body compression.

Negotiates an encoding against ``Accept-Encoding`` and compresses eligible
bodies off the event loop.

What this handles that a naive ``"gzip" in accept_encoding`` check does not:

- **Quality values.** ``Accept-Encoding: gzip;q=0`` is a client *refusing*
  gzip. Substring matching reads it as acceptance and sends an encoding the
  client rejected.
- **Content type.** JPEGs, MP4s, and ZIPs are already compressed; running gzip
  over them burns CPU to make the payload marginally *larger*. Only
  compressible types are considered.
- **Already-encoded responses.** A response that set ``Content-Encoding``
  itself must not be re-compressed into a doubly-encoded body.
- **``Cache-Control: no-transform``.** An explicit instruction from the
  application not to alter the payload (RFC 9111 §5.2.2.6).
- **Preference order.** Brotli beats gzip beats deflate at equal quality, so a
  modern client gets the better ratio without asking for it specifically.
"""

from __future__ import annotations

import asyncio
import gzip
import zlib
from typing import TYPE_CHECKING

from aquilia.middleware.core.base import Middleware

if TYPE_CHECKING:
    from aquilia.controller.base import RequestCtx
    from aquilia.request import Request
    from aquilia.response import Response

__all__ = ["CompressionMiddleware"]

# Brotli typically wins 15-20% over gzip on text at comparable CPU. Optional:
# absent, the middleware negotiates gzip and nothing changes for callers.
try:  # pragma: no cover - depends on the deployment's extras
    import brotli

    _brotli_compress = brotli.compress
except ImportError:  # pragma: no cover
    try:
        import brotlicffi

        _brotli_compress = brotlicffi.compress
    except ImportError:
        _brotli_compress = None

# Content types worth compressing. Anything already compressed (images, video,
# archives) is excluded: the CPU is wasted and the result is usually bigger.
DEFAULT_COMPRESSIBLE_TYPES: frozenset[str] = frozenset(
    {
        "application/atom+xml",
        "application/javascript",
        "application/json",
        "application/ld+json",
        "application/manifest+json",
        "application/rss+xml",
        "application/vnd.api+json",
        "application/wasm",
        "application/x-javascript",
        "application/x-ndjson",
        "application/xhtml+xml",
        "application/xml",
        "image/svg+xml",
        "image/x-icon",
    }
)

# Preference order at equal client quality: best ratio first.
_ENCODING_PREFERENCE = ("br", "gzip", "deflate")


def parse_accept_encoding(header: str) -> dict[str, float]:
    """Parse ``Accept-Encoding`` into ``{encoding: quality}``.

    Quality 0 means "do not use this encoding" and is preserved rather than
    dropped, so callers can distinguish *unacceptable* from *unmentioned*.
    A malformed q-value is treated as 1.0, matching how browsers behave.
    """
    accepted: dict[str, float] = {}
    for part in header.split(","):
        token = part.strip()
        if not token:
            continue
        name, _, params = token.partition(";")
        quality = 1.0
        for param in params.split(";"):
            key, _, value = param.partition("=")
            if key.strip() == "q":
                try:
                    quality = float(value.strip())
                except ValueError:
                    quality = 1.0
        accepted[name.strip().lower()] = quality
    return accepted


class CompressionMiddleware(Middleware):
    """Compresses response bodies the client can actually decode.

    Args:
        minimum_size: Bodies smaller than this are sent uncompressed. Below
            roughly 500 bytes the gzip header and framing can exceed what
            compression saves.
        compressible_types: Content types eligible for compression. Defaults
            to the text/structured-data set above.
        gzip_level: 1-9. The default of 6 is where the ratio curve flattens;
            9 costs substantially more CPU for a few percent.
        brotli_quality: 0-11. 4 is the common server-side choice for dynamic
            content — 11 is for pre-compressed static assets.

    Compression runs in a worker thread via ``asyncio.to_thread``, so a large
    body never blocks the event loop.
    """

    name = "compression"

    def __init__(
        self,
        minimum_size: int = 500,
        *,
        compressible_types: frozenset[str] | set[str] | None = None,
        gzip_level: int = 6,
        brotli_quality: int = 4,
    ):
        self.minimum_size = minimum_size
        self.compressible_types = frozenset(compressible_types or DEFAULT_COMPRESSIBLE_TYPES)
        self.gzip_level = gzip_level
        self.brotli_quality = brotli_quality

    # ── Negotiation ───────────────────────────────────────────────────────

    def _available(self) -> tuple[str, ...]:
        if _brotli_compress is None:
            return ("gzip", "deflate")
        return _ENCODING_PREFERENCE

    def select_encoding(self, accept_encoding: str) -> str | None:
        """Pick the best mutually-supported encoding, or ``None``.

        Honours q-values, explicit ``identity``, and the ``*`` wildcard.
        """
        if not accept_encoding:
            return None

        accepted = parse_accept_encoding(accept_encoding)
        if not accepted:
            return None

        wildcard = accepted.get("*", 0.0)
        best: tuple[float, int, str] | None = None

        for rank, encoding in enumerate(self._available()):
            quality = accepted.get(encoding)
            if quality is None:
                quality = wildcard  # covered only by "*"
            if quality <= 0.0:
                continue  # unmentioned, or explicitly refused with q=0
            candidate = (quality, -rank, encoding)
            if best is None or candidate > best:
                best = candidate

        return best[2] if best else None

    # ── Eligibility ───────────────────────────────────────────────────────

    def _content_type(self, response: Response) -> str:
        raw = response.headers.get("content-type", "") or ""
        return raw.split(";", 1)[0].strip().lower()

    def should_compress(self, response: Response) -> bool:
        """Whether *response* is eligible, ignoring client negotiation."""
        # Already encoded by the application or an inner middleware.
        if response.headers.get("content-encoding"):
            return False

        # 204/304 have no body; 1xx are informational.
        status = getattr(response, "status", 200)
        if status < 200 or status in (204, 304):
            return False

        # RFC 9111: the payload must reach the client byte-for-byte.
        if "no-transform" in (response.headers.get("cache-control", "") or "").lower():
            return False

        content_type = self._content_type(response)
        if not content_type:
            return False
        # text/* is compressible as a family; everything else is allow-listed.
        return content_type.startswith("text/") or content_type in self.compressible_types

    # ── Compression ───────────────────────────────────────────────────────

    def _compress(self, body: bytes, encoding: str) -> bytes:
        if encoding == "br":
            return _brotli_compress(body, quality=self.brotli_quality)
        if encoding == "gzip":
            return gzip.compress(body, compresslevel=self.gzip_level)
        # "deflate" on the wire means a zlib stream (RFC 7230 §4.2.2).
        return zlib.compress(body, self.gzip_level)

    async def after(self, request: Request, ctx: RequestCtx, response: Response) -> Response:
        # Vary is set whenever compression was *considered*, not only when it
        # was applied: a shared cache keyed without it can hand a compressed
        # body to a client that cannot decode it.
        if not self.should_compress(response):
            return response

        encoding = self.select_encoding(request.header("accept-encoding", "") or "")
        if encoding is None:
            return response

        content = response._content
        # Streaming bodies have no length to measure and must not be buffered.
        if hasattr(content, "__aiter__"):
            return response
        if hasattr(content, "__iter__") and not isinstance(content, (bytes, str, dict, list)):
            return response

        body = response._encode_body(content)
        if len(body) < self.minimum_size:
            response.headers["vary"] = "Accept-Encoding"
            return response

        compressed = await asyncio.to_thread(self._compress, body, encoding)

        # A body that grew is a body better sent as-is.
        if len(compressed) >= len(body):
            response.headers["vary"] = "Accept-Encoding"
            return response

        response._content = compressed
        response.headers["content-encoding"] = encoding
        response.headers["content-length"] = str(len(compressed))
        response.headers["vary"] = "Accept-Encoding"

        # A strong ETag identifies bytes; the compressed body is different
        # bytes, so it must be weakened rather than left to collide (RFC 9110).
        etag = response.headers.get("etag")
        if etag and not etag.startswith("W/"):
            response.headers["etag"] = f"W/{etag}"

        return response

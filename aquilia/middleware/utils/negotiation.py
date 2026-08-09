"""Content negotiation helpers — dependency-free leaf module.

Extracted from ``ExceptionMiddleware._wants_html``, where it was a private
method wrapped in a bare ``except Exception``. As a free function it is
unit-testable without constructing a request, and the error middleware, the
debug pages, and the fault engine can all share one answer to "does this client
want HTML?".
"""

from __future__ import annotations

from typing import Any


def accept_header(request: Any) -> str:
    """Read the Accept header, tolerating partially-built request objects.

    Called from exception handling, where the request may be malformed — that
    is often *why* we are here. Returns ``""`` rather than raising.
    """
    try:
        headers = getattr(request, "headers", None)
        if headers is None:
            return ""
        if hasattr(headers, "get"):
            return headers.get("accept", "") or ""
        if isinstance(headers, dict):
            return headers.get("accept", "") or headers.get("Accept", "") or ""
    except Exception:
        return ""
    return ""


def wants_html(request: Any) -> bool:
    """True when the client prefers an HTML error page over JSON."""
    return "text/html" in accept_header(request)


__all__ = ["accept_header", "wants_html"]

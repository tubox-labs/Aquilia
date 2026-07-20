"""
Effect introspection — ``@requires(...)`` effect names for operation extensions.
"""

from __future__ import annotations

from typing import Any

#: Human-readable descriptions of well-known Aquilia effects. The UI renders
#: these as chip tooltips.
EFFECT_DOCS: dict[str, str] = {
    "DBTx": "Database transaction — acquired/released per-request by EffectMiddleware",
    "Cache": "Cache read/write — uses CacheService (Redis or Memory backend)",
    "Queue": "Message queue — enqueues background tasks",
    "HTTP": "Outbound HTTP client — rate-limited, with retry and circuit-breaker",
    "Storage": "File storage — local, S3, GCS, Azure, or SFTP backend",
}


def handler_effects(handler: Any) -> list[str]:
    """Effect names declared via ``@requires(...)`` on a handler."""
    return list(getattr(handler, "__flow_effects__", None) or [])

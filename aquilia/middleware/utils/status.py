"""Fault → HTTP status mapping — dependency-free leaf module.

Extracted from the 150-line ``except Fault`` block inside
``ExceptionMiddleware``. As a pure function it is unit-testable without
constructing a request, and the fault engine can reuse it to answer "what
status would this fault produce?" without instantiating middleware.

Deliberately duck-typed rather than importing ``aquilia.faults``: this module
sits in the fault-free leaf zone, and everything it needs from a fault is
``code`` and ``domain``.
"""

from __future__ import annotations

from typing import Any

# Faults meaning "we do not know who you are" — 401, not the 403 the SECURITY
# domain would otherwise produce. Authorization failures (authenticated but not
# permitted) keep 403.
UNAUTHENTICATED_CODES: frozenset[str] = frozenset(
    {
        "AUTH_010",  # AUTH_REQUIRED
        "AUTHENTICATION_REQUIRED",  # AuthenticationRequiredFault / session decorators
        "SESSION_REQUIRED",  # SessionRequiredFault
        "INVALID_CREDENTIALS",  # Auth module login failure
    }
)

CONFLICT_CODES: frozenset[str] = frozenset(
    {
        "USER_ALREADY_EXISTS",  # Auth module registration failure
    }
)

# Keyed by ``FaultDomain`` *value* strings so this module need not import the
# enum. ``HTTPFault`` carries its own explicit status and is handled before
# this map is ever consulted.
DOMAIN_STATUS: dict[str, int] = {
    "routing": 404,
    "security": 403,
    "io": 502,
    "effect": 503,
    "model": 404,  # usually a DB row that was not found
    "cache": 502,
    "config": 500,
    "registry": 500,
    "di": 500,
    "flow": 500,
    "system": 500,
    "storage": 502,
    "tasks": 503,
    "template": 500,
    "http": 500,  # fallback; HTTPFault is caught earlier
}

DEFAULT_STATUS = 500


def _domain_value(domain: Any) -> str:
    """Normalise a ``FaultDomain`` or plain string to its lowercase value."""
    return str(getattr(domain, "value", domain) or "").lower()


def fault_to_status(fault: Any) -> int:
    """Map a fault to an HTTP status code.

    Resolution order, most specific first:

    1. Explicit ``status`` attribute (``HTTPFault``).
    2. Known authentication / conflict codes.
    3. Code-substring heuristics (``NOT_FOUND``/``MISSING`` → 404,
       ``VALIDATION``/``INVALID`` → 400).
    4. The ``auth`` domain → 401.
    5. The domain table above, defaulting to 500.
    """
    status = getattr(fault, "status", None)
    if isinstance(status, int):
        return status

    code = getattr(fault, "code", None)
    if code:
        code = str(code)
        if code in UNAUTHENTICATED_CODES:
            return 401
        if code in CONFLICT_CODES:
            return 409
        if "NOT_FOUND" in code or "MISSING" in code:
            return 404
        if "VALIDATION" in code or "INVALID" in code:
            return 400

    domain = _domain_value(getattr(fault, "domain", None))
    if domain == "auth":
        return 401
    return DOMAIN_STATUS.get(domain, DEFAULT_STATUS)


__all__ = [
    "fault_to_status",
    "DOMAIN_STATUS",
    "UNAUTHENTICATED_CODES",
    "CONFLICT_CODES",
    "DEFAULT_STATUS",
]

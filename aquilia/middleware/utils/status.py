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
# permitted) keep 403. All AUTH_0xx authentication codes (bad credentials,
# invalid/expired/revoked tokens, MFA challenges, locked accounts, OAuth
# client/grant failures) mean the caller did not prove an identity → 401
# (RFC 9110 §15.5.2). AUTH_1xx (password policy) and AUTH_4xx (MFA enrolment)
# are request-body problems → 400; AUTH_009/AUTH_304 carry Retry-After
# semantics → 429.
UNAUTHENTICATED_CODES: frozenset[str] = frozenset(
    {
        "AUTH_001",  # AUTH_INVALID_CREDENTIALS
        "AUTH_002",  # AUTH_TOKEN_INVALID
        "AUTH_003",  # AUTH_TOKEN_EXPIRED
        "AUTH_004",  # AUTH_TOKEN_REVOKED
        "AUTH_005",  # AUTH_MFA_REQUIRED (identity not yet proven)
        "AUTH_006",  # AUTH_MFA_INVALID
        "AUTH_007",  # AUTH_ACCOUNT_SUSPENDED
        "AUTH_010",  # AUTH_REQUIRED
        "AUTH_011",  # AUTH_CLIENT_INVALID
        "AUTH_012",  # AUTH_GRANT_INVALID
        "AUTH_013",  # AUTH_REDIRECT_URI_MISMATCH
        "AUTH_014",  # AUTH_SCOPE_INVALID
        "AUTH_015",  # AUTH_PKCE_INVALID
        "AUTH_201",  # AUTH_SESSION_REQUIRED
        "AUTH_202",  # AUTH_SESSION_INVALID
        "AUTH_203",  # AUTH_SESSION_HIJACK_DETECTED
        "AUTH_301",  # AUTH_CONSENT_REQUIRED (OAuth identity not yet granted)
        "AUTH_302",  # AUTH_DEVICE_CODE_PENDING
        "AUTH_303",  # AUTH_DEVICE_CODE_EXPIRED
        "AUTHENTICATION_REQUIRED",  # AuthenticationRequiredFault / session decorators
        "SESSION_REQUIRED",  # SessionRequiredFault
        "INVALID_CREDENTIALS",  # Auth module login failure
    }
)

#: Rate-limit-style auth faults — the caller must slow down (429), not
#: re-authenticate. ``retry_after`` on the fault carries the window.
AUTH_RATE_LIMIT_CODES: frozenset[str] = frozenset(
    {
        "AUTH_008",  # AUTH_ACCOUNT_LOCKED
        "AUTH_009",  # AUTH_RATE_LIMITED
        "AUTH_304",  # AUTH_SLOW_DOWN
    }
)

#: Request-payload auth faults — the submitted credential/consent data is
#: malformed per policy; re-submitting the same value cannot succeed.
AUTH_BAD_REQUEST_CODES: frozenset[str] = frozenset(
    {
        "AUTH_101",  # AUTH_PASSWORD_WEAK
        "AUTH_102",  # AUTH_PASSWORD_BREACHED
        "AUTH_103",  # AUTH_PASSWORD_REUSED
        "AUTH_401",  # AUTH_MFA_NOT_ENROLLED
        "AUTH_402",  # AUTH_MFA_ALREADY_ENROLLED
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
    # Contract faults (cast/seal/imprint) reject the *request payload* --
    # the client sent data the contract refused. Reporting these as 500
    # made every validation failure look like a server bug and hid the
    # per-field details behind an error clients treat as transient.
    "contract": 400,
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
    2. Known authentication / rate-limit / bad-request / conflict codes.
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
        if code in AUTH_RATE_LIMIT_CODES:
            return 429
        if code in AUTH_BAD_REQUEST_CODES:
            return 400
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
    "AUTH_RATE_LIMIT_CODES",
    "AUTH_BAD_REQUEST_CODES",
    "CONFLICT_CODES",
    "DEFAULT_STATUS",
]

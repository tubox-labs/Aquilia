"""Regression checks for the middleware audit follow-ups.

Covers the findings closed after BUG-01/BUG-02/FIND-05:

- FIND-06: ``MiddlewareStack.build_fast_handler`` and its skip-list were dead
  code advertised by the module docstring; both are gone.
- FIND-07: the priority layout documented in
  ``AquiliaServer._setup_security_middleware`` drifted from the actual
  ``add()`` calls (CSRF was documented at 10, registered at 20).
- Audit §7: the WebSocket rate limiter no longer reimplements its own token
  bucket -- it shares the HTTP one, and evicts idle connections.
"""

from __future__ import annotations

import inspect
import re

from aquilia.middleware.builtin.rate_limit import _BucketStore, _TokenBucket
from aquilia.middleware.core.priority import Priority
from aquilia.middleware.stack import MiddlewareStack
from aquilia.server import AquiliaServer
from aquilia.sockets.middleware import RateLimitMiddleware


# ── FIND-06: dead fast-path chain builder is gone ────────────────────────────


def test_build_fast_handler_is_gone():
    """The unreachable 'fast lane' chain builder must not come back unwired."""
    assert not hasattr(MiddlewareStack, "build_fast_handler")

    import aquilia.middleware as mw_mod

    assert not hasattr(mw_mod, "_FAST_SKIP_NAMES")


def test_module_docstring_no_longer_advertises_fast_handler():
    import aquilia.middleware as mw_mod

    assert "build_fast_handler" not in (mw_mod.__doc__ or "")


# ── FIND-07: documented priorities match registered priorities ───────────────


def _registered_priorities() -> dict[str, str]:
    """Map ``name=`` to the *expression* registered as its priority.

    FIND-07 was a docstring table drifting out of step with the ``add()`` calls
    below it. That table is gone: priorities now live in
    ``aquilia.middleware.core.priority.Priority`` and the registrations
    reference it by name, so there is only one place left to be wrong. These
    tests police the replacement invariant -- no bare integers here.
    """
    src = inspect.getsource(AquiliaServer._setup_security_middleware)
    return {name: expr for expr, name in re.findall(r'priority=([\w.]+),\s*name="([^"]+)"', src)}


def test_registered_priorities_use_named_constants():
    """No magic integers: every registration cites a Priority constant."""
    registered = _registered_priorities()
    assert registered, "regex failed to find any middleware registrations"

    literals = {name: expr for name, expr in registered.items() if expr.isdigit()}
    assert not literals, f"registered with bare integer priorities: {literals}"

    unknown = {
        name: expr
        for name, expr in registered.items()
        if not hasattr(Priority, expr.removeprefix("Priority."))
    }
    assert not unknown, f"registered with unknown Priority constants: {unknown}"


def test_csrf_registers_at_its_named_priority():
    """FIND-07: the docstring claimed CSRF ran at 10; it has always run at 20."""
    assert _registered_priorities()["csrf"] == "Priority.CSRF"
    assert Priority.CSRF == 20


def test_csrf_runs_after_auth():
    """The ordering CSRF depends on: it needs the session auth establishes."""
    from aquilia.server import _AUTH_PRIORITY

    assert Priority.CSRF > Priority.AUTH
    assert _AUTH_PRIORITY == Priority.AUTH


# ── Shared token bucket: zero refill rate must not divide by zero ────────────


def test_token_bucket_with_zero_refill_rate_reports_retry_instead_of_crashing():
    """A limit=0 rule yields refill_rate=0.0; the deficit branch must not divide by it."""
    bucket = _TokenBucket(capacity=1, refill_rate=0.0)

    allowed, retry_after = bucket.consume()
    assert allowed is True
    assert retry_after == 0.0

    allowed, retry_after = bucket.consume()  # drained, and it never refills
    assert allowed is False
    assert retry_after > 0.0


# ── Audit §7: WebSocket rate limiter shares the HTTP algorithm ──────────────
#
# The socket limiter moved to aquilia.sockets.middleware.builtin and now takes
# the three-hook SocketMiddleware interface. What these still pin down is the
# property the audit asked for: it is not a second implementation of the bucket.


def test_socket_rate_limiter_uses_the_http_token_bucket():
    """Not a reimplementation: the buckets are the HTTP ones, in the HTTP store."""
    mw = RateLimitMiddleware(messages_per_second=10, burst=20)

    assert isinstance(mw._buckets, _BucketStore)
    assert isinstance(mw._factory(), _TokenBucket)

    # The old inline implementation kept these two unbounded dicts.
    assert not hasattr(mw, "_tokens")
    assert not hasattr(mw, "_last_refill")


def test_deprecated_alias_points_at_the_socket_limiter():
    from aquilia.sockets.middleware import SocketRateLimitMiddleware

    assert RateLimitMiddleware is SocketRateLimitMiddleware

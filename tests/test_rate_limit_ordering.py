"""Regression tests for per-user rate-limit ordering (#64).

``user_key_extractor`` reads the identity that the auth middleware puts on
``request.state``. Rate limiting used to register at priority 12 and auth at 15
— and since ascending priority means outer/earlier, the extractor always ran
first, always returned None, and every per-user rule was silently skipped.
"""

import logging

from aquilia.middleware.builtin.rate_limit import (
    RateLimitMiddleware,
    RateLimitRule,
    ip_key_extractor,
    user_key_extractor,
)
from aquilia.response import Response
from aquilia.server import _AUTH_PRIORITY, _RATE_LIMIT_IDENTITY_PRIORITY


class _FakeIdentity:
    def __init__(self, ident: str):
        self.id = ident


class _FakeRequest:
    """Minimal stand-in — the extractors only touch .state."""

    def __init__(self, state: dict | None = None):
        self.state = state or {}
        self.method = "GET"
        self.path = "/api/thing"


def test_identity_rules_register_after_auth():
    """The whole bug: an identity rule evaluated before auth can never key."""
    assert _RATE_LIMIT_IDENTITY_PRIORITY > _AUTH_PRIORITY


def test_per_user_rule_is_flagged_as_identity_dependent():
    """Auto-detection drives the priority split, so it must hold for the config path."""
    rule = RateLimitRule(key_func=user_key_extractor)
    assert rule.requires_identity is True


def test_ip_rule_is_not_identity_dependent():
    rule = RateLimitRule(key_func=ip_key_extractor)
    assert rule.requires_identity is False

    # Default (no key_func) is IP-based and must stay early in the chain.
    assert RateLimitRule().requires_identity is False


def test_custom_extractor_can_declare_identity_dependence():
    rule = RateLimitRule(key_func=lambda r: "custom", requires_identity=True)
    assert rule.requires_identity is True


def test_user_key_extractor_needs_identity_on_state():
    """Before auth runs, state is empty and the rule yields no key."""
    assert user_key_extractor(_FakeRequest()) is None

    after_auth = _FakeRequest({"identity": _FakeIdentity("u-42")})
    assert user_key_extractor(after_auth) == "user:u-42"


async def test_missing_identity_warns_instead_of_silently_skipping(caplog):
    """A misregistered identity rule must be loud — that was the real defect."""
    mw = RateLimitMiddleware(rules=[RateLimitRule(key_func=user_key_extractor)])
    request = _FakeRequest()
    sentinel = object()

    async def next_handler(req, ctx):
        return sentinel

    with caplog.at_level(logging.WARNING, logger="aquilia.middleware.rate_limit"):
        result = await mw(request, None, next_handler)

    # Request still passes through — the rule is skipped, not enforced.
    assert result is sentinel
    assert "requires an authenticated identity" in caplog.text
    assert mw._warned_missing_identity is True

    # Warn once, not once per request.
    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="aquilia.middleware.rate_limit"):
        await mw(request, None, next_handler)
    assert "requires an authenticated identity" not in caplog.text


async def test_identity_rule_enforces_once_auth_has_run():
    """With identity present (post-auth ordering), the limit actually applies."""
    mw = RateLimitMiddleware(rules=[RateLimitRule(limit=1, window=60, key_func=user_key_extractor)])
    request = _FakeRequest({"identity": _FakeIdentity("u-42")})

    async def next_handler(req, ctx):
        return Response.json({"ok": True})

    first = await mw(request, None, next_handler)
    assert first.status == 200

    # Second call for the same identity exceeds limit=1.
    second = await mw(request, None, next_handler)
    assert second.status == 429


async def test_identity_rule_keys_per_user_not_globally():
    """Exhausting user A must not rate-limit user B."""
    mw = RateLimitMiddleware(rules=[RateLimitRule(limit=1, window=60, key_func=user_key_extractor)])

    async def next_handler(req, ctx):
        return Response.json({"ok": True})

    user_a = _FakeRequest({"identity": _FakeIdentity("u-a")})
    assert (await mw(user_a, None, next_handler)).status == 200
    assert (await mw(user_a, None, next_handler)).status == 429

    user_b = _FakeRequest({"identity": _FakeIdentity("u-b")})
    assert (await mw(user_b, None, next_handler)).status == 200

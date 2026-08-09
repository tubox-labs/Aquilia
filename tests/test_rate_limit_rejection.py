"""Regression tests for issue #67 -- rate-limit rejection must return 429.

`Response` was imported under TYPE_CHECKING only, so `_rate_limited_response`
raised NameError at runtime and no request was ever actually rejected. These
tests exercise the rejection path directly, for both response formats.
"""

from aquilia.middleware.builtin.rate_limit import RateLimitMiddleware, RateLimitRule
from aquilia.response import Response


class _FakeRequest:
    def __init__(self, ip: str = "1.2.3.4"):
        self.state: dict = {}
        self.method = "GET"
        self.path = "/limited"
        # ip_key_extractor reads the ASGI scope, not a .client attribute.
        self._scope = {"client": (ip, 0)}

    def header(self, name: str):
        return None


async def _next_handler(request, ctx):
    return Response.json({"ok": True})


async def test_json_rejection_returns_429():
    mw = RateLimitMiddleware(rules=[RateLimitRule(limit=1, window=60)])
    request = _FakeRequest()

    assert (await mw(request, None, _next_handler)).status == 200

    # Previously raised NameError instead of building the 429.
    rejected = await mw(request, None, _next_handler)
    assert rejected.status == 429


async def test_plain_rejection_returns_429():
    mw = RateLimitMiddleware(
        rules=[RateLimitRule(limit=1, window=60)],
        response_format="plain",
    )
    request = _FakeRequest()

    assert (await mw(request, None, _next_handler)).status == 200
    assert (await mw(request, None, _next_handler)).status == 429


async def test_rejection_carries_retry_and_limit_headers():
    mw = RateLimitMiddleware(rules=[RateLimitRule(limit=1, window=60)])
    request = _FakeRequest()

    await mw(request, None, _next_handler)
    rejected = await mw(request, None, _next_handler)

    assert rejected.headers["retry-after"]
    assert rejected.headers["x-ratelimit-limit"] == "1"
    assert rejected.headers["x-ratelimit-remaining"] == "0"


async def test_rejection_attaches_fault_for_observability():
    """resp._fault was unreachable while the path raised NameError."""
    mw = RateLimitMiddleware(rules=[RateLimitRule(limit=1, window=60)])
    request = _FakeRequest()

    await mw(request, None, _next_handler)
    rejected = await mw(request, None, _next_handler)

    assert rejected._fault is not None
    assert rejected._fault.code == rejected.headers["x-fault-code"]


async def test_under_limit_requests_are_untouched():
    mw = RateLimitMiddleware(rules=[RateLimitRule(limit=5, window=60)])
    request = _FakeRequest()

    for _ in range(5):
        assert (await mw(request, None, _next_handler)).status == 200


async def test_distinct_ips_are_limited_independently():
    mw = RateLimitMiddleware(rules=[RateLimitRule(limit=1, window=60)])

    assert (await mw(_FakeRequest("10.0.0.1"), None, _next_handler)).status == 200
    assert (await mw(_FakeRequest("10.0.0.1"), None, _next_handler)).status == 429
    assert (await mw(_FakeRequest("10.0.0.2"), None, _next_handler)).status == 200

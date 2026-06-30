"""
Comprehensive tests for Aquilia's API Versioning System.

Tests cover all 11 submodules:
  1. core.py — ApiVersion, VersionChannel, VersionStatus, sentinels
  2. errors.py — All versioning error classes
  3. parser.py — SemanticVersionParser (semantic + epoch formats)
  4. resolvers.py — URL, header, query, media-type, channel, composite
  5. graph.py — VersionGraph compile-time structure
  6. sunset.py — SunsetPolicy, SunsetRegistry, SunsetEnforcer
  7. negotiation.py — NegotiationMode, VersionNegotiator
  8. strategy.py — VersionConfig, VersionStrategy orchestrator
  9. middleware.py — VersionMiddleware request processing
  10. decorators.py — @version(), @version_neutral, @version_range()
  11. Integration — RouteDecorator version param, metadata, router, config
"""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

# ════════════════════════════════════════════════════════════════════════════
#  1. CORE TYPES
# ════════════════════════════════════════════════════════════════════════════


class TestApiVersion:
    """Tests for ApiVersion frozen dataclass."""

    def test_basic_creation(self):
        from aquilia.versioning.core import ApiVersion

        v = ApiVersion(2, 1)
        assert v.major == 2
        assert v.minor == 1
        assert v.patch == 0
        assert str(v) == "2.1"

    def test_with_patch(self):
        from aquilia.versioning.core import ApiVersion

        v = ApiVersion(1, 2, 3)
        assert str(v) == "1.2.3"

    def test_with_label(self):
        from aquilia.versioning.core import ApiVersion

        v = ApiVersion(2025, 1, label="2025-01")
        assert v.label == "2025-01"
        assert str(v) == "2025-01"

    def test_comparison_eq(self):
        from aquilia.versioning.core import ApiVersion

        assert ApiVersion(2, 0) == ApiVersion(2, 0)
        assert ApiVersion(2, 0) != ApiVersion(2, 1)

    def test_comparison_lt(self):
        from aquilia.versioning.core import ApiVersion

        assert ApiVersion(1, 0) < ApiVersion(2, 0)
        assert ApiVersion(2, 0) < ApiVersion(2, 1)
        assert ApiVersion(2, 1, 0) < ApiVersion(2, 1, 1)

    def test_comparison_ordering(self):
        from aquilia.versioning.core import ApiVersion

        versions = [ApiVersion(3, 0), ApiVersion(1, 0), ApiVersion(2, 1)]
        assert sorted(versions) == [
            ApiVersion(1, 0),
            ApiVersion(2, 1),
            ApiVersion(3, 0),
        ]

    def test_hash(self):
        from aquilia.versioning.core import ApiVersion

        s = {ApiVersion(1, 0), ApiVersion(2, 0), ApiVersion(1, 0)}
        assert len(s) == 2

    def test_parse_semantic(self):
        from aquilia.versioning.core import ApiVersion

        v = ApiVersion.parse("v2.1")
        assert v == ApiVersion(2, 1)

    def test_parse_without_prefix(self):
        from aquilia.versioning.core import ApiVersion

        v = ApiVersion.parse("3.0.1")
        assert v == ApiVersion(3, 0, 1)

    def test_parse_epoch(self):
        from aquilia.versioning.core import ApiVersion

        v = ApiVersion.parse("2025-06")
        assert v.label == "2025-06"
        assert v.major == 2025
        assert v.minor == 6

    def test_is_compatible_with(self):
        from aquilia.versioning.core import ApiVersion

        v1 = ApiVersion(2, 0)
        v2 = ApiVersion(2, 3)
        v3 = ApiVersion(3, 0)
        # v2.3 is compatible with v2.0 (same major, higher minor)
        assert v2.is_compatible_with(v1)
        # v2.0 is NOT compatible with v2.3 (same major, lower minor)
        assert not v1.is_compatible_with(v2)
        # v2.0 is NOT compatible with v3.0 (different major)
        assert not v1.is_compatible_with(v3)

    def test_matches(self):
        from aquilia.versioning.core import ApiVersion

        v = ApiVersion(2, 1, 3)
        assert v.matches(ApiVersion(2, 1))  # major.minor match
        assert v.matches(ApiVersion(2, 1, 5))  # different patch, same major.minor
        assert not v.matches(ApiVersion(2, 0))

    def test_url_segment(self):
        from aquilia.versioning.core import ApiVersion

        v = ApiVersion(2, 0)
        assert v.url_segment == "v2"  # minor=0 is omitted
        v2 = ApiVersion(2, 1)
        assert v2.url_segment == "v2.1"

    def test_with_status(self):
        from aquilia.versioning.core import ApiVersion, VersionStatus

        v = ApiVersion(1, 0)
        v2 = v.with_status(VersionStatus.DEPRECATED)
        assert v2.status == VersionStatus.DEPRECATED

    def test_with_channel(self):
        from aquilia.versioning.core import ApiVersion, VersionChannel

        v = ApiVersion(2, 0)
        v2 = v.with_channel(VersionChannel.PREVIEW)
        assert v2.channel == VersionChannel.PREVIEW

    def test_to_dict(self):
        from aquilia.versioning.core import ApiVersion

        v = ApiVersion(2, 1, 3)
        d = v.to_dict()
        assert d["major"] == 2
        assert d["minor"] == 1
        assert d["patch"] == 3

    def test_frozen(self):
        from dataclasses import FrozenInstanceError

        from aquilia.versioning.core import ApiVersion

        v = ApiVersion(1, 0)
        with pytest.raises(FrozenInstanceError):
            v.major = 2  # frozen dataclass


class TestVersionChannel:
    def test_values(self):
        from aquilia.versioning.core import VersionChannel

        assert VersionChannel.STABLE.value == "stable"
        assert VersionChannel.PREVIEW.value == "preview"
        assert VersionChannel.LEGACY.value == "legacy"
        assert VersionChannel.SUNSET.value == "sunset"
        assert VersionChannel.CANARY.value == "canary"


class TestVersionStatus:
    def test_lifecycle(self):
        from aquilia.versioning.core import VersionStatus

        assert VersionStatus.PREVIEW.is_usable
        assert VersionStatus.ACTIVE.is_usable
        assert VersionStatus.DEPRECATED.is_usable
        assert VersionStatus.DEPRECATED.is_warn
        assert VersionStatus.SUNSET.is_warn
        assert not VersionStatus.ACTIVE.is_warn
        assert not VersionStatus.SUNSET.is_terminal  # SUNSET is warn, not terminal
        assert VersionStatus.RETIRED.is_terminal  # Only RETIRED is terminal
        assert not VersionStatus.ACTIVE.is_terminal
        assert not VersionStatus.SUNSET.is_usable  # SUNSET cannot serve requests


class TestSentinels:
    def test_version_neutral(self):
        from aquilia.versioning.core import VERSION_NEUTRAL

        assert str(VERSION_NEUTRAL) == "VERSION_NEUTRAL"
        assert repr(VERSION_NEUTRAL) == "VERSION_NEUTRAL"
        assert VERSION_NEUTRAL == VERSION_NEUTRAL

    def test_version_any(self):
        from aquilia.versioning.core import VERSION_ANY

        assert str(VERSION_ANY) == "VERSION_ANY"


# ════════════════════════════════════════════════════════════════════════════
#  2. ERRORS
# ════════════════════════════════════════════════════════════════════════════


class TestVersionErrors:
    def test_invalid_version_error(self):
        from aquilia.versioning.errors import InvalidVersionError

        e = InvalidVersionError("abc")
        assert e.raw_version == "abc"
        assert "abc" in str(e.message)

    def test_unsupported_version_error(self):
        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.errors import UnsupportedVersionError

        v = ApiVersion(9, 9)
        e = UnsupportedVersionError(v, supported=[ApiVersion(1, 0), ApiVersion(2, 0)])
        assert e.version == v
        assert len(e.supported) == 2

    def test_sunset_error(self):
        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.errors import VersionSunsetError

        v = ApiVersion(1, 0)
        e = VersionSunsetError(
            version=v,
            sunset_date=datetime(2024, 1, 1),
            migration_url="https://docs.example.com/migrate",
            successor=ApiVersion(2, 0),
        )
        assert e.version == v
        assert e.successor == ApiVersion(2, 0)
        assert "migrate" in e.migration_url

    def test_missing_version_error(self):
        from aquilia.versioning.errors import MissingVersionError

        e = MissingVersionError(strategies=["header", "query"])
        assert len(e.metadata["strategies"]) == 2
        assert "header" in e.metadata["strategies"]
        assert "query" in e.metadata["strategies"]

    def test_negotiation_error(self):
        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.errors import VersionNegotiationError

        e = VersionNegotiationError(
            requested=ApiVersion(5, 0),
            available=[ApiVersion(1, 0), ApiVersion(2, 0)],
        )
        assert e.metadata["requested"] == "5"
        assert len(e.metadata["available"]) == 2


# ════════════════════════════════════════════════════════════════════════════
#  3. PARSER
# ════════════════════════════════════════════════════════════════════════════


class TestSemanticVersionParser:
    def setup_method(self):
        from aquilia.versioning.parser import SemanticVersionParser

        self.parser = SemanticVersionParser()

    def test_parse_major_minor(self):
        v = self.parser.parse("2.1")
        assert v.major == 2
        assert v.minor == 1
        assert v.patch == 0

    def test_parse_with_v_prefix(self):
        v = self.parser.parse("v3.2")
        assert v.major == 3
        assert v.minor == 2

    def test_parse_full_semver(self):
        v = self.parser.parse("1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3

    def test_parse_epoch(self):
        v = self.parser.parse("2025-06")
        assert v.label == "2025-06"
        assert v.major == 2025
        assert v.minor == 6

    def test_parse_single_number(self):
        v = self.parser.parse("3")
        assert v.major == 3
        assert v.minor == 0

    def test_parse_invalid(self):
        from aquilia.versioning.errors import InvalidVersionError

        with pytest.raises(InvalidVersionError):
            self.parser.parse("not-a-version")

    def test_format(self):
        from aquilia.versioning.core import ApiVersion

        v = ApiVersion(2, 1, 3)
        assert self.parser.format(v) == "2.1.3"

    def test_format_epoch(self):
        from aquilia.versioning.core import ApiVersion

        v = ApiVersion(2025, 6, label="2025-06")
        assert self.parser.format(v) == "2025-06"


# ════════════════════════════════════════════════════════════════════════════
#  4. RESOLVERS
# ════════════════════════════════════════════════════════════════════════════


def _make_request(
    path="/",
    headers=None,
    query_string=b"",
    method="GET",
):
    """Create a minimal mock request for resolver tests."""
    from aquilia.request import Request

    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "query_string": query_string,
        "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
    }
    return Request(scope, receive=AsyncMock())


class TestHeaderResolver:
    def test_resolve_default_header(self):
        from aquilia.versioning.resolvers import HeaderResolver

        r = HeaderResolver()
        req = _make_request(headers={"x-api-version": "2.0"})
        assert r.resolve(req) == "2.0"

    def test_resolve_custom_header(self):
        from aquilia.versioning.resolvers import HeaderResolver

        r = HeaderResolver(header_name="API-Version")
        req = _make_request(headers={"api-version": "3.1"})
        assert r.resolve(req) == "3.1"

    def test_missing_header(self):
        from aquilia.versioning.resolvers import HeaderResolver

        r = HeaderResolver()
        req = _make_request()
        assert r.resolve(req) is None

    def test_name(self):
        from aquilia.versioning.resolvers import HeaderResolver

        r = HeaderResolver()
        assert r.name == "header"


class TestQueryParamResolver:
    def test_resolve(self):
        from aquilia.versioning.resolvers import QueryParamResolver

        r = QueryParamResolver()
        req = _make_request(query_string=b"api_version=2.0&other=xyz")
        assert r.resolve(req) == "2.0"

    def test_custom_param(self):
        from aquilia.versioning.resolvers import QueryParamResolver

        r = QueryParamResolver(param_name="v")
        req = _make_request(query_string=b"v=1.0")
        assert r.resolve(req) == "1.0"

    def test_missing(self):
        from aquilia.versioning.resolvers import QueryParamResolver

        r = QueryParamResolver()
        req = _make_request()
        assert r.resolve(req) is None


class TestURLPathResolver:
    def test_resolve(self):
        from aquilia.versioning.resolvers import URLPathResolver

        r = URLPathResolver()
        req = _make_request(path="/v2/users")
        assert r.resolve(req) == "2"

    def test_resolve_with_minor(self):
        from aquilia.versioning.resolvers import URLPathResolver

        r = URLPathResolver()
        req = _make_request(path="/v2.1/items")
        assert r.resolve(req) == "2.1"

    def test_no_version(self):
        from aquilia.versioning.resolvers import URLPathResolver

        r = URLPathResolver()
        req = _make_request(path="/users")
        assert r.resolve(req) is None

    def test_strip_version_from_path(self):
        from aquilia.versioning.resolvers import URLPathResolver

        r = URLPathResolver(strip_from_path=True)
        result = r.strip_version_from_path("/v2/users/123")
        assert result == "/users/123"

    def test_strip_root_version(self):
        from aquilia.versioning.resolvers import URLPathResolver

        r = URLPathResolver(strip_from_path=True)
        result = r.strip_version_from_path("/v1")
        assert result == "/"


class TestMediaTypeResolver:
    def test_resolve_param(self):
        from aquilia.versioning.resolvers import MediaTypeResolver

        r = MediaTypeResolver()
        req = _make_request(headers={"accept": "application/json; version=2"})
        assert r.resolve(req) == "2"

    def test_resolve_vendor(self):
        from aquilia.versioning.resolvers import MediaTypeResolver

        r = MediaTypeResolver()
        req = _make_request(
            headers={"accept": "application/vnd.myapi.v3+json"},
        )
        assert r.resolve(req) == "3"

    def test_missing(self):
        from aquilia.versioning.resolvers import MediaTypeResolver

        r = MediaTypeResolver()
        req = _make_request(headers={"accept": "text/html"})
        assert r.resolve(req) is None


class TestChannelResolver:
    def test_resolve_via_header(self):
        from aquilia.versioning.resolvers import ChannelResolver

        r = ChannelResolver(
            channel_map={"stable": "2.0", "preview": "3.0"},
        )
        req = _make_request(headers={"x-api-channel": "preview"})
        assert r.resolve(req) == "3.0"

    def test_resolve_via_query(self):
        from aquilia.versioning.resolvers import ChannelResolver

        r = ChannelResolver(
            channel_map={"stable": "2.0", "legacy": "1.0"},
        )
        req = _make_request(query_string=b"api_channel=legacy")
        assert r.resolve(req) == "1.0"

    def test_unknown_channel(self):
        from aquilia.versioning.resolvers import ChannelResolver

        r = ChannelResolver(channel_map={"stable": "2.0"})
        req = _make_request(headers={"x-api-channel": "nope"})
        assert r.resolve(req) is None


class TestCompositeResolver:
    def test_fallback_chain(self):
        from aquilia.versioning.resolvers import (
            CompositeResolver,
            HeaderResolver,
            QueryParamResolver,
        )

        c = CompositeResolver()
        c.add(HeaderResolver())
        c.add(QueryParamResolver())
        # Header not set, but query is
        req = _make_request(query_string=b"api_version=1.5")
        assert c.resolve(req) == "1.5"

    def test_first_wins(self):
        from aquilia.versioning.resolvers import (
            CompositeResolver,
            HeaderResolver,
            QueryParamResolver,
        )

        c = CompositeResolver()
        c.add(HeaderResolver())
        c.add(QueryParamResolver())
        req = _make_request(
            headers={"x-api-version": "2.0"},
            query_string=b"api_version=1.0",
        )
        assert c.resolve(req) == "2.0"


class TestCustomResolver:
    def test_custom_callable(self):
        from aquilia.versioning.resolvers import CustomResolver

        def extract(request):
            return request.headers.get("my-custom-header")

        r = CustomResolver(extract)
        req = _make_request(headers={"my-custom-header": "4.2"})
        assert r.resolve(req) == "4.2"


# ════════════════════════════════════════════════════════════════════════════
#  5. GRAPH
# ════════════════════════════════════════════════════════════════════════════


class TestVersionGraph:
    def test_register_and_contains(self):
        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.graph import VersionGraph

        g = VersionGraph()
        v = ApiVersion(1, 0)
        g.register(v)
        assert g.contains(v)
        assert not g.contains(ApiVersion(9, 9))

    def test_latest(self):
        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.graph import VersionGraph

        g = VersionGraph()
        g.register(ApiVersion(1, 0))
        g.register(ApiVersion(3, 0))
        g.register(ApiVersion(2, 0))
        g.freeze()  # latest is computed during freeze
        assert g.latest == ApiVersion(3, 0)

    def test_freeze_links_successors(self):
        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.graph import VersionGraph

        g = VersionGraph()
        g.register(ApiVersion(1, 0))
        g.register(ApiVersion(2, 0))
        g.register(ApiVersion(3, 0))
        g.freeze()
        node = g.get(ApiVersion(1, 0))
        assert node.successor == ApiVersion(2, 0)
        node2 = g.get(ApiVersion(2, 0))
        assert node2.predecessor == ApiVersion(1, 0)
        assert node2.successor == ApiVersion(3, 0)

    def test_active_versions(self):
        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.graph import VersionGraph

        g = VersionGraph()
        g.register(ApiVersion(1, 0))
        g.register(ApiVersion(2, 0))
        g.freeze()
        active = g.active_versions
        assert len(active) == 2

    def test_channel(self):
        from aquilia.versioning.core import ApiVersion, VersionChannel
        from aquilia.versioning.graph import VersionGraph

        g = VersionGraph()
        v = ApiVersion(2, 0)
        g.register(v)
        g.set_channel(VersionChannel.STABLE, v)
        assert g.get_by_channel(VersionChannel.STABLE) == v

    def test_register_route(self):
        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.graph import VersionGraph

        g = VersionGraph()
        v = ApiVersion(2, 0)
        g.register(v)
        g.register_route(v, "GET", "/users")
        node = g.get(v)
        assert "GET /users" in node.routes

    def test_register_controller(self):
        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.graph import VersionGraph

        g = VersionGraph()
        v = ApiVersion(1, 0)
        g.register(v)
        g.register_controller(v, "UsersController")
        node = g.get(v)
        assert "UsersController" in node.controllers

    def test_to_dict(self):
        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.graph import VersionGraph

        g = VersionGraph()
        g.register(ApiVersion(1, 0))
        g.register(ApiVersion(2, 0))
        g.freeze()
        d = g.to_dict()
        assert "versions" in d
        assert len(d["versions"]) == 2


# ════════════════════════════════════════════════════════════════════════════
#  6. SUNSET
# ════════════════════════════════════════════════════════════════════════════


class TestSunsetPolicy:
    def test_defaults(self):
        from aquilia.versioning.sunset import SunsetPolicy

        p = SunsetPolicy()
        assert p.warn_header is True
        assert p.enforce_sunset is True
        assert p.grace_period.days == 180


class TestSunsetRegistry:
    def test_register_and_get(self):
        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.sunset import SunsetRegistry

        r = SunsetRegistry()
        v = ApiVersion(1, 0)
        now = datetime.now(timezone.utc)
        r.register(v, deprecated_at=now - timedelta(days=30))
        assert r.get(v) is not None
        deprecated = r.get_deprecated()
        assert len(deprecated) == 1
        assert deprecated[0].version == v

    def test_sunset_entries(self):
        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.sunset import SunsetRegistry

        r = SunsetRegistry()
        v = ApiVersion(1, 0)
        now = datetime.now(timezone.utc)
        r.register(
            v,
            deprecated_at=now - timedelta(days=200),
            sunset_at=now - timedelta(days=10),
        )
        sunset = r.get_sunset()
        assert len(sunset) == 1
        assert sunset[0].version == v

    def test_to_dict(self):
        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.sunset import SunsetRegistry

        r = SunsetRegistry()
        r.register(ApiVersion(1, 0))
        d = r.to_dict()
        assert isinstance(d, dict)


class TestSunsetEnforcer:
    def test_no_rejection_for_active(self):
        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.sunset import SunsetEnforcer, SunsetPolicy, SunsetRegistry

        reg = SunsetRegistry()
        v = ApiVersion(2, 0)
        # Not registered = active
        enforcer = SunsetEnforcer(SunsetPolicy(), reg)
        assert enforcer.check(v) is None

    def test_rejection_for_sunset(self):
        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.sunset import SunsetEnforcer, SunsetPolicy, SunsetRegistry

        reg = SunsetRegistry()
        v = ApiVersion(1, 0)
        now = datetime.now(timezone.utc)
        reg.register(
            v,
            deprecated_at=now - timedelta(days=365),
            sunset_at=now - timedelta(days=30),
        )
        enforcer = SunsetEnforcer(SunsetPolicy(enforce_sunset=True), reg)
        result = enforcer.check(v)
        assert result is not None

    def test_headers_for_deprecated(self):
        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.sunset import SunsetEnforcer, SunsetPolicy, SunsetRegistry

        reg = SunsetRegistry()
        v = ApiVersion(1, 0)
        now = datetime.now(timezone.utc)
        reg.register(
            v,
            deprecated_at=now - timedelta(days=10),
            sunset_at=now + timedelta(days=170),
        )
        enforcer = SunsetEnforcer(SunsetPolicy(warn_header=True), reg)
        headers = enforcer.get_headers(v)
        assert "Deprecation" in headers
        assert "Sunset" in headers


# ════════════════════════════════════════════════════════════════════════════
#  7. NEGOTIATION
# ════════════════════════════════════════════════════════════════════════════


class TestNegotiationMode:
    def test_enum_values(self):
        from aquilia.versioning.negotiation import NegotiationMode

        assert NegotiationMode.EXACT.value == "exact"
        assert NegotiationMode.COMPATIBLE.value == "compatible"
        assert NegotiationMode.LATEST.value == "latest"
        assert NegotiationMode.BEST_MATCH.value == "best_match"
        assert NegotiationMode.NEAREST.value == "nearest"


class TestVersionNegotiator:
    def _build(self, mode="exact", versions=None):
        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.graph import VersionGraph
        from aquilia.versioning.negotiation import NegotiationMode, VersionNegotiator

        g = VersionGraph()
        for v in versions or [ApiVersion(1, 0), ApiVersion(2, 0), ApiVersion(3, 0)]:
            g.register(v)
        g.freeze()
        return VersionNegotiator(g, NegotiationMode(mode))

    def test_exact_match(self):
        from aquilia.versioning.core import ApiVersion

        n = self._build("exact")
        result = n.negotiate(ApiVersion(2, 0))
        assert result == ApiVersion(2, 0)

    def test_exact_no_match(self):
        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.errors import VersionNegotiationError

        n = self._build("exact")
        with pytest.raises(VersionNegotiationError):
            n.negotiate(ApiVersion(9, 0))

    def test_compatible(self):
        from aquilia.versioning.core import ApiVersion

        n = self._build(
            "compatible",
            [
                ApiVersion(2, 0),
                ApiVersion(2, 3),
                ApiVersion(3, 0),
            ],
        )
        result = n.negotiate(ApiVersion(2, 1))
        # Should pick 2.3 (same major, highest minor >= requested)
        assert result.major == 2

    def test_latest(self):
        from aquilia.versioning.core import ApiVersion

        n = self._build("latest")
        result = n.negotiate(ApiVersion(1, 0))
        assert result == ApiVersion(3, 0)

    def test_nearest(self):
        from aquilia.versioning.core import ApiVersion

        n = self._build(
            "nearest",
            [
                ApiVersion(1, 0),
                ApiVersion(2, 0),
                ApiVersion(3, 0),
            ],
        )
        result = n.negotiate(ApiVersion(2, 5))
        assert result == ApiVersion(2, 0)  # nearest by distance (diff of 5 vs 6)

    def test_fallback(self):
        from aquilia.versioning.core import ApiVersion

        n = self._build("exact")
        result = n.negotiate(ApiVersion(9, 0), fallback=ApiVersion(1, 0))
        assert result == ApiVersion(1, 0)


# ════════════════════════════════════════════════════════════════════════════
#  8. STRATEGY
# ════════════════════════════════════════════════════════════════════════════


class TestVersionConfig:
    def test_defaults(self):
        from aquilia.versioning.strategy import VersionConfig

        c = VersionConfig()
        assert c.strategy == "header"
        assert c.header_name == "X-API-Version"
        assert c.require_version is False
        assert "/_health" in c.neutral_paths

    def test_to_dict(self):
        from aquilia.versioning.strategy import VersionConfig

        c = VersionConfig(versions=["1.0", "2.0"])
        d = c.to_dict()
        assert d["versions"] == ["1.0", "2.0"]


class TestVersionStrategy:
    def _build(self, **overrides):
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy

        defaults = dict(
            strategy="header",
            versions=["1.0", "2.0", "3.0"],
            default_version="2.0",
        )
        defaults.update(overrides)
        config = VersionConfig(**defaults)
        return VersionStrategy(config)

    def test_resolve_from_header(self):
        from aquilia.versioning.core import ApiVersion

        s = self._build(strategy="header")
        req = _make_request(headers={"x-api-version": "3.0"})
        v = s.resolve(req)
        assert v == ApiVersion(3, 0)

    def test_resolve_default(self):
        from aquilia.versioning.core import ApiVersion

        s = self._build(strategy="header")
        req = _make_request()  # no header
        v = s.resolve(req)
        assert v == ApiVersion(2, 0)  # default

    def test_resolve_neutral_path(self):
        s = self._build()
        req = _make_request(path="/_health")
        v = s.resolve(req)
        assert v is not None  # returns default

    def test_resolve_url_strategy(self):
        from aquilia.versioning.core import ApiVersion

        s = self._build(strategy="url")
        req = _make_request(path="/v3/users")
        v = s.resolve(req)
        assert v == ApiVersion(3, 0)

    def test_resolve_explicit_unsupported_url_version_raises(self):
        from aquilia.versioning.errors import UnsupportedVersionError

        s = self._build(
            strategy="url",
            versions=["1.0", "2.0"],
            default_version="1.0",
        )
        req = _make_request(path="/v9/users")
        with pytest.raises(UnsupportedVersionError):
            s.resolve(req)

    def test_resolve_query_strategy(self):
        from aquilia.versioning.core import ApiVersion

        s = self._build(strategy="query")
        req = _make_request(query_string=b"api_version=1.0")
        v = s.resolve(req)
        assert v == ApiVersion(1, 0)

    def test_resolve_composite(self):
        from aquilia.versioning.core import ApiVersion

        s = self._build(strategy="composite")
        req = _make_request(query_string=b"api_version=1.0")
        v = s.resolve(req)
        assert v == ApiVersion(1, 0)

    def test_require_version(self):
        from aquilia.versioning.errors import MissingVersionError

        s = self._build(require_version=True, default_version=None)
        req = _make_request()
        with pytest.raises(MissingVersionError):
            s.resolve(req)

    def test_get_response_headers(self):
        from aquilia.versioning.core import ApiVersion

        s = self._build()
        headers = s.get_response_headers(ApiVersion(2, 0))
        assert "X-API-Version" in headers
        assert headers["X-API-Version"] == "2"

    def test_strip_version_from_path(self):
        s = self._build(strategy="url")
        req = _make_request(path="/v2/users")
        result = s.strip_version_from_path(req)
        assert result == "/users"

    def test_register_version(self):
        from aquilia.versioning.core import ApiVersion

        # Version 4.0 is included in the config versions list
        s = self._build(versions=["1.0", "2.0", "3.0", "4.0"])
        assert s.graph.contains(ApiVersion(4, 0))

    def test_channel_strategy(self):
        from aquilia.versioning.core import ApiVersion

        s = self._build(
            strategy="channel",
            channels={"stable": "2.0", "preview": "3.0"},
        )
        req = _make_request(headers={"x-api-channel": "preview"})
        v = s.resolve(req)
        assert v == ApiVersion(3, 0)

    def test_sunset_schedules(self):
        from aquilia.versioning.sunset import SunsetPolicy

        now = datetime.now(timezone.utc)
        s = self._build(
            sunset_policy=SunsetPolicy(warn_header=True),
            sunset_schedules={
                "1.0": {
                    "deprecated_at": (now - timedelta(days=30)).isoformat(),
                    "sunset_at": (now + timedelta(days=150)).isoformat(),
                },
            },
        )
        entry = s.sunset_registry.get(s.parser.parse("1.0"))
        assert entry is not None

    def test_to_dict(self):
        s = self._build()
        d = s.to_dict()
        assert "config" in d
        assert "graph" in d
        assert "sunset" in d


# ════════════════════════════════════════════════════════════════════════════
#  9. MIDDLEWARE
# ════════════════════════════════════════════════════════════════════════════


class TestVersionMiddleware:
    def _build_strategy(self, **overrides):
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy

        defaults = dict(
            strategy="header",
            versions=["1.0", "2.0"],
            default_version="1.0",
        )
        defaults.update(overrides)
        return VersionStrategy(VersionConfig(**defaults))

    @pytest.mark.asyncio
    async def test_resolves_and_stores(self):
        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.middleware import VersionMiddleware

        strategy = self._build_strategy()
        mw = VersionMiddleware(strategy)

        req = _make_request(headers={"x-api-version": "2.0"})
        ctx = MagicMock()

        async def next_handler(r, c):
            from aquilia.response import Response

            return Response.json({"ok": True})

        resp = await mw(req, ctx, next_handler)
        assert req.state["api_version"] == ApiVersion(2, 0)
        assert req.state["api_version_str"] == "2"
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_default_version_used(self):
        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.middleware import VersionMiddleware

        strategy = self._build_strategy()
        mw = VersionMiddleware(strategy)

        req = _make_request()  # no header
        ctx = MagicMock()

        async def next_handler(r, c):
            from aquilia.response import Response

            return Response.json({"ok": True})

        resp = await mw(req, ctx, next_handler)
        assert req.state["api_version"] == ApiVersion(1, 0)

    @pytest.mark.asyncio
    async def test_missing_required_returns_400(self):
        from aquilia.versioning.middleware import VersionMiddleware

        strategy = self._build_strategy(require_version=True, default_version=None)
        mw = VersionMiddleware(strategy)

        req = _make_request()
        ctx = MagicMock()

        async def next_handler(r, c):
            from aquilia.response import Response

            return Response.json({"ok": True})

        resp = await mw(req, ctx, next_handler)
        assert resp.status == 400

    @pytest.mark.asyncio
    async def test_invalid_version_returns_400(self):
        from aquilia.versioning.middleware import VersionMiddleware

        strategy = self._build_strategy()
        mw = VersionMiddleware(strategy)

        req = _make_request(headers={"x-api-version": "not-a-version"})
        ctx = MagicMock()

        async def next_handler(r, c):
            from aquilia.response import Response

            return Response.json({"ok": True})

        resp = await mw(req, ctx, next_handler)
        assert resp.status == 400

    @pytest.mark.asyncio
    async def test_unsupported_url_version_returns_400(self):
        from aquilia.versioning.middleware import VersionMiddleware

        strategy = self._build_strategy(
            strategy="url",
            versions=["1.0", "2.0"],
            default_version="1.0",
        )
        mw = VersionMiddleware(strategy)

        req = _make_request(path="/v9/users")
        ctx = MagicMock()

        async def next_handler(r, c):
            from aquilia.response import Response

            return Response.json({"ok": True})

        resp = await mw(req, ctx, next_handler)
        assert resp.status == 400

    @pytest.mark.asyncio
    async def test_unsupported_url_version_renders_html_for_browser(self):
        from aquilia.versioning.middleware import VersionMiddleware

        strategy = self._build_strategy(
            strategy="url",
            versions=["1.0", "2.0"],
            default_version="1.0",
        )
        mw = VersionMiddleware(strategy)

        req = _make_request(path="/v9/users", headers={"accept": "text/html"})
        ctx = MagicMock()

        async def next_handler(r, c):
            from aquilia.response import Response

            return Response.json({"ok": True})

        resp = await mw(req, ctx, next_handler)
        assert resp.status == 400
        assert str(resp.headers.get("content-type", "")).startswith("text/html")
        body = resp._content.decode("utf-8") if isinstance(resp._content, (bytes, bytearray)) else str(resp._content)
        assert "UNSUPPORTED_API_VERSION" in body
        assert "API Version" in body

    @pytest.mark.asyncio
    async def test_unsupported_url_version_renders_html_for_browser_wildcard_accept(self):
        from aquilia.versioning.middleware import VersionMiddleware

        strategy = self._build_strategy(
            strategy="url",
            versions=["1.0", "2.0"],
            default_version="1.0",
        )
        mw = VersionMiddleware(strategy)

        req = _make_request(
            path="/v9/users",
            headers={
                "accept": "*/*",
                "user-agent": "Mozilla/5.0",
            },
        )
        ctx = MagicMock()

        async def next_handler(r, c):
            from aquilia.response import Response

            return Response.json({"ok": True})

        resp = await mw(req, ctx, next_handler)
        assert resp.status == 400
        assert str(resp.headers.get("content-type", "")).startswith("text/html")

    @pytest.mark.asyncio
    async def test_unsupported_url_version_keeps_json_for_non_browser_wildcard(self):
        from aquilia.versioning.middleware import VersionMiddleware

        strategy = self._build_strategy(
            strategy="url",
            versions=["1.0", "2.0"],
            default_version="1.0",
        )
        mw = VersionMiddleware(strategy)

        req = _make_request(
            path="/v9/users",
            headers={"accept": "*/*"},
        )
        ctx = MagicMock()

        async def next_handler(r, c):
            from aquilia.response import Response

            return Response.json({"ok": True})

        resp = await mw(req, ctx, next_handler)
        assert resp.status == 400
        assert str(resp.headers.get("content-type", "")).startswith("application/json")

    @pytest.mark.asyncio
    async def test_version_headers_in_response(self):
        from aquilia.versioning.middleware import VersionMiddleware

        strategy = self._build_strategy()
        mw = VersionMiddleware(strategy)

        req = _make_request(headers={"x-api-version": "2.0"})
        ctx = MagicMock()

        async def next_handler(r, c):
            from aquilia.response import Response

            return Response.json({"ok": True})

        resp = await mw(req, ctx, next_handler)
        assert resp.headers.get("X-API-Version") == "2"

    @pytest.mark.asyncio
    async def test_url_path_stripping(self):
        from aquilia.versioning.middleware import VersionMiddleware

        strategy = self._build_strategy(strategy="url", negotiation_mode="compatible")
        mw = VersionMiddleware(strategy)

        req = _make_request(path="/v2/users")
        ctx = MagicMock()

        async def next_handler(r, c):
            from aquilia.response import Response

            return Response.json({"path": r.path})

        resp = await mw(req, ctx, next_handler)
        # After middleware, path should be stripped
        assert req.state.get("_original_path") == "/v2/users"


# ════════════════════════════════════════════════════════════════════════════
#  10. DECORATORS
# ════════════════════════════════════════════════════════════════════════════


class TestVersionDecorators:
    def test_version_single(self):
        from aquilia.versioning.decorators import version

        @version("2.0")
        async def handler(ctx):
            pass

        assert hasattr(handler, "__version_metadata__")
        assert "2.0" in handler.__version_metadata__["versions"]

    def test_version_multiple(self):
        from aquilia.versioning.decorators import version

        @version(["1.0", "2.0"])
        async def handler(ctx):
            pass

        assert "1.0" in handler.__version_metadata__["versions"]
        assert "2.0" in handler.__version_metadata__["versions"]

    def test_version_neutral(self):
        from aquilia.versioning.decorators import version_neutral

        @version_neutral
        async def health(ctx):
            pass

        assert health.__version_metadata__["neutral"] is True

    def test_version_range(self):
        from aquilia.versioning.decorators import version_range

        @version_range("1.0", "3.0")
        async def handler(ctx):
            pass

        assert handler.__version_metadata__["range"]["min"] == "1.0"
        assert handler.__version_metadata__["range"]["max"] == "3.0"


# ════════════════════════════════════════════════════════════════════════════
#  11. INTEGRATION — RouteDecorator version, metadata, router
# ════════════════════════════════════════════════════════════════════════════


class TestRouteDecoratorVersion:
    """Test that the version parameter flows through the decorator system."""

    def test_get_with_version(self):
        from aquilia.controller.decorators import GET

        @GET("/users", version="2.0")
        async def list_users(self, ctx):
            pass

        meta = list_users.__route_metadata__[0]
        assert meta["version"] == "2.0"
        assert hasattr(list_users, "__version_metadata__")
        assert "2.0" in list_users.__version_metadata__["versions"]

    def test_post_with_version_list(self):
        from aquilia.controller.decorators import POST

        @POST("/items", version=["1.0", "2.0"])
        async def create_item(self, ctx):
            pass

        meta = create_item.__route_metadata__[0]
        assert meta["version"] == ["1.0", "2.0"]
        assert "1.0" in create_item.__version_metadata__["versions"]
        assert "2.0" in create_item.__version_metadata__["versions"]

    def test_route_without_version(self):
        from aquilia.controller.decorators import GET

        @GET("/health")
        async def health(self, ctx):
            pass

        meta = health.__route_metadata__[0]
        assert meta["version"] is None
        assert not hasattr(health, "__version_metadata__")


class TestMetadataVersionCapture:
    """Test version fields in ControllerMetadata and RouteMetadata."""

    def test_controller_metadata_version(self):
        from aquilia.controller.base import Controller
        from aquilia.controller.decorators import GET
        from aquilia.controller.metadata import extract_controller_metadata

        class UsersV2(Controller):
            prefix = "/users"
            version = "2.0"

            @GET("/")
            async def list(self, ctx):
                pass

        meta = extract_controller_metadata(UsersV2, "test:UsersV2")
        assert meta.version == "2.0"

    def test_route_metadata_version(self):
        from aquilia.controller.base import Controller
        from aquilia.controller.decorators import GET
        from aquilia.controller.metadata import extract_controller_metadata

        class Items(Controller):
            prefix = "/items"

            @GET("/", version="3.0")
            async def list(self, ctx):
                pass

        meta = extract_controller_metadata(Items, "test:Items")
        assert meta.routes[0].version == "3.0"

    def test_version_neutral_controller(self):
        from aquilia.controller.base import Controller
        from aquilia.controller.decorators import GET
        from aquilia.controller.metadata import extract_controller_metadata
        from aquilia.versioning.core import VERSION_NEUTRAL

        class Health(Controller):
            prefix = "/health"
            version = VERSION_NEUTRAL

            @GET("/")
            async def check(self, ctx):
                pass

        meta = extract_controller_metadata(Health, "test:Health")
        assert meta.version is VERSION_NEUTRAL


class TestRouterVersionFiltering:
    """Test version-aware route matching in ControllerRouter."""

    def _build_router_with_versioned_controllers(self):
        from aquilia.controller.base import Controller
        from aquilia.controller.compiler import ControllerCompiler
        from aquilia.controller.decorators import GET
        from aquilia.controller.router import ControllerRouter
        from aquilia.versioning.core import ApiVersion

        class UsersV1(Controller):
            prefix = "/v1/users"
            version = "1.0"

            @GET("/")
            async def list(self, ctx):
                return {"version": "1.0"}

        class UsersV2(Controller):
            prefix = "/v2/users"
            version = "2.0"

            @GET("/")
            async def list(self, ctx):
                return {"version": "2.0"}

        compiler = ControllerCompiler()
        router = ControllerRouter()

        c1 = compiler.compile_controller(UsersV1)
        c2 = compiler.compile_controller(UsersV2)

        router.add_controller(c1)
        router.add_controller(c2)
        router.initialize()

        return router, ApiVersion

    def test_version_filtered_match(self):
        router, ApiVersion = self._build_router_with_versioned_controllers()

        # Match v1.0 via v1 prefix
        match = router.match_sync("/v1/users", "GET", api_version=ApiVersion(1, 0))
        assert match is not None
        assert match.route.controller_metadata.version == "1.0"

    def test_version_filtered_match_v2(self):
        router, ApiVersion = self._build_router_with_versioned_controllers()

        match = router.match_sync("/v2/users", "GET", api_version=ApiVersion(2, 0))
        assert match is not None
        assert match.route.controller_metadata.version == "2.0"

    def test_version_mismatch_rejected(self):
        router, ApiVersion = self._build_router_with_versioned_controllers()

        # Request v2 path with v1 version filter → rejected
        match = router.match_sync("/v2/users", "GET", api_version=ApiVersion(1, 0))
        assert match is None

    def test_no_version_matches_any(self):
        router, ApiVersion = self._build_router_with_versioned_controllers()

        # Without version filter, any matching path should match
        match = router.match_sync("/v1/users", "GET")
        assert match is not None


class TestConfigVersioning:
    """Test versioning config getter."""

    def test_get_versioning_config_defaults(self):
        from aquilia.config import ConfigLoader

        c = ConfigLoader()
        vc = c.get_versioning_config()
        assert vc["enabled"] is False
        assert vc["strategy"] == "header"
        assert vc["header_name"] == "X-API-Version"

    def test_get_versioning_config_merge(self):
        from aquilia.config import ConfigLoader

        c = ConfigLoader()
        c.config_data["integrations"] = {
            "versioning": {
                "enabled": True,
                "strategy": "url",
                "versions": ["1.0", "2.0"],
            },
        }
        vc = c.get_versioning_config()
        assert vc["enabled"] is True
        assert vc["strategy"] == "url"
        assert vc["versions"] == ["1.0", "2.0"]


class TestIntegrationVersioning:
    """Test Integration.versioning() config builder."""

    def test_builder(self):
        from aquilia.integrations import Integration

        config = Integration.versioning(
            strategy="header",
            versions=["1.0", "2.0", "3.0"],
            default_version="2.0",
            channels={"stable": "2.0", "preview": "3.0"},
        )
        assert config["enabled"] is True
        assert config["_integration_type"] == "versioning"
        assert config["strategy"] == "header"
        assert config["versions"] == ["1.0", "2.0", "3.0"]
        assert config["default_version"] == "2.0"
        assert config["channels"]["stable"] == "2.0"

    def test_builder_with_sunset(self):
        from aquilia.integrations import Integration
        from aquilia.versioning.sunset import SunsetPolicy

        config = Integration.versioning(
            versions=["1.0", "2.0"],
            sunset_policy=SunsetPolicy(grace_period=timedelta(days=90)),
        )
        assert config["sunset_policy"] is not None

    def test_server_setup_with_sunset_policy_instance(self):
        from unittest.mock import MagicMock

        from aquilia.integrations import Integration
        from aquilia.server import AquiliaServer
        from aquilia.versioning.sunset import SunsetPolicy

        server = MagicMock(spec=AquiliaServer)
        server.middleware_stack = MagicMock()
        server.logger = MagicMock()
        server.config = {
            "integrations.versioning": Integration.versioning(
                strategy="url",
                versions=["1.0"],
                default_version="1.0",
                channels={"stable": "1.0"},
                sunset_policy=SunsetPolicy(warn_header=True),
            )
        }

        # Now call the actual method bound to our mock server
        AquiliaServer._setup_versioning(server)

        # Verify it successfully set up the version strategy and sunset policy
        assert server._version_strategy is not None
        assert server._version_strategy._config.sunset_policy is not None
        assert server._version_strategy._config.sunset_policy.warn_header is True

    def test_server_setup_with_sunset_policy_dict(self):
        from unittest.mock import MagicMock

        from aquilia.server import AquiliaServer

        server = MagicMock(spec=AquiliaServer)
        server.middleware_stack = MagicMock()
        server.logger = MagicMock()
        server.config = {
            "integrations.versioning": {
                "enabled": True,
                "strategy": "url",
                "versions": ["1.0"],
                "default_version": "1.0",
                "sunset_policy": {
                    "warn_header": False,
                    "grace_period_days": 45,
                },
            }
        }

        # Call the method
        AquiliaServer._setup_versioning(server)

        # Verify it successfully set up the version strategy and sunset policy
        assert server._version_strategy is not None
        assert server._version_strategy._config.sunset_policy is not None
        assert server._version_strategy._config.sunset_policy.warn_header is False
        assert server._version_strategy._config.sunset_policy.grace_period.days == 45


# ════════════════════════════════════════════════════════════════════════════
#  12. END-TO-END SCENARIO
# ════════════════════════════════════════════════════════════════════════════


class TestEndToEnd:
    """Full pipeline: config → strategy → middleware → resolve."""

    @pytest.mark.asyncio
    async def test_full_pipeline_header(self):
        """E2E: header-based versioning with sunset warning."""
        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.middleware import VersionMiddleware
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy
        from aquilia.versioning.sunset import SunsetPolicy

        now = datetime.now(timezone.utc)
        config = VersionConfig(
            strategy="header",
            versions=["1.0", "2.0", "3.0"],
            default_version="2.0",
            channels={"stable": "2.0", "preview": "3.0", "legacy": "1.0"},
            sunset_policy=SunsetPolicy(
                warn_header=True,
                grace_period=timedelta(days=180),
            ),
            sunset_schedules={
                "1.0": {
                    "deprecated_at": (now - timedelta(days=30)).isoformat(),
                    "sunset_at": (now + timedelta(days=150)).isoformat(),
                    "successor": "2.0",
                },
            },
        )
        strategy = VersionStrategy(config)
        mw = VersionMiddleware(strategy)

        # Request v1.0 — should succeed with deprecation warning
        req = _make_request(headers={"x-api-version": "1.0"})
        ctx = MagicMock()

        async def handler(r, c):
            from aquilia.response import Response

            return Response.json({"data": "legacy"})

        resp = await mw(req, ctx, handler)
        assert resp.status == 200
        assert req.state["api_version"] == ApiVersion(1, 0)
        # Should have deprecation header
        assert "Deprecation" in resp.headers

    @pytest.mark.asyncio
    async def test_full_pipeline_url(self):
        """E2E: URL path versioning with path stripping."""
        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.middleware import VersionMiddleware
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy

        config = VersionConfig(
            strategy="url",
            versions=["1.0", "2.0"],
            default_version="1.0",
            negotiation_mode="compatible",
        )
        strategy = VersionStrategy(config)
        mw = VersionMiddleware(strategy)

        req = _make_request(path="/v2/users/123")
        ctx = MagicMock()

        async def handler(r, c):
            from aquilia.response import Response

            return Response.json({"path": r.path})

        resp = await mw(req, ctx, handler)
        assert req.state["api_version"] == ApiVersion(2, 0)
        assert req.state["_original_path"] == "/v2/users/123"

    @pytest.mark.asyncio
    async def test_full_pipeline_channel(self):
        """E2E: Channel-based version resolution."""
        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.middleware import VersionMiddleware
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy

        config = VersionConfig(
            strategy="channel",
            versions=["1.0", "2.0", "3.0"],
            default_version="2.0",
            channels={"stable": "2.0", "preview": "3.0", "legacy": "1.0"},
        )
        strategy = VersionStrategy(config)
        mw = VersionMiddleware(strategy)

        req = _make_request(headers={"x-api-channel": "preview"})
        ctx = MagicMock()

        async def handler(r, c):
            from aquilia.response import Response

            return Response.json({"channel": "preview"})

        resp = await mw(req, ctx, handler)
        assert req.state["api_version"] == ApiVersion(3, 0)


# ════════════════════════════════════════════════════════════════════════════
#  13. ASGI ROUTING REGRESSIONS (Issue #12)
# ════════════════════════════════════════════════════════════════════════════


class _DummyRoute:
    app_name = None
    full_path = "/users"


class _DummyMatch:
    def __init__(self):
        self.route = _DummyRoute()
        self.params = {}
        self.query = {}


class TestASGIPreRoutingVersioning:
    def _build_adapter(self, strategy):
        from aquilia.asgi import ASGIAdapter
        from aquilia.middleware import MiddlewareStack

        router = MagicMock()
        engine = MagicMock()

        server = SimpleNamespace(_version_strategy=strategy)

        adapter = ASGIAdapter(
            controller_router=router,
            controller_engine=engine,
            middleware_stack=MiddlewareStack(),
            server=server,
        )
        return adapter, router, engine

    async def _run_http(self, adapter, scope):
        messages = []

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            messages.append(message)

        await adapter.handle_http(scope, receive, send)
        return messages

    @pytest.mark.asyncio
    async def test_url_strategy_strips_prefix_before_match(self):
        from aquilia.response import Response
        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy

        strategy = VersionStrategy(
            VersionConfig(
                strategy="url",
                versions=["1.0", "2.0"],
                default_version="1.0",
                negotiation_mode="compatible",
            )
        )
        adapter, router, engine = self._build_adapter(strategy)

        match_calls = []

        def _match(path, method, api_version=None):
            match_calls.append((path, method, api_version))
            return _DummyMatch()

        router.match_sync.side_effect = _match
        router.get_allowed_methods.return_value = []
        engine.execute = AsyncMock(return_value=Response.json({"ok": True}))

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/v2/users",
            "query_string": b"",
            "headers": [],
        }

        await self._run_http(adapter, scope)

        assert match_calls, "Router should be invoked"
        path, method, version = match_calls[0]
        assert path == "/users"
        assert method == "GET"
        assert version == ApiVersion(2, 0)

    @pytest.mark.asyncio
    async def test_url_strategy_uses_default_version_for_unversioned_path(self):
        """
        Under the corrected URL strategy, an unprefixed path (no version segment)
        is not silently treated as the default version. Thus, the resolved
        api_version should be None (which allows routing to look up exact compiled
        paths like /users, rather than collapsing /users onto a versioned /v1/users route).
        """
        from aquilia.response import Response
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy

        strategy = VersionStrategy(
            VersionConfig(
                strategy="url",
                versions=["1.0", "2.0"],
                default_version="1.0",
            )
        )
        adapter, router, engine = self._build_adapter(strategy)

        match_calls = []

        def _match(path, method, api_version=None):
            match_calls.append((path, method, api_version))
            return _DummyMatch()

        router.match_sync.side_effect = _match
        router.get_allowed_methods.return_value = []
        engine.execute = AsyncMock(return_value=Response.json({"ok": True}))

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/users",
            "query_string": b"",
            "headers": [],
        }

        await self._run_http(adapter, scope)

        assert match_calls, "Router should be invoked"
        path, method, version = match_calls[0]
        assert path == "/users"
        assert method == "GET"
        assert version is None

    @pytest.mark.asyncio
    async def test_url_strategy_preserves_dynamic_segments_after_strip(self):
        from aquilia.response import Response
        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy

        strategy = VersionStrategy(
            VersionConfig(
                strategy="url",
                versions=["1.0", "2.0"],
                default_version="1.0",
                negotiation_mode="compatible",
            )
        )
        adapter, router, engine = self._build_adapter(strategy)

        match_calls = []

        def _match(path, method, api_version=None):
            match_calls.append((path, method, api_version))
            return _DummyMatch()

        router.match_sync.side_effect = _match
        router.get_allowed_methods.return_value = []
        engine.execute = AsyncMock(return_value=Response.json({"ok": True}))

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/v2/users/123",
            "query_string": b"",
            "headers": [],
        }

        await self._run_http(adapter, scope)

        assert match_calls, "Router should be invoked"
        path, method, version = match_calls[0]
        assert path == "/users/123"
        assert method == "GET"
        assert version == ApiVersion(2, 0)

    @pytest.mark.asyncio
    async def test_unsupported_url_version_is_not_prestripped(self):
        from aquilia.response import Response
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy

        strategy = VersionStrategy(
            VersionConfig(
                strategy="url",
                versions=["1.0", "2.0"],
                default_version="1.0",
            )
        )
        adapter, router, engine = self._build_adapter(strategy)

        match_calls = []

        def _match(path, method, api_version=None):
            match_calls.append((path, method, api_version))
            return None

        router.match_sync.side_effect = _match
        router.get_allowed_methods.return_value = []
        engine.execute = AsyncMock(return_value=Response.json({"ok": True}))

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/v9/auth",
            "query_string": b"",
            "headers": [],
        }

        await self._run_http(adapter, scope)

        assert match_calls, "Router should be invoked"
        path, method, version = match_calls[0]
        assert path == "/v9/auth"
        assert method == "GET"
        assert version is None


# ════════════════════════════════════════════════════════════════════════════
#  14. REGRESSION TESTS — Versioning Bug Fixes (fix/versioning-url-strategy)
# ════════════════════════════════════════════════════════════════════════════


class TestBugA_UnversionedPathRejection:
    """Bug A: Unprefixed paths must NOT silently match the default version.

    Under structural URL versioning (strategy='url', negotiation_mode='exact'),
    an unversioned path like ``/users`` must not be treated as ``/v1/users``.
    The router sees the literal path; if no route is compiled for ``/users``
    (only ``/v1/users`` exists), it correctly 404s.
    """

    def test_structural_url_strategy_skips_resolve(self):
        """In structural mode, _resolve_route_inputs returns (raw_path, None)."""
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy

        strategy = VersionStrategy(
            VersionConfig(
                strategy="url",
                versions=["1.0", "2.0"],
                default_version="1.0",
            )
        )
        assert strategy.is_structural_url_versioning is True

        from types import SimpleNamespace

        from aquilia.asgi import ASGIAdapter
        from aquilia.middleware import MiddlewareStack

        router = MagicMock()
        engine = MagicMock()
        server = SimpleNamespace(_version_strategy=strategy)
        adapter = ASGIAdapter(
            controller_router=router,
            controller_engine=engine,
            middleware_stack=MiddlewareStack(),
            server=server,
        )

        req = _make_request(path="/users")
        path, version = adapter._resolve_route_inputs(req, "/users")
        assert path == "/users", "Path must not be rewritten"
        assert version is None, "Version must be None in structural mode"

    def test_structural_url_strategy_leaves_versioned_path_intact(self):
        """In structural mode, /v2/users is passed to the router as-is."""
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy

        strategy = VersionStrategy(
            VersionConfig(
                strategy="url",
                versions=["1.0", "2.0"],
                default_version="1.0",
            )
        )

        from types import SimpleNamespace

        from aquilia.asgi import ASGIAdapter
        from aquilia.middleware import MiddlewareStack

        router = MagicMock()
        engine = MagicMock()
        server = SimpleNamespace(_version_strategy=strategy)
        adapter = ASGIAdapter(
            controller_router=router,
            controller_engine=engine,
            middleware_stack=MiddlewareStack(),
            server=server,
        )

        req = _make_request(path="/v2/users")
        path, version = adapter._resolve_route_inputs(req, "/v2/users")
        assert path == "/v2/users", "Structural mode must not strip path"
        assert version is None

    def test_expose_unversioned_alias_disables_structural_mode(self):
        """When expose_unversioned_alias=True, structural mode is off."""
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy

        strategy = VersionStrategy(
            VersionConfig(
                strategy="url",
                versions=["1.0"],
                default_version="1.0",
                expose_unversioned_alias=True,
            )
        )
        assert strategy.is_structural_url_versioning is False


class TestBugB_ScopeImmutability:
    """Bug B: ASGI scope['path'] must never be mutated by versioning."""

    @pytest.mark.asyncio
    async def test_scope_path_unchanged_after_url_resolution(self):
        """The original scope dict is never modified by version resolution."""
        from aquilia.response import Response
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy

        strategy = VersionStrategy(
            VersionConfig(
                strategy="url",
                versions=["1.0", "2.0"],
                default_version="1.0",
                negotiation_mode="compatible",
            )
        )

        from types import SimpleNamespace

        from aquilia.asgi import ASGIAdapter
        from aquilia.middleware import MiddlewareStack

        router = MagicMock()
        engine = MagicMock()
        server = SimpleNamespace(_version_strategy=strategy)
        adapter = ASGIAdapter(
            controller_router=router,
            controller_engine=engine,
            middleware_stack=MiddlewareStack(),
            server=server,
        )

        router.match_sync.return_value = _DummyMatch()
        router.get_allowed_methods.return_value = []
        engine.execute = AsyncMock(return_value=Response.json({"ok": True}))

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/v2/users",
            "query_string": b"",
            "headers": [],
        }
        original_path = scope["path"]

        messages = []

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(msg):
            messages.append(msg)

        await adapter.handle_http(scope, receive, send)

        assert scope["path"] == original_path, (
            "scope['path'] must not be mutated — external logging/tracing depends on it"
        )

    @pytest.mark.asyncio
    async def test_middleware_does_not_write_scope(self):
        """VersionMiddleware must not touch request.scope['path']."""
        from aquilia.versioning.middleware import VersionMiddleware
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy

        strategy = VersionStrategy(
            VersionConfig(
                strategy="url",
                versions=["1.0", "2.0"],
                default_version="1.0",
                negotiation_mode="compatible",
            )
        )
        mw = VersionMiddleware(strategy)

        req = _make_request(path="/v2/users")
        ctx = MagicMock()
        scope_path_before = req.scope["path"]

        async def next_handler(r, c):
            from aquilia.response import Response

            return Response.json({"ok": True})

        await mw(req, ctx, next_handler)
        assert req.scope["path"] == scope_path_before


class TestBugC_VersionDisjointRoutes:
    """Bug C: Routes for different versions must not trigger false conflicts."""

    def test_disjoint_version_routes_no_conflict(self):
        """Two routes with the same base path but different bound_versions
        are NOT conflicts when compiled structurally."""
        from aquilia.controller.base import Controller
        from aquilia.controller.compiler import ControllerCompiler
        from aquilia.controller.decorators import GET
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy

        class UsersV1(Controller):
            prefix = "/users"
            version = "1.0"

            @GET("/")
            async def list(self, ctx):
                return {"v": "1"}

        class UsersV2(Controller):
            prefix = "/users"
            version = "2.0"

            @GET("/")
            async def list(self, ctx):
                return {"v": "2"}

        strategy = VersionStrategy(
            VersionConfig(
                strategy="url",
                versions=["1.0", "2.0"],
                default_version="1.0",
            )
        )

        compiler = ControllerCompiler()
        c1 = compiler.compile_controller(UsersV1, version_strategy=strategy)
        c2 = compiler.compile_controller(UsersV2, version_strategy=strategy)

        # Routes get different prefixes (/v1/users/ vs /v2/users/)
        paths = {r.full_path for r in c1.routes + c2.routes}
        assert "/v1/users/" in paths
        assert "/v2/users/" in paths

        # No conflicts
        conflicts = compiler.validate_route_tree([c1, c2])
        assert conflicts == [], f"Unexpected conflicts: {conflicts}"

    def test_same_version_routes_still_conflict(self):
        """Two controllers with the same version and path DO conflict."""
        from aquilia.controller.base import Controller
        from aquilia.controller.compiler import ControllerCompiler
        from aquilia.controller.decorators import GET

        class UsersA(Controller):
            prefix = "/users"

            @GET("/")
            async def list(self, ctx):
                pass

        class UsersB(Controller):
            prefix = "/users"

            @GET("/")
            async def list(self, ctx):
                pass

        compiler = ControllerCompiler()
        c1 = compiler.compile_controller(UsersA)
        c2 = compiler.compile_controller(UsersB)

        conflicts = compiler.validate_route_tree([c1, c2])
        assert len(conflicts) > 0


class TestBugD_UrlPositionConfiguration:
    """Bug D: url_position='after' must place version segment after the module prefix."""

    def test_before_position(self):
        """url_position='before' → /v1/api/users."""
        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy

        strategy = VersionStrategy(
            VersionConfig(
                strategy="url",
                versions=["1.0"],
                default_version="1.0",
                url_position="before",
            )
        )
        result = strategy.build_version_prefix("/api", ApiVersion(1, 0))
        assert result == "/v1/api", f"Expected /v1/api, got {result}"

    def test_after_position(self):
        """url_position='after' → /api/v1."""
        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy

        strategy = VersionStrategy(
            VersionConfig(
                strategy="url",
                versions=["1.0"],
                default_version="1.0",
                url_position="after",
            )
        )
        result = strategy.build_version_prefix("/api", ApiVersion(1, 0))
        assert result == "/api/v1", f"Expected /api/v1, got {result}"

    def test_module_position_override_in_compiler(self):
        """Per-module position override threads through the compiler."""
        from aquilia.controller.base import Controller
        from aquilia.controller.compiler import ControllerCompiler
        from aquilia.controller.decorators import GET
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy

        class Items(Controller):
            prefix = "/items"
            version = "1.0"

            @GET("/")
            async def list(self, ctx):
                pass

        strategy = VersionStrategy(
            VersionConfig(
                strategy="url",
                versions=["1.0"],
                default_version="1.0",
                url_position="before",
            )
        )
        compiler = ControllerCompiler()

        # With module_versioning overriding position to 'after':
        compiled = compiler.compile_controller(
            Items,
            base_prefix="/api",
            version_strategy=strategy,
            module_versioning={"enabled": True, "position": "after"},
        )

        paths = [r.full_path for r in compiled.routes]
        assert any("/api/v1" in p for p in paths), f"Expected after-position path, got {paths}"


class TestSunsetPerVersionCounters:
    """Sunset rejection counter must be per-version, not globally shared."""

    def test_independent_counters_for_different_versions(self):
        from datetime import datetime, timezone

        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.sunset import (
            SunsetEnforcer,
            SunsetPolicy,
            SunsetRegistry,
        )

        past = datetime(2020, 1, 1, tzinfo=timezone.utc)
        registry = SunsetRegistry()
        v1 = ApiVersion(1, 0)
        v2 = ApiVersion(2, 0)
        registry.register(v1, sunset_at=past)
        registry.register(v2, sunset_at=past)

        policy = SunsetPolicy(
            enforce_sunset=True,
            gradual_rejection_percent=50,
        )
        enforcer = SunsetEnforcer(policy, registry)

        # Hammer v1 ten times
        v1_results = [enforcer.check(v1) for _ in range(10)]
        # Hammer v2 once
        v2_results = [enforcer.check(v2)]

        # v1 counter should be at 10, v2 counter should be at 1
        assert v1 in enforcer._rejection_counters
        assert v2 in enforcer._rejection_counters
        assert enforcer._rejection_counters[v1] == 10
        assert enforcer._rejection_counters[v2] == 1

    def test_gradual_rejection_independently_applied(self):
        from datetime import datetime, timezone

        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.sunset import (
            SunsetEnforcer,
            SunsetPolicy,
            SunsetRegistry,
        )

        past = datetime(2020, 1, 1, tzinfo=timezone.utc)
        registry = SunsetRegistry()
        v1 = ApiVersion(1, 0)
        v2 = ApiVersion(2, 0)
        registry.register(v1, sunset_at=past)
        registry.register(v2, sunset_at=past)

        policy = SunsetPolicy(enforce_sunset=True, gradual_rejection_percent=50)
        enforcer = SunsetEnforcer(policy, registry)

        # Run v1 through 99 requests to advance its counter
        for _ in range(99):
            enforcer.check(v1)

        # Now check v2 — its counter should be at 1 (not 100)
        result = enforcer.check(v2)
        assert enforcer._rejection_counters[v2] == 1


class TestStructuralBaking:
    """Compiler structural baking: one CompiledRoute per active version."""

    def test_single_version_bakes_one_route(self):
        from aquilia.controller.base import Controller
        from aquilia.controller.compiler import ControllerCompiler
        from aquilia.controller.decorators import GET
        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy

        class Users(Controller):
            prefix = "/users"
            version = "1.0"

            @GET("/")
            async def list(self, ctx):
                pass

        strategy = VersionStrategy(VersionConfig(strategy="url", versions=["1.0"], default_version="1.0"))

        compiler = ControllerCompiler()
        compiled = compiler.compile_controller(Users, version_strategy=strategy)

        assert len(compiled.routes) == 1
        r = compiled.routes[0]
        assert r.full_path == "/v1/users/"
        assert r.bound_version == ApiVersion(1, 0)

    def test_multi_version_bakes_multiple_routes(self):
        from aquilia.controller.base import Controller
        from aquilia.controller.compiler import ControllerCompiler
        from aquilia.controller.decorators import GET
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy

        class Users(Controller):
            prefix = "/users"
            version = "1.0"

            @GET("/", version=["1.0", "2.0"])
            async def list(self, ctx):
                pass

        strategy = VersionStrategy(VersionConfig(strategy="url", versions=["1.0", "2.0"], default_version="1.0"))

        compiler = ControllerCompiler()
        compiled = compiler.compile_controller(Users, version_strategy=strategy)

        paths = sorted([r.full_path for r in compiled.routes])
        assert "/v1/users/" in paths
        assert "/v2/users/" in paths
        assert len(compiled.routes) == 2

        for r in compiled.routes:
            assert r.bound_version is not None

    def test_version_neutral_skips_baking(self):
        from aquilia.controller.base import Controller
        from aquilia.controller.compiler import ControllerCompiler
        from aquilia.controller.decorators import GET
        from aquilia.versioning.core import VERSION_NEUTRAL
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy

        class Health(Controller):
            prefix = "/health"
            version = VERSION_NEUTRAL

            @GET("/")
            async def check(self, ctx):
                pass

        strategy = VersionStrategy(VersionConfig(strategy="url", versions=["1.0"], default_version="1.0"))

        compiler = ControllerCompiler()
        compiled = compiler.compile_controller(Health, version_strategy=strategy)

        assert len(compiled.routes) == 1
        r = compiled.routes[0]
        assert r.full_path == "/health/"
        assert r.bound_version is None

    def test_no_version_annotation_compiles_unprefixed(self):
        """A controller with no version annotation compiles to its plain prefix."""
        from aquilia.controller.base import Controller
        from aquilia.controller.compiler import ControllerCompiler
        from aquilia.controller.decorators import GET
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy

        class Misc(Controller):
            prefix = "/misc"

            @GET("/")
            async def index(self, ctx):
                pass

        strategy = VersionStrategy(VersionConfig(strategy="url", versions=["1.0"], default_version="1.0"))

        compiler = ControllerCompiler()
        compiled = compiler.compile_controller(Misc, version_strategy=strategy)

        assert len(compiled.routes) == 1
        r = compiled.routes[0]
        assert r.full_path == "/misc/"
        assert r.bound_version is None


class TestRouterBoundVersionMatching:
    """Router _version_matches honours bound_version on CompiledRoute."""

    def test_bound_version_matches_exact(self):
        from aquilia.controller.router import ControllerRouter
        from aquilia.versioning.core import ApiVersion

        route = MagicMock()
        route.bound_version = ApiVersion(2, 0)

        assert ControllerRouter._version_matches(route, ApiVersion(2, 0)) is True
        assert ControllerRouter._version_matches(route, ApiVersion(1, 0)) is False

    def test_bound_version_with_none_api_version_matches(self):
        """When api_version is None (versioning disabled), bound routes still match."""
        from aquilia.controller.router import ControllerRouter
        from aquilia.versioning.core import ApiVersion

        route = MagicMock()
        route.bound_version = ApiVersion(1, 0)

        assert ControllerRouter._version_matches(route, None) is True

    def test_no_bound_version_falls_through_to_metadata(self):
        """When bound_version is None, the method falls through to version_metadata checks."""
        from aquilia.controller.router import ControllerRouter

        route = MagicMock()
        route.bound_version = None
        route.version_metadata = {"neutral": True}
        route.controller_metadata = MagicMock()
        route.controller_metadata.version = None

        from aquilia.versioning.core import ApiVersion

        assert ControllerRouter._version_matches(route, ApiVersion(1, 0)) is True


class TestASGIVersionErrorEarlyReturn:
    """Version errors raised during pre-routing resolution must return
    a proper error response immediately, not crash the pipeline."""

    @pytest.mark.asyncio
    async def test_missing_version_returns_400(self):
        """URL strategy with require_version=True and no version in path → 400."""
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy

        strategy = VersionStrategy(
            VersionConfig(
                strategy="url",
                versions=["1.0"],
                default_version="1.0",
                require_version=True,
                negotiation_mode="compatible",
            )
        )

        from types import SimpleNamespace

        from aquilia.asgi import ASGIAdapter
        from aquilia.middleware import MiddlewareStack

        router = MagicMock()
        engine = MagicMock()
        server = SimpleNamespace(_version_strategy=strategy)
        adapter = ASGIAdapter(
            controller_router=router,
            controller_engine=engine,
            middleware_stack=MiddlewareStack(),
            server=server,
        )

        router.match_sync.return_value = None
        router.get_allowed_methods.return_value = []

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/users",
            "query_string": b"",
            "headers": [],
        }

        messages = []

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(msg):
            messages.append(msg)

        await adapter.handle_http(scope, receive, send)

        # Should have sent an error response, not crashed
        assert len(messages) >= 1
        start = messages[0]
        assert start["type"] == "http.response.start"
        assert start["status"] in (400, 404)


class TestWorkspaceAutoDiscoveryPreservation:
    """Test that auto-discovery does not remove manual configurations in workspace.py."""

    def test_update_workspace_config_preserves_custom_chaining(self, tmp_path):
        from aquilia.cli.generators.workspace import WorkspaceGenerator

        workspace_py = tmp_path / "workspace.py"
        workspace_py.write_text(
            """
from aquilia import Workspace, Module

workspace = (
    Workspace("test_ws")
    .module(Module("brief", version="0.1.0", description="Brief module")
        .route_prefix("/brief")
        .tags("brief", "custom")
        .depends_on("auth"))
    # ---- Integrations ----------------------------------------------------
)
""",
            encoding="utf-8",
        )

        generator = WorkspaceGenerator("test_ws", tmp_path)
        discovered = {
            "brief": {
                "name": "brief",
                "version": "0.1.0",
                "description": "Brief module",
                "route_prefix": "/brief",
                "tags": ["brief"],
            }
        }

        generator.update_workspace_config(workspace_py, discovered)

        updated_content = workspace_py.read_text(encoding="utf-8")
        assert '.tags("brief", "custom")' in updated_content
        assert '.depends_on("auth")' in updated_content
        assert '.route_prefix("/brief")' in updated_content


class TestModuleLevelSunsetPolicy:
    """Test that module-level sunset policy overrides are correctly respected."""

    @pytest.mark.asyncio
    async def test_module_sunset_policy_override(self):
        from datetime import datetime, timezone
        from types import SimpleNamespace

        from aquilia.asgi import ASGIAdapter
        from aquilia.middleware import MiddlewareStack
        from aquilia.response import Response
        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy
        from aquilia.versioning.sunset import SunsetPolicy, SunsetRegistry

        # Setup SunsetRegistry with a sunset version (1.0)
        registry = SunsetRegistry()
        v1 = ApiVersion(1, 0)
        registry.register(v1, sunset_at=datetime(2020, 1, 1, tzinfo=timezone.utc))

        # Global policy: enforce sunset (reject)
        global_policy = SunsetPolicy(
            enforce_sunset=True,
            warn_header=True,
        )

        config = VersionConfig(
            strategy="url",
            versions=["1.0", "2.0"],
            default_version="1.0",
            negotiation_mode="compatible",
            sunset_policy=global_policy,
        )

        strategy = VersionStrategy(config)
        # Override the enforcer registry so it uses our registry
        strategy._sunset_enforcer._registry = registry

        # Define manifest-level versioning overrides:
        # 'brief' module: overrides sunset policy to warn-only (enforce_sunset=False)
        strategy._module_versioning_overrides = {
            "brief": {
                "enabled": True,
                "sunset_policy": SunsetPolicy(
                    enforce_sunset=False,
                    warn_header=True,
                ),
            }
        }
        # 'other' module: fallback workspace-level configs (uses default/no override, so rejection happens)
        strategy._workspace_modules = {
            "other": {
                "versioning": {
                    "enabled": True,
                }
            }
        }

        from aquilia.versioning.middleware import VersionMiddleware

        router = MagicMock()
        engine = MagicMock()
        server = SimpleNamespace(_version_strategy=strategy)

        stack = MiddlewareStack()
        stack.add(VersionMiddleware(strategy))

        adapter = ASGIAdapter(
            controller_router=router,
            controller_engine=engine,
            middleware_stack=stack,
            server=server,
        )

        # Mock route matching
        route_brief = MagicMock()
        route_brief.app_name = "brief"
        match_brief = MagicMock()
        match_brief.route = route_brief

        route_other = MagicMock()
        route_other.app_name = "other"
        match_other = MagicMock()
        match_other.route = route_other

        router.match_sync.side_effect = lambda path, method, api_version: (
            match_brief if "brief" in path else match_other
        )
        router.get_allowed_methods.return_value = []
        engine.execute = AsyncMock(return_value=Response.json({"ok": True}))

        # 1. Request brief module with sunset version 1.0 (should succeed with warning headers)
        scope_brief = {
            "type": "http",
            "method": "GET",
            "path": "/v1/brief/users",
            "query_string": b"",
            "headers": [],
        }
        messages_brief = []

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send_brief(msg):
            messages_brief.append(msg)

        await adapter.handle_http(scope_brief, receive, send_brief)

        # Ensure response was allowed (200 OK) and has Sunset headers
        assert len(messages_brief) >= 1
        start_brief = messages_brief[0]
        assert start_brief["type"] == "http.response.start"
        assert start_brief["status"] == 200
        headers_dict = {k.decode().lower(): v.decode() for k, v in start_brief["headers"]}
        assert "sunset" in headers_dict

        # 2. Request other module with sunset version 1.0 (should be rejected with 410)
        scope_other = {
            "type": "http",
            "method": "GET",
            "path": "/v1/other/users",
            "query_string": b"",
            "headers": [],
        }
        messages_other = []

        async def send_other(msg):
            messages_other.append(msg)

        await adapter.handle_http(scope_other, receive, send_other)

        # Ensure response was rejected (410 Gone)
        assert len(messages_other) >= 1
        start_other = messages_other[0]
        assert start_other["type"] == "http.response.start"
        assert start_other["status"] == 410


class TestManifestLevelVersioningConfig:
    """Brutal tests verifying manifest-level overrides (enabled, position, auto_version_unmarked)."""

    def test_app_versioning_config_serialization(self):
        from aquilia.manifest import AppVersioningConfig
        from aquilia.versioning.sunset import SunsetPolicy

        policy = SunsetPolicy(warn_header=True)
        config = AppVersioningConfig(
            enabled=True,
            position="after",
            auto_version_unmarked=True,
            sunset_policy=policy,
        )
        dct = config.to_dict()
        assert dct["enabled"] is True
        assert dct["position"] == "after"
        assert dct["auto_version_unmarked"] is True
        assert dct["sunset_policy"] == policy

    def test_manifest_override_disabled_versioning(self):
        from aquilia.controller.base import Controller
        from aquilia.controller.compiler import ControllerCompiler
        from aquilia.controller.decorators import GET
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy

        # Global URL versioning is active
        strategy = VersionStrategy(
            VersionConfig(
                strategy="url",
                versions=["1.0", "2.0"],
                default_version="1.0",
            )
        )

        class MyController(Controller):
            prefix = "/items"

            @GET("/")
            def get_items(self):
                return "items"

        compiler = ControllerCompiler()

        # 1. When module versioning override has enabled=False
        module_versioning = {"enabled": False}
        compiled = compiler.compile_controller(
            MyController,
            base_prefix="/api",
            version_strategy=strategy,
            module_versioning=module_versioning,
        )
        # Should NOT compile versioned routes (only standard unversioned route)
        assert len(compiled.routes) == 1
        assert compiled.routes[0].full_path == "/api/items/"
        assert compiled.routes[0].bound_version is None

    def test_manifest_override_auto_version_unmarked(self):
        from aquilia.controller.base import Controller
        from aquilia.controller.compiler import ControllerCompiler
        from aquilia.controller.decorators import GET
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy

        strategy = VersionStrategy(
            VersionConfig(
                strategy="url",
                versions=["1.0", "2.0"],
                default_version="1.0",
            )
        )

        class MyController(Controller):
            prefix = "/items"

            @GET("/")
            def get_items(self):
                return "items"

        compiler = ControllerCompiler()

        # 2. When auto_version_unmarked=True is set on module level
        module_versioning = {"enabled": True, "auto_version_unmarked": True}
        compiled = compiler.compile_controller(
            MyController,
            base_prefix="/api",
            version_strategy=strategy,
            module_versioning=module_versioning,
        )
        # Should generate versioned routes for unmarked route
        versioned_paths = [r.full_path for r in compiled.routes if r.bound_version is not None]
        assert len(versioned_paths) == 2
        assert "/v1/api/items/" in versioned_paths
        assert "/v2/api/items/" in versioned_paths


class TestVersioningPerformanceStress:
    """Stress tests measuring route compilation and trie matching performance under load."""

    def test_trie_matching_stress_under_load(self):
        import time

        from aquilia.controller.base import Controller
        from aquilia.controller.compiler import ControllerCompiler
        from aquilia.controller.decorators import GET
        from aquilia.controller.router import ControllerRouter
        from aquilia.versioning.core import ApiVersion
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy

        router = ControllerRouter()
        compiler = ControllerCompiler()

        # Build strategy
        strategy = VersionStrategy(
            VersionConfig(
                strategy="url",
                versions=["1.0", "2.0"],
                default_version="1.0",
            )
        )

        # Register 200 routes representing A and B modules
        for i in range(100):
            # We can define Controller class dynamically
            attrs_a = {
                "prefix": f"/resource-{i}",
                "get_item": GET("/")(lambda self: "ok"),
            }
            ctrl_a = type(f"ControllerA_{i}", (Controller,), attrs_a)

            # Module A uses default URL position (before)
            compiled_a = compiler.compile_controller(
                ctrl_a,
                base_prefix="/api/module-a",
                version_strategy=strategy,
                module_versioning={"enabled": True, "auto_version_unmarked": True},
            )
            for r in compiled_a.routes:
                r.app_name = "module_a"
            router.add_controller(compiled_a)

            # Module B overrides position to "after"
            attrs_b = {
                "prefix": f"/resource-{i}",
                "get_item": GET("/")(lambda self: "ok"),
            }
            ctrl_b = type(f"ControllerB_{i}", (Controller,), attrs_b)

            compiled_b = compiler.compile_controller(
                ctrl_b,
                base_prefix="/api/module-b",
                version_strategy=strategy,
                module_versioning={"enabled": True, "position": "after", "auto_version_unmarked": True},
            )
            for r in compiled_b.routes:
                r.app_name = "module_b"
            router.add_controller(compiled_b)

        router.initialize()

        # Stress test: perform 5000 lookups to verify O(k) performance
        start_time = time.perf_counter()

        for k in range(25):
            for i in range(100):
                # Look up module A route
                match_a = router.match_sync(f"/v1/api/module-a/resource-{i}/", "GET", ApiVersion(1, 0))
                assert match_a is not None
                assert match_a.route.app_name == "module_a"

                # Look up module B route
                match_b = router.match_sync(f"/api/module-b/v2/resource-{i}/", "GET", ApiVersion(2, 0))
                assert match_b is not None
                assert match_b.route.app_name == "module_b"

        duration = time.perf_counter() - start_time
        # Trie matching should be extremely fast (under 250ms for 5000 lookups)
        assert duration < 0.25, f"Stress test took too long: {duration:.3f}s"

    @pytest.mark.asyncio
    async def test_manifest_independent_module_versioning_strategy(self):
        from types import SimpleNamespace

        from aquilia.asgi import ASGIAdapter
        from aquilia.controller import GET, Controller
        from aquilia.controller.compiler import ControllerCompiler
        from aquilia.controller.router import ControllerRouter
        from aquilia.manifest import AppManifest, AppVersioningConfig
        from aquilia.middleware import MiddlewareStack
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy

        # Global config is url-path strategy
        global_config = VersionConfig(strategy="url", versions=["1.0", "2.0"], default_version="1.0")
        strategy = VersionStrategy(global_config)

        # Module A overrides to header strategy
        manifest_a = AppManifest(
            name="module_a",
            version="1.0.0",
            versioning=AppVersioningConfig(
                strategy="header", header_name="X-Custom-Module-Version", versions=["1.5", "2.5"], default_version="1.5"
            ),
        )

        class ControllerA(Controller):
            prefix = "/resource"

            @GET("/")
            def get_item(self):
                return "a"

        compiler = ControllerCompiler()
        router = ControllerRouter()

        class DummyAppContext:
            def __init__(self, name, route_prefix, manifest):
                self.name = name
                self.route_prefix = route_prefix
                self.manifest = manifest

        app_ctx_a = DummyAppContext("module_a", "/api/module-a", manifest_a)

        mv_dict = manifest_a.versioning.to_dict()
        merged_dict = global_config.to_dict()
        for k, v in mv_dict.items():
            if v is not None and k not in ("enabled", "auto_version_unmarked", "position"):
                merged_dict[k] = v

        local_cfg = VersionConfig(**merged_dict)
        local_strat = VersionStrategy(local_cfg)
        strategy._module_versioning_overrides = {"module_a": mv_dict}
        strategy._module_strategies = {"module_a": local_strat}

        compiled_a = compiler.compile_controller(
            ControllerA, base_prefix="/api/module-a", version_strategy=strategy, module_versioning=mv_dict
        )
        for r in compiled_a.routes:
            r.app_name = "module_a"
        router.add_controller(compiled_a)
        router.initialize()

        server = SimpleNamespace(
            _version_strategy=strategy,
            runtime=SimpleNamespace(meta=SimpleNamespace(app_contexts=[app_ctx_a]), di_containers={}),
            middleware_stack=MiddlewareStack(),
        )

        adapter = ASGIAdapter(
            controller_router=router,
            controller_engine=SimpleNamespace(),
            middleware_stack=MiddlewareStack(),
            server=server,
        )

        # Request Module A with X-Custom-Module-Version header
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/module-a/resource/",
            "query_string": b"",
            "headers": [(b"x-custom-module-version", b"2.5")],
        }

        from aquilia.request import Request

        request_obj = Request(scope, lambda: None)
        path_for_match, resolved_version = adapter._resolve_route_inputs(request_obj, "/api/module-a/resource/")

        assert path_for_match == "/api/module-a/resource/"
        assert resolved_version is not None
        assert str(resolved_version) == "2.5"

    def test_url_position_after_automatic_segment_detection(self):
        from aquilia.request import Request
        from aquilia.versioning.resolvers import URLPathResolver

        resolver = URLPathResolver(segment_index=0, prefix="v", strip_from_path=True)

        # 1. Test position "after": version is at index 1
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/brief/v1/article",
            "headers": [],
        }
        req = Request(scope, lambda: None)
        assert resolver.resolve(req) == "1"
        assert resolver.strip_version_from_path(req.path) == "/brief/article"

        # 2. Test position "before": version is at index 0
        scope2 = {
            "type": "http",
            "method": "GET",
            "path": "/v2/brief/article",
            "headers": [],
        }
        req2 = Request(scope2, lambda: None)
        assert resolver.resolve(req2) == "2"
        assert resolver.strip_version_from_path(req2.path) == "/brief/article"

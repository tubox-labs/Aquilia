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

import asyncio
import pytest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch


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
            ApiVersion(1, 0), ApiVersion(2, 1), ApiVersion(3, 0),
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
        from aquilia.versioning.core import ApiVersion
        from dataclasses import FrozenInstanceError
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
        assert VersionStatus.RETIRED.is_terminal     # Only RETIRED is terminal
        assert not VersionStatus.ACTIVE.is_terminal
        assert not VersionStatus.SUNSET.is_usable    # SUNSET cannot serve requests


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
        from aquilia.versioning.errors import UnsupportedVersionError
        from aquilia.versioning.core import ApiVersion
        v = ApiVersion(9, 9)
        e = UnsupportedVersionError(v, supported=[ApiVersion(1, 0), ApiVersion(2, 0)])
        assert e.version == v
        assert len(e.supported) == 2

    def test_sunset_error(self):
        from aquilia.versioning.errors import VersionSunsetError
        from aquilia.versioning.core import ApiVersion
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
        from aquilia.versioning.errors import VersionNegotiationError
        from aquilia.versioning.core import ApiVersion
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
        "headers": [
            (k.lower().encode(), v.encode())
            for k, v in (headers or {}).items()
        ],
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
        from aquilia.versioning.graph import VersionGraph
        from aquilia.versioning.core import ApiVersion
        g = VersionGraph()
        v = ApiVersion(1, 0)
        g.register(v)
        assert g.contains(v)
        assert not g.contains(ApiVersion(9, 9))

    def test_latest(self):
        from aquilia.versioning.graph import VersionGraph
        from aquilia.versioning.core import ApiVersion
        g = VersionGraph()
        g.register(ApiVersion(1, 0))
        g.register(ApiVersion(3, 0))
        g.register(ApiVersion(2, 0))
        g.freeze()  # latest is computed during freeze
        assert g.latest == ApiVersion(3, 0)

    def test_freeze_links_successors(self):
        from aquilia.versioning.graph import VersionGraph
        from aquilia.versioning.core import ApiVersion
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
        from aquilia.versioning.graph import VersionGraph
        from aquilia.versioning.core import ApiVersion
        g = VersionGraph()
        g.register(ApiVersion(1, 0))
        g.register(ApiVersion(2, 0))
        g.freeze()
        active = g.active_versions
        assert len(active) == 2

    def test_channel(self):
        from aquilia.versioning.graph import VersionGraph
        from aquilia.versioning.core import ApiVersion, VersionChannel
        g = VersionGraph()
        v = ApiVersion(2, 0)
        g.register(v)
        g.set_channel(VersionChannel.STABLE, v)
        assert g.get_by_channel(VersionChannel.STABLE) == v

    def test_register_route(self):
        from aquilia.versioning.graph import VersionGraph
        from aquilia.versioning.core import ApiVersion
        g = VersionGraph()
        v = ApiVersion(2, 0)
        g.register(v)
        g.register_route(v, "GET", "/users")
        node = g.get(v)
        assert "GET /users" in node.routes

    def test_register_controller(self):
        from aquilia.versioning.graph import VersionGraph
        from aquilia.versioning.core import ApiVersion
        g = VersionGraph()
        v = ApiVersion(1, 0)
        g.register(v)
        g.register_controller(v, "UsersController")
        node = g.get(v)
        assert "UsersController" in node.controllers

    def test_to_dict(self):
        from aquilia.versioning.graph import VersionGraph
        from aquilia.versioning.core import ApiVersion
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
        from aquilia.versioning.sunset import SunsetRegistry
        from aquilia.versioning.core import ApiVersion
        r = SunsetRegistry()
        v = ApiVersion(1, 0)
        now = datetime.now(timezone.utc)
        r.register(v, deprecated_at=now - timedelta(days=30))
        assert r.get(v) is not None
        deprecated = r.get_deprecated()
        assert len(deprecated) == 1
        assert deprecated[0].version == v

    def test_sunset_entries(self):
        from aquilia.versioning.sunset import SunsetRegistry
        from aquilia.versioning.core import ApiVersion
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
        from aquilia.versioning.sunset import SunsetRegistry
        from aquilia.versioning.core import ApiVersion
        r = SunsetRegistry()
        r.register(ApiVersion(1, 0))
        d = r.to_dict()
        assert isinstance(d, dict)


class TestSunsetEnforcer:
    def test_no_rejection_for_active(self):
        from aquilia.versioning.sunset import SunsetPolicy, SunsetRegistry, SunsetEnforcer
        from aquilia.versioning.core import ApiVersion
        reg = SunsetRegistry()
        v = ApiVersion(2, 0)
        # Not registered = active
        enforcer = SunsetEnforcer(SunsetPolicy(), reg)
        assert enforcer.check(v) is None

    def test_rejection_for_sunset(self):
        from aquilia.versioning.sunset import SunsetPolicy, SunsetRegistry, SunsetEnforcer
        from aquilia.versioning.core import ApiVersion
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
        from aquilia.versioning.sunset import SunsetPolicy, SunsetRegistry, SunsetEnforcer
        from aquilia.versioning.core import ApiVersion
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
        from aquilia.versioning.graph import VersionGraph
        from aquilia.versioning.negotiation import NegotiationMode, VersionNegotiator
        from aquilia.versioning.core import ApiVersion
        g = VersionGraph()
        for v in (versions or [ApiVersion(1, 0), ApiVersion(2, 0), ApiVersion(3, 0)]):
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
        n = self._build("compatible", [
            ApiVersion(2, 0), ApiVersion(2, 3), ApiVersion(3, 0),
        ])
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
        n = self._build("nearest", [
            ApiVersion(1, 0), ApiVersion(2, 0), ApiVersion(3, 0),
        ])
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
        from aquilia.versioning.middleware import VersionMiddleware
        from aquilia.versioning.core import ApiVersion

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
        from aquilia.versioning.middleware import VersionMiddleware
        from aquilia.versioning.core import ApiVersion

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

        strategy = self._build_strategy(strategy="url")
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
        from aquilia.controller.metadata import extract_controller_metadata
        from aquilia.controller.decorators import GET

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
        from aquilia.controller.metadata import extract_controller_metadata
        from aquilia.controller.decorators import GET

        class Items(Controller):
            prefix = "/items"

            @GET("/", version="3.0")
            async def list(self, ctx):
                pass

        meta = extract_controller_metadata(Items, "test:Items")
        assert meta.routes[0].version == "3.0"

    def test_version_neutral_controller(self):
        from aquilia.controller.base import Controller
        from aquilia.controller.metadata import extract_controller_metadata
        from aquilia.controller.decorators import GET
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
        from aquilia.controller.decorators import GET
        from aquilia.controller.compiler import ControllerCompiler
        from aquilia.controller.router import ControllerRouter
        from aquilia.versioning.core import ApiVersion, VERSION_NEUTRAL

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
        from aquilia.config_builders import Integration
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
        from aquilia.config_builders import Integration
        from aquilia.versioning.sunset import SunsetPolicy
        config = Integration.versioning(
            versions=["1.0", "2.0"],
            sunset_policy=SunsetPolicy(grace_period=timedelta(days=90)),
        )
        assert config["sunset_policy"] is not None


# ════════════════════════════════════════════════════════════════════════════
#  12. END-TO-END SCENARIO
# ════════════════════════════════════════════════════════════════════════════

class TestEndToEnd:
    """Full pipeline: config → strategy → middleware → resolve."""

    @pytest.mark.asyncio
    async def test_full_pipeline_header(self):
        """E2E: header-based versioning with sunset warning."""
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy
        from aquilia.versioning.middleware import VersionMiddleware
        from aquilia.versioning.sunset import SunsetPolicy
        from aquilia.versioning.core import ApiVersion

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
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy
        from aquilia.versioning.middleware import VersionMiddleware
        from aquilia.versioning.core import ApiVersion

        config = VersionConfig(
            strategy="url",
            versions=["1.0", "2.0"],
            default_version="1.0",
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
        from aquilia.versioning.strategy import VersionConfig, VersionStrategy
        from aquilia.versioning.middleware import VersionMiddleware
        from aquilia.versioning.core import ApiVersion

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
        from aquilia.response import Response
        from aquilia.versioning.core import ApiVersion
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
        assert version == ApiVersion(1, 0)

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

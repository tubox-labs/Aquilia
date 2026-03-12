"""
Aquilia Versioning System — Epoch-Based API Versioning

A unique, comprehensive versioning architecture that goes beyond traditional
URL/Header/Query approaches with:

  1. **Epoch-Based Versions**: Semantic `major.minor` with optional epoch
     labels (e.g. "2025-01", "v2.1", "stable", "preview")
  2. **Version Channels**: Named release channels (stable, preview, legacy,
     sunset) with promotion/demotion workflows
  3. **Multi-Strategy Resolution**: URL path, header, query param, media type,
     and custom extractors — composable and stackable
  4. **Sunset Lifecycle**: Built-in deprecation/sunset with RFC 8594/9745
     response headers, automatic sunset enforcement, and migration hints
  5. **Compile-Time Version Graph**: Version relationships resolved at compile
     time — no per-request version tree walks
  6. **Version-Neutral Routes**: Endpoints that respond to any version
  7. **Version Negotiation**: Automatic best-match selection when client
     sends a range or wildcard
  8. **Version Middleware**: Injects resolved version into RequestCtx
  9. **Controller & Route-Level Binding**: Per-controller and per-route
     version declarations with inheritance
  10. **Admin Dashboard Integration**: Version map visualization

Architecture:
    VersionConfig → VersionStrategy → VersionResolver → VersionParser →
    VersionGraph → VersionMiddleware → Controller/Route binding

Usage:

    # workspace.py
    workspace = (
        Workspace("myapp")
        .integrate(
            Integration.versioning(
                strategy="header",          # or "url", "query", "media_type", "composite"
                default_version="1.0",
                header_name="X-API-Version",
                versions=["1.0", "2.0", "2.1"],
                channels={
                    "stable": "2.0",
                    "preview": "2.1",
                    "legacy": "1.0",
                },
                sunset_policy=SunsetPolicy(
                    grace_period=timedelta(days=180),
                    warn_header=True,
                ),
            )
        )
    )

    # Controller-level
    class UsersController(Controller):
        prefix = "/users"
        version = "2.0"          # binds to version 2.0

    class UsersV1Controller(Controller):
        prefix = "/users"
        version = "1.0"          # binds to version 1.0 (legacy)

    # Route-level override
    class ItemsController(Controller):
        prefix = "/items"
        version = "2.0"

        @GET("/", version="2.1")  # This route only serves 2.1+
        async def list_v21(self, ctx):
            ...

        @GET("/")                  # Inherits controller version 2.0
        async def list(self, ctx):
            ...

    # Version-neutral
    class HealthController(Controller):
        prefix = "/health"
        version = VERSION_NEUTRAL  # Responds to any version
"""

# ── Core types ───────────────────────────────────────────────────────────
from .core import (
    VERSION_ANY,
    VERSION_NEUTRAL,
    ApiVersion,
    VersionChannel,
    VersionStatus,
)

# ── Decorators — route-level version binding ─────────────────────────────
from .decorators import version, version_neutral, version_range

# ── Errors ───────────────────────────────────────────────────────────────
from .errors import (
    InvalidVersionError,
    MissingVersionError,
    UnsupportedVersionError,
    VersionError,
    VersionNegotiationError,
    VersionSunsetError,
)

# ── Graph — compile-time version relationship map ────────────────────────
from .graph import VersionGraph, VersionNode

# ── Middleware — inject version into request context ─────────────────────
from .middleware import VersionMiddleware

# ── Negotiation — best-match version selection ───────────────────────────
from .negotiation import VersionNegotiator

# ── Parser — parse raw strings into ApiVersion ───────────────────────────
from .parser import SemanticVersionParser, VersionParser

# ── Resolvers — extract version from request ─────────────────────────────
from .resolvers import (
    BaseVersionResolver,
    ChannelResolver,
    CompositeResolver,
    HeaderResolver,
    MediaTypeResolver,
    QueryParamResolver,
    URLPathResolver,
)

# ── Strategy — central orchestrator ──────────────────────────────────────
from .strategy import VersionConfig, VersionStrategy

# ── Sunset — deprecation / sunset lifecycle ──────────────────────────────
from .sunset import (
    SunsetEnforcer,
    SunsetEntry,
    SunsetPolicy,
    SunsetRegistry,
)

__all__ = [
    # Core
    "ApiVersion",
    "VersionChannel",
    "VersionStatus",
    "VERSION_NEUTRAL",
    "VERSION_ANY",
    # Resolvers
    "BaseVersionResolver",
    "URLPathResolver",
    "HeaderResolver",
    "QueryParamResolver",
    "MediaTypeResolver",
    "CompositeResolver",
    "ChannelResolver",
    # Parser
    "VersionParser",
    "SemanticVersionParser",
    # Graph
    "VersionGraph",
    "VersionNode",
    # Strategy
    "VersionStrategy",
    "VersionConfig",
    # Sunset
    "SunsetPolicy",
    "SunsetEntry",
    "SunsetRegistry",
    "SunsetEnforcer",
    # Middleware
    "VersionMiddleware",
    # Negotiation
    "VersionNegotiator",
    # Decorators
    "version",
    "version_neutral",
    "version_range",
    # Errors
    "VersionError",
    "InvalidVersionError",
    "UnsupportedVersionError",
    "VersionSunsetError",
    "MissingVersionError",
    "VersionNegotiationError",
]

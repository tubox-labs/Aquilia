"""
Aquilia Versioning — Version Strategy

Central orchestrator that ties together all versioning components:
resolver, parser, graph, negotiator, and sunset enforcer.

This is the single entry point used by ``VersionMiddleware`` and
the controller engine at request time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from .core import ApiVersion, VersionChannel
from .errors import (
    InvalidVersionError,
    MissingVersionError,
    VersionSunsetError,
)
from .graph import VersionGraph
from .negotiation import NegotiationMode, VersionNegotiator
from .parser import SemanticVersionParser, VersionParser
from .resolvers import (
    BaseVersionResolver,
    ChannelResolver,
    CompositeResolver,
    HeaderResolver,
    MediaTypeResolver,
    QueryParamResolver,
    URLPathResolver,
)
from .sunset import SunsetEnforcer, SunsetPolicy, SunsetRegistry

if TYPE_CHECKING:
    from ..request import Request


@dataclass
class VersionConfig:
    """
    Complete versioning configuration.

    Used by ``Integration.versioning()`` in ``workspace.py``.

    Example::

        VersionConfig(
            strategy="header",
            versions=["1.0", "2.0", "2.1"],
            default_version="2.0",
            header_name="X-API-Version",
            channels={"stable": "2.0", "preview": "2.1"},
            require_version=False,
            negotiation_mode="compatible",
            sunset_policy=SunsetPolicy(grace_period=timedelta(days=180)),
        )
    """

    # Strategy: "url", "header", "query", "media_type", "composite", "channel"
    strategy: str = "header"

    # Registered versions (strings, parsed at init)
    versions: list[str] = field(default_factory=list)

    # Default version when client doesn't specify one
    default_version: str | None = None

    # Whether version is required (if False, uses default)
    require_version: bool = False

    # Header-based resolver config
    header_name: str = "X-API-Version"

    # Query param resolver config
    query_param: str = "api_version"

    # URL path resolver config
    url_prefix: str = "v"
    url_segment_index: int = 0
    strip_version_from_path: bool = True

    # Media type resolver config
    media_type_param: str = "version"

    # Channel configuration
    channels: dict[str, str] = field(default_factory=dict)
    channel_header: str = "X-API-Channel"
    channel_query_param: str = "api_channel"

    # Negotiation mode
    negotiation_mode: str = "exact"

    # Sunset policy
    sunset_policy: SunsetPolicy | None = None

    # Sunset schedules: {version_str: {deprecated_at, sunset_at, ...}}
    sunset_schedules: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Response header: include API-Version in response
    include_version_header: bool = True
    response_header_name: str = "X-API-Version"

    # Response header: include Supported-Versions
    include_supported_versions_header: bool = True
    supported_versions_header: str = "X-API-Supported-Versions"

    # Version-neutral paths (always served regardless of version)
    neutral_paths: list[str] = field(default_factory=lambda: [
        "/_health",
        "/openapi.json",
        "/docs",
        "/redoc",
    ])

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "versions": self.versions,
            "default_version": self.default_version,
            "require_version": self.require_version,
            "header_name": self.header_name,
            "channels": self.channels,
            "negotiation_mode": self.negotiation_mode,
            "neutral_paths": self.neutral_paths,
        }


class VersionStrategy:
    """
    Central versioning orchestrator.

    Wired into the server at startup. Provides the ``resolve()`` method
    used by ``VersionMiddleware`` on every request.

    Architecture::

        Request → Resolver → Parser → Validator → Negotiator → Sunset Check → Version
    """

    def __init__(self, config: VersionConfig) -> None:
        self._config = config

        # 1. Build parser
        self._parser: VersionParser = SemanticVersionParser()

        # 2. Build resolver
        self._resolver = self._build_resolver(config)

        # 3. Build version graph
        self._graph = VersionGraph()

        # 4. Parse and register versions
        self._default_version: ApiVersion | None = None
        self._register_versions(config)

        # 5. Build negotiator
        self._negotiator = VersionNegotiator(
            graph=self._graph,
            mode=NegotiationMode(config.negotiation_mode),
        )

        # 6. Build sunset system
        self._sunset_policy = config.sunset_policy or SunsetPolicy()
        self._sunset_registry = SunsetRegistry()
        self._sunset_enforcer = SunsetEnforcer(
            policy=self._sunset_policy,
            registry=self._sunset_registry,
        )
        self._register_sunset_schedules(config)

        # 7. Pre-compute neutral paths set
        self._neutral_paths = frozenset(config.neutral_paths)

        # 8. Freeze graph
        self._graph.freeze()

    # ── Builder helpers ───────────────────────────────────────────────

    def _build_resolver(self, config: VersionConfig) -> BaseVersionResolver:
        """Build resolver from config strategy."""
        strategy = config.strategy.lower()

        if strategy == "url":
            return URLPathResolver(
                segment_index=config.url_segment_index,
                prefix=config.url_prefix,
                strip_from_path=config.strip_version_from_path,
            )
        elif strategy == "header":
            return HeaderResolver(header_name=config.header_name)
        elif strategy == "query":
            return QueryParamResolver(param_name=config.query_param)
        elif strategy == "media_type":
            return MediaTypeResolver(param_name=config.media_type_param)
        elif strategy == "channel":
            return ChannelResolver(
                channel_map=config.channels,
                header_name=config.channel_header,
                query_param=config.channel_query_param,
            )
        elif strategy == "composite":
            composite = CompositeResolver()
            # Stack all resolvers with URL first (highest priority)
            composite.add(URLPathResolver(
                segment_index=config.url_segment_index,
                prefix=config.url_prefix,
                strip_from_path=config.strip_version_from_path,
            ))
            composite.add(HeaderResolver(header_name=config.header_name))
            composite.add(QueryParamResolver(param_name=config.query_param))
            composite.add(MediaTypeResolver(param_name=config.media_type_param))
            if config.channels:
                composite.add(ChannelResolver(
                    channel_map=config.channels,
                    header_name=config.channel_header,
                    query_param=config.channel_query_param,
                ))
            return composite
        else:
            # Default to header
            return HeaderResolver(header_name=config.header_name)

    def _register_versions(self, config: VersionConfig) -> None:
        """Parse and register all configured versions."""
        for v_str in config.versions:
            try:
                version = self._parser.parse(v_str)
                self._graph.register(version)
            except InvalidVersionError as exc:
                raise InvalidVersionError(
                    v_str,
                    reason=f"Cannot parse configured version '{v_str}'.",
                ) from exc

        # Register default version
        if config.default_version:
            self._default_version = self._parser.parse(config.default_version)
            if not self._graph.contains(self._default_version):
                self._graph.register(self._default_version)

        # Register channel mappings
        for channel_name, version_str in config.channels.items():
            version = self._parser.parse(version_str)
            try:
                channel = VersionChannel(channel_name.lower())
            except ValueError:
                channel = VersionChannel.STABLE
            self._graph.set_channel(channel, version)

    def _register_sunset_schedules(self, config: VersionConfig) -> None:
        """Register sunset schedules from config."""
        for version_str, schedule in config.sunset_schedules.items():
            version = self._parser.parse(version_str)

            deprecated_at: datetime | None = None
            sunset_at: datetime | None = None
            retired_at: datetime | None = None
            successor: ApiVersion | None = None

            if "deprecated_at" in schedule:
                deprecated_at = self._parse_datetime(schedule["deprecated_at"])
            if "sunset_at" in schedule:
                sunset_at = self._parse_datetime(schedule["sunset_at"])
            if "retired_at" in schedule:
                retired_at = self._parse_datetime(schedule["retired_at"])
            if "successor" in schedule:
                successor = self._parser.parse(schedule["successor"])

            self._sunset_registry.register(
                version,
                deprecated_at=deprecated_at,
                sunset_at=sunset_at,
                retired_at=retired_at,
                successor=successor,
                migration_url=schedule.get("migration_url"),
                notes=schedule.get("notes", ""),
            )

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        """Parse datetime from string or datetime object."""
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return None
        return None

    # ── Request resolution (hot path) ─────────────────────────────────

    def resolve(self, request: Request) -> ApiVersion:
        """
        Resolve API version from request.

        This is the main entry point called by ``VersionMiddleware``
        on every request.

        Flow:
        1. Check if path is version-neutral → skip
        2. Resolve raw version string from request
        3. Parse raw string into ApiVersion
        4. Validate against registered versions
        5. Negotiate best match
        6. Check sunset status
        7. Return resolved version

        Args:
            request: The incoming HTTP request.

        Returns:
            Resolved ``ApiVersion``.

        Raises:
            MissingVersionError: If version is required but not provided.
            InvalidVersionError: If version string cannot be parsed.
            UnsupportedVersionError: If version is not registered.
            VersionSunsetError: If version is sunset/retired.
        """
        # Step 1: Check neutral paths
        path = request.path if hasattr(request, "path") else "/"
        if path in self._neutral_paths:
            if self._default_version:
                return self._default_version
            latest = self._graph.latest
            if latest:
                return latest
            return ApiVersion(1, 0)

        # Step 2: Resolve raw version string
        raw_version = self._resolver.resolve(request)

        # Step 3: Handle missing version
        if raw_version is None:
            if self._default_version:
                return self._default_version
            if self._config.require_version:
                raise MissingVersionError(
                    strategies=[self._resolver.name],
                )
            # Use latest as ultimate fallback
            latest = self._graph.latest
            if latest:
                return latest
            return ApiVersion(1, 0)

        # Step 4: Parse
        version = self._parser.parse(raw_version)

        # Step 5: Negotiate
        version = self._negotiator.negotiate(
            version,
            fallback=self._default_version,
        )

        # Step 6: Sunset check
        rejection = self._sunset_enforcer.check(version)
        if rejection:
            raise VersionSunsetError(
                version=version,
                sunset_date=rejection.get("sunset_date"),
                migration_url=rejection.get("migration_url"),
                successor=rejection.get("successor"),
            )

        return version

    def get_response_headers(self, version: ApiVersion) -> dict[str, str]:
        """
        Get response headers to add for this version.

        Includes:
        - X-API-Version (resolved version)
        - X-API-Supported-Versions (all active versions)
        - Deprecation / Sunset (if applicable, RFC 8594/9745)
        """
        headers: dict[str, str] = {}

        # Version header
        if self._config.include_version_header:
            headers[self._config.response_header_name] = str(version)

        # Supported versions header
        if self._config.include_supported_versions_header:
            active = self._graph.active_versions
            if active:
                headers[self._config.supported_versions_header] = ", ".join(
                    str(v) for v in active
                )

        # Sunset headers
        sunset_headers = self._sunset_enforcer.get_headers(version)
        headers.update(sunset_headers)

        return headers

    def strip_version_from_path(self, request: Request) -> str | None:
        """
        If using URL path versioning, strip the version segment from
        the path so the router sees the version-less path.

        Returns the stripped path, or None if no stripping needed.
        """
        if isinstance(self._resolver, URLPathResolver):
            if self._resolver.strip_from_path:
                return self._resolver.strip_version_from_path(request.path)
        elif isinstance(self._resolver, CompositeResolver):
            url_resolver = self._resolver.get_url_resolver()
            if url_resolver and url_resolver.strip_from_path:
                return url_resolver.strip_version_from_path(request.path)
        return None

    # ── Version registration (for controller/route binding) ───────────

    def register_version(self, version: ApiVersion) -> None:
        """Register a version discovered from a controller/route."""
        if not self._graph.contains(version):
            self._graph.register(version)

    def register_controller_version(
        self,
        version: ApiVersion,
        controller_name: str,
    ) -> None:
        """Register a controller's version binding."""
        self._graph.register_controller(version, controller_name)

    def register_route_version(
        self,
        version: ApiVersion,
        method: str,
        path: str,
    ) -> None:
        """Register a route's version binding."""
        self._graph.register_route(version, method, path)

    # ── Accessors ─────────────────────────────────────────────────────

    @property
    def config(self) -> VersionConfig:
        return self._config

    @property
    def graph(self) -> VersionGraph:
        return self._graph

    @property
    def parser(self) -> VersionParser:
        return self._parser

    @property
    def resolver(self) -> BaseVersionResolver:
        return self._resolver

    @property
    def negotiator(self) -> VersionNegotiator:
        return self._negotiator

    @property
    def sunset_registry(self) -> SunsetRegistry:
        return self._sunset_registry

    @property
    def sunset_policy(self) -> SunsetPolicy:
        return self._sunset_policy

    @property
    def default_version(self) -> ApiVersion | None:
        return self._default_version

    def is_neutral_path(self, path: str) -> bool:
        """Check if a path is version-neutral."""
        return path in self._neutral_paths

    def to_dict(self) -> dict[str, Any]:
        """Serialize for admin dashboard."""
        return {
            "config": self._config.to_dict(),
            "graph": self._graph.to_dict(),
            "sunset": self._sunset_registry.to_dict(),
            "default_version": str(self._default_version) if self._default_version else None,
        }

# Versioning API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
| --- | --- | --- | --- |
| `VersionStatus` | `aquilia/versioning/core.py` | str, Enum | Version lifecycle status. |
| `VersionChannel` | `aquilia/versioning/core.py` | str, Enum | Named release channels. |
| `ApiVersion` | `aquilia/versioning/core.py` | object | Immutable API version value object. |
| `VersionError` | `aquilia/versioning/errors.py` | Fault | Base class for all versioning errors. |
| `InvalidVersionError` | `aquilia/versioning/errors.py` | VersionError | Raised when a version string cannot be parsed. |
| `UnsupportedVersionError` | `aquilia/versioning/errors.py` | VersionError | Raised when a valid version is not in the supported set. |
| `VersionSunsetError` | `aquilia/versioning/errors.py` | VersionError | Raised when a version has been sunset (permanently retired). |
| `MissingVersionError` | `aquilia/versioning/errors.py` | VersionError | Raised when no version is present and no default is configured. |
| `VersionNegotiationError` | `aquilia/versioning/errors.py` | VersionError | Raised when version negotiation fails. |
| `VersionNode` | `aquilia/versioning/graph.py` | object | A node in the version graph. |
| `VersionGraph` | `aquilia/versioning/graph.py` | object | Compile-time version relationship graph. |
| `VersionMiddleware` | `aquilia/versioning/middleware.py` | object | Middleware that resolves API version for every request. |
| `NegotiationMode` | `aquilia/versioning/negotiation.py` | str, Enum | Version negotiation mode. |
| `VersionNegotiator` | `aquilia/versioning/negotiation.py` | object | Version negotiation engine. |
| `VersionParser` | `aquilia/versioning/parser.py` | ABC | Abstract version parser protocol. |
| `SemanticVersionParser` | `aquilia/versioning/parser.py` | VersionParser | Default version parser supporting semantic and epoch formats. |
| `BaseVersionResolver` | `aquilia/versioning/resolvers.py` | ABC | Abstract base class for version resolvers. |
| `URLPathResolver` | `aquilia/versioning/resolvers.py` | BaseVersionResolver | Extract version from URL path segment. |
| `HeaderResolver` | `aquilia/versioning/resolvers.py` | BaseVersionResolver | Extract version from a custom HTTP header. |
| `QueryParamResolver` | `aquilia/versioning/resolvers.py` | BaseVersionResolver | Extract version from query parameter. |
| `MediaTypeResolver` | `aquilia/versioning/resolvers.py` | BaseVersionResolver | Extract version from Accept header media type parameter. |
| `ChannelResolver` | `aquilia/versioning/resolvers.py` | BaseVersionResolver | Resolve version via named channels (unique to Aquilia). |
| `CompositeResolver` | `aquilia/versioning/resolvers.py` | BaseVersionResolver | Combine multiple resolvers with priority fallback. |
| `CustomResolver` | `aquilia/versioning/resolvers.py` | BaseVersionResolver | User-defined version resolver. |
| `VersionConfig` | `aquilia/versioning/strategy.py` | object | Complete versioning configuration. |
| `VersionStrategy` | `aquilia/versioning/strategy.py` | object | Central versioning orchestrator. |
| `SunsetPolicy` | `aquilia/versioning/sunset.py` | object | Global sunset policy configuration. |
| `SunsetEntry` | `aquilia/versioning/sunset.py` | object | Per-version sunset schedule entry. |
| `SunsetRegistry` | `aquilia/versioning/sunset.py` | object | Registry of sunset schedules. |
| `SunsetEnforcer` | `aquilia/versioning/sunset.py` | object | Enforces sunset policies at request time. |

## Public Function Summary

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `version` | `aquilia/versioning/decorators.py` | `def version(ver: str &#124; list[str] &#124; ApiVersion &#124; list[ApiVersion]) -> Callable[[F], F]` | Bind a specific version (or list of versions) to a route. |
| `version_neutral` | `aquilia/versioning/decorators.py` | `def version_neutral(func: F) -> F` | Mark a route as version-neutral. |
| `version_range` | `aquilia/versioning/decorators.py` | `def version_range(min_version: str &#124; ApiVersion, max_version: str &#124; ApiVersion &#124; None = None) -> Callable[[F], F]` | Bind a version range to a route. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `VERSION_NEUTRAL` | `aquilia/versioning/core.py` | `_VersionSentinel('VERSION_NEUTRAL')` |
| `VERSION_ANY` | `aquilia/versioning/core.py` | `_VersionSentinel('VERSION_ANY')` |
| `F` | `aquilia/versioning/decorators.py` | `TypeVar('F', bound=Callable[..., Any])` |
| `_SEMANTIC_RE` | `aquilia/versioning/parser.py` | `re.compile('^v?(\\d+)(?:\\.(\\d+))?(?:\\.(\\d+))?$', re.IGNORECASE)` |
| `_EPOCH_RE` | `aquilia/versioning/parser.py` | `re.compile('^(\\d{4})-(\\d{1,2})(?:-(\\d{1,2}))?$')` |

## Detailed Classes And Methods

### Class: `VersionStatus`

- Source: `aquilia/versioning/core.py`
- Bases: `str, Enum`
- Summary: Version lifecycle status.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `PREVIEW` |  | `'preview'` |
| `ACTIVE` |  | `'active'` |
| `DEPRECATED` |  | `'deprecated'` |
| `SUNSET` |  | `'sunset'` |
| `RETIRED` |  | `'retired'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_usable` | `def is_usable(self) -> bool` | property | Whether this version can still serve requests. |
| `is_warn` | `def is_warn(self) -> bool` | property | Whether clients should be warned. |
| `is_terminal` | `def is_terminal(self) -> bool` | property | Whether this version is permanently unavailable. |

### Class: `VersionChannel`

- Source: `aquilia/versioning/core.py`
- Bases: `str, Enum`
- Summary: Named release channels.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `STABLE` |  | `'stable'` |
| `PREVIEW` |  | `'preview'` |
| `LEGACY` |  | `'legacy'` |
| `SUNSET` |  | `'sunset'` |
| `CANARY` |  | `'canary'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `from_string` | `def from_string(cls, value: str) -> VersionChannel` | classmethod | Parse channel from string (case-insensitive). |

### Class: `ApiVersion`

- Source: `aquilia/versioning/core.py`
- Bases: `object`
- Decorators: `total_ordering, dataclass`
- Summary: Immutable API version value object.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `major` | `int` |  |
| `minor` | `int` | `0` |
| `patch` | `int` | `0` |
| `label` | `str` | `''` |
| `status` | `VersionStatus` | `VersionStatus.ACTIVE` |
| `channel` | `VersionChannel &#124; None` | `None` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict, hash=False, compare=False)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_usable` | `def is_usable(self) -> bool` | property | Whether this version can serve requests. |
| `short` | `def short(self) -> str` | property | Short display form (e.g. 'v2.1'). |
| `url_segment` | `def url_segment(self) -> str` | property | URL path segment form (e.g. 'v2' or 'v2.1'). |
| `matches` | `def matches(self, other: ApiVersion) -> bool` |  | Check if this version matches another (major.minor match only). |
| `is_compatible_with` | `def is_compatible_with(self, other: ApiVersion) -> bool` |  | Check if this version is backward-compatible with another. |
| `with_status` | `def with_status(self, status: VersionStatus) -> ApiVersion` |  | Return a copy with updated status. |
| `with_channel` | `def with_channel(self, channel: VersionChannel) -> ApiVersion` |  | Return a copy with updated channel. |
| `parse` | `def parse(cls, raw: str) -> ApiVersion` | classmethod | Parse version from string. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize to dictionary. |

### Class: `VersionError`

- Source: `aquilia/versioning/errors.py`
- Bases: `Fault`
- Summary: Base class for all versioning errors.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.ROUTING` |
| `severity` |  | `Severity.ERROR` |
| `public` |  | `True` |

### Class: `InvalidVersionError`

- Source: `aquilia/versioning/errors.py`
- Bases: `VersionError`
- Summary: Raised when a version string cannot be parsed.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'INVALID_API_VERSION'` |
| `message` |  | `'Invalid API version'` |

### Class: `UnsupportedVersionError`

- Source: `aquilia/versioning/errors.py`
- Bases: `VersionError`
- Summary: Raised when a valid version is not in the supported set.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'UNSUPPORTED_API_VERSION'` |
| `message` |  | `'Unsupported API version'` |

### Class: `VersionSunsetError`

- Source: `aquilia/versioning/errors.py`
- Bases: `VersionError`
- Summary: Raised when a version has been sunset (permanently retired).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'API_VERSION_SUNSET'` |
| `message` |  | `'API version has been retired'` |

### Class: `MissingVersionError`

- Source: `aquilia/versioning/errors.py`
- Bases: `VersionError`
- Summary: Raised when no version is present and no default is configured.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'MISSING_API_VERSION'` |
| `message` |  | `'API version is required'` |

### Class: `VersionNegotiationError`

- Source: `aquilia/versioning/errors.py`
- Bases: `VersionError`
- Summary: Raised when version negotiation fails.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'VERSION_NEGOTIATION_FAILED'` |
| `message` |  | `'Version negotiation failed'` |

### Class: `VersionNode`

- Source: `aquilia/versioning/graph.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A node in the version graph.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `version` | `ApiVersion` |  |
| `successor` | `ApiVersion &#124; None` | `None` |
| `predecessor` | `ApiVersion &#124; None` | `None` |
| `channels` | `set[VersionChannel]` | `field(default_factory=set)` |
| `routes` | `set[str]` | `field(default_factory=set)` |
| `controllers` | `set[str]` | `field(default_factory=set)` |
| `deprecated_at` | `datetime &#124; None` | `None` |
| `sunset_at` | `datetime &#124; None` | `None` |
| `migration_url` | `str &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `status` | `def status(self) -> VersionStatus` | property | Method. |
| `is_usable` | `def is_usable(self) -> bool` | property | Method. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize for admin dashboard / API. |

### Class: `VersionGraph`

- Source: `aquilia/versioning/graph.py`
- Bases: `object`
- Summary: Compile-time version relationship graph.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `register` | `def register(self, version: ApiVersion, *, successor: ApiVersion &#124; None = None, predecessor: ApiVersion &#124; None = None, channels: set[VersionChannel] &#124; None = None, deprecated_at: datetime &#124; None = None, sunset_at: datetime &#124; None = None, migration_url: str &#124; None = None) -> VersionNode` |  | Register a version in the graph. |
| `register_route` | `def register_route(self, version: ApiVersion, method: str, path: str) -> None` |  | Associate a route with a version. |
| `register_controller` | `def register_controller(self, version: ApiVersion, controller_name: str) -> None` |  | Associate a controller with a version. |
| `set_channel` | `def set_channel(self, channel: VersionChannel, version: ApiVersion) -> None` |  | Map a channel to a concrete version. |
| `freeze` | `def freeze(self) -> None` |  | Freeze the graph after startup. |
| `get` | `def get(self, version: ApiVersion) -> VersionNode &#124; None` |  | Get node by ApiVersion. |
| `get_by_string` | `def get_by_string(self, version_str: str) -> ApiVersion &#124; None` |  | Get ApiVersion by string representation. |
| `get_by_channel` | `def get_by_channel(self, channel: VersionChannel) -> ApiVersion &#124; None` |  | Get version for a named channel. |
| `latest` | `def latest(self) -> ApiVersion &#124; None` | property | The latest active version. |
| `versions` | `def versions(self) -> list[ApiVersion]` | property | All registered versions (sorted ascending). |
| `active_versions` | `def active_versions(self) -> list[ApiVersion]` | property | Only active/preview versions. |
| `channels` | `def channels(self) -> dict[VersionChannel, ApiVersion]` | property | Channel -> version mapping. |
| `contains` | `def contains(self, version: ApiVersion) -> bool` |  | Check if a version is registered. |
| `is_supported` | `def is_supported(self, version: ApiVersion) -> bool` |  | Check if a version is registered AND usable. |
| `get_successor` | `def get_successor(self, version: ApiVersion) -> ApiVersion &#124; None` |  | Get the successor version (for migration hints). |
| `get_migration_url` | `def get_migration_url(self, version: ApiVersion) -> str &#124; None` |  | Get migration guide URL for a version. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize entire graph for admin dashboard. |

### Class: `VersionMiddleware`

- Source: `aquilia/versioning/middleware.py`
- Bases: `object`
- Summary: Middleware that resolves API version for every request.

### Class: `NegotiationMode`

- Source: `aquilia/versioning/negotiation.py`
- Bases: `str, Enum`
- Summary: Version negotiation mode.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `EXACT` |  | `'exact'` |
| `COMPATIBLE` |  | `'compatible'` |
| `LATEST` |  | `'latest'` |
| `BEST_MATCH` |  | `'best_match'` |
| `NEAREST` |  | `'nearest'` |

### Class: `VersionNegotiator`

- Source: `aquilia/versioning/negotiation.py`
- Bases: `object`
- Summary: Version negotiation engine.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `mode` | `def mode(self) -> NegotiationMode` | property | Method. |
| `negotiate` | `def negotiate(self, requested: ApiVersion, *, fallback: ApiVersion &#124; None = None) -> ApiVersion` |  | Negotiate the best version for a request. |

### Class: `VersionParser`

- Source: `aquilia/versioning/parser.py`
- Bases: `ABC`
- Summary: Abstract version parser protocol.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `parse` | `def parse(self, raw: str) -> ApiVersion` | abstractmethod | Parse a raw version string into an ``ApiVersion``. |
| `format` | `def format(self, version: ApiVersion) -> str` | abstractmethod | Format an ``ApiVersion`` back to a string. |

### Class: `SemanticVersionParser`

- Source: `aquilia/versioning/parser.py`
- Bases: `VersionParser`
- Summary: Default version parser supporting semantic and epoch formats.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `parse` | `def parse(self, raw: str) -> ApiVersion` |  | Parse version string. |
| `format` | `def format(self, version: ApiVersion) -> str` |  | Format version to string. |

### Class: `BaseVersionResolver`

- Source: `aquilia/versioning/resolvers.py`
- Bases: `ABC`
- Summary: Abstract base class for version resolvers.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `name` | `def name(self) -> str` | property, abstractmethod | Human-readable name for this resolver. |
| `resolve` | `def resolve(self, request: Request) -> str &#124; None` | abstractmethod | Extract version string from request. |

### Class: `URLPathResolver`

- Source: `aquilia/versioning/resolvers.py`
- Bases: `BaseVersionResolver`
- Summary: Extract version from URL path segment.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `name` | `def name(self) -> str` | property | Method. |
| `strip_from_path` | `def strip_from_path(self) -> bool` | property | Method. |
| `resolve` | `def resolve(self, request: Request) -> str &#124; None` |  | Method. |
| `strip_version_from_path` | `def strip_version_from_path(self, path: str) -> str` |  | Remove the version segment from the path. |

### Class: `HeaderResolver`

- Source: `aquilia/versioning/resolvers.py`
- Bases: `BaseVersionResolver`
- Summary: Extract version from a custom HTTP header.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `name` | `def name(self) -> str` | property | Method. |
| `resolve` | `def resolve(self, request: Request) -> str &#124; None` |  | Method. |

### Class: `QueryParamResolver`

- Source: `aquilia/versioning/resolvers.py`
- Bases: `BaseVersionResolver`
- Summary: Extract version from query parameter.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `name` | `def name(self) -> str` | property | Method. |
| `resolve` | `def resolve(self, request: Request) -> str &#124; None` |  | Method. |

### Class: `MediaTypeResolver`

- Source: `aquilia/versioning/resolvers.py`
- Bases: `BaseVersionResolver`
- Summary: Extract version from Accept header media type parameter.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `name` | `def name(self) -> str` | property | Method. |
| `resolve` | `def resolve(self, request: Request) -> str &#124; None` |  | Method. |

### Class: `ChannelResolver`

- Source: `aquilia/versioning/resolvers.py`
- Bases: `BaseVersionResolver`
- Summary: Resolve version via named channels (unique to Aquilia).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `name` | `def name(self) -> str` | property | Method. |
| `resolve` | `def resolve(self, request: Request) -> str &#124; None` |  | Method. |
| `update_channel` | `def update_channel(self, channel: str, version: str) -> None` |  | Update channel -> version mapping (for deployment-time changes). |

### Class: `CompositeResolver`

- Source: `aquilia/versioning/resolvers.py`
- Bases: `BaseVersionResolver`
- Summary: Combine multiple resolvers with priority fallback.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `name` | `def name(self) -> str` | property | Method. |
| `add` | `def add(self, resolver: BaseVersionResolver) -> CompositeResolver` |  | Add a resolver to the chain. |
| `resolve` | `def resolve(self, request: Request) -> str &#124; None` |  | Method. |
| `resolvers` | `def resolvers(self) -> list[BaseVersionResolver]` | property | Get the resolver chain. |
| `get_url_resolver` | `def get_url_resolver(self) -> URLPathResolver &#124; None` |  | Get the URL path resolver (if any) for path stripping. |

### Class: `CustomResolver`

- Source: `aquilia/versioning/resolvers.py`
- Bases: `BaseVersionResolver`
- Summary: User-defined version resolver.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `name` | `def name(self) -> str` | property | Method. |
| `resolve` | `def resolve(self, request: Request) -> str &#124; None` |  | Method. |

### Class: `VersionConfig`

- Source: `aquilia/versioning/strategy.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Complete versioning configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `strategy` | `str` | `'header'` |
| `versions` | `list[str]` | `field(default_factory=list)` |
| `default_version` | `str &#124; None` | `None` |
| `require_version` | `bool` | `False` |
| `header_name` | `str` | `'X-API-Version'` |
| `query_param` | `str` | `'api_version'` |
| `url_prefix` | `str` | `'v'` |
| `url_segment_index` | `int` | `0` |
| `strip_version_from_path` | `bool` | `True` |
| `media_type_param` | `str` | `'version'` |
| `channels` | `dict[str, str]` | `field(default_factory=dict)` |
| `channel_header` | `str` | `'X-API-Channel'` |
| `channel_query_param` | `str` | `'api_channel'` |
| `negotiation_mode` | `str` | `'exact'` |
| `sunset_policy` | `SunsetPolicy &#124; None` | `None` |
| `sunset_schedules` | `dict[str, dict[str, Any]]` | `field(default_factory=dict)` |
| `include_version_header` | `bool` | `True` |
| `response_header_name` | `str` | `'X-API-Version'` |
| `include_supported_versions_header` | `bool` | `True` |
| `supported_versions_header` | `str` | `'X-API-Supported-Versions'` |
| `neutral_paths` | `list[str]` | `field(default_factory=lambda: ['/_health', '/openapi.json', '/docs', '/redoc'])` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `VersionStrategy`

- Source: `aquilia/versioning/strategy.py`
- Bases: `object`
- Summary: Central versioning orchestrator.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `resolve` | `def resolve(self, request: Request) -> ApiVersion` |  | Resolve API version from request. |
| `get_response_headers` | `def get_response_headers(self, version: ApiVersion) -> dict[str, str]` |  | Get response headers to add for this version. |
| `strip_version_from_path` | `def strip_version_from_path(self, request: Request) -> str &#124; None` |  | If using URL path versioning, strip the version segment from |
| `register_version` | `def register_version(self, version: ApiVersion) -> None` |  | Register a version discovered from a controller/route. |
| `register_controller_version` | `def register_controller_version(self, version: ApiVersion, controller_name: str) -> None` |  | Register a controller's version binding. |
| `register_route_version` | `def register_route_version(self, version: ApiVersion, method: str, path: str) -> None` |  | Register a route's version binding. |
| `config` | `def config(self) -> VersionConfig` | property | Method. |
| `graph` | `def graph(self) -> VersionGraph` | property | Method. |
| `parser` | `def parser(self) -> VersionParser` | property | Method. |
| `resolver` | `def resolver(self) -> BaseVersionResolver` | property | Method. |
| `negotiator` | `def negotiator(self) -> VersionNegotiator` | property | Method. |
| `sunset_registry` | `def sunset_registry(self) -> SunsetRegistry` | property | Method. |
| `sunset_policy` | `def sunset_policy(self) -> SunsetPolicy` | property | Method. |
| `default_version` | `def default_version(self) -> ApiVersion &#124; None` | property | Method. |
| `is_neutral_path` | `def is_neutral_path(self, path: str) -> bool` |  | Check if a path is version-neutral. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize for admin dashboard. |

### Class: `SunsetPolicy`

- Source: `aquilia/versioning/sunset.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Global sunset policy configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `warn_header` | `bool` | `True` |
| `grace_period` | `timedelta` | `field(default_factory=lambda: timedelta(days=180))` |
| `enforce_sunset` | `bool` | `True` |
| `enforce_retired` | `bool` | `True` |
| `sunset_message` | `str` | `'This API version has been retired. Please migrate to the latest version.'` |
| `migration_url_template` | `str &#124; None` | `None` |
| `gradual_rejection_percent` | `int` | `0` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `SunsetEntry`

- Source: `aquilia/versioning/sunset.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Per-version sunset schedule entry.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `version` | `ApiVersion` |  |
| `deprecated_at` | `datetime &#124; None` | `None` |
| `sunset_at` | `datetime &#124; None` | `None` |
| `retired_at` | `datetime &#124; None` | `None` |
| `successor` | `ApiVersion &#124; None` | `None` |
| `migration_url` | `str &#124; None` | `None` |
| `notes` | `str` | `''` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_deprecated` | `def is_deprecated(self) -> bool` | property | Method. |
| `is_sunset` | `def is_sunset(self) -> bool` | property | Method. |
| `is_retired` | `def is_retired(self) -> bool` | property | Method. |
| `effective_status` | `def effective_status(self) -> VersionStatus` | property | Compute current status from dates. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `SunsetRegistry`

- Source: `aquilia/versioning/sunset.py`
- Bases: `object`
- Summary: Registry of sunset schedules.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `register` | `def register(self, version: ApiVersion, *, deprecated_at: datetime &#124; None = None, sunset_at: datetime &#124; None = None, retired_at: datetime &#124; None = None, successor: ApiVersion &#124; None = None, migration_url: str &#124; None = None, notes: str = '') -> SunsetEntry` |  | Register a sunset schedule for a version. |
| `get` | `def get(self, version: ApiVersion) -> SunsetEntry &#124; None` |  | Get sunset entry for a version. |
| `get_deprecated` | `def get_deprecated(self) -> list[SunsetEntry]` |  | Get all currently deprecated versions. |
| `get_sunset` | `def get_sunset(self) -> list[SunsetEntry]` |  | Get all currently sunset versions. |
| `get_retired` | `def get_retired(self) -> list[SunsetEntry]` |  | Get all retired versions. |
| `entries` | `def entries(self) -> list[SunsetEntry]` | property | Method. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `SunsetEnforcer`

- Source: `aquilia/versioning/sunset.py`
- Bases: `object`
- Summary: Enforces sunset policies at request time.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `check` | `def check(self, version: ApiVersion) -> dict[str, Any] &#124; None` |  | Check if a version is sunset/retired and should be rejected. |
| `get_headers` | `def get_headers(self, version: ApiVersion) -> dict[str, str]` |  | Get deprecation/sunset response headers for a version. |

## Functions

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `version` | `aquilia/versioning/decorators.py` | `def version(ver: str &#124; list[str] &#124; ApiVersion &#124; list[ApiVersion]) -> Callable[[F], F]` | Bind a specific version (or list of versions) to a route. |
| `version_neutral` | `aquilia/versioning/decorators.py` | `def version_neutral(func: F) -> F` | Mark a route as version-neutral. |
| `version_range` | `aquilia/versioning/decorators.py` | `def version_range(min_version: str &#124; ApiVersion, max_version: str &#124; ApiVersion &#124; None = None) -> Callable[[F], F]` | Bind a version range to a route. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `VERSION_NEUTRAL` | `aquilia/versioning/core.py` | `_VersionSentinel('VERSION_NEUTRAL')` |
| `VERSION_ANY` | `aquilia/versioning/core.py` | `_VersionSentinel('VERSION_ANY')` |
| `F` | `aquilia/versioning/decorators.py` | `TypeVar('F', bound=Callable[..., Any])` |
| `_SEMANTIC_RE` | `aquilia/versioning/parser.py` | `re.compile('^v?(\\d+)(?:\\.(\\d+))?(?:\\.(\\d+))?$', re.IGNORECASE)` |
| `_EPOCH_RE` | `aquilia/versioning/parser.py` | `re.compile('^(\\d{4})-(\\d{1,2})(?:-(\\d{1,2}))?$')` |

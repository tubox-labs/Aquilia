# Versioning API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/versioning/__init__.py` | 181 | 0 | 0 | Aquilia Versioning System — Epoch-Based API Versioning |
| `aquilia/versioning/core.py` | 290 | 3 | 0 | Aquilia Versioning — Core Types |
| `aquilia/versioning/decorators.py` | 138 | 0 | 3 | Aquilia Versioning — Route-Level Decorators |
| `aquilia/versioning/errors.py` | 144 | 6 | 0 | Aquilia Versioning — Version Errors |
| `aquilia/versioning/graph.py` | 261 | 2 | 0 | Aquilia Versioning — Version Graph |
| `aquilia/versioning/middleware.py` | 223 | 1 | 0 | Aquilia Versioning — Version Middleware |
| `aquilia/versioning/negotiation.py` | 193 | 2 | 0 | Aquilia Versioning — Version Negotiation |
| `aquilia/versioning/parser.py` | 137 | 2 | 0 | Aquilia Versioning — Version Parser |
| `aquilia/versioning/resolvers.py` | 486 | 8 | 0 | Aquilia Versioning — Version Resolvers |
| `aquilia/versioning/strategy.py` | 500 | 2 | 0 | Aquilia Versioning — Version Strategy |
| `aquilia/versioning/sunset.py` | 291 | 4 | 0 | Aquilia Versioning — Sunset Lifecycle |

## Public Exports

`ApiVersion`, `BaseVersionResolver`, `ChannelResolver`, `CompositeResolver`, `HeaderResolver`, `InvalidVersionError`, `MediaTypeResolver`, `MissingVersionError`, `QueryParamResolver`, `SemanticVersionParser`, `SunsetEnforcer`, `SunsetEntry`, `SunsetPolicy`, `SunsetRegistry`, `URLPathResolver`, `UnsupportedVersionError`, `VERSION_ANY`, `VERSION_NEUTRAL`, `VersionChannel`, `VersionConfig`, `VersionError`, `VersionGraph`, `VersionMiddleware`, `VersionNegotiationError`, `VersionNegotiator`, `VersionNode`, `VersionParser`, `VersionStatus`, `VersionStrategy`, `VersionSunsetError`, `version`, `version_neutral`, `version_range`

## Public Class Summary

| Class | Source | Bases | Summary |
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

| Function | Source | Signature | Summary |
| --- | --- | --- | --- |
| `version` | `aquilia/versioning/decorators.py` | `def version(ver: str \| list[str] \| ApiVersion \| list[ApiVersion])` | Bind a specific version (or list of versions) to a route. |
| `version_neutral` | `aquilia/versioning/decorators.py` | `def version_neutral(func: F)` | Mark a route as version-neutral. |
| `version_range` | `aquilia/versioning/decorators.py` | `def version_range(min_version: str \| ApiVersion, max_version: str \| ApiVersion \| None=None)` | Bind a version range to a route. |

## Constants And Module Flags

| Name | Source | Value or Type |
| --- | --- | --- |
| `VERSION_NEUTRAL` | `aquilia/versioning/core.py` | `_VersionSentinel('VERSION_NEUTRAL')` |
| `VERSION_ANY` | `aquilia/versioning/core.py` | `_VersionSentinel('VERSION_ANY')` |
| `F` | `aquilia/versioning/decorators.py` | `TypeVar('F', bound=Callable[..., Any])` |
| `_SEMANTIC_RE` | `aquilia/versioning/parser.py` | `re.compile('^v?(\\d+)(?:\\.(\\d+))?(?:\\.(\\d+))?$', re.IGNORECASE)` |
| `_EPOCH_RE` | `aquilia/versioning/parser.py` | `re.compile('^(\\d{4})-(\\d{1,2})(?:-(\\d{1,2}))?$')` |

## Detailed Classes And Methods

### `VersionStatus`

- Source: `aquilia/versioning/core.py`
- Bases: `str, Enum`
- Summary: Version lifecycle status.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `PREVIEW` | `` | `'preview'` |
| `ACTIVE` | `` | `'active'` |
| `DEPRECATED` | `` | `'deprecated'` |
| `SUNSET` | `` | `'sunset'` |
| `RETIRED` | `` | `'retired'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_usable` | `def is_usable(self)` | Whether this version can still serve requests. |
| `is_warn` | `def is_warn(self)` | Whether clients should be warned. |
| `is_terminal` | `def is_terminal(self)` | Whether this version is permanently unavailable. |

### `VersionChannel`

- Source: `aquilia/versioning/core.py`
- Bases: `str, Enum`
- Summary: Named release channels.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `STABLE` | `` | `'stable'` |
| `PREVIEW` | `` | `'preview'` |
| `LEGACY` | `` | `'legacy'` |
| `SUNSET` | `` | `'sunset'` |
| `CANARY` | `` | `'canary'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `from_string` | `def from_string(cls, value: str)` | Parse channel from string (case-insensitive). |

### `ApiVersion`

- Source: `aquilia/versioning/core.py`
- Bases: `object`
- Summary: Immutable API version value object.
- Decorators: `total_ordering`, `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `major` | `int` | `` |
| `minor` | `int` | `0` |
| `patch` | `int` | `0` |
| `label` | `str` | `''` |
| `status` | `VersionStatus` | `VersionStatus.ACTIVE` |
| `channel` | `VersionChannel \| None` | `None` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict, hash=False, compare=False)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_usable` | `def is_usable(self)` | Whether this version can serve requests. |
| `short` | `def short(self)` | Short display form (e.g. 'v2.1'). |
| `url_segment` | `def url_segment(self)` | URL path segment form (e.g. 'v2' or 'v2.1'). |
| `matches` | `def matches(self, other: ApiVersion)` | Check if this version matches another (major.minor match only). |
| `is_compatible_with` | `def is_compatible_with(self, other: ApiVersion)` | Check if this version is backward-compatible with another. |
| `with_status` | `def with_status(self, status: VersionStatus)` | Return a copy with updated status. |
| `with_channel` | `def with_channel(self, channel: VersionChannel)` | Return a copy with updated channel. |
| `parse` | `def parse(cls, raw: str)` | Parse version from string. |
| `to_dict` | `def to_dict(self)` | Serialize to dictionary. |

### `VersionError`

- Source: `aquilia/versioning/errors.py`
- Bases: `Fault`
- Summary: Base class for all versioning errors.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `public` | `` | `True` |

### `InvalidVersionError`

- Source: `aquilia/versioning/errors.py`
- Bases: `VersionError`
- Summary: Raised when a version string cannot be parsed.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'INVALID_API_VERSION'` |
| `message` | `` | `'Invalid API version'` |

### `UnsupportedVersionError`

- Source: `aquilia/versioning/errors.py`
- Bases: `VersionError`
- Summary: Raised when a valid version is not in the supported set.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'UNSUPPORTED_API_VERSION'` |
| `message` | `` | `'Unsupported API version'` |

### `VersionSunsetError`

- Source: `aquilia/versioning/errors.py`
- Bases: `VersionError`
- Summary: Raised when a version has been sunset (permanently retired).

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'API_VERSION_SUNSET'` |
| `message` | `` | `'API version has been retired'` |

### `MissingVersionError`

- Source: `aquilia/versioning/errors.py`
- Bases: `VersionError`
- Summary: Raised when no version is present and no default is configured.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'MISSING_API_VERSION'` |
| `message` | `` | `'API version is required'` |

### `VersionNegotiationError`

- Source: `aquilia/versioning/errors.py`
- Bases: `VersionError`
- Summary: Raised when version negotiation fails.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'VERSION_NEGOTIATION_FAILED'` |
| `message` | `` | `'Version negotiation failed'` |

### `VersionNode`

- Source: `aquilia/versioning/graph.py`
- Bases: `object`
- Summary: A node in the version graph.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `version` | `ApiVersion` | `` |
| `successor` | `ApiVersion \| None` | `None` |
| `predecessor` | `ApiVersion \| None` | `None` |
| `channels` | `set[VersionChannel]` | `field(default_factory=set)` |
| `routes` | `set[str]` | `field(default_factory=set)` |
| `controllers` | `set[str]` | `field(default_factory=set)` |
| `deprecated_at` | `datetime \| None` | `None` |
| `sunset_at` | `datetime \| None` | `None` |
| `migration_url` | `str \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `status` | `def status(self)` |  |
| `is_usable` | `def is_usable(self)` |  |
| `to_dict` | `def to_dict(self)` | Serialize for admin dashboard / API. |

### `VersionGraph`

- Source: `aquilia/versioning/graph.py`
- Bases: `object`
- Summary: Compile-time version relationship graph.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `register` | `def register(self, version: ApiVersion, *, successor: ApiVersion \| None=None, predecessor: ApiVersion \| None=None, channels: set[VersionChannel] \| None=None, deprecated_at: datetime \| None=None, sunset_at: datetime \| None=None, migration_url: str \| None=None)` | Register a version in the graph. |
| `register_route` | `def register_route(self, version: ApiVersion, method: str, path: str)` | Associate a route with a version. |
| `register_controller` | `def register_controller(self, version: ApiVersion, controller_name: str)` | Associate a controller with a version. |
| `set_channel` | `def set_channel(self, channel: VersionChannel, version: ApiVersion)` | Map a channel to a concrete version. |
| `freeze` | `def freeze(self)` | Freeze the graph after startup. |
| `get` | `def get(self, version: ApiVersion)` | Get node by ApiVersion. |
| `get_by_string` | `def get_by_string(self, version_str: str)` | Get ApiVersion by string representation. |
| `get_by_channel` | `def get_by_channel(self, channel: VersionChannel)` | Get version for a named channel. |
| `latest` | `def latest(self)` | The latest active version. |
| `versions` | `def versions(self)` | All registered versions (sorted ascending). |
| `active_versions` | `def active_versions(self)` | Only active/preview versions. |
| `channels` | `def channels(self)` | Channel → version mapping. |
| `contains` | `def contains(self, version: ApiVersion)` | Check if a version is registered. |
| `is_supported` | `def is_supported(self, version: ApiVersion)` | Check if a version is registered AND usable. |
| `get_successor` | `def get_successor(self, version: ApiVersion)` | Get the successor version (for migration hints). |
| `get_migration_url` | `def get_migration_url(self, version: ApiVersion)` | Get migration guide URL for a version. |
| `to_dict` | `def to_dict(self)` | Serialize entire graph for admin dashboard. |

### `VersionMiddleware`

- Source: `aquilia/versioning/middleware.py`
- Bases: `object`
- Summary: Middleware that resolves API version for every request.

### `NegotiationMode`

- Source: `aquilia/versioning/negotiation.py`
- Bases: `str, Enum`
- Summary: Version negotiation mode.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `EXACT` | `` | `'exact'` |
| `COMPATIBLE` | `` | `'compatible'` |
| `LATEST` | `` | `'latest'` |
| `BEST_MATCH` | `` | `'best_match'` |
| `NEAREST` | `` | `'nearest'` |

### `VersionNegotiator`

- Source: `aquilia/versioning/negotiation.py`
- Bases: `object`
- Summary: Version negotiation engine.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `mode` | `def mode(self)` |  |
| `negotiate` | `def negotiate(self, requested: ApiVersion, *, fallback: ApiVersion \| None=None)` | Negotiate the best version for a request. |

### `VersionParser`

- Source: `aquilia/versioning/parser.py`
- Bases: `ABC`
- Summary: Abstract version parser protocol.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `parse` | `def parse(self, raw: str)` | Parse a raw version string into an ``ApiVersion``. |
| `format` | `def format(self, version: ApiVersion)` | Format an ``ApiVersion`` back to a string. |

### `SemanticVersionParser`

- Source: `aquilia/versioning/parser.py`
- Bases: `VersionParser`
- Summary: Default version parser supporting semantic and epoch formats.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `parse` | `def parse(self, raw: str)` | Parse version string. |
| `format` | `def format(self, version: ApiVersion)` | Format version to string. |

### `BaseVersionResolver`

- Source: `aquilia/versioning/resolvers.py`
- Bases: `ABC`
- Summary: Abstract base class for version resolvers.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `name` | `def name(self)` | Human-readable name for this resolver. |
| `resolve` | `def resolve(self, request: Request)` | Extract version string from request. |

### `URLPathResolver`

- Source: `aquilia/versioning/resolvers.py`
- Bases: `BaseVersionResolver`
- Summary: Extract version from URL path segment.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `name` | `def name(self)` |  |
| `strip_from_path` | `def strip_from_path(self)` |  |
| `resolve` | `def resolve(self, request: Request)` |  |
| `strip_version_from_path` | `def strip_version_from_path(self, path: str)` | Remove the version segment from the path. |

### `HeaderResolver`

- Source: `aquilia/versioning/resolvers.py`
- Bases: `BaseVersionResolver`
- Summary: Extract version from a custom HTTP header.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `name` | `def name(self)` |  |
| `resolve` | `def resolve(self, request: Request)` |  |

### `QueryParamResolver`

- Source: `aquilia/versioning/resolvers.py`
- Bases: `BaseVersionResolver`
- Summary: Extract version from query parameter.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `name` | `def name(self)` |  |
| `resolve` | `def resolve(self, request: Request)` |  |

### `MediaTypeResolver`

- Source: `aquilia/versioning/resolvers.py`
- Bases: `BaseVersionResolver`
- Summary: Extract version from Accept header media type parameter.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `name` | `def name(self)` |  |
| `resolve` | `def resolve(self, request: Request)` |  |

### `ChannelResolver`

- Source: `aquilia/versioning/resolvers.py`
- Bases: `BaseVersionResolver`
- Summary: Resolve version via named channels (unique to Aquilia).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `name` | `def name(self)` |  |
| `resolve` | `def resolve(self, request: Request)` |  |
| `update_channel` | `def update_channel(self, channel: str, version: str)` | Update channel → version mapping (for deployment-time changes). |

### `CompositeResolver`

- Source: `aquilia/versioning/resolvers.py`
- Bases: `BaseVersionResolver`
- Summary: Combine multiple resolvers with priority fallback.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `name` | `def name(self)` |  |
| `add` | `def add(self, resolver: BaseVersionResolver)` | Add a resolver to the chain. |
| `resolve` | `def resolve(self, request: Request)` |  |
| `resolvers` | `def resolvers(self)` | Get the resolver chain. |
| `get_url_resolver` | `def get_url_resolver(self)` | Get the URL path resolver (if any) for path stripping. |

### `CustomResolver`

- Source: `aquilia/versioning/resolvers.py`
- Bases: `BaseVersionResolver`
- Summary: User-defined version resolver.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `name` | `def name(self)` |  |
| `resolve` | `def resolve(self, request: Request)` |  |

### `VersionConfig`

- Source: `aquilia/versioning/strategy.py`
- Bases: `object`
- Summary: Complete versioning configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `strategy` | `str` | `'header'` |
| `versions` | `list[str]` | `field(default_factory=list)` |
| `default_version` | `str \| None` | `None` |
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
| `sunset_policy` | `SunsetPolicy \| None` | `None` |
| `sunset_schedules` | `dict[str, dict[str, Any]]` | `field(default_factory=dict)` |
| `include_version_header` | `bool` | `True` |
| `response_header_name` | `str` | `'X-API-Version'` |
| `include_supported_versions_header` | `bool` | `True` |
| `supported_versions_header` | `str` | `'X-API-Supported-Versions'` |
| `neutral_paths` | `list[str]` | `field(default_factory=lambda: ['/_health', '/openapi.json', '/docs', '/redoc'])` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `VersionStrategy`

- Source: `aquilia/versioning/strategy.py`
- Bases: `object`
- Summary: Central versioning orchestrator.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `resolve` | `def resolve(self, request: Request)` | Resolve API version from request. |
| `get_response_headers` | `def get_response_headers(self, version: ApiVersion)` | Get response headers to add for this version. |
| `strip_version_from_path` | `def strip_version_from_path(self, request: Request)` | If using URL path versioning, strip the version segment from the path so the router sees the version-less path. |
| `register_version` | `def register_version(self, version: ApiVersion)` | Register a version discovered from a controller/route. |
| `register_controller_version` | `def register_controller_version(self, version: ApiVersion, controller_name: str)` | Register a controller's version binding. |
| `register_route_version` | `def register_route_version(self, version: ApiVersion, method: str, path: str)` | Register a route's version binding. |
| `config` | `def config(self)` |  |
| `graph` | `def graph(self)` |  |
| `parser` | `def parser(self)` |  |
| `resolver` | `def resolver(self)` |  |
| `negotiator` | `def negotiator(self)` |  |
| `sunset_registry` | `def sunset_registry(self)` |  |
| `sunset_policy` | `def sunset_policy(self)` |  |
| `default_version` | `def default_version(self)` |  |
| `is_neutral_path` | `def is_neutral_path(self, path: str)` | Check if a path is version-neutral. |
| `to_dict` | `def to_dict(self)` | Serialize for admin dashboard. |

### `SunsetPolicy`

- Source: `aquilia/versioning/sunset.py`
- Bases: `object`
- Summary: Global sunset policy configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `warn_header` | `bool` | `True` |
| `grace_period` | `timedelta` | `field(default_factory=lambda: timedelta(days=180))` |
| `enforce_sunset` | `bool` | `True` |
| `enforce_retired` | `bool` | `True` |
| `sunset_message` | `str` | `'This API version has been retired. Please migrate to the latest version.'` |
| `migration_url_template` | `str \| None` | `None` |
| `gradual_rejection_percent` | `int` | `0` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `SunsetEntry`

- Source: `aquilia/versioning/sunset.py`
- Bases: `object`
- Summary: Per-version sunset schedule entry.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `version` | `ApiVersion` | `` |
| `deprecated_at` | `datetime \| None` | `None` |
| `sunset_at` | `datetime \| None` | `None` |
| `retired_at` | `datetime \| None` | `None` |
| `successor` | `ApiVersion \| None` | `None` |
| `migration_url` | `str \| None` | `None` |
| `notes` | `str` | `''` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_deprecated` | `def is_deprecated(self)` |  |
| `is_sunset` | `def is_sunset(self)` |  |
| `is_retired` | `def is_retired(self)` |  |
| `effective_status` | `def effective_status(self)` | Compute current status from dates. |
| `to_dict` | `def to_dict(self)` |  |

### `SunsetRegistry`

- Source: `aquilia/versioning/sunset.py`
- Bases: `object`
- Summary: Registry of sunset schedules.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `register` | `def register(self, version: ApiVersion, *, deprecated_at: datetime \| None=None, sunset_at: datetime \| None=None, retired_at: datetime \| None=None, successor: ApiVersion \| None=None, migration_url: str \| None=None, notes: str='')` | Register a sunset schedule for a version. |
| `get` | `def get(self, version: ApiVersion)` | Get sunset entry for a version. |
| `get_deprecated` | `def get_deprecated(self)` | Get all currently deprecated versions. |
| `get_sunset` | `def get_sunset(self)` | Get all currently sunset versions. |
| `get_retired` | `def get_retired(self)` | Get all retired versions. |
| `entries` | `def entries(self)` |  |
| `to_dict` | `def to_dict(self)` |  |

### `SunsetEnforcer`

- Source: `aquilia/versioning/sunset.py`
- Bases: `object`
- Summary: Enforces sunset policies at request time.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `check` | `def check(self, version: ApiVersion)` | Check if a version is sunset/retired and should be rejected. |
| `get_headers` | `def get_headers(self, version: ApiVersion)` | Get deprecation/sunset response headers for a version. |

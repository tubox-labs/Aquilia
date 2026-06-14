# API Versioning

Aquilia provides a complete API versioning system with multiple resolution strategies, declarative decorators, lifecycle state machines, sunset policies, and RFC-compliant deprecation headers.

## Core Types

### `ApiVersion`

```python
@total_ordering
@dataclass(frozen=True, slots=True)
class ApiVersion:
    """
    Immutable API version value object.

    Supports:
    - Semantic versioning: major.minor.patch (minor/patch optional)
    - Epoch labels: "2025-01" → major=2025, minor=1
    - Simple integers: "2" → major=2, minor=0
    - String prefixes: "v2.1" → major=2, minor=1
    """

    major: int
    minor: int = 0
    patch: int = 0
    label: str = ""
    status: VersionStatus = VersionStatus.ACTIVE
    channel: VersionChannel | None = None
    metadata: dict[str, Any] = field(default_factory=dict, hash=False, compare=False)
```

**Comparison:** Uses `(major, minor, patch)` tuple ordering. Supports `==`, `<`, `>`, `<=`, `>=` against other `ApiVersion` instances or strings.

**Properties:**

| Property | Return | Description |
|---|---|---|
| `is_usable` | `bool` | Can this version serve requests? |
| `short` | `str` | Short display form (e.g. `"v2.1"`) |
| `url_segment` | `str` | URL path segment form (e.g. `"v2"`) |

**Methods:**

```python
@classmethod
def parse(cls, raw: str) -> ApiVersion:
    """Parse version from string. Supports '1', '1.0', '2.1.3', 'v2', 'v2.1', '2025-01'."""

def matches(self, other: ApiVersion) -> bool:
    """Check if this version matches another (major.minor only)."""

def is_compatible_with(self, other: ApiVersion) -> bool:
    """Check backward compatibility: same major, >= minor."""

def with_status(self, status: VersionStatus) -> ApiVersion:
    """Return a copy with updated status."""

def with_channel(self, channel: VersionChannel) -> ApiVersion:
    """Return a copy with updated channel."""

def to_dict(self) -> dict[str, Any]:
    """Serialize to dictionary."""
```

### Sentinels

```python
VERSION_NEUTRAL  # Routes marked VERSION_NEUTRAL respond to ALL versions
VERSION_ANY      # Matches any version during resolution (internal fallback)
```

### `VersionStatus`

```python
class VersionStatus(str, Enum):
    """Version lifecycle status."""
    PREVIEW = "preview"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUNSET = "sunset"
    RETIRED = "retired"

    @property
    def is_usable(self) -> bool:
        """PREVIEW, ACTIVE, or DEPRECATED → can serve requests."""

    @property
    def is_warn(self) -> bool:
        """DEPRECATED or SUNSET → clients should be warned."""

    @property
    def is_terminal(self) -> bool:
        """RETIRED → permanently unavailable."""
```

**State machine:**

```
PREVIEW → ACTIVE → DEPRECATED → SUNSET → RETIRED
                ↑                       │
                └── ACTIVE (re-promote) ─┘ (only before RETIRED)
```

### `VersionChannel`

```python
class VersionChannel(str, Enum):
    """Named release channels."""
    STABLE = "stable"
    PREVIEW = "preview"
    LEGACY = "legacy"
    SUNSET = "sunset"
    CANARY = "canary"

    @classmethod
    def from_string(cls, value: str) -> VersionChannel:
        """Parse channel from string (case-insensitive)."""
```

---

## Version Resolution Strategies

### `VersionStrategy`

```python
class VersionStrategy:
    """Abstract strategy for resolving API version from request."""

    async def resolve(self, request: Request) -> ApiVersion | None: ...

    def strip_version_from_path(self, request: Request) -> str | None: ...

    def get_response_headers(self, version: ApiVersion) -> dict[str, str]: ...
```

### Resolution Order

The server attempts resolution from multiple sources in order:

1. **URL Path** — `/v2/users` → version `2.0`, route path `/users`
2. **Query Parameter** — `?api_version=2.0`
3. **Header** — `X-API-Version: 2.0`
4. **Accept Header** — `Accept: application/json; version=2.0`
5. **Channel Header** — `X-API-Channel: stable` → mapped to concrete version

The strategy is configured in `workspace.py` via `VersionConfig`.

### `VersionConfig`

```python
@dataclass
class VersionConfig:
    default_version: str = ""

    # Resolution sources (enabled/disabled)
    use_url_path: bool = True
    use_query_param: bool = False
    use_header: bool = True
    use_accept_header: bool = False
    use_channel: bool = False

    # Naming
    url_prefix: str = "v"
    query_param_name: str = "api_version"
    header_name: str = "X-API-Version"
    channel_header_name: str = "X-API-Channel"

    # Channel mapping
    channel_mapping: dict[VersionChannel, str] = field(default_factory=dict)

    # Version listing (for discovery)
    versions: list[ApiVersion] = field(default_factory=list)
```

---

## Decorators

### `@version()`

```python
def version(
    ver: str | list[str] | ApiVersion | list[ApiVersion],
) -> Callable[[F], F]:
```

Bind a specific version (or list) to a route, overriding the controller-level `version`.

```python
class ItemsController(Controller):
    prefix = "/items"
    version = "2.0"

    @GET("/")
    @version("2.1")  # This route only serves v2.1
    async def list_v21(self, ctx): ...

    @GET("/")
    async def list(self, ctx):  # Inherits controller v2.0
        ...

    @GET("/legacy")
    @version(["1.0", "2.0"])  # Serves both
    async def legacy_endpoint(self, ctx): ...
```

### `@version_neutral`

```python
def version_neutral(func: F) -> F:
```

Mark a route as version-neutral — it responds to ALL versions and unversioned requests.

```python
@GET("/health")
@version_neutral
async def health(self, ctx):
    return {"status": "ok"}
```

### `@version_range()`

```python
def version_range(
    min_version: str | ApiVersion,
    max_version: str | ApiVersion | None = None,
) -> Callable[[F], F]:
```

Bind a version range to a route. Serves any version `>= min_version` and `< max_version` (exclusive). If `max_version` is `None`, serves all versions `>= min_version`.

```python
@GET("/beta")
@version_range("2.0", "3.0")
async def beta_feature(self, ctx):
    ...  # Serves v2.0, v2.1, ..., v2.x
```

---

## VersionMiddleware

```python
class VersionMiddleware:
    """
    Middleware that resolves API version for every request.

    After execution, the resolved version is available via:
    - request.state["api_version"] → ApiVersion
    - request.state["api_version_str"] → string
    - request.state["_original_path"] → pre-stripping path (URL path versioning)
    """

    def __init__(self, strategy: VersionStrategy) -> None:
```

### Response Headers

After successful resolution, the middleware adds these headers to responses:

- `X-API-Version`: The resolved version string
- `Deprecation`: ISO 8601 date (if deprecated, RFC 9745)
- `Sunset`: ISO 8601 date (if sunset, RFC 8594)
- `Link`: Migration guide URL with `rel="deprecation"` (if configured)
- `X-API-Successor-Version`: Successor version hint

### Error Handling

The middleware catches version errors and returns appropriate HTTP responses:

| Error Class | HTTP Status | Description |
|---|---|---|
| `MissingVersionError` | 400 | No version provided when required |
| `InvalidVersionError` | 400 | Malformed version string |
| `UnsupportedVersionError` | 400 | Version not in supported list |
| `VersionSunsetError` | 410 | Version has been sunset/retired |

---

## Sunset Lifecycle

### `SunsetPolicy`

```python
@dataclass
class SunsetPolicy:
    warn_header: bool = True
    grace_period: timedelta = timedelta(days=180)
    enforce_sunset: bool = True
    enforce_retired: bool = True
    sunset_message: str = "This API version has been retired. Please migrate to the latest version."
    migration_url_template: str | None = None
    gradual_rejection_percent: int = 0  # 0-100, for gradual traffic rejection
```

### `SunsetEntry`

```python
@dataclass
class SunsetEntry:
    version: ApiVersion
    deprecated_at: datetime | None = None
    sunset_at: datetime | None = None
    retired_at: datetime | None = None
    successor: ApiVersion | None = None
    migration_url: str | None = None
    notes: str = ""

    @property
    def is_deprecated(self) -> bool: ...
    @property
    def is_sunset(self) -> bool: ...
    @property
    def is_retired(self) -> bool: ...
    @property
    def effective_status(self) -> VersionStatus: ...
```

### `SunsetRegistry`

```python
class SunsetRegistry:
    """Registry of sunset schedules for all versions."""

    def register(self, version, *, deprecated_at=None, sunset_at=None,
                 retired_at=None, successor=None, migration_url=None, notes="") -> SunsetEntry:

    def get(self, version: ApiVersion) -> SunsetEntry | None: ...
    def get_deprecated(self) -> list[SunsetEntry]: ...
    def get_sunset(self) -> list[SunsetEntry]: ...
    def get_retired(self) -> list[SunsetEntry]: ...
```

### `SunsetEnforcer`

```python
class SunsetEnforcer:
    """Enforces sunset policies at request time."""

    def __init__(self, policy: SunsetPolicy, registry: SunsetRegistry):

    def check(self, version: ApiVersion) -> dict[str, Any] | None:
        """Check if version is sunset/retired. Returns None if allowed,
           or error dict if rejected."""

    def get_headers(self, version: ApiVersion) -> dict[str, str]:
        """Get deprecation/sunset response headers (RFC 8594/9745)."""
```

**Headers emitted by `SunsetEnforcer`:**

| Header | RFC | Condition |
|---|---|---|
| `Deprecation` | RFC 9745 | When version is DEPRECATED or SUNSET |
| `Sunset` | RFC 8594 | When version is DEPRECATED or SUNSET |
| `Link` | RFC 8288 | Migration guide URL with `rel="deprecation"` |
| `X-API-Successor-Version` | Custom | When a successor version is defined |

### Gradual Sunset

When `gradual_rejection_percent > 0`, the enforcer probabilistically rejects a percentage of requests to sunset versions using a simple counter-based approach.

---

## Version Parser

```python
class SemanticVersionParser:
    """Parses version strings into ApiVersion objects."""

    def parse(self, raw: str) -> ApiVersion:
        """Parse a string like 'v2.1.3', '2.0', '2025-01'."""
```

Supports:
- `"1"` → `(1, 0, 0)`
- `"1.0"` → `(1, 0, 0)`
- `"2.1"` → `(2, 1, 0)`
- `"2.1.3"` → `(2, 1, 3)`
- `"v2"` → `(2, 0, 0)`
- `"v2.1"` → `(2, 1, 0)`
- `"2025-01"` → `(2025, 1, 0)` with `label="2025-01"`

---

## Version Graph

```python
class VersionGraph:
    """Tracks version compatibility relationships for discovery."""
```

---

## Version Errors

```python
class VersionError(Fault): ...
class MissingVersionError(VersionError): ...      # No version provided
class InvalidVersionError(VersionError): ...       # Malformed version
class UnsupportedVersionError(VersionError): ...   # Not in supported list
class VersionSunsetError(VersionError): ...        # Version is sunset/retired
class VersionConflictError(VersionError): ...      # Ambiguous version
class VersionNegotiationError(VersionError): ...   # Negotiation failure
```
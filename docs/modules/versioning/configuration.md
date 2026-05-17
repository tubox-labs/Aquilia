# Versioning Configuration

## Configuration Entry Points

The implementation exposes the following configuration-like classes, policies, integrations, or dataclasses.

| Type | Source | Fields | Purpose |
| --- | --- | --- | --- |
| `ApiVersion` | `aquilia/versioning/core.py` | major: int, minor: int, patch: int, label: str, status: VersionStatus, channel: VersionChannel &#124; None, metadata: dict[str, Any] | Immutable API version value object. |
| `VersionNode` | `aquilia/versioning/graph.py` | version: ApiVersion, successor: ApiVersion &#124; None, predecessor: ApiVersion &#124; None, channels: set[VersionChannel], routes: set[str], controllers: set[str], deprecated_at: datetime &#124; None, sunset_at: datetime &#124; None, migration_url: str &#124; None | A node in the version graph. |
| `VersionConfig` | `aquilia/versioning/strategy.py` | strategy: str, versions: list[str], default_version: str &#124; None, require_version: bool, header_name: str, query_param: str, url_prefix: str, url_segment_index: int, strip_version_from_path: bool, media_type_param: str, channels: dict[str, str], channel_header: str, ... | Complete versioning configuration. |
| `SunsetPolicy` | `aquilia/versioning/sunset.py` | warn_header: bool, grace_period: timedelta, enforce_sunset: bool, enforce_retired: bool, sunset_message: str, migration_url_template: str &#124; None, gradual_rejection_percent: int | Global sunset policy configuration. |
| `SunsetEntry` | `aquilia/versioning/sunset.py` | version: ApiVersion, deprecated_at: datetime &#124; None, sunset_at: datetime &#124; None, retired_at: datetime &#124; None, successor: ApiVersion &#124; None, migration_url: str &#124; None, notes: str | Per-version sunset schedule entry. |

## Common Entry Points

- `VersioningIntegration`
- `VersionConfig`
- `SunsetPolicy`

## Precedence Model

Aquilia generally resolves configuration in this order:

1. Explicit constructor arguments or typed integration dataclass values.
2. `Workspace` builder methods and `Workspace.integrate(...)` output.
3. `ConfigLoader` defaults and environment overlays.
4. Runtime defaults inside the subsystem service or provider constructor.

When this module is registered through an `AppManifest`, keep component declarations inside `modules/<name>/manifest.py` and keep cross-cutting integration settings in `workspace.py`.

## Datatype Guidance

- Prefer typed dataclasses, policy objects, and config objects listed above when they exist.
- Keep secret values in environment-backed config, not literal strings in committed workspace files.
- Keep runtime-only state in services, stores, providers, or request state rather than static configuration.
- Use `to_dict()` on integration dataclasses when you need to inspect exactly what enters `ConfigLoader`.

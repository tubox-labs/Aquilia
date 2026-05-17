# Aquilary Registry Configuration

## Configuration Entry Points

The implementation exposes the following configuration-like classes, policies, integrations, or dataclasses.

| Type | Source | Fields | Purpose |
| --- | --- | --- | --- |
| `AppContext` | `aquilia/aquilary/core.py` | name: str, version: str, manifest: Any, config_namespace: dict[str, Any], route_prefix: str, controllers: list[str], services: list[str], models: list[str], middlewares: list[tuple[str, dict]], depends_on: list[str], on_startup: Callable &#124; None, on_shutdown: Callable &#124; None, ... | Runtime context for a loaded app. |
| `RegistryFingerprint` | `aquilia/aquilary/core.py` | hash: str, timestamp: str, mode: str, app_count: int, route_count: int, manifest_sources: list[str] | Immutable registry fingerprint for deployment gating. |
| `ErrorSpan` | `aquilia/aquilary/errors.py` | file: str, line: int &#124; None, column: int &#124; None, snippet: str &#124; None | File location for error context. |
| `ValidationReport` | `aquilia/aquilary/errors.py` | errors: list[RegistryError], warnings: list[str] | Aggregated validation report. |
| `GraphNode` | `aquilia/aquilary/graph.py` | name: str, dependencies: list[str], index: int &#124; None, lowlink: int &#124; None, on_stack: bool | Dependency graph node. |
| `ManifestSource` | `aquilia/aquilary/loader.py` | type: str, value: Any, origin: str | Manifest source descriptor. |
| `RouteInfo` | `aquilia/aquilary/route_compiler.py` | pattern: str, method: str, handler: Any, controller_class: type, flow: Any, metadata: dict[str, Any] | Information about a single route. |
| `RouteTable` | `aquilia/aquilary/route_compiler.py` | routes: list[RouteInfo], patterns: dict[str, RouteInfo], conflicts: list[tuple[RouteInfo, RouteInfo]] | Compiled routing table. |

## Common Entry Points

- No dedicated workspace integration was detected from module naming. Configure this module through direct constructors, manifests, or the subsystem that owns it.

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

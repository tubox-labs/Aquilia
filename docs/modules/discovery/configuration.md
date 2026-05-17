# Discovery Configuration

## Configuration Entry Points

The implementation exposes the following configuration-like classes, policies, integrations, or dataclasses.

| Type | Source | Fields | Purpose |
| --- | --- | --- | --- |
| `ClassifiedComponent` | `aquilia/discovery/engine.py` | name: str, kind: ComponentKind, file_path: Path, line: int, import_path: str, bases: list[str], decorators: list[str] | A component discovered by the AST classifier. |
| `DiscoveryResult` | `aquilia/discovery/engine.py` | module_name: str, components: list[ClassifiedComponent], errors: list[str], files_scanned: int | Result of scanning a single module. |
| `SyncAction` | `aquilia/discovery/engine.py` | action: str, component: ClassifiedComponent, field_name: str | Describes a change to make to a manifest file. |
| `SyncReport` | `aquilia/discovery/engine.py` | module_name: str, manifest_path: Path, actions: list[SyncAction], dry_run: bool | Report from a manifest sync operation. |

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

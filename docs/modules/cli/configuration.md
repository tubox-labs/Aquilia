# CLI Configuration

## Configuration Entry Points

The implementation exposes the following configuration-like classes, policies, integrations, or dataclasses.

| Type | Source | Fields | Purpose |
| --- | --- | --- | --- |
| `DiagnosticResult` | `aquilia/cli/commands/doctor.py` | category: str, label: str, passed: bool, detail: str | Structured diagnostic result. |
| `DiagnosticReport` | `aquilia/cli/commands/doctor.py` | results: list[DiagnosticResult], issues: list[str], warnings: list[str] | Complete diagnostic report. |
| `MigrationResult` | `aquilia/cli/commands/migrate.py` | changes: list[str] | Result of migration operation. |
| `ValidationResult` | `aquilia/cli/commands/validate.py` | is_valid: bool, module_count: int, route_count: int, provider_count: int, faults: list[str], warnings: list[str], fingerprint: str &#124; None | Result of manifest validation. |
| `ModuleManifest` | `aquilia/cli/parsers/module.py` | name: str, version: str, description: str, route_prefix: str, fault_domain: str, depends_on: list[str], providers: list[dict[str, Any]], routes: list[dict[str, Any]] | Parsed module manifest (module.aq). |
| `WorkspaceManifest` | `aquilia/cli/parsers/workspace.py` | name: str, version: str, description: str, modules: list[str], runtime: dict[str, Any], integrations: dict[str, Any] | Parsed workspace manifest (aquilia.aq). |

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

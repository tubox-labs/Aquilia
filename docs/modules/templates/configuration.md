# Templates Configuration

## Configuration Entry Points

The implementation exposes the following configuration-like classes, policies, integrations, or dataclasses.

| Type | Source | Fields | Purpose |
| --- | --- | --- | --- |
| `TemplateContext` | `aquilia/templates/context.py` | user_context: dict[str, Any], request: Optional['Request'], session: Optional['Session'], identity: Optional['Identity'], extras: dict[str, Any] | Template rendering context. |
| `TemplateLintIssue` | `aquilia/templates/manager.py` | template_name: str, severity: str, message: str, code: str, line: int &#124; None, column: int &#124; None, context: str &#124; None | Template lint issue. |
| `TemplateMetadata` | `aquilia/templates/manager.py` | name: str, path: str, module: str &#124; None, hash: str, size: int, mtime: float, compiled_at: str &#124; None | Template metadata for compilation. |
| `TemplateManifestConfig` | `aquilia/templates/manifest_integration.py` | See class attributes and constructor methods. | Configuration for templates from manifest file. |
| `SandboxPolicy` | `aquilia/templates/security.py` | allow_unsafe_filters: bool, allow_unsafe_tests: bool, allow_unsafe_globals: bool, allowed_filters: set[str], allowed_tests: set[str], allowed_globals: set[str], autoescape: bool, autoescape_extensions: list[str], max_recursion_depth: int | Template sandbox security policy. |

## Common Entry Points

- `TemplatesIntegration`
- `TemplateConfig`
- `SandboxPolicy`

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

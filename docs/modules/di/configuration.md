# Dependency Injection Configuration

## Configuration Entry Points

The implementation exposes the following configuration-like classes, policies, integrations, or dataclasses.

| Type | Source | Fields | Purpose |
| --- | --- | --- | --- |
| `ProviderMeta` | `aquilia/di/core.py` | name: str, token: str, scope: str, tags: tuple[str, ...], module: str, qualname: str, line: int &#124; None, version: str &#124; None, allow_lazy: bool | Compact, serializable provider metadata. |
| `Inject` | `aquilia/di/decorators.py` | token: type &#124; str &#124; None, tag: str &#124; None, optional: bool | Injection metadata marker. |
| `Dep` | `aquilia/di/dep.py` | call: Callable[..., Any] &#124; None, cached: bool, scope: str &#124; None, tag: str &#124; None, use_cache: bool | Dependency descriptor for Annotated[]-based injection. |
| `Header` | `aquilia/di/dep.py` | name: str, alias: str &#124; None, required: bool, default: Any | Extract a header value from the current request. |
| `Query` | `aquilia/di/dep.py` | name: str, default: Any, required: bool | Extract a query parameter from the current request. |
| `Body` | `aquilia/di/dep.py` | media_type: str, embed: bool | Mark a parameter as coming from the request body. |
| `LifecycleHook` | `aquilia/di/lifecycle.py` | name: str, callback: Callable[[], Coroutine[Any, Any, None]], priority: int, phase: str | Lifecycle hook registration. |
| `Scope` | `aquilia/di/scopes.py` | name: str, cacheable: bool, parent: str &#124; None | Scope metadata and rules. |

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

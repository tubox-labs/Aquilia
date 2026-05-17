# Extended Middleware Configuration

## Configuration Entry Points

The implementation exposes the following configuration-like classes, policies, integrations, or dataclasses.

| Type | Source | Fields | Purpose |
| --- | --- | --- | --- |
| `CSPPolicy` | `aquilia/middleware_ext/security.py` | See class attributes and constructor methods. | Builder for Content-Security-Policy directives. |

## Common Entry Points

- `MiddlewareChain`
- `MiddlewareEntry`
- `CorsIntegration`
- `CspIntegration`
- `RateLimitIntegration`
- `CsrfIntegration`

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

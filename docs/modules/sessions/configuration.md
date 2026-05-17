# Sessions Configuration

## Configuration Entry Points

The implementation exposes the following configuration-like classes, policies, integrations, or dataclasses.

| Type | Source | Fields | Purpose |
| --- | --- | --- | --- |
| `SessionPrincipal` | `aquilia/sessions/core.py` | kind: Literal['user', 'service', 'device', 'anonymous'], id: str, attributes: dict[str, Any] | Represents who the session belongs to. |
| `Session` | `aquilia/sessions/core.py` | id: SessionID, principal: SessionPrincipal &#124; None, data: dict[str, Any], created_at: datetime, last_accessed_at: datetime, expires_at: datetime &#124; None, scope: SessionScope, flags: set[SessionFlag], version: int | Core session object - explicit state container with lifecycle. |
| `PersistencePolicy` | `aquilia/sessions/policy.py` | enabled: bool, store_name: str, write_through: bool, compress: bool | Controls how sessions persist to storage. |
| `ConcurrencyPolicy` | `aquilia/sessions/policy.py` | max_sessions_per_principal: int &#124; None, behavior_on_limit: Literal['reject', 'evict_oldest', 'evict_all'] | Controls concurrent session limits per principal. |
| `TransportPolicy` | `aquilia/sessions/policy.py` | adapter: Literal['cookie', 'header', 'token'], cookie_name: str, cookie_httponly: bool, cookie_secure: bool, cookie_samesite: Literal['strict', 'lax', 'none'], cookie_path: str, cookie_domain: str &#124; None, header_name: str | Controls how sessions travel across network. |
| `SessionPolicy` | `aquilia/sessions/policy.py` | name: str, ttl: timedelta &#124; None, idle_timeout: timedelta &#124; None, absolute_timeout: timedelta &#124; None, rotate_on_use: bool, rotate_on_privilege_change: bool, fingerprint_binding: bool, persistence: PersistencePolicy, concurrency: ConcurrencyPolicy, transport: TransportPolicy, scope: str | Master policy that defines how sessions behave. |

## Common Entry Points

- `SessionPolicy`
- `PersistencePolicy`
- `TransportPolicy`
- `SessionIntegration`

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

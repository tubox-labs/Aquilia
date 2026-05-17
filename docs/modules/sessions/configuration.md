# Sessions Configuration

Session IDs, policies, stores, transports, engine, decorators, typed session state, and session faults.

This page distinguishes direct configuration APIs from indirect runtime wiring. All class names and source files below are extracted from the current source tree.

## Configuration Model

This module exposes config-oriented public classes. Use the table below to locate exact constructors and `to_dict()` behavior in `api-reference.md`.

## Source Inventory

| File | Lines | Public classes | Public functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/sessions/__init__.py` | 144 | 0 | 0 | AquilaSessions - Production-grade session management for Aquilia. |
| `aquilia/sessions/core.py` | 602 | 5 | 0 | AquilaSessions - Core types. |
| `aquilia/sessions/decorators.py` | 442 | 4 | 2 | Unique Session Decorators for Aquilia. |
| `aquilia/sessions/engine.py` | 407 | 1 | 0 | AquilaSessions - Session Engine. |
| `aquilia/sessions/faults.py` | 320 | 16 | 0 | AquilaSessions - Fault definitions. |
| `aquilia/sessions/policy.py` | 456 | 5 | 0 | AquilaSessions - Policy types. |
| `aquilia/sessions/state.py` | 189 | 4 | 0 | Typed Session State for Aquilia. |
| `aquilia/sessions/store.py` | 309 | 3 | 0 | AquilaSessions - Session storage abstraction. |
| `aquilia/sessions/transport.py` | 290 | 3 | 1 | AquilaSessions - Transport adapters. |

## Detected Config-Oriented Classes

| Class | Source | Methods | Summary |
| --- | --- | --- | --- |
| `SessionPolicyViolationFault` | `aquilia/sessions/faults.py` |  | Session violates policy constraints. |
| `PersistencePolicy` | `aquilia/sessions/policy.py` |  | Controls how sessions persist to storage. |
| `ConcurrencyPolicy` | `aquilia/sessions/policy.py` | `violated`, `should_reject`, `should_evict_oldest`, `should_evict_all` | Controls concurrent session limits per principal. |
| `TransportPolicy` | `aquilia/sessions/policy.py` |  | Controls how sessions travel across network. |
| `SessionPolicy` | `aquilia/sessions/policy.py` | `should_rotate`, `calculate_expiry`, `is_valid`, `should_persist`, `requires_store`, `from_dict`, `for_web_users`, `for_api_tokens`, `for_mobile_users`, `for_admin_users` | Master policy that defines how sessions behave. |
| `SessionPolicyBuilder` | `aquilia/sessions/policy.py` | `named`, `lasting`, `idle_timeout`, `no_idle_timeout`, `absolute_timeout`, `with_fingerprint_binding`, `rotating_on_auth`, `rotating_on_use`, `scoped_to`, `max_concurrent`, `unlimited_concurrent`, `with_smart_defaults`, `web_defaults`, `api_defaults`, `mobile_defaults`, `admin_defaults`, `build` | Fluent builder for SessionPolicy with unique Aquilia syntax. |

## Runtime Wiring Paths

- `workspace.py` defines workspace-level structure with `Workspace`, `Module`, and `Integration` builders.
- `modules/<name>/manifest.py` defines module internals with `AppManifest`.
- `ConfigLoader.get(...)` resolves dotted configuration paths at runtime.
- `AquiliaServer` consumes resolved config during middleware and subsystem setup.
- Subsystems with optional providers only require optional dependencies when their backend/provider is configured.

## Verification Checklist

1. Run `aq validate` to verify manifests.
2. Run `aq inspect config` to inspect resolved configuration.
3. Run `aq doctor` for workspace and integration diagnostics.
4. For server-only wiring, start via `aq run` and check startup logs plus `GET /_health`.

## Related Pages

- `api-reference.md` for exact class fields, methods, constants, and signatures.
- `integration-guide.md` for the workspace/manifest wiring pattern.
- `edge-cases-and-limitations.md` for fallback and compatibility behavior.

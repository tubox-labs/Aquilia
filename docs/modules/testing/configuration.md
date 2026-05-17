# Testing Configuration

Test client/server, test cases, fixtures, auth/cache/mail/fault/effect/DI test helpers, config overrides, and request factory utilities.

This page distinguishes direct configuration APIs from indirect runtime wiring. All class names and source files below are extracted from the current source tree.

## Configuration Model

This module exposes config-oriented public classes. Use the table below to locate exact constructors and `to_dict()` behavior in `api-reference.md`.

## Source Inventory

| File | Lines | Public classes | Public functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/testing/__init__.py` | 117 | 0 | 0 | Aquilia Testing Framework. |
| `aquilia/testing/assertions.py` | 442 | 1 | 0 | Aquilia Testing - Custom Assertion Helpers. |
| `aquilia/testing/auth.py` | 290 | 3 | 0 | Aquilia Testing - Auth & Identity Helpers. |
| `aquilia/testing/cache.py` | 221 | 2 | 0 | Aquilia Testing - Cache Testing Utilities. |
| `aquilia/testing/cases.py` | 274 | 4 | 0 | Aquilia Testing - Test Case Base Classes. |
| `aquilia/testing/client.py` | 606 | 3 | 0 | Aquilia Testing - HTTP & WebSocket Test Client. |
| `aquilia/testing/config.py` | 299 | 2 | 2 | Aquilia Testing - Config Override Utilities. |
| `aquilia/testing/di.py` | 290 | 1 | 4 | Aquilia Testing - DI Container Testing Utilities. |
| `aquilia/testing/effects.py` | 258 | 4 | 0 | Aquilia Testing - Effect System Testing Utilities. |
| `aquilia/testing/faults.py` | 167 | 2 | 0 | Aquilia Testing - Fault Testing Utilities. |
| `aquilia/testing/fixtures.py` | 212 | 0 | 14 | Aquilia Testing - Pytest Fixtures. |
| `aquilia/testing/mail.py` | 168 | 2 | 3 | Aquilia Testing - Mail Testing Utilities. |
| `aquilia/testing/server.py` | 267 | 1 | 1 | Aquilia Testing - TestServer Factory. |
| `aquilia/testing/utils.py` | 263 | 0 | 6 | Aquilia Testing - Request/Response Utility Factories. |

## Detected Config-Oriented Classes

| Class | Source | Methods | Summary |
| --- | --- | --- | --- |
| `IdentityBuilder` | `aquilia/testing/auth.py` | `with_roles`, `with_scopes`, `with_email`, `with_name`, `with_tenant`, `with_status`, `with_type`, `with_attr`, `as_service`, `as_suspended`, `create` | Fluent builder for constructing test identities. |
| `TestConfig` | `aquilia/testing/config.py` | `get`, `set`, `has`, `keys`, `config_data`, `to_dict`, `get_cache_config`, `get_session_config`, `get_auth_config`, `get_mail_config`, `get_template_config` | Lightweight config wrapper for test overrides. |
| `MockEffectProvider` | `aquilia/testing/effects.py` | `initialize`, `acquire`, `release`, `finalize`, `last_acquired_mode`, `reset` | Stub provider that returns configurable values. |

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

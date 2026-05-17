# Core Troubleshooting

Root framework runtime files: ASGI adapter, server, runtime bootstrap, config, pyconfig, request/response, middleware, lifecycle, signing, effects, dotenv, uploads, and data structures.

## Fast Diagnosis Flow

1. Confirm the command is run from a directory containing `workspace.py` unless it is help/version/init/doctor.
2. Run `aq doctor` for workspace, environment, registry, integration, and deployment checks.
3. Run `aq validate` to catch manifest errors.
4. Run `aq inspect config` to inspect resolved settings.
5. Run `aq inspect modules` and `aq inspect routes` when discovery or routing is suspect.
6. Check `api-reference.md` for exact public API signatures.

## Module-Relevant Commands

- `aq validate`
- `aq compile`
- `aq run`
- `aq serve`
- `aq freeze`
- `aq manifest update`
- `aq inspect routes`
- `aq inspect di`
- `aq inspect modules`
- `aq inspect faults`
- `aq inspect config`
- `aq doctor`

## Symptoms And Actions

| Symptom | Likely Source | Action |
| --- | --- | --- |
| Import error during startup | Bad manifest class path or optional provider dependency | Check `modules/<name>/manifest.py`, install the relevant extra, and rerun `aq validate`. |
| Route not found | Controller omitted from manifest, wrong route prefix, or startup conflict | Run `aq inspect routes`; inspect controller decorators and `Module.route_prefix()`. |
| Dependency not found | Service not registered or constructor annotation cannot be resolved | Check `AppManifest.services`, DI provider registrations, and `aq inspect di`. |
| Config value missing | Dotenv/env overlay not loaded or wrong nested key | Check `ConfigLoader` precedence and `AQ_` double-underscore key names. |
| Production security failure | Insecure secret or required key not configured | Set `AQ_SECRET_KEY`, `SECRET_KEY`, or Python-native secret config. |
| Optional subsystem unavailable | Provider/backend dependency or startup connection failed | Check startup logs; optional subsystems often log non-fatal failures. |

## Source Files To Inspect

| File | Lines | Public classes | Public functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/__init__.py` | 1581 | 0 | 0 | Aquilia - Production-ready async Python web framework |
| `aquilia/_datastructures.py` | 440 | 5 | 2 | Core data structures for Aquilia Request handling. |
| `aquilia/_uploads.py` | 431 | 4 | 2 | Upload file handling for Aquilia Request. |
| `aquilia/_version.py` | 26 | 0 | 0 | Single source of truth for the Aquilia framework version. |
| `aquilia/asgi.py` | 641 | 1 | 0 | ASGI adapter -- Bridges the ASGI protocol to Aquilia's request / response system. Supports HTTP, WebSocket, and Lifespan events. |
| `aquilia/config.py` | 969 | 4 | 0 | Config system - Layered typed configuration with validation. Supports dataclass/pydantic-like behavior with merge precedence. |
| `aquilia/config_builders.py` | 5650 | 6 | 0 | Fluent Configuration Builders for Aquilia. |
| `aquilia/dotenv.py` | 898 | 2 | 6 | Aquilia Native Dotenv Loader (``aquilia.dotenv``) ================================================= |
| `aquilia/effects.py` | 794 | 21 | 0 | Effect System -- Typed Capabilities with Providers and Layers. |
| `aquilia/engine.py` | 295 | 3 | 1 | Engine -- Core runtime primitives for the Aquilia request lifecycle. |
| `aquilia/entrypoint.py` | 206 | 0 | 1 | Aquilia ASGI Entrypoint — Zero-Config Production Application Factory. |
| `aquilia/flow.py` | 1622 | 10 | 8 | Aquilia Flow -- Typed Pipeline System with Effect Integration. |
| `aquilia/health.py` | 162 | 3 | 0 | Health Registry -- Centralized subsystem health tracking. |
| `aquilia/lifecycle.py` | 363 | 5 | 1 | Lifecycle Coordinator - Orchestrates startup and shutdown hooks. |
| `aquilia/manifest.py` | 663 | 14 | 0 | AppManifest - Production-grade, data-driven application manifest system. |
| `aquilia/middleware.py` | 648 | 8 | 0 | Middleware system - Composable, async-first middleware with effect awareness. |
| `aquilia/pyconfig.py` | 1644 | 4 | 2 | Aquilia Python-Native Configuration System  (``aquilia.pyconfig``) ================================================================== |
| `aquilia/request.py` | 1998 | 11 | 0 | Request - Production-grade ASGI request wrapper. |
| `aquilia/response.py` | 2037 | 14 | 14 | Response - Production-grade HTTP response builder with streaming support. |
| `aquilia/runtime.py` | 721 | 3 | 0 | AquiliaRuntime — Structured ASGI Bootstrap Lifecycle Manager. |
| `aquilia/server.py` | 4001 | 1 | 0 | AquiliaServer - Main server orchestrating all components with lifecycle management. |
| `aquilia/signing.py` | 1532 | 13 | 9 | Aquilia Signing Engine  (``aquilia.signing``) ============================================= |

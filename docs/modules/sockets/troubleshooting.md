# Sockets Troubleshooting

WebSocket decorators, controllers, runtime, connection state, guards, middleware, message envelopes, compile metadata, and in-memory/Redis adapters.

## Fast Diagnosis Flow

1. Confirm the command is run from a directory containing `workspace.py` unless it is help/version/init/doctor.
2. Run `aq doctor` for workspace, environment, registry, integration, and deployment checks.
3. Run `aq validate` to catch manifest errors.
4. Run `aq inspect config` to inspect resolved settings.
5. Run `aq inspect modules` and `aq inspect routes` when discovery or routing is suspect.
6. Check `api-reference.md` for exact public API signatures.

## Module-Relevant Commands

- `aq ws inspect`
- `aq ws broadcast`
- `aq ws gen-client`
- `aq ws purge-room`
- `aq ws kick`

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
| `aquilia/sockets/__init__.py` | 131 | 0 | 0 | AquilaSockets - WebSocket subsystem for Aquilia |
| `aquilia/sockets/adapters/__init__.py` | 14 | 0 | 0 | Adapters Package - WebSocket scaling adapters |
| `aquilia/sockets/adapters/base.py` | 203 | 2 | 0 | Adapter Base - Protocol for WebSocket scaling adapters |
| `aquilia/sockets/adapters/inmemory.py` | 227 | 1 | 0 | In-Memory Adapter - Single-process WebSocket adapter |
| `aquilia/sockets/adapters/redis.py` | 338 | 1 | 0 | Redis Adapter - Production-ready WebSocket adapter using Redis |
| `aquilia/sockets/compile.py` | 280 | 3 | 1 | WebSocket Compiler - Compile-time metadata extraction |
| `aquilia/sockets/connection.py` | 344 | 3 | 0 | Connection - WebSocket connection abstraction with DI scope |
| `aquilia/sockets/controller.py` | 211 | 1 | 0 | Socket Controller - Base class for WebSocket controllers |
| `aquilia/sockets/decorators.py` | 303 | 8 | 0 | Socket Controller Decorators - Declarative WebSocket controller syntax |
| `aquilia/sockets/envelope.py` | 274 | 8 | 0 | Message Envelope - Typed message protocol for WebSocket communication |
| `aquilia/sockets/faults.py` | 200 | 1 | 17 | WebSocket Faults - Structured error handling for WebSocket operations |
| `aquilia/sockets/guards.py` | 272 | 5 | 0 | WebSocket Guards - Security and validation guards |
| `aquilia/sockets/middleware.py` | 234 | 5 | 0 | WebSocket Middleware - Per-message processing pipeline |
| `aquilia/sockets/runtime.py` | 656 | 3 | 0 | WebSocket Runtime - ASGI integration and connection management |

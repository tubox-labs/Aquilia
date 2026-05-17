# Di Troubleshooting

Scoped dependency injection container, providers, request DAG, decorators, lifecycle disposal, diagnostics, scopes, and testing utilities.

## Fast Diagnosis Flow

1. Confirm the command is run from a directory containing `workspace.py` unless it is help/version/init/doctor.
2. Run `aq doctor` for workspace, environment, registry, integration, and deployment checks.
3. Run `aq validate` to catch manifest errors.
4. Run `aq inspect config` to inspect resolved settings.
5. Run `aq inspect modules` and `aq inspect routes` when discovery or routing is suspect.
6. Check `api-reference.md` for exact public API signatures.

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
| `aquilia/di/__init__.py` | 132 | 0 | 0 | Aquilia Dependency Injection System |
| `aquilia/di/cli.py` | 479 | 0 | 7 | CLI commands for DI system. |
| `aquilia/di/compat.py` | 105 | 1 | 3 | Compatibility layer with legacy Aquilia DI system. |
| `aquilia/di/core.py` | 1034 | 5 | 0 | Core DI types and protocols. |
| `aquilia/di/decorators.py` | 242 | 1 | 5 | Decorators and injection helpers for ergonomic DI usage. |
| `aquilia/di/dep.py` | 398 | 4 | 0 | Dep -- Composable dependency descriptor for annotation-driven DI. |
| `aquilia/di/diagnostics.py` | 122 | 5 | 0 | DI Diagnostics - Observability and event tracking for DI containers. |
| `aquilia/di/errors.py` | 239 | 9 | 0 | DI-specific error types with rich diagnostics. |
| `aquilia/di/graph.py` | 261 | 1 | 0 | Graph analysis and cycle detection for DI system. |
| `aquilia/di/lifecycle.py` | 241 | 4 | 0 | Lifecycle management for providers and containers. |
| `aquilia/di/providers.py` | 822 | 8 | 0 | Provider implementations for different instantiation strategies. |
| `aquilia/di/request_dag.py` | 431 | 1 | 0 | RequestDAG -- Per-request dependency graph resolver. |
| `aquilia/di/scopes.py` | 99 | 3 | 0 | Scope definitions and validation. |
| `aquilia/di/testing.py` | 195 | 2 | 1 | Testing utilities for DI system. |

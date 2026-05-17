# Versioning Troubleshooting

API version parsing, resolvers, decorators, negotiation, graph, sunset policy/enforcement, middleware, and route registration integration.

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
| `aquilia/versioning/__init__.py` | 181 | 0 | 0 | Aquilia Versioning System — Epoch-Based API Versioning |
| `aquilia/versioning/core.py` | 290 | 3 | 0 | Aquilia Versioning — Core Types |
| `aquilia/versioning/decorators.py` | 138 | 0 | 3 | Aquilia Versioning — Route-Level Decorators |
| `aquilia/versioning/errors.py` | 144 | 6 | 0 | Aquilia Versioning — Version Errors |
| `aquilia/versioning/graph.py` | 261 | 2 | 0 | Aquilia Versioning — Version Graph |
| `aquilia/versioning/middleware.py` | 223 | 1 | 0 | Aquilia Versioning — Version Middleware |
| `aquilia/versioning/negotiation.py` | 193 | 2 | 0 | Aquilia Versioning — Version Negotiation |
| `aquilia/versioning/parser.py` | 137 | 2 | 0 | Aquilia Versioning — Version Parser |
| `aquilia/versioning/resolvers.py` | 486 | 8 | 0 | Aquilia Versioning — Version Resolvers |
| `aquilia/versioning/strategy.py` | 500 | 2 | 0 | Aquilia Versioning — Version Strategy |
| `aquilia/versioning/sunset.py` | 291 | 4 | 0 | Aquilia Versioning — Sunset Lifecycle |

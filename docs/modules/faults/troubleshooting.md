# Faults Troubleshooting

Structured fault taxonomy, domains, handlers, middleware, response mapping, and subsystem patch integrations.

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
| `aquilia/faults/__init__.py` | 292 | 0 | 0 | AquilaFaults - Production-grade fault handling system. |
| `aquilia/faults/core.py` | 490 | 8 | 0 | AquilaFaults - Core types and fault taxonomy. |
| `aquilia/faults/default_handlers.py` | 535 | 8 | 0 | AquilaFaults - Default Handlers. |
| `aquilia/faults/domains.py` | 1540 | 92 | 1 | AquilaFaults - Domain-specific fault types. |
| `aquilia/faults/engine.py` | 499 | 2 | 2 | AquilaFaults - Fault Engine. |
| `aquilia/faults/handlers.py` | 193 | 3 | 0 | AquilaFaults - Fault handlers. |
| `aquilia/faults/integrations/__init__.py` | 130 | 0 | 2 | AquilaFaults - Subsystem Integrations. |
| `aquilia/faults/integrations/di.py` | 185 | 3 | 2 | AquilaFaults - DI Integration. |
| `aquilia/faults/integrations/flow.py` | 355 | 3 | 7 | AquilaFaults - Flow Engine Integration. |
| `aquilia/faults/integrations/models.py` | 223 | 1 | 4 | AquilaFaults - Model/Database Integration. |
| `aquilia/faults/integrations/registry.py` | 148 | 4 | 2 | AquilaFaults - Registry Integration. |
| `aquilia/faults/integrations/routing.py` | 211 | 3 | 3 | AquilaFaults - Routing Integration. |

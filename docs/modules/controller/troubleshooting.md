# Controller Troubleshooting

Controller base class, route decorators, compiler, router, execution engine, renderers, filters, pagination, and OpenAPI generation.

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
| `aquilia/controller/__init__.py` | 169 | 0 | 0 | Aquilia Controller System |
| `aquilia/controller/base.py` | 650 | 5 | 0 | Controller Base Class |
| `aquilia/controller/compiler.py` | 381 | 3 | 0 | Controller Compiler - Compiles controllers to patterns and routes. |
| `aquilia/controller/decorators.py` | 739 | 10 | 1 | Controller Method Decorators |
| `aquilia/controller/engine.py` | 1386 | 1 | 0 | Controller Engine - Executes controller methods with full integration. |
| `aquilia/controller/factory.py` | 403 | 3 | 0 | Controller Factory |
| `aquilia/controller/filters.py` | 766 | 5 | 5 | Aquilia Filter System -- declarative filtering, searching, and ordering. |
| `aquilia/controller/metadata.py` | 461 | 3 | 1 | Controller Metadata Extraction |
| `aquilia/controller/openapi.py` | 1089 | 3 | 2 | OpenAPI 3.1.0 Generation for Aquilia Controllers. |
| `aquilia/controller/pagination.py` | 724 | 5 | 0 | Aquilia Pagination System -- declarative pagination backends. |
| `aquilia/controller/renderers.py` | 453 | 8 | 1 | Aquilia Content Negotiation & Renderer System. |
| `aquilia/controller/router.py` | 592 | 2 | 0 | Controller Router - Pattern-based router for controllers. |

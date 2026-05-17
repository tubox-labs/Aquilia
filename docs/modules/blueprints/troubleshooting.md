# Blueprints Troubleshooting

Model-to-world contracts for request validation, response rendering, schema generation, facets, projections, and lenses.

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
| `aquilia/blueprints/__init__.py` | 162 | 0 | 0 | Aquilia Blueprints -- first-class model↔world contracts. |
| `aquilia/blueprints/annotations.py` | 1117 | 3 | 2 | Aquilia Blueprint Annotations -- type-annotation–driven schema declaration. |
| `aquilia/blueprints/core.py` | 1194 | 2 | 0 | Aquilia Blueprint Core -- the Blueprint metaclass and base class. |
| `aquilia/blueprints/exceptions.py` | 150 | 7 | 0 | Aquilia Blueprint Exceptions -- Fault-domain-integrated error hierarchy. |
| `aquilia/blueprints/facets.py` | 1397 | 27 | 1 | Aquilia Blueprint Facets -- the field-level primitives of a Blueprint. |
| `aquilia/blueprints/integration.py` | 293 | 0 | 5 | Aquilia Blueprint Integration -- hooks into Controller, DI, Request/Response. |
| `aquilia/blueprints/lenses.py` | 201 | 1 | 0 | Aquilia Blueprint Lenses -- depth-controlled relational views. |
| `aquilia/blueprints/projections.py` | 146 | 1 | 0 | Aquilia Blueprint Projections -- named, reusable field subsets. |
| `aquilia/blueprints/schema.py` | 68 | 0 | 2 | Aquilia Blueprint Schema -- OpenAPI/JSON Schema generation. |

# Aquilary Troubleshooting

Manifest registry, validation, dependency graph, route table compilation metadata, fingerprinting, and runtime registry construction.

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
| `aquilia/aquilary/__init__.py` | 78 | 0 | 0 | Aquilary - Manifest-driven App Registry for Aquilia |
| `aquilia/aquilary/cli.py` | 501 | 0 | 7 | Aquilary CLI commands for manifest validation, inspection, and deployment. |
| `aquilia/aquilary/core.py` | 1498 | 6 | 0 | Core Aquilary types and main registry class. |
| `aquilia/aquilary/errors.py` | 448 | 11 | 0 | Aquilary registry error types with rich diagnostics. |
| `aquilia/aquilary/fingerprint.py` | 424 | 1 | 0 | Fingerprint generator for reproducible deployments. |
| `aquilia/aquilary/graph.py` | 334 | 2 | 0 | Dependency graph analysis with Tarjan's algorithm for cycle detection. |
| `aquilia/aquilary/handler_wrapper.py` | 204 | 2 | 2 | Handler wrapper for dependency injection into controller methods. |
| `aquilia/aquilary/loader.py` | 487 | 2 | 0 | Safe manifest loader with no import-time side effects. |
| `aquilia/aquilary/route_compiler.py` | 249 | 4 | 0 | Route Compiler - Extracts routes from controllers and compiles route table. |
| `aquilia/aquilary/validator.py` | 453 | 1 | 0 | Registry validator for manifests and configuration. |

# Artifacts Troubleshooting

Typed artifact envelopes, artifact kinds, integrity metadata, readers, builders, and memory/filesystem stores.

## Fast Diagnosis Flow

1. Confirm the command is run from a directory containing `workspace.py` unless it is help/version/init/doctor.
2. Run `aq doctor` for workspace, environment, registry, integration, and deployment checks.
3. Run `aq validate` to catch manifest errors.
4. Run `aq inspect config` to inspect resolved settings.
5. Run `aq inspect modules` and `aq inspect routes` when discovery or routing is suspect.
6. Check `api-reference.md` for exact public API signatures.

## Module-Relevant Commands

- `aq artifact list`
- `aq artifact inspect`
- `aq artifact verify`
- `aq artifact verify-all`
- `aq artifact gc`
- `aq artifact export`
- `aq artifact diff`
- `aq artifact history`
- `aq artifact import`
- `aq artifact count`
- `aq artifact stats`

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
| `aquilia/artifacts/__init__.py` | 91 | 0 | 0 | Aquilia Artifacts -- Unified artifact system for the framework. |
| `aquilia/artifacts/builder.py` | 240 | 1 | 0 | Artifact Builder -- fluent API for constructing artifacts. |
| `aquilia/artifacts/core.py` | 416 | 5 | 1 | Artifact Core -- the foundational types for Aquilia's artifact system. |
| `aquilia/artifacts/kinds.py` | 413 | 9 | 0 | Typed Artifact Kinds -- convenience subclasses with kind-specific helpers. |
| `aquilia/artifacts/reader.py` | 250 | 1 | 0 | Artifact Reader -- load, inspect, verify, and query artifacts. |
| `aquilia/artifacts/store.py` | 449 | 3 | 1 | Artifact Store -- pluggable storage backends for artifacts. |

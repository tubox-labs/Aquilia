# Providers Troubleshooting

Cloud provider clients and deployment tooling, currently focused on the Render provider and encrypted credential store.

## Fast Diagnosis Flow

1. Confirm the command is run from a directory containing `workspace.py` unless it is help/version/init/doctor.
2. Run `aq doctor` for workspace, environment, registry, integration, and deployment checks.
3. Run `aq validate` to catch manifest errors.
4. Run `aq inspect config` to inspect resolved settings.
5. Run `aq inspect modules` and `aq inspect routes` when discovery or routing is suspect.
6. Check `api-reference.md` for exact public API signatures.

## Module-Relevant Commands

- `aq deploy dockerfile`
- `aq deploy compose`
- `aq deploy kubernetes`
- `aq deploy nginx`
- `aq deploy ci`
- `aq deploy monitoring`
- `aq deploy env`
- `aq deploy all`
- `aq deploy makefile`
- `aq deploy render`
- `aq provider render env list`
- `aq provider render env set`
- `aq provider render env delete`
- `aq provider login`
- `aq provider logout`
- `aq provider status`

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
| `aquilia/providers/__init__.py` | 21 | 0 | 0 | Aquilia Cloud Providers — Pluggable PaaS/IaaS Deployment Backends. |
| `aquilia/providers/render/__init__.py` | 153 | 0 | 0 | Aquilia Render Provider — Comprehensive PaaS Deployment v2. |
| `aquilia/providers/render/client.py` | 1406 | 1 | 0 | Render REST API Client — Comprehensive v2. |
| `aquilia/providers/render/deployer.py` | 661 | 2 | 0 | Render Deployment Orchestrator — Enhanced v2. |
| `aquilia/providers/render/store.py` | 752 | 1 | 0 | Render Credential Store — Military-Grade Encrypted Token Persistence. |
| `aquilia/providers/render/types.py` | 993 | 53 | 0 | Render API Type Definitions — Comprehensive v2. |
| `aquilia/providers/render_backup_phase10/__init__.py` | 53 | 0 | 0 | Aquilia Render Provider — One-command PaaS deployment. |
| `aquilia/providers/render_backup_phase10/client.py` | 571 | 1 | 0 | Render REST API Client. |
| `aquilia/providers/render_backup_phase10/deployer.py` | 544 | 2 | 0 | Render Deployment Orchestrator. |
| `aquilia/providers/render_backup_phase10/store.py` | 344 | 1 | 0 | Render Credential Store — Crous-Encrypted Token Persistence. |
| `aquilia/providers/render_backup_phase10/types.py` | 384 | 11 | 0 | Render API Type Definitions. |

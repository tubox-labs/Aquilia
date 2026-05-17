# Cli Troubleshooting

The `aq` command line interface, workspace/module generators, deployment generators, diagnostics, validation, inspection, and subsystem commands.

## Fast Diagnosis Flow

1. Confirm the command is run from a directory containing `workspace.py` unless it is help/version/init/doctor.
2. Run `aq doctor` for workspace, environment, registry, integration, and deployment checks.
3. Run `aq validate` to catch manifest errors.
4. Run `aq inspect config` to inspect resolved settings.
5. Run `aq inspect modules` and `aq inspect routes` when discovery or routing is suspect.
6. Check `api-reference.md` for exact public API signatures.

## Module-Relevant Commands

- `aq init workspace`
- `aq add module`
- `aq generate controller`
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
- `aq migrate`
- `aq doctor`
- `aq ws inspect`
- `aq ws broadcast`
- `aq ws gen-client`
- `aq ws purge-room`

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
| `aquilia/cli/__init__.py` | 36 | 0 | 1 | Aquilate - Aquilia Native CLI System. |
| `aquilia/cli/__main__.py` | 3865 | 1 | 66 | Aquilate CLI - Main Entry Point. |
| `aquilia/cli/commands/__init__.py` | 49 | 0 | 0 | Command implementations package. |
| `aquilia/cli/commands/add.py` | 189 | 0 | 1 | Add module to workspace command. |
| `aquilia/cli/commands/analytics.py` | 299 | 1 | 1 | Advanced module discovery analytics and reporting. Provides deep insights into module relationships, health metrics, and optimization suggestions. |
| `aquilia/cli/commands/artifacts.py` | 443 | 0 | 12 | Artifact CLI commands -- ``aq artifact list``, ``aq artifact inspect``, ``aq artifact gc``, ``aq artifact export``, ``aq artifact verify``. |
| `aquilia/cli/commands/cache.py` | 193 | 0 | 4 | AquilaCache CLI commands -- ``aq cache`` group. |
| `aquilia/cli/commands/compile.py` | 52 | 0 | 1 | Manifest compilation command. |
| `aquilia/cli/commands/deploy_gen.py` | 2168 | 0 | 12 | Deploy CLI commands -- ``aq deploy`` group. |
| `aquilia/cli/commands/discover.py` | 258 | 1 | 1 | CLI command for module discovery inspection, validation, and auto-sync. |
| `aquilia/cli/commands/doctor.py` | 580 | 2 | 1 | Workspace diagnostics command -- ``aq doctor``. |
| `aquilia/cli/commands/freeze.py` | 82 | 0 | 1 | Artifact freezing command. |
| `aquilia/cli/commands/i18n.py` | 532 | 0 | 6 | AquilaI18n CLI commands — ``aq i18n`` group. |
| `aquilia/cli/commands/init.py` | 95 | 0 | 1 | Workspace and module initialization commands. |
| `aquilia/cli/commands/inspect.py` | 419 | 0 | 5 | Artifact inspection commands -- live workspace introspection. |
| `aquilia/cli/commands/mail.py` | 173 | 0 | 3 | AquilaMail CLI commands -- ``aq mail`` group. |
| `aquilia/cli/commands/manifest.py` | 367 | 0 | 1 | Manifest management commands. |
| `aquilia/cli/commands/migrate.py` | 160 | 1 | 1 | Legacy project migration command. |
| `aquilia/cli/commands/mlops_cmds.py` | 807 | 0 | 32 | MLOps CLI commands -- ``aq pack``, ``aq model``, ``aq deploy``, ``aq observe``, ``aq rollout``, ``aq export``, ``aq plugin``, ``aq lineage``, ``aq experiment``. |
| `aquilia/cli/commands/model_cmds.py` | 1038 | 0 | 8 | Model CLI Commands -- aq db makemigrations, aq db migrate, aq db dump, aq db shell. |
| `aquilia/cli/commands/provider.py` | 528 | 0 | 9 | Provider CLI commands — ``aq provider``. |
| `aquilia/cli/commands/run.py` | 1094 | 0 | 1 | Development server command. |
| `aquilia/cli/commands/serve.py` | 201 | 0 | 1 | Production server command. |
| `aquilia/cli/commands/test.py` | 147 | 0 | 1 | Aquilia CLI - ``aq test`` command. |
| `aquilia/cli/commands/validate.py` | 317 | 1 | 1 | Manifest validation command. |
| `aquilia/cli/commands/ws.py` | 489 | 0 | 6 | WebSocket CLI Commands - Admin tools for WebSocket management |
| `aquilia/cli/compilers/__init__.py` | 7 | 0 | 0 | Artifact compilers. |
| `aquilia/cli/compilers/workspace.py` | 369 | 1 | 0 | Workspace compiler - converts manifests to artifacts. |
| `aquilia/cli/discovery_cli.py` | 151 | 1 | 1 | Aquilia CLI integration for enhanced auto-discovery commands. Provides convenient shortcuts for module discovery, inspection, and analytics. |
| `aquilia/cli/discovery_utils.py` | 816 | 2 | 0 | Enhanced discovery utilities for Aquilia CLI. |
| `aquilia/cli/generators/__init__.py` | 34 | 0 | 0 | Code generators for workspace and modules. |
| `aquilia/cli/generators/controller.py` | 206 | 0 | 1 | Controller generator - creates modern controller templates. |
| `aquilia/cli/generators/deployment.py` | 3122 | 10 | 0 | Aquilia Deployment Generators -- Production-ready Docker, Compose, Kubernetes, Nginx, CI/CD, and monitoring file generators. |
| `aquilia/cli/generators/module.py` | 753 | 1 | 0 | Module generator. |
| `aquilia/cli/generators/workspace.py` | 1749 | 1 | 0 | Workspace generator. |
| `aquilia/cli/parsers/__init__.py` | 9 | 0 | 0 | Manifest parsers. |
| `aquilia/cli/parsers/module.py` | 43 | 1 | 0 | Module manifest parser. |
| `aquilia/cli/parsers/workspace.py` | 65 | 1 | 0 | Workspace manifest parser. |
| `aquilia/cli/utils/__init__.py` | 29 | 0 | 0 | Aquilia CLI -- UI utilities (re-exports from colors module). |
| `aquilia/cli/utils/colors.py` | 557 | 0 | 26 | Aquilia CLI -- UI toolkit. |
| `aquilia/cli/utils/prompts.py` | 637 | 0 | 8 | Aquilia CLI -- Interactive prompt toolkit. |
| `aquilia/cli/utils/workspace.py` | 56 | 0 | 3 | Utility functions for finding and loading workspace configuration. |

# Cli Configuration

The `aq` command line interface, workspace/module generators, deployment generators, diagnostics, validation, inspection, and subsystem commands.

This page distinguishes direct configuration APIs from indirect runtime wiring. All class names and source files below are extracted from the current source tree.

## Configuration Model

No public config-specific class was detected in this module. It is configured through workspace/module declarations, related integration objects, or direct Python APIs.

## Source Inventory

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

## Runtime Wiring Paths

- `workspace.py` defines workspace-level structure with `Workspace`, `Module`, and `Integration` builders.
- `modules/<name>/manifest.py` defines module internals with `AppManifest`.
- `ConfigLoader.get(...)` resolves dotted configuration paths at runtime.
- `AquiliaServer` consumes resolved config during middleware and subsystem setup.
- Subsystems with optional providers only require optional dependencies when their backend/provider is configured.

## Verification Checklist

1. Run `aq validate` to verify manifests.
2. Run `aq inspect config` to inspect resolved configuration.
3. Run `aq doctor` for workspace and integration diagnostics.
4. For server-only wiring, start via `aq run` and check startup logs plus `GET /_health`.

## Related Pages

- `api-reference.md` for exact class fields, methods, constants, and signatures.
- `integration-guide.md` for the workspace/manifest wiring pattern.
- `edge-cases-and-limitations.md` for fallback and compatibility behavior.

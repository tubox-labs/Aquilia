# cli Module

## Purpose

Aquilia native command line tooling. Use this module for workspace generation, module generation, discovery, compilation, inspection, migrations, model commands, providers, deployment manifests, i18n, tests, and server startup.

## Source Coverage

- Python files: 42
- Public classes: 25
- Dataclasses: 6
- Enums: 0
- Public functions: 216

## How It Fits In Aquilia

1. Import the package from `aquilia.cli` or its concrete submodules.
2. Configure it through workspace integrations, manifests, or direct service construction depending on the subsystem.
3. Keep business logic outside transport and framework glue so the subsystem stays testable.

## Practical Guidance

- Prefer typed configuration objects and framework helpers over ad hoc dictionaries when they exist.
- Use the tests in `tests/` as behavioral examples when changing this subsystem.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `AquiliaGroup` | `aquilia/cli/__main__.py` | Click group subclass with branded help output. |
| `DiscoveryCLI` | `aquilia/cli/discovery_cli.py` | CLI interface for discovery operations. |
| `TypeClassifier` | `aquilia/cli/discovery_utils.py` | Classifies discovered classes as controllers, services, or other. |
| `EnhancedDiscovery` | `aquilia/cli/discovery_utils.py` | Enhanced discovery with intelligent classification and filtering. |
| `ModuleManifest` | `aquilia/cli/parsers/module.py` | Parsed module manifest (module.aq). |
| `WorkspaceManifest` | `aquilia/cli/parsers/workspace.py` | Parsed workspace manifest (aquilia.aq). |
| `DiscoveryAnalytics` | `aquilia/cli/commands/analytics.py` | Analyze discovered modules and provide insights. |
| `DiscoveryInspector` | `aquilia/cli/commands/discover.py` | Inspect, validate, and auto-sync discovered modules. |
| `DiagnosticResult` | `aquilia/cli/commands/doctor.py` | Structured diagnostic result. |
| `DiagnosticReport` | `aquilia/cli/commands/doctor.py` | Complete diagnostic report. |
| `MigrationResult` | `aquilia/cli/commands/migrate.py` | Result of migration operation. |
| `ValidationResult` | `aquilia/cli/commands/validate.py` | Result of manifest validation. |
| `WorkspaceIntrospector` | `aquilia/cli/generators/deployment.py` | Introspects an Aquilia workspace to discover configuration needed |
| `DockerfileGenerator` | `aquilia/cli/generators/deployment.py` | Generates production-ready, multi-stage Dockerfile for Aquilia workspaces. |
| `ComposeGenerator` | `aquilia/cli/generators/deployment.py` | Generates production-ready docker-compose.yml for Aquilia workspaces. |
| `KubernetesGenerator` | `aquilia/cli/generators/deployment.py` | Generates production-ready Kubernetes manifests for Aquilia workspaces. |
| `NginxGenerator` | `aquilia/cli/generators/deployment.py` | Generate production-ready Nginx configuration for Aquilia. |
| `CIGenerator` | `aquilia/cli/generators/deployment.py` | Generate CI/CD pipelines (GitHub Actions, GitLab CI). |
| `PrometheusGenerator` | `aquilia/cli/generators/deployment.py` | Generate Prometheus configuration. |
| `GrafanaGenerator` | `aquilia/cli/generators/deployment.py` | Generate Grafana provisioning configuration. |
| `EnvGenerator` | `aquilia/cli/generators/deployment.py` | Generate .env templates for local and production. |
| `MakefileGenerator` | `aquilia/cli/generators/deployment.py` | Generate a production-ready Makefile for Aquilia workspaces. |
| `ModuleGenerator` | `aquilia/cli/generators/module.py` | Generate Aquilia module structure. |
| `WorkspaceGenerator` | `aquilia/cli/generators/workspace.py` | Generate Aquilia workspace structure. |
| `WorkspaceCompiler` | `aquilia/cli/compilers/workspace.py` | Compile workspace manifests to artifacts via the unified artifact system. |

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| `main` | `aquilia/cli/__init__.py` | Wrapper to avoid eager import of __main__ which causes warnings with -m. |
| `cli` | `aquilia/cli/__main__.py` | Manifest-driven, artifact-first project orchestration. |
| `init` | `aquilia/cli/__main__.py` | Initialize new workspace or module. |
| `init_workspace` | `aquilia/cli/__main__.py` | Create a new Aquilia workspace. |
| `add` | `aquilia/cli/__main__.py` | Add module to workspace. |
| `add_module` | `aquilia/cli/__main__.py` | Add a new module to the workspace. |
| `generate` | `aquilia/cli/__main__.py` | Generate code from templates. |
| `generate_controller` | `aquilia/cli/__main__.py` | Generate a new controller. |
| `validate` | `aquilia/cli/__main__.py` | Validate workspace manifests. |
| `compile` | `aquilia/cli/__main__.py` | Compile manifests to artifacts. |
| `run` | `aquilia/cli/__main__.py` | Start development server. |
| `serve` | `aquilia/cli/__main__.py` | Start production server. |
| `freeze` | `aquilia/cli/__main__.py` | Freeze generated artifacts for production integrity checks. |
| `manifest` | `aquilia/cli/__main__.py` | Manage module manifests. |
| `manifest_update` | `aquilia/cli/__main__.py` | Update manifest with auto-discovered resources. |
| `inspect` | `aquilia/cli/__main__.py` | Inspect compiled artifacts. |
| `inspect_routes` | `aquilia/cli/__main__.py` | Show compiled routes. |
| `inspect_di` | `aquilia/cli/__main__.py` | Show DI graph. |
| `inspect_modules` | `aquilia/cli/__main__.py` | List all modules. |
| `inspect_faults` | `aquilia/cli/__main__.py` | Show fault domains. |
| `inspect_config` | `aquilia/cli/__main__.py` | Show resolved configuration. |
| `migrate` | `aquilia/cli/__main__.py` | Migrate from legacy layout. |
| `doctor` | `aquilia/cli/__main__.py` | Diagnose workspace issues. |
| `ws` | `aquilia/cli/__main__.py` | WebSocket management commands. |
| `ws_inspect` | `aquilia/cli/__main__.py` | Inspect compiled WebSocket namespaces. |
| `ws_broadcast` | `aquilia/cli/__main__.py` | Broadcast message to namespace or room. |
| `ws_gen_client` | `aquilia/cli/__main__.py` | Generate TypeScript client SDK from compiled WebSocket artifacts. |
| `ws_purge_room` | `aquilia/cli/__main__.py` | Purge a room's state from the adapter. |
| `ws_kick` | `aquilia/cli/__main__.py` | Kick (disconnect) a WebSocket connection. |
| `discover` | `aquilia/cli/__main__.py` | Inspect auto-discovered modules in workspace. |
| `analytics` | `aquilia/cli/__main__.py` | Run discovery analytics and show health report. |
| `mail` | `aquilia/cli/__main__.py` | AquilaMail -- test, inspect, and validate mail configuration. |
| `mail_check` | `aquilia/cli/__main__.py` | Validate mail configuration and report issues. |
| `mail_send_test` | `aquilia/cli/__main__.py` | Send a test email to verify mail provider configuration. |
| `mail_inspect` | `aquilia/cli/__main__.py` | Display current mail configuration as JSON. |
| `cache` | `aquilia/cli/__main__.py` | AquilaCache -- check, inspect, clear, and view cache stats. |
| `cache_check` | `aquilia/cli/__main__.py` | Validate cache configuration and test backend connectivity. |
| `cache_inspect` | `aquilia/cli/__main__.py` | Display current cache configuration as JSON. |
| `cache_stats` | `aquilia/cli/__main__.py` | Display cache statistics from trace diagnostics. |
| `cache_clear` | `aquilia/cli/__main__.py` | Clear all or namespace-scoped cache entries. |
| `i18n` | `aquilia/cli/__main__.py` | AquilaI18n -- init, check, inspect, extract, coverage, and compile. |
| `i18n_init` | `aquilia/cli/__main__.py` | Initialize i18n in the current workspace. |
| `i18n_check` | `aquilia/cli/__main__.py` | Validate i18n configuration and catalog structure. |
| `i18n_inspect` | `aquilia/cli/__main__.py` | Display current i18n configuration as JSON. |
| `i18n_extract` | `aquilia/cli/__main__.py` | Extract translation keys from source files. |
| `i18n_coverage` | `aquilia/cli/__main__.py` | Show translation coverage per locale. |
| `i18n_compile` | `aquilia/cli/__main__.py` | Compile JSON locale files to CROUS format. |
| `db` | `aquilia/cli/__main__.py` | Database and model ORM commands. |
| `db_makemigrations` | `aquilia/cli/__main__.py` | Generate migration files from Python Model definitions. |
| `db_migrate` | `aquilia/cli/__main__.py` | Apply pending migrations to the database. |
| `db_dump` | `aquilia/cli/__main__.py` | Dump model schema -- annotated Python overview or raw SQL DDL. |
| `db_shell` | `aquilia/cli/__main__.py` | Open an async REPL with models pre-loaded. |
| `db_inspectdb` | `aquilia/cli/__main__.py` | Introspect database and generate Model definitions. |
| `db_showmigrations` | `aquilia/cli/__main__.py` | Show all migrations and their applied/pending status. |
| `db_sqlmigrate` | `aquilia/cli/__main__.py` | Display SQL statements for a specific migration. |
| `db_status` | `aquilia/cli/__main__.py` | Show database status -- tables, row counts, columns. |
| `test` | `aquilia/cli/__main__.py` | Run the test suite with Aquilia-aware defaults. |
| `admin` | `aquilia/cli/__main__.py` | Admin dashboard management and diagnostics. |
| `admin_check` | `aquilia/cli/__main__.py` | Pre-flight check for admin dashboard dependencies. |
| `admin_createsuperuser` | `aquilia/cli/__main__.py` | Create an admin superuser in the database. |
| `admin_createstaff` | `aquilia/cli/__main__.py` | Create an admin staff user in the database. |
| `admin_listusers` | `aquilia/cli/__main__.py` | List all admin users. |
| `admin_changepassword` | `aquilia/cli/__main__.py` | Change an admin user's password. |
| `admin_setup` | `aquilia/cli/__main__.py` | Auto-configure all admin dependencies in workspace.py. |
| `admin_status` | `aquilia/cli/__main__.py` | Show admin dashboard status and registered models. |
| `admin_audit` | `aquilia/cli/__main__.py` | View admin audit trail. |
| `main` | `aquilia/cli/__main__.py` | Entry point for `aq` command. |
| `main` | `aquilia/cli/discovery_cli.py` | Main CLI entry point. |
| `success` | `aquilia/cli/utils/colors.py` | Print success message in green. |
| `error` | `aquilia/cli/utils/colors.py` | Print error message in red. |
| `warning` | `aquilia/cli/utils/colors.py` | Print warning message in yellow. |
| `info` | `aquilia/cli/utils/colors.py` | Print info message in cyan. |
| `dim` | `aquilia/cli/utils/colors.py` | Print dimmed message. |
| `bold` | `aquilia/cli/utils/colors.py` | Return bold-styled text (does not echo). |
| `accent` | `aquilia/cli/utils/colors.py` | Return magenta-accented text (does not echo). |
| `banner` | `aquilia/cli/utils/colors.py` | Print a bordered banner with centred title and optional icon. |
| `section` | `aquilia/cli/utils/colors.py` | Print a section header with a ruled line. |
| `rule` | `aquilia/cli/utils/colors.py` | Print a thin horizontal rule. |
| `kv` | `aquilia/cli/utils/colors.py` | Print an aligned key-value pair. |
| `badge` | `aquilia/cli/utils/colors.py` | Return an inline badge string (not echoed). |

Only the first 80 functions are shown here. See the file inventory for the rest of the package.

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/cli/__init__.py` | Aquilate - Aquilia Native CLI System. |
| `aquilia/cli/__main__.py` | Aquilate CLI - Main Entry Point. |
| `aquilia/cli/commands/__init__.py` | Command implementations package. |
| `aquilia/cli/commands/add.py` | Add module to workspace command. |
| `aquilia/cli/commands/analytics.py` | Advanced module discovery analytics and reporting. |
| `aquilia/cli/commands/artifacts.py` | Artifact CLI commands -- ``aq artifact list``, ``aq artifact inspect``, |
| `aquilia/cli/commands/cache.py` | AquilaCache CLI commands -- ``aq cache`` group. |
| `aquilia/cli/commands/compile.py` | Manifest compilation command. |
| `aquilia/cli/commands/deploy_gen.py` | Deploy CLI commands -- ``aq deploy`` group. |
| `aquilia/cli/commands/discover.py` | CLI command for module discovery inspection, validation, and auto-sync. |
| `aquilia/cli/commands/doctor.py` | Workspace diagnostics command -- ``aq doctor``. |
| `aquilia/cli/commands/freeze.py` | Artifact freezing command. |
| `aquilia/cli/commands/i18n.py` | AquilaI18n CLI commands - ``aq i18n`` group. |
| `aquilia/cli/commands/init.py` | Workspace and module initialization commands. |
| `aquilia/cli/commands/inspect.py` | Artifact inspection commands -- live workspace introspection. |
| `aquilia/cli/commands/mail.py` | AquilaMail CLI commands -- ``aq mail`` group. |
| `aquilia/cli/commands/manifest.py` | Manifest management commands. |
| `aquilia/cli/commands/migrate.py` | Legacy project migration command. |
| `aquilia/cli/commands/mlops_cmds.py` | MLOps CLI commands -- ``aq pack``, ``aq model``, ``aq deploy``, ``aq observe``, |
| `aquilia/cli/commands/model_cmds.py` | Model CLI Commands -- aq db makemigrations, aq db migrate, aq db dump, aq db shell. |
| `aquilia/cli/commands/provider.py` | Provider CLI commands - ``aq provider``. |
| `aquilia/cli/commands/run.py` | Development server command. |
| `aquilia/cli/commands/serve.py` | Production server command. |
| `aquilia/cli/commands/test.py` | Aquilia CLI - ``aq test`` command. |
| `aquilia/cli/commands/validate.py` | Manifest validation command. |
| `aquilia/cli/commands/ws.py` | WebSocket CLI Commands - Admin tools for WebSocket management |
| `aquilia/cli/compilers/__init__.py` | Artifact compilers. |
| `aquilia/cli/compilers/workspace.py` | Workspace compiler - converts manifests to artifacts. |
| `aquilia/cli/discovery_cli.py` | Aquilia CLI integration for enhanced auto-discovery commands. |
| `aquilia/cli/discovery_utils.py` | Enhanced discovery utilities for Aquilia CLI. |
| `aquilia/cli/generators/__init__.py` | Code generators for workspace and modules. |
| `aquilia/cli/generators/controller.py` | Controller generator - creates modern controller templates. |
| `aquilia/cli/generators/deployment.py` | Aquilia Deployment Generators -- Production-ready Docker, Compose, Kubernetes, |
| `aquilia/cli/generators/module.py` | Module generator. |
| `aquilia/cli/generators/workspace.py` | Workspace generator. |
| `aquilia/cli/parsers/__init__.py` | Manifest parsers. |
| `aquilia/cli/parsers/module.py` | Module manifest parser. |
| `aquilia/cli/parsers/workspace.py` | Workspace manifest parser. |
| `aquilia/cli/utils/__init__.py` | Aquilia CLI -- UI utilities (re-exports from colors module). |
| `aquilia/cli/utils/colors.py` | Aquilia CLI -- UI toolkit. |
| `aquilia/cli/utils/prompts.py` | Aquilia CLI -- Interactive prompt toolkit. |
| `aquilia/cli/utils/workspace.py` | Utility functions for finding and loading workspace configuration. |

## Testing Pointers

Search `tests/` for `cli` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.

# Cli Documentation

The `aq` command line interface, workspace/module generators, deployment generators, diagnostics, validation, inspection, and subsystem commands.

## Coverage Snapshot

- Source files: 42
- Source lines: 23184
- Public classes: 25
- Public module functions: 216
- Constants/module flags: 54
- Public exports in `__all__`: 37

## Source Files Read

- `aquilia/cli/__init__.py`: Aquilate - Aquilia Native CLI System.
- `aquilia/cli/__main__.py`: Aquilate CLI - Main Entry Point.
- `aquilia/cli/commands/__init__.py`: Command implementations package.
- `aquilia/cli/commands/add.py`: Add module to workspace command.
- `aquilia/cli/commands/analytics.py`: Advanced module discovery analytics and reporting. Provides deep insights into module relationships, health metrics, and optimization suggestions.
- `aquilia/cli/commands/artifacts.py`: Artifact CLI commands -- ``aq artifact list``, ``aq artifact inspect``, ``aq artifact gc``, ``aq artifact export``, ``aq artifact verify``.
- `aquilia/cli/commands/cache.py`: AquilaCache CLI commands -- ``aq cache`` group.
- `aquilia/cli/commands/compile.py`: Manifest compilation command.
- `aquilia/cli/commands/deploy_gen.py`: Deploy CLI commands -- ``aq deploy`` group.
- `aquilia/cli/commands/discover.py`: CLI command for module discovery inspection, validation, and auto-sync.
- `aquilia/cli/commands/doctor.py`: Workspace diagnostics command -- ``aq doctor``.
- `aquilia/cli/commands/freeze.py`: Artifact freezing command.
- `aquilia/cli/commands/i18n.py`: AquilaI18n CLI commands — ``aq i18n`` group.
- `aquilia/cli/commands/init.py`: Workspace and module initialization commands.
- `aquilia/cli/commands/inspect.py`: Artifact inspection commands -- live workspace introspection.
- `aquilia/cli/commands/mail.py`: AquilaMail CLI commands -- ``aq mail`` group.
- `aquilia/cli/commands/manifest.py`: Manifest management commands.
- `aquilia/cli/commands/migrate.py`: Legacy project migration command.
- `aquilia/cli/commands/mlops_cmds.py`: MLOps CLI commands -- ``aq pack``, ``aq model``, ``aq deploy``, ``aq observe``, ``aq rollout``, ``aq export``, ``aq plugin``, ``aq lineage``, ``aq experiment``.
- `aquilia/cli/commands/model_cmds.py`: Model CLI Commands -- aq db makemigrations, aq db migrate, aq db dump, aq db shell.
- `aquilia/cli/commands/provider.py`: Provider CLI commands — ``aq provider``.
- `aquilia/cli/commands/run.py`: Development server command.
- `aquilia/cli/commands/serve.py`: Production server command.
- `aquilia/cli/commands/test.py`: Aquilia CLI - ``aq test`` command.
- `aquilia/cli/commands/validate.py`: Manifest validation command.
- `aquilia/cli/commands/ws.py`: WebSocket CLI Commands - Admin tools for WebSocket management
- `aquilia/cli/compilers/__init__.py`: Artifact compilers.
- `aquilia/cli/compilers/workspace.py`: Workspace compiler - converts manifests to artifacts.
- `aquilia/cli/discovery_cli.py`: Aquilia CLI integration for enhanced auto-discovery commands. Provides convenient shortcuts for module discovery, inspection, and analytics.
- `aquilia/cli/discovery_utils.py`: Enhanced discovery utilities for Aquilia CLI.
- `aquilia/cli/generators/__init__.py`: Code generators for workspace and modules.
- `aquilia/cli/generators/controller.py`: Controller generator - creates modern controller templates.
- `aquilia/cli/generators/deployment.py`: Aquilia Deployment Generators -- Production-ready Docker, Compose, Kubernetes, Nginx, CI/CD, and monitoring file generators.
- `aquilia/cli/generators/module.py`: Module generator.
- `aquilia/cli/generators/workspace.py`: Workspace generator.
- `aquilia/cli/parsers/__init__.py`: Manifest parsers.
- `aquilia/cli/parsers/module.py`: Module manifest parser.
- `aquilia/cli/parsers/workspace.py`: Workspace manifest parser.
- `aquilia/cli/utils/__init__.py`: Aquilia CLI -- UI utilities (re-exports from colors module).
- `aquilia/cli/utils/colors.py`: Aquilia CLI -- UI toolkit.
- `aquilia/cli/utils/prompts.py`: Aquilia CLI -- Interactive prompt toolkit.
- `aquilia/cli/utils/workspace.py`: Utility functions for finding and loading workspace configuration.

## Document Map

- `architecture.md`: module boundaries, dependencies, lifecycle, and extension points.
- `configuration.md`: configuration classes, builders, server wiring, and precedence.
- `api-reference.md`: source-extracted classes, methods, functions, constants, exports, and signatures.
- `integration-guide.md`: how to wire the module into an Aquilia app.
- `cli-reference.md`: mounted `aq` commands for this module, if any.
- `examples.md`: usage examples derived from source and checked example apps.
- `edge-cases-and-limitations.md`: implementation limits and compatibility behavior.
- `troubleshooting.md`: diagnostic commands and common failure patterns.

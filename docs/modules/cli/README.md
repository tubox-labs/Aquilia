# CLI Documentation

This directory is the professional documentation set for `cli`. It is implementation-driven and aligned with the current source files under `aquilia/cli`.

## What This Covers

The `aq` command implementation for project generation, module generation, serving, inspection, model commands, migrations, cache, mail, i18n, deployment, and MLOps commands.

## Source Files Read

- `aquilia/cli/__init__.py`: Aquilate - Aquilia Native CLI System.
- `aquilia/cli/__main__.py`: Aquilate CLI - Main Entry Point.
- `aquilia/cli/commands/__init__.py`: Command implementations package.
- `aquilia/cli/commands/add.py`: Add module to workspace command.
- `aquilia/cli/commands/analytics.py`: Advanced module discovery analytics and reporting.
- `aquilia/cli/commands/artifacts.py`: Artifact CLI commands -- ``aq artifact list``, ``aq artifact inspect``,
- `aquilia/cli/commands/cache.py`: AquilaCache CLI commands -- ``aq cache`` group.
- `aquilia/cli/commands/compile.py`: Manifest compilation command.
- `aquilia/cli/commands/deploy_gen.py`: Deploy CLI commands -- ``aq deploy`` group.
- `aquilia/cli/commands/discover.py`: CLI command for module discovery inspection, validation, and auto-sync.
- `aquilia/cli/commands/doctor.py`: Workspace diagnostics command -- ``aq doctor``.
- `aquilia/cli/commands/freeze.py`: Artifact freezing command.
- `aquilia/cli/commands/i18n.py`: AquilaI18n CLI commands - ``aq i18n`` group.
- `aquilia/cli/commands/init.py`: Workspace and module initialization commands.
- `aquilia/cli/commands/inspect.py`: Artifact inspection commands -- live workspace introspection.
- `aquilia/cli/commands/mail.py`: AquilaMail CLI commands -- ``aq mail`` group.
- `aquilia/cli/commands/manifest.py`: Manifest management commands.
- `aquilia/cli/commands/migrate.py`: Legacy project migration command.
- `aquilia/cli/commands/mlops_cmds.py`: MLOps CLI commands -- ``aq pack``, ``aq model``, ``aq deploy``, ``aq observe``,
- `aquilia/cli/commands/model_cmds.py`: Model CLI Commands -- aq db makemigrations, aq db migrate, aq db dump, aq db shell.
- `aquilia/cli/commands/provider.py`: Provider CLI commands - ``aq provider``.
- `aquilia/cli/commands/run.py`: Development server command.
- `aquilia/cli/commands/serve.py`: Production server command.
- `aquilia/cli/commands/test.py`: Aquilia CLI - ``aq test`` command.
- `aquilia/cli/commands/validate.py`: Manifest validation command.
- `aquilia/cli/commands/ws.py`: WebSocket CLI Commands - Admin tools for WebSocket management
- `aquilia/cli/compilers/__init__.py`: Artifact compilers.
- `aquilia/cli/compilers/workspace.py`: Workspace compiler - converts manifests to artifacts.
- `aquilia/cli/discovery_cli.py`: Aquilia CLI integration for enhanced auto-discovery commands.
- `aquilia/cli/discovery_utils.py`: Enhanced discovery utilities for Aquilia CLI.
- `aquilia/cli/generators/__init__.py`: Code generators for workspace and modules.
- `aquilia/cli/generators/controller.py`: Controller generator - creates modern controller templates.
- `aquilia/cli/generators/deployment.py`: Aquilia Deployment Generators -- Production-ready Docker, Compose, Kubernetes,
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

- `architecture.md`: Runtime architecture and module boundaries
- `configuration.md`: Configuration entry points, datatypes, and precedence
- `api-reference.md`: Classes, methods, functions, constants, and data fields extracted from source
- `integration-guide.md`: How to wire the module into a real Aquilia application
- `cli-reference.md`: Command line surface and operational commands
- `edge-cases-and-limitations.md`: Known edge cases and implementation limits
- `troubleshooting.md`: Common failures and diagnosis steps
- `examples.md`: Code examples and usage patterns

## Public Surface Snapshot

- Python files: 42
- Public classes: 25
- Configuration or dataclass-like types: 6
- Public functions: 216
- Constants detected: 49

## Fast Start

```python
from aquilia.cli import __version__

# The imported symbols above are public exports from this module.
# See api-reference.md for constructor signatures, methods, and data fields.
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.

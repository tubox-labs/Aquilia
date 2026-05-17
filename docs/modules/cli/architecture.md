# CLI Architecture

## Runtime Role

The `aq` command implementation for project generation, module generation, serving, inspection, model commands, migrations, cache, mail, i18n, deployment, and MLOps commands.

The implementation is split across 42 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

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

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `pathlib` | 32 |
| `sys` | 20 |
| `__future__` | 12 |
| `utils` | 12 |
| `click` | 11 |
| `json` | 10 |
| `re` | 10 |
| `aquilia` | 8 |
| `importlib` | 8 |
| `typing` | 7 |
| `asyncio` | 5 |
| `contextlib` | 5 |
| `dataclasses` | 5 |
| `commands` | 4 |
| `os` | 4 |
| `textwrap` | 4 |
| `generators` | 3 |
| `workspace` | 3 |
| `collections` | 2 |
| `colors` | 2 |
| `datetime` | 2 |
| `module` | 2 |
| `shutil` | 2 |
| `argparse` | 1 |
| `ast` | 1 |
| `controller` | 1 |
| `deployment` | 1 |
| `hashlib` | 1 |
| `logging` | 1 |
| `platform` | 1 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.

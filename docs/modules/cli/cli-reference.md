# CLI CLI Reference

## Command Surface

This module owns the command runner and command registry. Read `aquilia/cli/__main__.py` plus files under `aquilia/cli/commands/` for exact command behavior.

## Related Files

- `aquilia/cli/__init__.py`
- `aquilia/cli/__main__.py`
- `aquilia/cli/commands/__init__.py`
- `aquilia/cli/commands/add.py`
- `aquilia/cli/commands/analytics.py`
- `aquilia/cli/commands/artifacts.py`
- `aquilia/cli/commands/cache.py`
- `aquilia/cli/commands/compile.py`
- `aquilia/cli/commands/deploy_gen.py`
- `aquilia/cli/commands/discover.py`
- `aquilia/cli/commands/doctor.py`
- `aquilia/cli/commands/freeze.py`
- `aquilia/cli/commands/i18n.py`
- `aquilia/cli/commands/init.py`
- `aquilia/cli/commands/inspect.py`
- `aquilia/cli/commands/mail.py`
- `aquilia/cli/commands/manifest.py`
- `aquilia/cli/commands/migrate.py`
- `aquilia/cli/commands/mlops_cmds.py`
- `aquilia/cli/commands/model_cmds.py`
- `aquilia/cli/commands/provider.py`
- `aquilia/cli/commands/run.py`
- `aquilia/cli/commands/serve.py`
- `aquilia/cli/commands/test.py`
- `aquilia/cli/commands/validate.py`
- `aquilia/cli/commands/ws.py`
- `aquilia/cli/compilers/__init__.py`
- `aquilia/cli/compilers/workspace.py`
- `aquilia/cli/discovery_cli.py`
- `aquilia/cli/discovery_utils.py`
- `aquilia/cli/generators/__init__.py`
- `aquilia/cli/generators/controller.py`
- `aquilia/cli/generators/deployment.py`
- `aquilia/cli/generators/module.py`
- `aquilia/cli/generators/workspace.py`
- `aquilia/cli/parsers/__init__.py`
- `aquilia/cli/parsers/module.py`
- `aquilia/cli/parsers/workspace.py`
- `aquilia/cli/utils/__init__.py`
- `aquilia/cli/utils/colors.py`
- `aquilia/cli/utils/prompts.py`
- `aquilia/cli/utils/workspace.py`

## Operational Pattern

1. Use `aq init workspace` and `aq add module` to create the workspace and module shape.
2. Configure this subsystem in `workspace.py` or `modules/<name>/manifest.py`.
3. Use subsystem-specific commands only when this page lists an implementation file.
4. Use `aq inspect`, `aq doctor`, `aq validate`, and tests to verify runtime wiring.

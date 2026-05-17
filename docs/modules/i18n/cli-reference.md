# Internationalization CLI Reference

## Command Surface

The `aq i18n` command group is implemented in `aquilia/cli/commands/i18n.py`.

## Related Files

- No module-local CLI files detected.

## Operational Pattern

1. Use `aq init workspace` and `aq add module` to create the workspace and module shape.
2. Configure this subsystem in `workspace.py` or `modules/<name>/manifest.py`.
3. Use subsystem-specific commands only when this page lists an implementation file.
4. Use `aq inspect`, `aq doctor`, `aq validate`, and tests to verify runtime wiring.

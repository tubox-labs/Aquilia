# Aquilary Registry CLI Reference

## Command Surface

Registry and manifest inspection is surfaced by CLI inspection and manifest commands.

## Related Files

- `aquilia/aquilary/cli.py`

## Operational Pattern

1. Use `aq init workspace` and `aq add module` to create the workspace and module shape.
2. Configure this subsystem in `workspace.py` or `modules/<name>/manifest.py`.
3. Use subsystem-specific commands only when this page lists an implementation file.
4. Use `aq inspect`, `aq doctor`, `aq validate`, and tests to verify runtime wiring.

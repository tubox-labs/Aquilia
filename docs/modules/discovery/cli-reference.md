# Discovery CLI Reference

## Command Surface

No dedicated command group was detected for this module. It is configured through workspace files, manifests, or direct Python APIs. Related commands may still exist in the main `aq` CLI for inspection, serving, validation, or project generation.

## Related Files

- No module-local CLI files detected.

## Operational Pattern

1. Use `aq init workspace` and `aq add module` to create the workspace and module shape.
2. Configure this subsystem in `workspace.py` or `modules/<name>/manifest.py`.
3. Use subsystem-specific commands only when this page lists an implementation file.
4. Use `aq inspect`, `aq doctor`, `aq validate`, and tests to verify runtime wiring.

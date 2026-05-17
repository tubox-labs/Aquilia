# Blueprints Edge Cases And Limitations

Model-to-world contracts for request validation, response rendering, schema generation, facets, projections, and lenses.

## Source-Backed Limits

- No module-specific edge branch was detected beyond optional imports, validation, and dependency availability.

## Fault And Error Classes Detected

`BlueprintFault`, `CastFault`, `SealFault`, `ImprintFault`, `ProjectionFault`, `LensDepthFault`, `LensCycleFault`

## Operational Boundaries

- Optional external libraries are only required when the corresponding provider/backend/runtime is configured.
- Deprecated APIs generally warn when retained for migration rather than disappearing silently.
- Server startup intentionally degrades non-critical optional subsystems where source catches and logs exceptions.
- Use `api-reference.md` to check exact constructor defaults and method signatures before depending on behavior.

## Verification

- `aq doctor` for workspace/integration issues.
- `aq validate` for manifest issues.
- `aq inspect config` for merged configuration.
- `GET /_health` for live subsystem status once the app is running.

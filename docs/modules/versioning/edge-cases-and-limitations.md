# Versioning Edge Cases And Limitations

API version parsing, resolvers, decorators, negotiation, graph, sunset policy/enforcement, middleware, and route registration integration.

## Source-Backed Limits

- URL version pre-resolution is best-effort for route matching; middleware remains authoritative for state/headers.

## Fault And Error Classes Detected

`VersionError`, `InvalidVersionError`, `UnsupportedVersionError`, `VersionSunsetError`, `MissingVersionError`, `VersionNegotiationError`

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

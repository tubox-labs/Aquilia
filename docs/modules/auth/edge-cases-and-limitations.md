# Auth Edge Cases And Limitations

Authentication, authorization, identity stores, token management, guards, clearance rules, MFA, OAuth, and session integration.

## Source-Backed Limits

- Auth enables sessions automatically.
- Local dev/test can force secure cookies off for HTTP localhost.
- Insecure auth secrets fail in non-dev mode.

## Fault And Error Classes Detected

`AuthorizationRequiredFault`, `FaultHandlerMiddleware`

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

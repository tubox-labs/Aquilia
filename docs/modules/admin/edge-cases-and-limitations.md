# Admin Edge Cases And Limitations

Built-in administration interface, audit log, permissions, dashboards, model CRUD, operational pages, and admin security.

## Source-Backed Limits

- Admin route injection happens after controller loading.
- Admin requires sessions/auth for login state and warns when absent.
- Some disabled admin modules still have routes; handlers render disabled/forbidden pages.

## Fault And Error Classes Detected

`ErrorRecord`, `ErrorGroup`, `ErrorTracker`, `AdminFault`, `AdminAuthenticationFault`, `AdminAuthorizationFault`, `AdminSecurityFault`, `AdminCSRFViolationFault`, `AdminRateLimitFault`, `AdminModelNotFoundFault`, `AdminRecordNotFoundFault`, `AdminValidationFault`, `AdminActionFault`, `AdminConfigurationFault`, `AdminRegistrationFault`, `AdminInlineFault`, `AdminTemplateFault`, `AdminExportFault`

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

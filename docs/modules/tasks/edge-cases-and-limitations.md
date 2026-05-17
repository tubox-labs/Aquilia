# Tasks Edge Cases And Limitations

Async background job manager, task decorator registry, jobs, schedules, memory backend, worker loops, retries, and faults.

## Source-Backed Limits

- Current server wiring falls back to memory backend for unknown task backend names.

## Fault And Error Classes Detected

`TaskFault`, `TaskScheduleFault`, `TaskNotBoundFault`, `TaskEnqueueFault`, `TaskResolutionFault`

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

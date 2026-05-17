# Tasks Configuration

## Configuration Entry Points

The implementation exposes the following configuration-like classes, policies, integrations, or dataclasses.

| Type | Source | Fields | Purpose |
| --- | --- | --- | --- |
| `JobResult` | `aquilia/tasks/job.py` | success: bool, value: Any, error: str &#124; None, error_type: str &#124; None, traceback: str &#124; None, duration_ms: float | Stores the result or error from a completed/failed job. |
| `Job` | `aquilia/tasks/job.py` | id: str, name: str, queue: str, priority: Priority, func_ref: str, args: tuple[Any, ...], kwargs: dict[str, Any], state: JobState, result: JobResult &#124; None, max_retries: int, retry_count: int, retry_delay: float, ... | Represents a background task job. |
| `IntervalSchedule` | `aquilia/tasks/schedule.py` | interval: float | Fixed-interval periodic schedule. |
| `CronSchedule` | `aquilia/tasks/schedule.py` | expression: str | Cron-expression periodic schedule. |

## Common Entry Points

- `TasksIntegration`
- `TaskManager constructor`
- `BackgroundTaskConfig`

## Precedence Model

Aquilia generally resolves configuration in this order:

1. Explicit constructor arguments or typed integration dataclass values.
2. `Workspace` builder methods and `Workspace.integrate(...)` output.
3. `ConfigLoader` defaults and environment overlays.
4. Runtime defaults inside the subsystem service or provider constructor.

When this module is registered through an `AppManifest`, keep component declarations inside `modules/<name>/manifest.py` and keep cross-cutting integration settings in `workspace.py`.

## Datatype Guidance

- Prefer typed dataclasses, policy objects, and config objects listed above when they exist.
- Keep secret values in environment-backed config, not literal strings in committed workspace files.
- Keep runtime-only state in services, stores, providers, or request state rather than static configuration.
- Use `to_dict()` on integration dataclasses when you need to inspect exactly what enters `ConfigLoader`.

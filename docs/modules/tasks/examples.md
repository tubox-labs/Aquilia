# Tasks Examples

Async background job manager, task decorator registry, jobs, schedules, memory backend, worker loops, retries, and faults.

Examples here use public symbols and checked patterns from the repository. When a module has no safe standalone constructor example, the example focuses on importing and wiring the actual source-backed API.

## Source-Backed Import Examples

```python
from aquilia.tasks.decorators import task
from aquilia.tasks.engine import TaskBackend
from aquilia.tasks.engine import MemoryBackend
from aquilia.tasks.faults import TaskFault
from aquilia.tasks.faults import TaskScheduleFault
from aquilia.tasks.job import JobState
```

## Workspace/Manifest Wiring Example

```python
from aquilia import AppManifest, Integration, Module, Workspace

workspace = (
    Workspace("example", version="1.0.0")
    .runtime(mode="dev", port=8000)
    .module(Module("example").route_prefix("/example"))
    .integrate(Integration.di(auto_wire=True))
)

manifest = AppManifest(
    name="example",
    version="1.0.0",
    controllers=["modules.example.controllers:ExampleController"],
    services=["modules.example.services:ExampleService"],
)
```

## Task Pattern

```python
from aquilia.tasks import task

@task(name="jobs.cleanup", queue="maintenance", max_retries=3)
async def cleanup_job():
    return {"ok": True}
```

## Verification

- Run `python -m aquilia.cli.__main__ --help` to confirm CLI availability.
- Run `aq validate` in a workspace to validate manifest paths.
- Run related tests under `tests/` or `examples/*/tests/` for executable behavior.

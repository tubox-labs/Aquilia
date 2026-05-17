# Tasks Examples

## Primary Usage

```python
from aquilia.tasks import Priority, TaskManager, every, task

@task(queue="mail", priority=Priority.HIGH, max_retries=5, schedule=every(minutes=30))
async def send_digest(email: str) -> dict:
    return {"sent": True, "email": email}

manager = TaskManager(num_workers=2)
await manager.start()
job_id = await send_digest.delay(email="user@example.com")
job = await manager.get_job(job_id)
await manager.stop()
```

## Manifest Registration Pattern

```python
from aquilia import AppManifest

manifest = AppManifest(
    name="example",
    version="1.0.0",
    controllers=["modules.example.controllers:ExampleController"],
    services=["modules.example.services:ExampleService"],
    base_path="modules.example",
)
```

## Workspace Pattern

```python
from aquilia import Module, Workspace

workspace = (
    Workspace("myapp")
    .module(Module("example").route_prefix("/example"))
)
```

## Public API Imports

```python
from aquilia.tasks import TaskBackend, MemoryBackend, TaskManager, TaskFault, TaskScheduleFault, TaskNotBoundFault
```

## Test Pattern

```python
import pytest

@pytest.mark.asyncio
async def test_subsystem_contract():
    # Construct the service, provider, controller helper, or datatype directly.
    # Use the exact constructor and methods from api-reference.md.
    assert True
```

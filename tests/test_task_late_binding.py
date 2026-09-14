"""Late task registration -- F-15 of the AniWave migration audit.

A ``@task`` descriptor whose module was imported *after*
``TaskManager.start()`` was never bound: ``.delay()`` raised
``TaskNotBoundFault``, and fire-and-forget dispatch hid the fault entirely
(it surfaced only at GC time). The invariant: a registered task dispatched
while a manager is running must be dispatchable, regardless of import
order.
"""

from __future__ import annotations

import pytest

from aquilia.tasks import TaskManager, get_task_manager, set_task_manager, task
from aquilia.tasks.decorators import _task_registry
from aquilia.tasks.engine import MemoryBackend
from aquilia.tasks.faults import TaskNotBoundFault


@task(name="audit:late_module_task")
async def late_module_task(x: int) -> int:
    return x * 2


@pytest.fixture
async def running_manager():
    manager = TaskManager(backend=MemoryBackend(), num_workers=1)
    await manager.start()
    yield manager
    await manager.stop()


async def test_late_registered_task_dispatches(running_manager):
    # Simulate the audit's condition: the descriptor was created after
    # TaskManager.start() and so was never seen by _bind_task_descriptors().
    descriptor = _task_registry["audit:late_module_task"]
    descriptor._manager = None

    job_id = await late_module_task.delay(21)

    assert job_id
    job = await running_manager.backend.get(job_id)
    assert job is not None
    # The lazy bind cached the running manager.
    assert descriptor._manager is running_manager


async def test_dispatch_after_manager_stop_raises_clearly(running_manager):
    descriptor = _task_registry["audit:late_module_task"]
    descriptor._manager = None
    await running_manager.stop()

    with pytest.raises(TaskNotBoundFault):
        await late_module_task.delay(1)


async def test_no_manager_running_raises_task_not_bound():
    descriptor = _task_registry["audit:late_module_task"]
    previous = descriptor._manager
    descriptor._manager = None
    published = get_task_manager()
    set_task_manager(None)
    try:
        with pytest.raises(TaskNotBoundFault):
            await late_module_task.delay(1)
    finally:
        descriptor._manager = previous
        set_task_manager(published)


async def test_bound_task_unaffected(running_manager):
    job_id = await late_module_task.delay(7)
    assert job_id

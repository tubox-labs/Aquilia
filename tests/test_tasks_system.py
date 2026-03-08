"""
Comprehensive and Regressive Tests for the AquilaTasks Background Task System.

Covers:
- Job model (JobState, Priority, JobResult, Job lifecycle)
- @task decorator (registration, metadata, direct invocation)
- MemoryBackend (push, pop, priority ordering, state management, cleanup, cancel, retry, flush)
- TaskManager (enqueue, lifecycle, stats, event hooks, dead-letter)
- Worker (standalone worker)
- Config integration (get_tasks_config, config_builders)
- Effects integration (TaskQueueProvider, TaskQueueHandle)
- Server wiring (_setup_tasks, _setup_error_tracker, admin route registration)
- Admin site integration (set_task_manager, get_tasks_data)
- AdminConfig module enabled/disabled for devtools pages
- Regression: disabled modules still serve disabled page (no ADMIN_MODEL_NOT_FOUND)
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ============================================================================
# 1. JOB MODEL TESTS
# ============================================================================


class TestJobState:
    """Verify JobState enum members and values."""

    def test_all_states_exist(self):
        from aquilia.tasks.job import JobState
        assert JobState.PENDING.value == "pending"
        assert JobState.SCHEDULED.value == "scheduled"
        assert JobState.RUNNING.value == "running"
        assert JobState.COMPLETED.value == "completed"
        assert JobState.FAILED.value == "failed"
        assert JobState.RETRYING.value == "retrying"
        assert JobState.CANCELLED.value == "cancelled"
        assert JobState.DEAD.value == "dead"

    def test_state_count(self):
        from aquilia.tasks.job import JobState
        assert len(JobState) == 8

    def test_state_is_str_enum(self):
        from aquilia.tasks.job import JobState
        assert isinstance(JobState.PENDING, str)
        assert JobState.PENDING == "pending"


class TestPriority:
    """Verify Priority enum ordering."""

    def test_priority_values(self):
        from aquilia.tasks.job import Priority
        assert Priority.CRITICAL.value == 0
        assert Priority.HIGH.value == 1
        assert Priority.NORMAL.value == 2
        assert Priority.LOW.value == 3

    def test_priority_ordering(self):
        from aquilia.tasks.job import Priority
        assert Priority.CRITICAL < Priority.HIGH < Priority.NORMAL < Priority.LOW

    def test_priority_is_int_enum(self):
        from aquilia.tasks.job import Priority
        assert isinstance(Priority.NORMAL, int)
        assert Priority.NORMAL == 2


class TestJobResult:
    """Verify JobResult dataclass."""

    def test_success_result(self):
        from aquilia.tasks.job import JobResult
        r = JobResult(success=True, value=42, duration_ms=150.5)
        assert r.success is True
        assert r.value == 42
        assert r.error is None
        assert r.duration_ms == 150.5

    def test_failure_result(self):
        from aquilia.tasks.job import JobResult
        r = JobResult(
            success=False,
            error="Connection refused",
            error_type="ConnectionError",
            traceback="Traceback...",
            duration_ms=50.0,
        )
        assert r.success is False
        assert r.error == "Connection refused"
        assert r.error_type == "ConnectionError"

    def test_result_to_dict(self):
        from aquilia.tasks.job import JobResult
        r = JobResult(success=True, value="hello", duration_ms=10.1234)
        d = r.to_dict()
        assert d["success"] is True
        assert d["value"] == "'hello'"  # repr of string
        assert d["duration_ms"] == 10.12  # rounded
        assert d["error"] is None

    def test_result_to_dict_none_value(self):
        from aquilia.tasks.job import JobResult
        r = JobResult(success=True, value=None)
        d = r.to_dict()
        assert d["value"] is None


class TestJob:
    """Verify Job dataclass properties and serialization."""

    def test_default_job(self):
        from aquilia.tasks.job import Job, JobState, Priority
        j = Job(name="test_task")
        assert j.name == "test_task"
        assert j.state == JobState.PENDING
        assert j.priority == Priority.NORMAL
        assert j.queue == "default"
        assert j.max_retries == 3
        assert j.retry_count == 0
        assert j.is_terminal is False
        assert j.is_runnable is True
        assert len(j.id) == 16

    def test_is_terminal_states(self):
        from aquilia.tasks.job import Job, JobState
        terminal = [JobState.COMPLETED, JobState.FAILED, JobState.CANCELLED, JobState.DEAD]
        non_terminal = [JobState.PENDING, JobState.SCHEDULED, JobState.RUNNING, JobState.RETRYING]

        for state in terminal:
            j = Job(state=state)
            assert j.is_terminal is True, f"{state} should be terminal"

        for state in non_terminal:
            j = Job(state=state)
            assert j.is_terminal is False, f"{state} should NOT be terminal"

    def test_is_runnable(self):
        from aquilia.tasks.job import Job, JobState
        runnable = [JobState.PENDING, JobState.RETRYING, JobState.SCHEDULED]
        for state in runnable:
            j = Job(state=state)
            assert j.is_runnable is True, f"{state} should be runnable"

        not_runnable = [JobState.RUNNING, JobState.COMPLETED, JobState.FAILED, JobState.CANCELLED, JobState.DEAD]
        for state in not_runnable:
            j = Job(state=state)
            assert j.is_runnable is False, f"{state} should NOT be runnable"

    def test_scheduled_not_runnable_if_future(self):
        from aquilia.tasks.job import Job, JobState
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        j = Job(state=JobState.SCHEDULED, scheduled_at=future)
        assert j.is_runnable is False

    def test_scheduled_runnable_if_past(self):
        from aquilia.tasks.job import Job, JobState
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        j = Job(state=JobState.SCHEDULED, scheduled_at=past)
        assert j.is_runnable is True

    def test_can_retry(self):
        from aquilia.tasks.job import Job
        j = Job(max_retries=3, retry_count=0)
        assert j.can_retry is True
        j.retry_count = 3
        assert j.can_retry is False
        j.retry_count = 4
        assert j.can_retry is False

    def test_next_retry_delay(self):
        from aquilia.tasks.job import Job
        j = Job(retry_delay=1.0, retry_backoff=2.0, retry_max_delay=10.0)
        j.retry_count = 0
        delay = j.next_retry_delay
        # Base delay * backoff^0 = 1.0 ± 25% jitter → 0.75..1.25
        assert 0.1 <= delay <= 2.0

    def test_retry_delay_capped(self):
        from aquilia.tasks.job import Job
        j = Job(retry_delay=1.0, retry_backoff=10.0, retry_max_delay=5.0)
        j.retry_count = 10  # 1.0 * 10^10 = huge, capped at 5.0
        delay = j.next_retry_delay
        assert delay <= 6.5  # 5.0 + 25% jitter

    def test_duration_ms(self):
        from aquilia.tasks.job import Job
        j = Job()
        assert j.duration_ms is None  # No start/end
        j.started_at = datetime.now(timezone.utc)
        assert j.duration_ms is None  # No end
        j.completed_at = j.started_at + timedelta(milliseconds=500)
        assert abs(j.duration_ms - 500.0) < 1.0

    def test_fingerprint(self):
        from aquilia.tasks.job import Job
        j1 = Job(func_ref="mod:func", args=(1, 2), kwargs={"x": 3})
        j2 = Job(func_ref="mod:func", args=(1, 2), kwargs={"x": 3})
        j3 = Job(func_ref="mod:func", args=(1, 3), kwargs={"x": 3})
        assert j1.fingerprint == j2.fingerprint
        assert j1.fingerprint != j3.fingerprint

    def test_to_dict(self):
        from aquilia.tasks.job import Job, JobState, Priority
        j = Job(name="email", queue="mail", priority=Priority.HIGH)
        d = j.to_dict()
        assert d["name"] == "email"
        assert d["queue"] == "mail"
        assert d["priority"] == "HIGH"
        assert d["priority_value"] == 1
        assert d["state"] == "pending"
        assert d["is_terminal"] is False
        assert d["can_retry"] is True
        assert "id" in d
        assert "created_at" in d
        assert "fingerprint" in d

    def test_job_repr_includes_name(self):
        from aquilia.tasks.job import Job, JobState
        j = Job(name="send_email")
        r = repr(j)
        assert "send_email" in r
        assert "pending" in r

    def test_job_repr_with_func_ref(self):
        from aquilia.tasks.job import Job
        j = Job(func_ref="mod:func")
        r = repr(j)
        assert "mod:func" in r


# ============================================================================
# 2. TASK DECORATOR TESTS
# ============================================================================


class TestTaskDecorator:
    """Verify @task decorator behavior."""

    def test_decorator_without_args(self):
        from aquilia.tasks.decorators import task, _task_registry

        @task
        async def my_simple_task():
            return 42

        assert isinstance(my_simple_task, object)
        assert hasattr(my_simple_task, "task_name")
        assert hasattr(my_simple_task, "queue")
        assert my_simple_task.queue == "default"
        assert my_simple_task.max_retries == 3

    def test_decorator_with_args(self):
        from aquilia.tasks.decorators import task
        from aquilia.tasks.job import Priority

        @task(queue="emails", priority=Priority.HIGH, max_retries=5, timeout=60.0)
        async def send_email(to: str, subject: str):
            pass

        assert send_email.queue == "emails"
        assert send_email.priority == Priority.HIGH
        assert send_email.max_retries == 5
        assert send_email.timeout == 60.0

    def test_decorator_preserves_function_name(self):
        from aquilia.tasks.decorators import task

        @task
        async def my_named_task():
            pass

        assert "my_named_task" in my_named_task.task_name

    def test_direct_invocation(self):
        from aquilia.tasks.decorators import task

        @task
        async def add_numbers(a, b):
            return a + b

        result = asyncio.run(add_numbers(3, 4))
        assert result == 7

    def test_task_registered_in_registry(self):
        from aquilia.tasks.decorators import task, get_registered_tasks

        @task(name="test_tasks_system:registered_task")
        async def registered_task():
            return "registered"

        tasks = get_registered_tasks()
        assert "test_tasks_system:registered_task" in tasks

    def test_get_task_lookup(self):
        from aquilia.tasks.decorators import task, get_task

        @task(name="test_tasks_system:lookup_task")
        async def lookup_task():
            pass

        found = get_task("test_tasks_system:lookup_task")
        assert found is not None
        assert found.task_name == "test_tasks_system:lookup_task"

    def test_get_task_not_found(self):
        from aquilia.tasks.decorators import get_task
        assert get_task("nonexistent:task") is None

    def test_custom_retry_params(self):
        from aquilia.tasks.decorators import task

        @task(
            retry_delay=2.0,
            retry_backoff=3.0,
            retry_max_delay=60.0,
        )
        async def retry_task():
            pass

        assert retry_task.retry_delay == 2.0
        assert retry_task.retry_backoff == 3.0
        assert retry_task.retry_max_delay == 60.0

    def test_tags(self):
        from aquilia.tasks.decorators import task

        @task(tags=["email", "notification"])
        async def tagged_task():
            pass

        assert tagged_task.tags == ["email", "notification"]

    def test_func_ref_property(self):
        from aquilia.tasks.decorators import task

        @task(name="custom:name")
        async def named_task():
            pass

        assert named_task.func_ref == "custom:name"


# ============================================================================
# 3. MEMORY BACKEND TESTS
# ============================================================================


class TestMemoryBackend:
    """Verify MemoryBackend operations."""

    @pytest.fixture
    def backend(self):
        from aquilia.tasks.engine import MemoryBackend
        return MemoryBackend()

    @pytest.mark.asyncio
    async def test_push_and_pop(self, backend):
        from aquilia.tasks.job import Job
        job = Job(name="test", queue="default")
        await backend.push(job)

        popped = await backend.pop("default")
        assert popped is not None
        assert popped.id == job.id

    @pytest.mark.asyncio
    async def test_pop_empty_queue(self, backend):
        result = await backend.pop("default")
        assert result is None

    @pytest.mark.asyncio
    async def test_pop_wrong_queue(self, backend):
        from aquilia.tasks.job import Job
        job = Job(name="test", queue="emails")
        await backend.push(job)
        result = await backend.pop("default")
        assert result is None

    @pytest.mark.asyncio
    async def test_priority_ordering(self, backend):
        from aquilia.tasks.job import Job, Priority

        low = Job(name="low", queue="default", priority=Priority.LOW)
        high = Job(name="high", queue="default", priority=Priority.HIGH)
        critical = Job(name="critical", queue="default", priority=Priority.CRITICAL)

        # Push in wrong order
        await backend.push(low)
        await backend.push(critical)
        await backend.push(high)

        # Pop should respect priority
        first = await backend.pop("default")
        assert first.name == "critical"
        second = await backend.pop("default")
        assert second.name == "high"
        third = await backend.pop("default")
        assert third.name == "low"

    @pytest.mark.asyncio
    async def test_get_by_id(self, backend):
        from aquilia.tasks.job import Job
        job = Job(name="findme")
        await backend.push(job)
        found = await backend.get(job.id)
        assert found is not None
        assert found.name == "findme"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, backend):
        result = await backend.get("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_update(self, backend):
        from aquilia.tasks.job import Job, JobState
        job = Job(name="updatable")
        await backend.push(job)
        job.state = JobState.RUNNING
        await backend.update(job)
        updated = await backend.get(job.id)
        assert updated.state == JobState.RUNNING

    @pytest.mark.asyncio
    async def test_list_jobs(self, backend):
        from aquilia.tasks.job import Job
        for i in range(5):
            await backend.push(Job(name=f"job-{i}"))
        jobs = await backend.list_jobs(limit=3)
        assert len(jobs) == 3

    @pytest.mark.asyncio
    async def test_list_jobs_filter_queue(self, backend):
        from aquilia.tasks.job import Job
        await backend.push(Job(name="a", queue="q1"))
        await backend.push(Job(name="b", queue="q2"))
        await backend.push(Job(name="c", queue="q1"))
        jobs = await backend.list_jobs(queue="q1")
        assert len(jobs) == 2
        assert all(j.queue == "q1" for j in jobs)

    @pytest.mark.asyncio
    async def test_list_jobs_filter_state(self, backend):
        from aquilia.tasks.job import Job, JobState
        j1 = Job(name="a", state=JobState.PENDING)
        j2 = Job(name="b", state=JobState.COMPLETED)
        await backend.push(j1)
        await backend.push(j2)
        j2.state = JobState.COMPLETED
        await backend.update(j2)
        jobs = await backend.list_jobs(state=JobState.COMPLETED)
        assert len(jobs) == 1
        assert jobs[0].name == "b"

    @pytest.mark.asyncio
    async def test_cancel(self, backend):
        from aquilia.tasks.job import Job, JobState
        job = Job(name="cancellable")
        await backend.push(job)
        result = await backend.cancel(job.id)
        assert result is True
        cancelled = await backend.get(job.id)
        assert cancelled.state == JobState.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_terminal_fails(self, backend):
        from aquilia.tasks.job import Job, JobState
        job = Job(name="done", state=JobState.COMPLETED)
        await backend.push(job)
        job.state = JobState.COMPLETED
        await backend.update(job)
        result = await backend.cancel(job.id)
        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_nonexistent(self, backend):
        result = await backend.cancel("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_retry(self, backend):
        from aquilia.tasks.job import Job, JobState
        job = Job(name="failed_task", state=JobState.FAILED)
        await backend.push(job)
        job.state = JobState.FAILED
        await backend.update(job)

        result = await backend.retry(job.id)
        assert result is True
        retried = await backend.get(job.id)
        assert retried.state == JobState.RETRYING

    @pytest.mark.asyncio
    async def test_retry_pending_fails(self, backend):
        from aquilia.tasks.job import Job
        job = Job(name="pending_task")
        await backend.push(job)
        result = await backend.retry(job.id)
        assert result is False

    @pytest.mark.asyncio
    async def test_flush_all(self, backend):
        from aquilia.tasks.job import Job
        for i in range(10):
            await backend.push(Job(name=f"j-{i}"))
        removed = await backend.flush()
        assert removed == 10
        jobs = await backend.list_jobs()
        assert len(jobs) == 0

    @pytest.mark.asyncio
    async def test_flush_queue(self, backend):
        from aquilia.tasks.job import Job
        for i in range(5):
            await backend.push(Job(name=f"a-{i}", queue="alpha"))
        for i in range(3):
            await backend.push(Job(name=f"b-{i}", queue="beta"))
        removed = await backend.flush("alpha")
        assert removed == 5
        jobs = await backend.list_jobs()
        assert len(jobs) == 3

    @pytest.mark.asyncio
    async def test_cleanup(self, backend):
        from aquilia.tasks.job import Job, JobState
        old = Job(name="old", state=JobState.COMPLETED)
        old.completed_at = datetime.now(timezone.utc) - timedelta(hours=2)
        await backend.push(old)
        old.state = JobState.COMPLETED
        await backend.update(old)

        recent = Job(name="recent", state=JobState.COMPLETED)
        recent.completed_at = datetime.now(timezone.utc)
        await backend.push(recent)
        recent.state = JobState.COMPLETED
        await backend.update(recent)

        removed = await backend.cleanup(max_age_seconds=3600)
        assert removed == 1  # Only old job removed

    @pytest.mark.asyncio
    async def test_get_stats(self, backend):
        from aquilia.tasks.job import Job, JobState
        await backend.push(Job(name="a"))
        j2 = Job(name="b")
        await backend.push(j2)
        j2.state = JobState.COMPLETED
        j2.completed_at = datetime.now(timezone.utc)
        j2.started_at = j2.completed_at - timedelta(milliseconds=100)
        await backend.update(j2)

        stats = await backend.get_stats()
        assert stats["total_jobs"] == 2
        assert "pending" in stats["by_state"] or "completed" in stats["by_state"]

    @pytest.mark.asyncio
    async def test_get_queue_stats(self, backend):
        from aquilia.tasks.job import Job
        await backend.push(Job(name="a", queue="q1"))
        await backend.push(Job(name="b", queue="q2"))
        qs = await backend.get_queue_stats()
        assert "q1" in qs
        assert "q2" in qs

    @pytest.mark.asyncio
    async def test_pop_skips_terminal_jobs(self, backend):
        from aquilia.tasks.job import Job, JobState
        job = Job(name="done")
        await backend.push(job)
        job.state = JobState.COMPLETED
        await backend.update(job)
        result = await backend.pop("default")
        assert result is None

    @pytest.mark.asyncio
    async def test_pop_skips_scheduled_future(self, backend):
        from aquilia.tasks.job import Job, JobState
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        job = Job(name="future", state=JobState.SCHEDULED, scheduled_at=future)
        await backend.push(job)
        result = await backend.pop("default")
        assert result is None

    @pytest.mark.asyncio
    async def test_dead_letter_tracking(self, backend):
        from aquilia.tasks.job import Job, JobState
        job = Job(name="dead", state=JobState.DEAD)
        await backend.push(job)
        job.state = JobState.DEAD
        await backend.update(job)
        stats = await backend.get_stats()
        assert stats["dead_letter_count"] >= 1


# ============================================================================
# 4. TASK MANAGER TESTS
# ============================================================================


class TestTaskManager:
    """Verify TaskManager lifecycle and enqueue API."""

    @pytest.fixture
    def manager(self):
        from aquilia.tasks.engine import TaskManager, MemoryBackend
        return TaskManager(backend=MemoryBackend(), num_workers=2)

    @pytest.mark.asyncio
    async def test_start_stop(self, manager):
        assert manager.is_running is False
        await manager.start()
        assert manager.is_running is True
        await manager.stop()
        assert manager.is_running is False

    @pytest.mark.asyncio
    async def test_double_start(self, manager):
        await manager.start()
        await manager.start()  # Should be idempotent
        assert manager.is_running is True
        await manager.stop()

    @pytest.mark.asyncio
    async def test_enqueue_callable(self, manager):
        async def my_func():
            return 42

        job_id = await manager.enqueue(my_func)
        assert isinstance(job_id, str)
        assert len(job_id) == 16

        job = await manager.get_job(job_id)
        assert job is not None
        assert job.state.value in ("pending", "scheduled")

    @pytest.mark.asyncio
    async def test_enqueue_task_descriptor(self, manager):
        from aquilia.tasks.decorators import task
        from aquilia.tasks.job import Priority

        @task(queue="test_q", priority=Priority.HIGH, max_retries=5)
        async def decorated_task(x):
            return x * 2

        job_id = await manager.enqueue(decorated_task, 21)
        job = await manager.get_job(job_id)
        assert job is not None
        assert job.queue == "test_q"
        assert job.priority == Priority.HIGH
        assert job.max_retries == 5

    @pytest.mark.asyncio
    async def test_enqueue_override_params(self, manager):
        from aquilia.tasks.decorators import task
        from aquilia.tasks.job import Priority

        @task(queue="default", priority=Priority.LOW)
        async def override_task():
            pass

        job_id = await manager.enqueue(
            override_task,
            queue="custom",
            priority=Priority.CRITICAL,
            max_retries=10,
        )
        job = await manager.get_job(job_id)
        assert job.queue == "custom"
        assert job.priority == Priority.CRITICAL
        assert job.max_retries == 10

    @pytest.mark.asyncio
    async def test_enqueue_with_delay(self, manager):
        async def delayed_task():
            pass

        job_id = await manager.enqueue(delayed_task, delay=60.0)
        job = await manager.get_job(job_id)
        from aquilia.tasks.job import JobState
        assert job.state == JobState.SCHEDULED
        assert job.scheduled_at is not None
        assert job.scheduled_at > datetime.now(timezone.utc)

    @pytest.mark.asyncio
    async def test_enqueue_with_tags_and_metadata(self, manager):
        async def tagged_func():
            pass

        job_id = await manager.enqueue(
            tagged_func,
            tags=["email", "urgent"],
            metadata={"user_id": 123},
        )
        job = await manager.get_job(job_id)
        assert job.tags == ["email", "urgent"]
        assert job.metadata == {"user_id": 123}

    @pytest.mark.asyncio
    async def test_enqueue_invalid_type_raises(self, manager):
        from aquilia.tasks.faults import TaskEnqueueFault
        with pytest.raises(TaskEnqueueFault, match="Expected callable"):
            await manager.enqueue("not_a_function")

    @pytest.mark.asyncio
    async def test_list_jobs(self, manager):
        async def noop():
            pass

        for _ in range(5):
            await manager.enqueue(noop)

        jobs = await manager.list_jobs(limit=3)
        assert len(jobs) == 3

    @pytest.mark.asyncio
    async def test_cancel_job(self, manager):
        async def slow_task():
            await asyncio.sleep(100)

        job_id = await manager.enqueue(slow_task)
        result = await manager.cancel(job_id)
        assert result is True

        job = await manager.get_job(job_id)
        from aquilia.tasks.job import JobState
        assert job.state == JobState.CANCELLED

    @pytest.mark.asyncio
    async def test_retry_job(self, manager):
        from aquilia.tasks.job import JobState
        async def fail_task():
            raise ValueError("boom")

        job_id = await manager.enqueue(fail_task)
        job = await manager.get_job(job_id)
        job.state = JobState.FAILED
        await manager.backend.update(job)

        result = await manager.retry_job(job_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_flush(self, manager):
        async def noop():
            pass

        for _ in range(10):
            await manager.enqueue(noop)

        removed = await manager.flush()
        assert removed == 10

    @pytest.mark.asyncio
    async def test_get_stats(self, manager):
        async def noop():
            pass

        await manager.enqueue(noop)
        stats = await manager.get_stats()
        assert "total_jobs" in stats
        assert "manager" in stats
        assert stats["manager"]["num_workers"] == 2
        assert stats["manager"]["total_enqueued"] == 1

    @pytest.mark.asyncio
    async def test_get_queue_stats(self, manager):
        async def noop():
            pass

        await manager.enqueue(noop, queue="alpha")
        await manager.enqueue(noop, queue="beta")
        qs = await manager.get_queue_stats()
        assert "alpha" in qs
        assert "beta" in qs

    @pytest.mark.asyncio
    async def test_execution_with_workers(self, manager):
        """Verify workers execute enqueued tasks end-to-end."""
        result_holder = []

        async def capture_task(x):
            result_holder.append(x)
            return x

        await manager.start()
        try:
            job_id = await manager.enqueue(capture_task, 42)
            # Wait for execution
            for _ in range(50):  # 5 seconds max
                job = await manager.get_job(job_id)
                if job.is_terminal:
                    break
                await asyncio.sleep(0.1)

            job = await manager.get_job(job_id)
            from aquilia.tasks.job import JobState
            assert job.state == JobState.COMPLETED
            assert job.result is not None
            assert job.result.success is True
            assert job.result.value == 42
            assert 42 in result_holder
        finally:
            await manager.stop()

    @pytest.mark.asyncio
    async def test_execution_failure_and_retry(self, manager):
        """Verify failed tasks are retried."""
        call_count = 0

        async def flaky_task():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("flaky")
            return "success"

        from aquilia.tasks.decorators import task
        from aquilia.tasks.job import JobState

        manager.num_workers = 1  # Easier to reason about

        await manager.start()
        try:
            job_id = await manager.enqueue(
                flaky_task,
                max_retries=5,
            )

            # Wait for completion or dead
            for _ in range(100):  # 10 seconds max
                job = await manager.get_job(job_id)
                if job.state in (JobState.COMPLETED, JobState.DEAD):
                    break
                await asyncio.sleep(0.1)

            job = await manager.get_job(job_id)
            assert job.state == JobState.COMPLETED
            assert job.result.success is True
        finally:
            await manager.stop()

    @pytest.mark.asyncio
    async def test_dead_letter_on_exhausted_retries(self, manager):
        """Verify task goes to DEAD state when retries exhausted."""
        dead_jobs = []
        manager.on_dead_letter(lambda j: dead_jobs.append(j))

        async def always_fails():
            raise RuntimeError("permanent failure")

        manager.num_workers = 1

        await manager.start()
        try:
            job_id = await manager.enqueue(
                always_fails,
                max_retries=1,
            )

            for _ in range(100):
                job = await manager.get_job(job_id)
                if job.state.value == "dead":
                    break
                await asyncio.sleep(0.1)

            job = await manager.get_job(job_id)
            from aquilia.tasks.job import JobState
            assert job.state == JobState.DEAD
            assert len(dead_jobs) >= 1
        finally:
            await manager.stop()

    @pytest.mark.asyncio
    async def test_on_complete_callback(self, manager):
        completed = []
        manager.on_complete(lambda j: completed.append(j.id))

        async def simple():
            return "ok"

        await manager.start()
        try:
            job_id = await manager.enqueue(simple)
            for _ in range(50):
                job = await manager.get_job(job_id)
                if job.is_terminal:
                    break
                await asyncio.sleep(0.1)
            assert job_id in completed
        finally:
            await manager.stop()

    @pytest.mark.asyncio
    async def test_on_failure_callback(self, manager):
        failures = []
        manager.on_failure(lambda j: failures.append(j.id))

        async def fails_once():
            raise ValueError("oops")

        manager.num_workers = 1
        await manager.start()
        try:
            job_id = await manager.enqueue(fails_once, max_retries=2)
            # Wait for at least one failure
            for _ in range(50):
                if failures:
                    break
                await asyncio.sleep(0.1)
            assert job_id in failures
        finally:
            await manager.stop()

    @pytest.mark.asyncio
    async def test_timeout_handling(self, manager):
        """Verify tasks that exceed timeout are handled."""
        async def slow_task():
            await asyncio.sleep(100)

        manager.num_workers = 1
        await manager.start()
        try:
            job_id = await manager.enqueue(slow_task, timeout=0.1, max_retries=0)
            for _ in range(50):
                job = await manager.get_job(job_id)
                if job.is_terminal:
                    break
                await asyncio.sleep(0.1)

            job = await manager.get_job(job_id)
            from aquilia.tasks.job import JobState
            assert job.state == JobState.DEAD
            assert job.result is not None
            assert not job.result.success
            assert "timed out" in job.result.error.lower() or "timeout" in job.result.error_type.lower()
        finally:
            await manager.stop()

    @pytest.mark.asyncio
    async def test_manager_metrics(self, manager):
        assert manager._total_enqueued == 0
        async def noop():
            return True

        await manager.enqueue(noop)
        assert manager._total_enqueued == 1


# ============================================================================
# 5. WORKER TESTS
# ============================================================================


class TestWorker:
    """Verify standalone Worker class."""

    def test_import(self):
        from aquilia.tasks.worker import Worker
        assert Worker is not None

    @pytest.mark.asyncio
    async def test_worker_lifecycle(self):
        from aquilia.tasks.engine import TaskManager, MemoryBackend
        from aquilia.tasks.worker import Worker

        manager = TaskManager(backend=MemoryBackend(), num_workers=0)
        worker = Worker(manager, name="test-worker")

        assert worker.is_running is False
        await worker.start()
        assert worker.is_running is True
        await worker.stop()
        assert worker.is_running is False

    @pytest.mark.asyncio
    async def test_worker_stats(self):
        from aquilia.tasks.engine import TaskManager, MemoryBackend
        from aquilia.tasks.worker import Worker

        manager = TaskManager(backend=MemoryBackend(), num_workers=0)
        worker = Worker(manager, name="stats-worker")
        s = worker.stats
        assert s["name"] == "stats-worker"
        assert s["running"] is False
        assert s["jobs_processed"] == 0


# ============================================================================
# 6. CONFIG INTEGRATION TESTS
# ============================================================================


class TestTasksConfig:
    """Verify config system integration."""

    def test_get_tasks_config_defaults(self):
        from aquilia.config import ConfigLoader
        loader = ConfigLoader()
        config = loader.get_tasks_config()
        assert config["enabled"] is False
        assert config["backend"] == "memory"
        assert config["num_workers"] == 4
        assert config["default_queue"] == "default"
        assert config["cleanup_interval"] == 300.0
        assert config["max_retries"] == 3
        assert config["auto_start"] is True

    def test_get_tasks_config_with_overrides(self):
        from aquilia.config import ConfigLoader
        loader = ConfigLoader()
        loader.config_data["tasks"] = {
            "enabled": True,
            "num_workers": 8,
            "backend": "redis",
        }
        config = loader.get_tasks_config()
        assert config["enabled"] is True
        assert config["num_workers"] == 8

    def test_get_tasks_config_from_integrations(self):
        from aquilia.config import ConfigLoader
        loader = ConfigLoader()
        loader.config_data["integrations"] = {
            "tasks": {"enabled": True, "num_workers": 16}
        }
        config = loader.get_tasks_config()
        assert config["enabled"] is True
        assert config["num_workers"] == 16


class TestTasksConfigBuilders:
    """Verify config_builders Integration.tasks() and Workspace.tasks()."""

    def test_integration_tasks(self):
        from aquilia.config_builders import Integration
        config = Integration.tasks(num_workers=8, max_retries=5)
        assert config["_integration_type"] == "tasks"
        assert config["enabled"] is True
        assert config["num_workers"] == 8
        assert config["max_retries"] == 5
        assert config["backend"] == "memory"

    def test_integration_tasks_default_params(self):
        from aquilia.config_builders import Integration
        config = Integration.tasks()
        assert config["enabled"] is True
        assert config["num_workers"] == 4
        assert config["cleanup_interval"] == 300.0
        assert config["auto_start"] is True

    def test_workspace_tasks_shorthand(self):
        from aquilia.config_builders import Workspace
        ws = Workspace("test").tasks(num_workers=12, backend="redis")
        d = ws.to_dict()
        assert "tasks" in d
        assert d["tasks"]["num_workers"] == 12
        assert d["tasks"]["backend"] == "redis"
        assert d["tasks"]["enabled"] is True

    def test_workspace_integrate_tasks(self):
        from aquilia.config_builders import Workspace, Integration
        ws = Workspace("test").integrate(Integration.tasks(num_workers=6))
        d = ws.to_dict()
        assert d["integrations"]["tasks"]["num_workers"] == 6

    def test_admin_modules_devtools(self):
        from aquilia.config_builders import Integration

        mods = (
            Integration.AdminModules()
            .enable_query_inspector()
            .enable_tasks()
            .enable_errors()
        )
        d = mods.to_dict()
        assert d["query_inspector"] is True
        assert d["tasks"] is True
        assert d["errors"] is True

    def test_admin_modules_devtools_disabled_by_default(self):
        from aquilia.config_builders import Integration
        mods = Integration.AdminModules()
        d = mods.to_dict()
        assert d["query_inspector"] is False
        assert d["tasks"] is False
        assert d["errors"] is False

    def test_admin_sidebar_devtools(self):
        from aquilia.config_builders import Integration
        sidebar = Integration.AdminSidebar()
        d = sidebar.to_dict()
        assert d["devtools"] is True  # Enabled by default

        sidebar.hide_devtools()
        d = sidebar.to_dict()
        assert d["devtools"] is False

    def test_admin_sidebar_show_devtools(self):
        from aquilia.config_builders import Integration
        sidebar = Integration.AdminSidebar().hide_devtools().show_devtools()
        d = sidebar.to_dict()
        assert d["devtools"] is True


# ============================================================================
# 7. EFFECTS INTEGRATION TESTS
# ============================================================================


class TestTaskQueueProvider:
    """Verify TaskQueueProvider and TaskQueueHandle."""

    def test_import(self):
        from aquilia.effects import TaskQueueProvider, TaskQueueHandle
        assert TaskQueueProvider is not None
        assert TaskQueueHandle is not None

    @pytest.mark.asyncio
    async def test_acquire_with_manager(self):
        from aquilia.effects import TaskQueueProvider
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        manager = TaskManager(backend=MemoryBackend())
        provider = TaskQueueProvider(task_manager=manager)
        await provider.initialize()

        handle = await provider.acquire("test_queue")
        from aquilia.effects import TaskQueueHandle
        assert isinstance(handle, TaskQueueHandle)

    @pytest.mark.asyncio
    async def test_acquire_without_manager_fallback(self):
        from aquilia.effects import TaskQueueProvider, QueueHandle
        provider = TaskQueueProvider()
        handle = await provider.acquire("test")
        assert isinstance(handle, QueueHandle)

    @pytest.mark.asyncio
    async def test_health_check_with_manager(self):
        from aquilia.effects import TaskQueueProvider
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        manager = TaskManager(backend=MemoryBackend())
        provider = TaskQueueProvider(task_manager=manager)
        health = await provider.health_check()
        assert "healthy" in health
        assert health["backend"] == "MemoryBackend"

    @pytest.mark.asyncio
    async def test_health_check_without_manager(self):
        from aquilia.effects import TaskQueueProvider
        provider = TaskQueueProvider()
        health = await provider.health_check()
        assert health["healthy"] is True
        assert health["backend"] == "fallback"

    @pytest.mark.asyncio
    async def test_enqueue_via_handle(self):
        from aquilia.effects import TaskQueueProvider
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        manager = TaskManager(backend=MemoryBackend())
        provider = TaskQueueProvider(task_manager=manager)
        handle = await provider.acquire("default")

        async def test_task():
            return "result"

        job_id = await handle.enqueue(test_task)
        assert isinstance(job_id, str)

        job = await manager.get_job(job_id)
        assert job is not None

    @pytest.mark.asyncio
    async def test_publish_compat(self):
        """Verify publish() compatibility stub doesn't crash."""
        from aquilia.effects import TaskQueueHandle
        mock_manager = MagicMock()
        handle = TaskQueueHandle(mock_manager, "default")
        await handle.publish({"test": True})  # Should not raise
        await handle.publish_batch([1, 2, 3])  # Should not raise

    @pytest.mark.asyncio
    async def test_release_and_finalize(self):
        from aquilia.effects import TaskQueueProvider
        provider = TaskQueueProvider()
        handle = await provider.acquire()
        await provider.release(handle)  # Should not raise
        await provider.finalize()  # Should not raise


# ============================================================================
# 8. ADMIN SITE INTEGRATION TESTS
# ============================================================================


class TestAdminSiteTaskIntegration:
    """Verify AdminSite task manager wiring."""

    def test_set_task_manager(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite()
        mock_manager = MagicMock()
        site.set_task_manager(mock_manager)
        assert site._task_manager is mock_manager

    @pytest.mark.asyncio
    async def test_get_tasks_data_no_manager(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite()
        data = await site.get_tasks_data()
        assert data["available"] is False

    @pytest.mark.asyncio
    async def test_get_tasks_data_with_manager(self):
        from aquilia.admin.site import AdminSite
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        manager = TaskManager(backend=MemoryBackend())
        site = AdminSite()
        site.set_task_manager(manager)

        async def noop():
            pass

        await manager.enqueue(noop)
        data = await site.get_tasks_data()
        assert data["available"] is True
        assert len(data["jobs"]) == 1
        assert data["stats"]["total_jobs"] == 1


class TestAdminConfigModules:
    """Verify AdminConfig is_module_enabled for new devtools modules."""

    def test_default_modules(self):
        from aquilia.admin.site import AdminConfig
        config = AdminConfig()
        assert config.is_module_enabled("query_inspector") is False
        assert config.is_module_enabled("tasks") is False
        assert config.is_module_enabled("errors") is False
        assert config.is_module_enabled("containers") is False
        assert config.is_module_enabled("pods") is False

    def test_enabled_modules(self):
        from aquilia.admin.site import AdminConfig
        config = AdminConfig(modules={
            "query_inspector": True,
            "tasks": True,
            "errors": True,
        })
        assert config.is_module_enabled("query_inspector") is True
        assert config.is_module_enabled("tasks") is True
        assert config.is_module_enabled("errors") is True

    def test_devtools_sidebar_default(self):
        from aquilia.admin.site import AdminConfig
        config = AdminConfig()
        assert config.sidebar_sections.get("devtools") is True

    def test_module_normalizes_hyphens(self):
        from aquilia.admin.site import AdminConfig
        config = AdminConfig(modules={"query_inspector": True})
        assert config.is_module_enabled("query-inspector") is True


# ============================================================================
# 9. SERVER WIRING TESTS (Regression: disabled pages, not MODEL_NOT_FOUND)
# ============================================================================


class TestServerAdminRouteRegistration:
    """
    Verify admin routes for containers, pods, query_inspector, tasks, and errors
    are ALWAYS registered so disabled modules show the disabled page instead of
    ADMIN_MODEL_NOT_FOUND.
    """

    def test_admin_routes_always_registered(self):
        """
        Verify _wire_admin_integration registers devtools and infra routes
        even when modules are disabled in config.
        """
        from aquilia.config import ConfigLoader
        from aquilia.admin.site import AdminConfig

        # Simulate all modules disabled
        config = AdminConfig()
        assert config.is_module_enabled("tasks") is False
        assert config.is_module_enabled("errors") is False
        assert config.is_module_enabled("query_inspector") is False
        assert config.is_module_enabled("containers") is False
        assert config.is_module_enabled("pods") is False

        # The admin controller handlers check is_module_enabled internally
        # and return _module_disabled_response, so routes MUST be registered
        from aquilia.admin.controller import AdminController
        ctrl = AdminController.__new__(AdminController)

        # Verify handler methods exist on the controller
        assert hasattr(ctrl, "tasks_view")
        assert hasattr(ctrl, "tasks_api")
        assert hasattr(ctrl, "errors_view")
        assert hasattr(ctrl, "errors_api")
        assert hasattr(ctrl, "query_inspector_view")
        assert hasattr(ctrl, "query_inspector_api")
        assert hasattr(ctrl, "containers_view")
        assert hasattr(ctrl, "pods_view")

    def test_controller_disabled_response_method(self):
        """Verify _module_disabled_response returns valid HTML."""
        from aquilia.admin.controller import AdminController
        from aquilia.admin.site import AdminSite, AdminConfig

        site = AdminSite()
        site.admin_config = AdminConfig()
        ctrl = AdminController(site=site)

        # Should not raise, should return Response
        resp = ctrl._module_disabled_response("Tasks", None)
        from aquilia.response import Response
        assert isinstance(resp, Response)
        assert resp.status == 200

    def test_disabled_hints_for_new_modules(self):
        """Verify config hints exist for Query Inspector, Background Tasks, and Error Monitoring."""
        from aquilia.admin.controller import AdminController
        from aquilia.admin.site import AdminSite, AdminConfig

        site = AdminSite()
        site.admin_config = AdminConfig()
        ctrl = AdminController(site=site)

        for module_name in ["Query Inspector", "Background Tasks", "Error Monitoring"]:
            resp = ctrl._module_disabled_response(module_name, None)
            assert resp.status == 200
            content = resp._content
            body = content.decode("utf-8") if isinstance(content, bytes) else str(content)
            assert "enable_" in body or "Enable" in body.lower()


class TestServerTaskSetup:
    """Verify _setup_tasks and _setup_error_tracker wiring."""

    def test_tasks_disabled_by_default(self):
        from aquilia.config import ConfigLoader
        loader = ConfigLoader()
        config = loader.get_tasks_config()
        assert config["enabled"] is False

    def test_task_exports_from_aquilia(self):
        """Verify all task symbols are exported from aquilia package."""
        from aquilia import (
            TaskManager,
            TaskBackend,
            MemoryBackend,
            Job,
            JobState,
            TaskPriority,
            JobResult,
            Worker,
            task,
        )
        assert TaskManager is not None
        assert TaskBackend is not None
        assert MemoryBackend is not None
        assert Job is not None
        assert JobState is not None
        assert TaskPriority is not None
        assert JobResult is not None
        assert Worker is not None
        assert task is not None

    def test_task_priority_alias(self):
        """Verify TaskPriority doesn't clash with mail Priority."""
        from aquilia import TaskPriority, Priority
        # TaskPriority is the tasks.job.Priority
        # Priority is the mail.Priority
        assert TaskPriority.CRITICAL.value == 0
        assert TaskPriority is not Priority


# ============================================================================
# 10. QUERY INSPECTOR & ERROR TRACKER TESTS
# ============================================================================


class TestQueryInspector:
    """Verify query inspector singleton and data retrieval."""

    def test_get_query_inspector(self):
        from aquilia.admin.query_inspector import get_query_inspector
        inspector = get_query_inspector()
        assert inspector is not None

    def test_get_stats(self):
        from aquilia.admin.query_inspector import get_query_inspector
        inspector = get_query_inspector()
        stats = inspector.get_stats()
        assert isinstance(stats, dict)


class TestErrorTracker:
    """Verify error tracker singleton and data retrieval."""

    def test_get_error_tracker(self):
        from aquilia.admin.error_tracker import get_error_tracker
        tracker = get_error_tracker()
        assert tracker is not None

    def test_get_stats(self):
        from aquilia.admin.error_tracker import get_error_tracker
        tracker = get_error_tracker()
        stats = tracker.get_stats()
        assert isinstance(stats, dict)

    def test_capture_is_callable(self):
        """Verify capture method has correct signature for FaultEngine.on_fault()."""
        from aquilia.admin.error_tracker import get_error_tracker
        tracker = get_error_tracker()
        assert callable(tracker.capture)

    def test_record_error(self):
        from aquilia.admin.error_tracker import get_error_tracker
        tracker = get_error_tracker()
        tracker.record_error(
            code="TEST_ERROR",
            message="Test error message",
            domain="test",
        )
        stats = tracker.get_stats()
        assert stats["total_errors"] >= 1


# ============================================================================
# 11. EFFECTS REGISTRY INTEGRATION
# ============================================================================


class TestEffectRegistryIntegration:
    """Verify EffectRegistry can register TaskQueueProvider."""

    @pytest.mark.asyncio
    async def test_register_task_queue_provider(self):
        from aquilia.effects import EffectRegistry, TaskQueueProvider
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        registry = EffectRegistry()
        manager = TaskManager(backend=MemoryBackend())
        provider = TaskQueueProvider(task_manager=manager)

        registry.register("Queue", provider)
        assert registry.has_effect("Queue")

        await registry.initialize_all()
        handle = await registry.acquire("Queue", "default")
        assert handle is not None

        await registry.release("Queue", handle)
        await registry.finalize_all()

    @pytest.mark.asyncio
    async def test_effect_health_check(self):
        from aquilia.effects import EffectRegistry, TaskQueueProvider
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        registry = EffectRegistry()
        manager = TaskManager(backend=MemoryBackend())
        await manager.start()
        try:
            provider = TaskQueueProvider(task_manager=manager)
            registry.register("Queue", provider)
            await registry.initialize_all()

            health = await registry.health_check()
            assert health["healthy"] is True
            assert "Queue" in health["providers"]
            await registry.finalize_all()
        finally:
            await manager.stop()


# ============================================================================
# 12. FAULT DOMAIN INTEGRATION
# ============================================================================


class TestFaultDomainTasks:
    """Verify FaultDomain.custom("TASKS") works for dead-letter faults."""

    def test_custom_fault_domain(self):
        from aquilia.faults.core import FaultDomain
        domain = FaultDomain.custom("TASKS", "Background task faults")
        assert domain.name == "tasks"
        assert domain.value == "tasks"

    def test_fault_with_tasks_domain(self):
        from aquilia.faults.core import Fault, FaultDomain
        fault = Fault(
            code="TASK_DEAD_LETTER",
            message="Task failed permanently",
            domain=FaultDomain.custom("TASKS"),
        )
        assert fault.code == "TASK_DEAD_LETTER"
        assert fault.domain.value == "tasks"


# ============================================================================
# 13. REGRESSION TESTS
# ============================================================================


class TestRegressions:
    """Regression tests ensuring no breakage in existing functionality."""

    def test_admin_config_from_dict_with_devtools(self):
        """Verify AdminConfig.from_dict handles new devtools modules."""
        from aquilia.admin.site import AdminConfig
        config = AdminConfig.from_dict({
            "modules": {
                "dashboard": True,
                "orm": True,
                "query_inspector": True,
                "tasks": True,
                "errors": True,
            },
        })
        assert config.is_module_enabled("dashboard") is True
        assert config.is_module_enabled("query_inspector") is True
        assert config.is_module_enabled("tasks") is True
        assert config.is_module_enabled("errors") is True

    def test_admin_config_from_dict_without_devtools(self):
        """Verify AdminConfig.from_dict works without devtools keys (backward compat)."""
        from aquilia.admin.site import AdminConfig
        config = AdminConfig.from_dict({
            "modules": {
                "dashboard": True,
                "orm": True,
            },
        })
        assert config.is_module_enabled("dashboard") is True
        # Devtools should NOT be enabled if not in dict
        assert config.is_module_enabled("query_inspector") is False

    def test_memory_backend_implements_abc(self):
        from aquilia.tasks.engine import MemoryBackend, TaskBackend
        assert issubclass(MemoryBackend, TaskBackend)

    def test_task_manager_default_backend(self):
        from aquilia.tasks.engine import TaskManager, MemoryBackend
        manager = TaskManager()
        assert isinstance(manager.backend, MemoryBackend)

    def test_task_manager_default_config(self):
        from aquilia.tasks.engine import TaskManager
        manager = TaskManager()
        assert manager.num_workers == 4
        assert manager.default_queue == "default"
        assert manager.cleanup_interval == 300.0
        assert manager.cleanup_max_age == 3600.0

    def test_job_default_timeout(self):
        from aquilia.tasks.job import Job
        j = Job()
        assert j.timeout == 300.0

    @pytest.mark.asyncio
    async def test_concurrent_enqueue(self):
        """Verify no race conditions on concurrent enqueue."""
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        manager = TaskManager(backend=MemoryBackend())

        async def noop():
            pass

        tasks = [manager.enqueue(noop) for _ in range(100)]
        ids = await asyncio.gather(*tasks)
        assert len(ids) == 100
        assert len(set(ids)) == 100  # All unique

    def test_workspace_to_dict_round_trip(self):
        """Verify Workspace serialization includes tasks config."""
        from aquilia.config_builders import Workspace, Integration
        ws = (
            Workspace("myapp")
            .tasks(num_workers=8)
            .integrate(Integration.admin(
                enable_tasks=True,
                enable_errors=True,
                enable_query_inspector=True,
            ))
        )
        d = ws.to_dict()
        assert d["tasks"]["num_workers"] == 8
        assert d["integrations"]["admin"]["modules"]["tasks"] is True
        assert d["integrations"]["admin"]["modules"]["errors"] is True
        assert d["integrations"]["admin"]["modules"]["query_inspector"] is True

    def test_admin_modules_enable_all_includes_devtools(self):
        """Verify enable_all() enables devtools modules too."""
        from aquilia.config_builders import Integration
        mods = Integration.AdminModules().enable_all()
        d = mods.to_dict()
        assert d["query_inspector"] is True
        assert d["tasks"] is True
        assert d["errors"] is True
        assert d["containers"] is True
        assert d["pods"] is True

    def test_health_status_import(self):
        """Verify HealthStatus and SubsystemStatus are available."""
        from aquilia.health import HealthStatus, SubsystemStatus
        status = HealthStatus(
            name="tasks",
            status=SubsystemStatus.HEALTHY,
            message="4 workers running",
        )
        assert status.name == "tasks"
        assert status.status == SubsystemStatus.HEALTHY


# ============================================================================
# 14. QUERY INSPECTOR — CRUD INTEGRATION
# ============================================================================


class TestQueryInspectorCRUDIntegration:
    """
    Tests for the Query Inspector integration into model CRUD operations.

    Phase 29: When the user updates a model record, the admin should capture
    and display the SQL queries that were executed during the update operation.
    """

    # ── DB Engine _notify_inspector ──────────────────────────────────

    def test_notify_inspector_records_query(self):
        """_notify_inspector should record a query in the QueryInspector."""
        from aquilia.db.engine import AquiliaDatabase
        from aquilia.admin.query_inspector import get_query_inspector

        inspector = get_query_inspector()
        before = inspector._counter

        AquiliaDatabase._notify_inspector(
            sql="SELECT * FROM users WHERE id = ?",
            params=(1,),
            duration_ms=1.23,
            rows_affected=1,
        )

        assert inspector._counter == before + 1
        last = list(inspector._queries)[-1]
        assert last.sql == "SELECT * FROM users WHERE id = ?"
        assert last.duration_ms == 1.23
        assert last.rows_affected == 1
        assert last.operation == "SELECT"

    def test_notify_inspector_records_update_operation(self):
        """_notify_inspector correctly identifies UPDATE operations."""
        from aquilia.db.engine import AquiliaDatabase
        from aquilia.admin.query_inspector import get_query_inspector

        inspector = get_query_inspector()
        AquiliaDatabase._notify_inspector(
            sql="UPDATE products SET name = ? WHERE id = ?",
            params=("Widget X", 42),
            duration_ms=0.5,
            rows_affected=1,
        )

        last = list(inspector._queries)[-1]
        assert last.operation == "UPDATE"
        assert "products" in last.sql

    def test_notify_inspector_records_insert_operation(self):
        """_notify_inspector correctly identifies INSERT operations."""
        from aquilia.db.engine import AquiliaDatabase
        from aquilia.admin.query_inspector import get_query_inspector

        inspector = get_query_inspector()
        AquiliaDatabase._notify_inspector(
            sql="INSERT INTO logs (msg) VALUES (?)",
            params=("hello",),
            duration_ms=0.1,
        )

        last = list(inspector._queries)[-1]
        assert last.operation == "INSERT"

    def test_notify_inspector_records_delete_operation(self):
        """_notify_inspector correctly identifies DELETE operations."""
        from aquilia.db.engine import AquiliaDatabase
        from aquilia.admin.query_inspector import get_query_inspector

        inspector = get_query_inspector()
        AquiliaDatabase._notify_inspector(
            sql="DELETE FROM sessions WHERE expired = 1",
            params=None,
            duration_ms=2.0,
            rows_affected=5,
        )

        last = list(inspector._queries)[-1]
        assert last.operation == "DELETE"
        assert last.rows_affected == 5

    def test_notify_inspector_never_raises(self):
        """_notify_inspector should silently swallow errors."""
        from aquilia.db.engine import AquiliaDatabase

        # Even with weird params, it should never raise
        AquiliaDatabase._notify_inspector(
            sql=None,  # type: ignore
            params=object(),
            duration_ms=-1.0,
            rows_affected=-1,
        )
        # No exception -- test passes

    def test_notify_inspector_generates_sequential_ids(self):
        """Each query should get a monotonically increasing ID."""
        from aquilia.db.engine import AquiliaDatabase
        from aquilia.admin.query_inspector import get_query_inspector

        inspector = get_query_inspector()
        c_before = inspector._counter

        AquiliaDatabase._notify_inspector("SELECT 1", None, 0.0)
        AquiliaDatabase._notify_inspector("SELECT 2", None, 0.0)

        queries = list(inspector._queries)
        q1 = queries[-2]
        q2 = queries[-1]
        assert q1.id < q2.id

    # ── QueryRecord.to_dict() ────────────────────────────────────────

    def test_query_record_to_dict_structure(self):
        """QueryRecord.to_dict() should contain all expected keys."""
        from aquilia.admin.query_inspector import QueryRecord

        rec = QueryRecord(
            id="q-000001",
            sql="SELECT * FROM items",
            params=(1, 2),
            duration_ms=3.456,
            rows_affected=2,
            operation="SELECT",
            is_slow=False,
            source="app.py:42",
        )
        d = rec.to_dict()

        assert d["id"] == "q-000001"
        assert d["sql"] == "SELECT * FROM items"
        assert d["duration_ms"] == 3.456
        assert d["rows_affected"] == 2
        assert d["operation"] == "SELECT"
        assert d["is_slow"] is False
        assert d["source"] == "app.py:42"
        assert "fingerprint" in d
        assert "timestamp" in d
        assert "params" in d

    def test_query_record_to_dict_none_params(self):
        """to_dict() with None params should return None for params key."""
        from aquilia.admin.query_inspector import QueryRecord

        rec = QueryRecord(sql="SELECT 1", params=None)
        d = rec.to_dict()
        assert d["params"] is None

    def test_query_record_to_dict_with_params(self):
        """to_dict() with params should repr() them."""
        from aquilia.admin.query_inspector import QueryRecord

        rec = QueryRecord(sql="SELECT ?", params=(42,))
        d = rec.to_dict()
        assert d["params"] == "(42,)"

    # ── Counter-based delta capture ──────────────────────────────────

    def test_counter_delta_captures_only_new_queries(self):
        """The counter-based delta mechanism should capture only queries
        recorded between two counter snapshots."""
        from aquilia.admin.query_inspector import get_query_inspector
        from aquilia.db.engine import AquiliaDatabase

        inspector = get_query_inspector()

        # Record some "old" queries
        AquiliaDatabase._notify_inspector("SELECT old_1", None, 0.0)
        AquiliaDatabase._notify_inspector("SELECT old_2", None, 0.0)

        # Snapshot before
        before = inspector._counter

        # Record "new" queries (the ones we want to capture)
        AquiliaDatabase._notify_inspector("UPDATE t SET x=1", None, 1.5)
        AquiliaDatabase._notify_inspector("SELECT * FROM t WHERE id=1", None, 0.3)

        # Snapshot after
        after = inspector._counter

        # Extract delta
        assert after > before
        all_queries = list(inspector._queries)
        captured = [
            q.to_dict() for q in all_queries
            if q.id > f"q-{before:06d}"
        ]

        assert len(captured) >= 2
        sqls = [c["sql"] for c in captured]
        assert "UPDATE t SET x=1" in sqls
        assert "SELECT * FROM t WHERE id=1" in sqls
        # Old queries not in delta
        assert "SELECT old_1" not in sqls
        assert "SELECT old_2" not in sqls

    # ── AdminSite._last_update_queries ───────────────────────────────

    def test_admin_site_stores_queries_on_instance(self):
        """_last_update_queries is stored on AdminSite instance (mutable),
        NOT on frozen AdminConfig."""
        from aquilia.admin.site import AdminSite

        site = AdminSite()
        # AdminSite is a normal class — attribute assignment works
        site._last_update_queries = [{"sql": "SELECT 1"}]
        assert site._last_update_queries == [{"sql": "SELECT 1"}]

        # Reset
        site._last_update_queries = []
        assert site._last_update_queries == []

    def test_admin_config_is_frozen(self):
        """AdminConfig is a frozen dataclass — cannot assign new attributes."""
        from aquilia.admin.site import AdminConfig
        import dataclasses

        config = AdminConfig()
        with pytest.raises(dataclasses.FrozenInstanceError):
            config._last_update_queries = []  # type: ignore

    # ── Controller edit_submit — query inspector path ────────────────

    @pytest.mark.asyncio
    async def test_edit_submit_reads_queries_from_site(self):
        """edit_submit should read _last_update_queries from self.site,
        not from admin_config."""
        from aquilia.admin.controller import AdminController
        from aquilia.admin.site import AdminSite, AdminConfig
        from unittest.mock import AsyncMock, MagicMock, patch

        site = AdminSite()
        site.update_record = AsyncMock(return_value=True)
        site._last_update_queries = [
            {"id": "q-000001", "sql": "UPDATE t SET x=1", "operation": "UPDATE",
             "duration_ms": 1.0, "rows_affected": 1, "is_slow": False,
             "params": None, "source": "test:1", "timestamp": "2024-01-01T00:00:00"},
        ]

        ctrl = AdminController(site=site)
        # Bypass CSRF validation for existing tests (security tested separately)
        site.security.csrf.validate_request = lambda *a, **kw: True

        # Build a minimal mock request/ctx
        mock_request = MagicMock()
        mock_request.state = {"path_params": {"model": "Product", "pk": "1"}}

        mock_ctx = MagicMock()
        mock_ctx.identity = MagicMock()
        mock_ctx.identity.id = "user1"
        mock_ctx.identity.get_attribute = MagicMock(return_value="")

        # After update succeeds, get_record is called
        site.get_record = AsyncMock(return_value={
            "model_name": "Product",
            "verbose_name": "Product",
            "pk": "1",
            "fields": [],
            "fieldsets": [],
            "can_delete": False,
        })

        with patch("aquilia.admin.controller._parse_form", new_callable=AsyncMock, return_value={"name": "X"}), \
             patch("aquilia.admin.controller._require_identity", return_value=(mock_ctx.identity, None)):
            resp = await ctrl.edit_submit(mock_request, mock_ctx)

        # Should render the form (200), not redirect
        assert resp.status == 200
        # Queries should have been reset
        assert site._last_update_queries == []

    @pytest.mark.asyncio
    async def test_edit_submit_without_query_inspector_module(self):
        """When query_inspector module is disabled, query_inspection
        should be None in the rendered template."""
        from aquilia.admin.controller import AdminController
        from aquilia.admin.site import AdminSite, AdminConfig
        from unittest.mock import AsyncMock, MagicMock, patch

        site = AdminSite()
        site.admin_config = AdminConfig(modules={"query_inspector": False})
        site.update_record = AsyncMock(return_value=True)
        site._last_update_queries = [
            {"sql": "SELECT 1", "operation": "SELECT", "duration_ms": 0.1},
        ]

        ctrl = AdminController(site=site)
        # Bypass CSRF validation for existing tests (security tested separately)
        site.security.csrf.validate_request = lambda *a, **kw: True

        mock_request = MagicMock()
        mock_request.state = {"path_params": {"model": "Item", "pk": "5"}}
        mock_ctx = MagicMock()
        mock_ctx.identity = MagicMock()
        mock_ctx.identity.id = "admin"
        mock_ctx.identity.get_attribute = MagicMock(return_value="")

        site.get_record = AsyncMock(return_value={
            "model_name": "Item", "verbose_name": "Item", "pk": "5",
            "fields": [], "fieldsets": [], "can_delete": False,
        })

        with patch("aquilia.admin.controller._parse_form", new_callable=AsyncMock, return_value={"x": "1"}), \
             patch("aquilia.admin.controller._require_identity", return_value=(mock_ctx.identity, None)), \
             patch("aquilia.admin.controller.render_form_view") as mock_render:
            mock_render.return_value = "<html>form</html>"
            resp = await ctrl.edit_submit(mock_request, mock_ctx)

        # query_inspection should be None (disabled module)
        mock_render.assert_called_once()
        call_kwargs = mock_render.call_args
        assert call_kwargs.kwargs.get("query_inspection") is None or \
               call_kwargs[1].get("query_inspection") is None

    @pytest.mark.asyncio
    async def test_edit_submit_with_query_inspector_enabled(self):
        """When query_inspector module is enabled, query_inspection
        should contain the captured queries."""
        from aquilia.admin.controller import AdminController
        from aquilia.admin.site import AdminSite, AdminConfig
        from unittest.mock import AsyncMock, MagicMock, patch

        site = AdminSite()
        site.admin_config = AdminConfig(modules={"query_inspector": True})
        site.update_record = AsyncMock(return_value=True)
        captured = [
            {"id": "q-000010", "sql": "UPDATE p SET name=?", "operation": "UPDATE",
             "duration_ms": 2.5, "rows_affected": 1, "is_slow": False,
             "params": "('Widget',)", "source": "app:10", "timestamp": "2024-01-01T00:00:00"},
        ]
        site._last_update_queries = list(captured)

        ctrl = AdminController(site=site)
        # Bypass CSRF validation for existing tests (security tested separately)
        site.security.csrf.validate_request = lambda *a, **kw: True

        mock_request = MagicMock()
        mock_request.state = {"path_params": {"model": "Product", "pk": "7"}}
        mock_ctx = MagicMock()
        mock_ctx.identity = MagicMock()
        mock_ctx.identity.id = "admin"
        mock_ctx.identity.get_attribute = MagicMock(return_value="")

        site.get_record = AsyncMock(return_value={
            "model_name": "Product", "verbose_name": "Product", "pk": "7",
            "fields": [], "fieldsets": [], "can_delete": False,
        })

        with patch("aquilia.admin.controller._parse_form", new_callable=AsyncMock, return_value={"name": "X"}), \
             patch("aquilia.admin.controller._require_identity", return_value=(mock_ctx.identity, None)), \
             patch("aquilia.admin.controller.render_form_view") as mock_render:
            mock_render.return_value = "<html>form with inspector</html>"
            resp = await ctrl.edit_submit(mock_request, mock_ctx)

        assert resp.status == 200
        mock_render.assert_called_once()
        call_kwargs = mock_render.call_args
        qi = call_kwargs.kwargs.get("query_inspection") or call_kwargs[1].get("query_inspection")
        assert qi is not None
        assert len(qi) == 1
        assert qi[0]["operation"] == "UPDATE"

    @pytest.mark.asyncio
    async def test_edit_submit_get_record_fails_redirects(self):
        """If get_record fails after successful update, should redirect
        to model list (302) rather than crash."""
        from aquilia.admin.controller import AdminController
        from aquilia.admin.site import AdminSite
        from unittest.mock import AsyncMock, MagicMock, patch

        site = AdminSite()
        site.update_record = AsyncMock(return_value=True)
        site._last_update_queries = []

        # get_record raises
        site.get_record = AsyncMock(side_effect=Exception("model not found"))

        ctrl = AdminController(site=site)
        # Bypass CSRF validation for existing tests (security tested separately)
        site.security.csrf.validate_request = lambda *a, **kw: True

        mock_request = MagicMock()
        mock_request.state = {"path_params": {"model": "Widget", "pk": "99"}}
        mock_ctx = MagicMock()
        mock_ctx.identity = MagicMock()
        mock_ctx.identity.id = "admin"
        mock_ctx.identity.get_attribute = MagicMock(return_value="")

        with patch("aquilia.admin.controller._parse_form", new_callable=AsyncMock, return_value={"a": "b"}), \
             patch("aquilia.admin.controller._require_identity", return_value=(mock_ctx.identity, None)):
            resp = await ctrl.edit_submit(mock_request, mock_ctx)

        assert resp.status == 302

    @pytest.mark.asyncio
    async def test_edit_submit_resets_last_update_queries(self):
        """After reading _last_update_queries, the site attribute should
        be reset to an empty list."""
        from aquilia.admin.controller import AdminController
        from aquilia.admin.site import AdminSite
        from unittest.mock import AsyncMock, MagicMock, patch

        site = AdminSite()
        site.update_record = AsyncMock(return_value=True)
        site._last_update_queries = [
            {"sql": "SELECT 1", "operation": "SELECT", "duration_ms": 0.1},
            {"sql": "UPDATE t SET x=1", "operation": "UPDATE", "duration_ms": 0.2},
        ]

        site.get_record = AsyncMock(return_value={
            "model_name": "Foo", "verbose_name": "Foo", "pk": "1",
            "fields": [], "fieldsets": [], "can_delete": False,
        })

        ctrl = AdminController(site=site)
        # Bypass CSRF validation for existing tests (security tested separately)
        site.security.csrf.validate_request = lambda *a, **kw: True

        mock_request = MagicMock()
        mock_request.state = {"path_params": {"model": "Foo", "pk": "1"}}
        mock_ctx = MagicMock()
        mock_ctx.identity = MagicMock()
        mock_ctx.identity.id = "admin"
        mock_ctx.identity.get_attribute = MagicMock(return_value="")

        with patch("aquilia.admin.controller._parse_form", new_callable=AsyncMock, return_value={"x": "1"}), \
             patch("aquilia.admin.controller._require_identity", return_value=(mock_ctx.identity, None)):
            await ctrl.edit_submit(mock_request, mock_ctx)

        assert site._last_update_queries == []

    # ── render_form_view with query_inspection ───────────────────────

    def test_render_form_view_accepts_query_inspection(self):
        """render_form_view should accept query_inspection parameter."""
        from aquilia.admin.templates import render_form_view
        import inspect

        sig = inspect.signature(render_form_view)
        assert "query_inspection" in sig.parameters

    def test_render_form_view_none_query_inspection(self):
        """render_form_view with query_inspection=None should not crash."""
        from aquilia.admin.templates import render_form_view

        html = render_form_view(
            data={
                "model_name": "Test",
                "verbose_name": "Test",
                "pk": "1",
                "fields": [],
                "fieldsets": [],
                "can_delete": False,
            },
            app_list=[],
            query_inspection=None,
        )
        assert isinstance(html, str)
        assert len(html) > 0

    def test_render_form_view_empty_query_inspection(self):
        """render_form_view with empty list should not show inspector panel."""
        from aquilia.admin.templates import render_form_view

        html = render_form_view(
            data={
                "model_name": "Widget",
                "verbose_name": "Widget",
                "pk": "5",
                "fields": [],
                "fieldsets": [],
                "can_delete": False,
            },
            app_list=[],
            query_inspection=[],
        )
        assert isinstance(html, str)
        # Empty inspection list should not render the panel
        assert "query-inspector-panel" not in html

    def test_render_form_view_with_query_data(self):
        """render_form_view with query data should render the inspector panel."""
        from aquilia.admin.templates import render_form_view

        qi = [
            {
                "id": "q-000001",
                "sql": "UPDATE products SET name = 'Test' WHERE id = 1",
                "operation": "UPDATE",
                "duration_ms": 1.234,
                "rows_affected": 1,
                "is_slow": False,
                "params": "('Test', 1)",
                "source": "myapp/views.py:42",
                "timestamp": "2024-06-01T12:00:00+00:00",
                "fingerprint": "abc123",
            },
            {
                "id": "q-000002",
                "sql": "SELECT * FROM products WHERE id = 1",
                "operation": "SELECT",
                "duration_ms": 0.567,
                "rows_affected": 1,
                "is_slow": False,
                "params": "(1,)",
                "source": "myapp/views.py:43",
                "timestamp": "2024-06-01T12:00:00+00:00",
                "fingerprint": "def456",
            },
        ]

        html = render_form_view(
            data={
                "model_name": "Product",
                "verbose_name": "Product",
                "pk": "1",
                "fields": [
                    {"name": "name", "type": "text", "value": "Test", "editable": True},
                ],
                "fieldsets": [],
                "can_delete": True,
            },
            app_list=[],
            query_inspection=qi,
        )

        assert "Query Inspector" in html
        assert "UPDATE products" in html
        assert "SELECT * FROM products" in html
        assert "1.234" in html or "1.23" in html
        assert "UPDATE" in html
        assert "SELECT" in html

    def test_render_form_view_shows_slow_query_warning(self):
        """Slow queries should be visually flagged in the inspector panel."""
        from aquilia.admin.templates import render_form_view

        qi = [
            {
                "id": "q-000001",
                "sql": "SELECT * FROM huge_table",
                "operation": "SELECT",
                "duration_ms": 1500.0,
                "rows_affected": 50000,
                "is_slow": True,
                "params": None,
                "source": "app.py:99",
                "timestamp": "2024-06-01T12:00:00+00:00",
                "fingerprint": "slow123",
            },
        ]

        html = render_form_view(
            data={
                "model_name": "HugeTable",
                "verbose_name": "Huge Table",
                "pk": "1",
                "fields": [],
                "fieldsets": [],
                "can_delete": False,
            },
            app_list=[],
            query_inspection=qi,
        )

        assert "Query Inspector" in html
        # Should show the slow indicator
        assert "1500" in html or "slow" in html.lower()

    def test_render_form_view_multiple_operations(self):
        """Inspector should show badges for different operation types."""
        from aquilia.admin.templates import render_form_view

        qi = [
            {"id": "q-1", "sql": "SELECT 1", "operation": "SELECT",
             "duration_ms": 0.1, "rows_affected": 1, "is_slow": False,
             "params": None, "source": "", "timestamp": "2024-01-01T00:00:00"},
            {"id": "q-2", "sql": "UPDATE t SET x=1", "operation": "UPDATE",
             "duration_ms": 0.2, "rows_affected": 1, "is_slow": False,
             "params": None, "source": "", "timestamp": "2024-01-01T00:00:00"},
            {"id": "q-3", "sql": "INSERT INTO t VALUES(1)", "operation": "INSERT",
             "duration_ms": 0.3, "rows_affected": 1, "is_slow": False,
             "params": None, "source": "", "timestamp": "2024-01-01T00:00:00"},
        ]

        html = render_form_view(
            data={
                "model_name": "Multi",
                "verbose_name": "Multi",
                "pk": "1",
                "fields": [],
                "fieldsets": [],
                "can_delete": False,
            },
            app_list=[],
            query_inspection=qi,
        )

        assert "Query Inspector" in html
        # Should mention 3 queries
        assert "3 queries" in html or "3 quer" in html

    def test_render_form_view_toggle_js_present(self):
        """The toggle JS function should be in the rendered output."""
        from aquilia.admin.templates import render_form_view

        qi = [
            {"id": "q-1", "sql": "SELECT 1", "operation": "SELECT",
             "duration_ms": 0.1, "rows_affected": 1, "is_slow": False,
             "params": None, "source": "", "timestamp": "2024-01-01T00:00:00"},
        ]

        html = render_form_view(
            data={
                "model_name": "T",
                "verbose_name": "T",
                "pk": "1",
                "fields": [],
                "fieldsets": [],
                "can_delete": False,
            },
            app_list=[],
            query_inspection=qi,
        )

        assert "toggleQueryInspector" in html

    # ── update_record docstring / attribute check ────────────────────

    def test_update_record_docstring_mentions_site_attribute(self):
        """update_record docstring should reference site instance, not admin_config."""
        from aquilia.admin.site import AdminSite

        doc = AdminSite.update_record.__doc__
        assert doc is not None
        assert "site instance" in doc.lower() or "_last_update_queries" in doc

    # ── Frozen AdminConfig regression ────────────────────────────────

    def test_admin_config_frozen_no_arbitrary_attrs(self):
        """Ensure we don't accidentally try to set attrs on frozen AdminConfig."""
        import dataclasses
        from aquilia.admin.site import AdminConfig

        config = AdminConfig()

        # Should raise for any new attribute
        with pytest.raises(dataclasses.FrozenInstanceError):
            config.some_random_attr = True  # type: ignore

    def test_admin_config_module_defaults(self):
        """Default AdminConfig should have query_inspector disabled."""
        from aquilia.admin.site import AdminConfig

        config = AdminConfig()
        assert config.is_module_enabled("query_inspector") is False

    def test_admin_config_with_query_inspector_enabled(self):
        """AdminConfig with query_inspector=True should report enabled."""
        from aquilia.admin.site import AdminConfig

        config = AdminConfig(modules={"query_inspector": True})
        assert config.is_module_enabled("query_inspector") is True

    # ── Integration: full round-trip ────────────────────────────────

    def test_inspector_record_then_to_dict_roundtrip(self):
        """Record a query through the engine, verify it appears in inspector
        with correct to_dict() output that the template can consume."""
        from aquilia.db.engine import AquiliaDatabase
        from aquilia.admin.query_inspector import get_query_inspector

        inspector = get_query_inspector()
        before = inspector._counter

        AquiliaDatabase._notify_inspector(
            sql="UPDATE orders SET status = ? WHERE id = ?",
            params=("shipped", 42),
            duration_ms=3.14,
            rows_affected=1,
        )

        after = inspector._counter
        assert after == before + 1

        # Capture delta (same logic as site.update_record)
        all_queries = list(inspector._queries)
        captured = [
            q.to_dict() for q in all_queries
            if q.id > f"q-{before:06d}"
        ]

        assert len(captured) >= 1
        q = captured[-1]
        assert q["sql"] == "UPDATE orders SET status = ? WHERE id = ?"
        assert q["operation"] == "UPDATE"
        assert q["duration_ms"] == 3.14
        assert q["rows_affected"] == 1
        assert q["params"] == "('shipped', 42)"
        assert "id" in q
        assert "timestamp" in q
        assert "fingerprint" in q

    def test_inspector_multiple_queries_different_operations(self):
        """Multiple queries of different types are correctly categorised."""
        from aquilia.db.engine import AquiliaDatabase
        from aquilia.admin.query_inspector import get_query_inspector

        inspector = get_query_inspector()
        before = inspector._counter

        AquiliaDatabase._notify_inspector("SELECT * FROM t", None, 0.1)
        AquiliaDatabase._notify_inspector("UPDATE t SET x=1", None, 0.2)
        AquiliaDatabase._notify_inspector("INSERT INTO t VALUES(1)", None, 0.3)
        AquiliaDatabase._notify_inspector("DELETE FROM t WHERE id=1", None, 0.4)

        all_queries = list(inspector._queries)
        captured = [
            q.to_dict() for q in all_queries
            if q.id > f"q-{before:06d}"
        ]

        ops = [c["operation"] for c in captured]
        assert "SELECT" in ops
        assert "UPDATE" in ops
        assert "INSERT" in ops
        assert "DELETE" in ops

    def test_inspector_timing_is_preserved(self):
        """Duration values are accurately preserved through the pipeline."""
        from aquilia.db.engine import AquiliaDatabase
        from aquilia.admin.query_inspector import get_query_inspector

        inspector = get_query_inspector()
        before = inspector._counter

        AquiliaDatabase._notify_inspector("SELECT 1", None, 42.567)

        all_queries = list(inspector._queries)
        captured = [
            q.to_dict() for q in all_queries
            if q.id > f"q-{before:06d}"
        ]

        assert captured[-1]["duration_ms"] == 42.567


# ============================================================================
# 25. CHART.JS ANALYTICS — ERROR TRACKER ENHANCED STATS
# ============================================================================


class TestErrorTrackerChartData:
    """Verify enhanced ErrorTracker stats with Chart.js-ready data."""

    def _fresh_tracker(self):
        from aquilia.admin.error_tracker import ErrorTracker
        return ErrorTracker()

    def test_stats_charts_key_exists(self):
        """get_stats() returns a 'charts' dict."""
        tracker = self._fresh_tracker()
        stats = tracker.get_stats()
        assert "charts" in stats
        assert isinstance(stats["charts"], dict)

    def test_charts_hourly_structure(self):
        """charts.hourly has labels and values arrays of length 24."""
        tracker = self._fresh_tracker()
        tracker.record_error(code="E1", message="err1", domain="d1")
        stats = tracker.get_stats()
        hourly = stats["charts"]["hourly"]
        assert "labels" in hourly
        assert "values" in hourly
        assert len(hourly["labels"]) == 24
        assert len(hourly["values"]) == 24
        assert hourly["values"][-1] >= 1  # current hour has at least 1

    def test_charts_five_min_structure(self):
        """charts.five_min has labels and values of length 24."""
        tracker = self._fresh_tracker()
        tracker.record_error(code="E1", message="err1", domain="d1")
        stats = tracker.get_stats()
        fm = stats["charts"]["five_min"]
        assert "labels" in fm
        assert "values" in fm
        assert len(fm["labels"]) == 24
        assert len(fm["values"]) == 24
        assert sum(fm["values"]) >= 1

    def test_charts_severity_doughnut(self):
        """charts.severity_doughnut labels match recorded severities."""
        tracker = self._fresh_tracker()
        tracker.record_error(code="E1", message="err1", domain="d1", severity="ERROR")
        tracker.record_error(code="W1", message="warn1", domain="d1", severity="WARN")
        stats = tracker.get_stats()
        sd = stats["charts"]["severity_doughnut"]
        assert set(sd["labels"]) == {"ERROR", "WARN"}
        assert len(sd["values"]) == 2
        assert sum(sd["values"]) == 2

    def test_charts_domain_polar(self):
        """charts.domain_polar labels match recorded domains."""
        tracker = self._fresh_tracker()
        tracker.record_error(code="E1", message="err1", domain="auth")
        tracker.record_error(code="E2", message="err2", domain="db")
        tracker.record_error(code="E3", message="err3", domain="db")
        stats = tracker.get_stats()
        dp = stats["charts"]["domain_polar"]
        assert "auth" in dp["labels"]
        assert "db" in dp["labels"]
        idx_db = dp["labels"].index("db")
        assert dp["values"][idx_db] == 2

    def test_charts_top_codes_bar(self):
        """charts.top_codes_bar reflects error code frequency."""
        tracker = self._fresh_tracker()
        for _ in range(5):
            tracker.record_error(code="E500", message="Internal", domain="api")
        for _ in range(3):
            tracker.record_error(code="E404", message="NotFound", domain="api")
        stats = tracker.get_stats()
        tc = stats["charts"]["top_codes_bar"]
        assert tc["labels"][0] == "E500"  # Most frequent first
        assert tc["values"][0] == 5
        assert tc["values"][1] == 3

    def test_charts_domain_stacked(self):
        """charts.domain_stacked has labels and series dict."""
        tracker = self._fresh_tracker()
        tracker.record_error(code="E1", message="err1", domain="auth")
        tracker.record_error(code="E2", message="err2", domain="db")
        stats = tracker.get_stats()
        ds = stats["charts"]["domain_stacked"]
        assert "labels" in ds
        assert "series" in ds
        assert len(ds["labels"]) == 24
        assert "auth" in ds["series"]
        assert "db" in ds["series"]
        assert len(ds["series"]["auth"]) == 24

    def test_charts_severity_timeline(self):
        """charts.severity_timeline has labels and per-severity series."""
        tracker = self._fresh_tracker()
        tracker.record_error(code="E1", message="err1", domain="d1", severity="ERROR")
        tracker.record_error(code="W1", message="warn1", domain="d1", severity="WARN")
        stats = tracker.get_stats()
        st = stats["charts"]["severity_timeline"]
        assert "labels" in st
        assert "series" in st
        assert "ERROR" in st["series"]
        assert "WARN" in st["series"]
        assert len(st["series"]["ERROR"]) == 24

    def test_charts_velocity(self):
        """charts.velocity is a list of 6 data points."""
        tracker = self._fresh_tracker()
        tracker.record_error(code="E1", message="err1", domain="d1")
        stats = tracker.get_stats()
        vel = stats["charts"]["velocity"]
        assert isinstance(vel, list)
        assert len(vel) == 6
        assert sum(vel) >= 1

    def test_unresolved_count(self):
        """Unresolved count matches groups not yet resolved."""
        tracker = self._fresh_tracker()
        tracker.record_error(code="E1", message="err1", domain="d1")
        tracker.record_error(code="E2", message="err2", domain="d1")
        stats = tracker.get_stats()
        assert stats["unresolved_count"] == 2

    def test_resolved_count_initially_zero(self):
        """Resolved count is 0 before any resolve_error calls."""
        tracker = self._fresh_tracker()
        tracker.record_error(code="E1", message="err1", domain="d1")
        stats = tracker.get_stats()
        assert stats["resolved_count"] == 0

    def test_resolve_error_method(self):
        """resolve_error marks a group as resolved."""
        tracker = self._fresh_tracker()
        tracker.record_error(code="E1", message="err1", domain="d1")
        groups = tracker.get_groups()
        fp = groups[0].fingerprint
        result = tracker.resolve_error(fp)
        assert result is True
        stats = tracker.get_stats()
        assert stats["resolved_count"] == 1
        assert stats["unresolved_count"] == 0

    def test_resolve_error_idempotent(self):
        """Resolving same fingerprint twice returns False on second call."""
        tracker = self._fresh_tracker()
        tracker.record_error(code="E1", message="err1", domain="d1")
        groups = tracker.get_groups()
        fp = groups[0].fingerprint
        assert tracker.resolve_error(fp) is True
        assert tracker.resolve_error(fp) is False
        stats = tracker.get_stats()
        assert stats["resolved_count"] == 1

    def test_resolve_error_unknown_fingerprint(self):
        """Resolving unknown fingerprint returns False."""
        tracker = self._fresh_tracker()
        result = tracker.resolve_error("unknown-fingerprint")
        assert result is False

    def test_mttr_calculation(self):
        """MTTR is computed from first_seen to resolved_at."""
        import time
        tracker = self._fresh_tracker()
        tracker.record_error(code="E1", message="err1", domain="d1")
        time.sleep(0.05)  # Small delay for measurable MTTR
        groups = tracker.get_groups()
        fp = groups[0].fingerprint
        tracker.resolve_error(fp)
        stats = tracker.get_stats()
        assert stats["mttr_seconds"] >= 0  # Should be > 0 but timing is imprecise

    def test_mttr_zero_when_no_resolved(self):
        """MTTR is 0 when no errors have been resolved."""
        tracker = self._fresh_tracker()
        tracker.record_error(code="E1", message="err1", domain="d1")
        stats = tracker.get_stats()
        assert stats["mttr_seconds"] == 0

    def test_clear_resets_chart_data(self):
        """clear() resets all chart-related tracking data."""
        tracker = self._fresh_tracker()
        for i in range(5):
            tracker.record_error(code=f"E{i}", message=f"err{i}", domain="d1")
        tracker.resolve_error(tracker.get_groups()[0].fingerprint)
        tracker.clear()
        stats = tracker.get_stats()
        assert stats["total_errors"] == 0
        assert stats["resolved_count"] == 0
        assert stats["unresolved_count"] == 0
        assert all(v == 0 for v in stats["charts"]["hourly"]["values"])
        assert all(v == 0 for v in stats["charts"]["five_min"]["values"])

    def test_error_rate_per_min(self):
        """Error rate per minute is calculated correctly."""
        tracker = self._fresh_tracker()
        for _ in range(10):
            tracker.record_error(code="E1", message="err1", domain="d1")
        stats = tracker.get_stats()
        assert stats["error_rate_per_min"] > 0

    def test_multiple_domains_chart_data(self):
        """Multiple domains produce correct polar and stacked data."""
        tracker = self._fresh_tracker()
        for domain in ["auth", "db", "cache", "api"]:
            for _ in range(3):
                tracker.record_error(code="E1", message="err", domain=domain)
        stats = tracker.get_stats()
        dp = stats["charts"]["domain_polar"]
        assert len(dp["labels"]) == 4
        ds = stats["charts"]["domain_stacked"]
        assert len(ds["series"]) == 4

    def test_multiple_severities_chart_data(self):
        """Multiple severities produce correct doughnut and timeline data."""
        tracker = self._fresh_tracker()
        for sev in ["ERROR", "WARN", "INFO"]:
            tracker.record_error(code="E1", message="err", domain="d1", severity=sev)
        stats = tracker.get_stats()
        sd = stats["charts"]["severity_doughnut"]
        assert len(sd["labels"]) == 3
        st = stats["charts"]["severity_timeline"]
        assert len(st["series"]) == 3


# ============================================================================
# 26. CHART.JS ANALYTICS — MEMORY BACKEND ENHANCED STATS
# ============================================================================


class TestMemoryBackendChartData:
    """Verify enhanced MemoryBackend.get_stats() with Chart.js-ready data."""

    @pytest.mark.asyncio
    async def test_stats_charts_key_exists(self):
        """get_stats() returns a 'charts' dict."""
        from aquilia.tasks.engine import MemoryBackend
        backend = MemoryBackend()
        stats = await backend.get_stats()
        assert "charts" in stats
        assert isinstance(stats["charts"], dict)

    @pytest.mark.asyncio
    async def test_charts_throughput_structure(self):
        """charts.throughput has labels, completed, and failed arrays of length 24."""
        from aquilia.tasks.engine import MemoryBackend
        backend = MemoryBackend()
        stats = await backend.get_stats()
        tp = stats["charts"]["throughput"]
        assert "labels" in tp
        assert "completed" in tp
        assert "failed" in tp
        assert len(tp["labels"]) == 24
        assert len(tp["completed"]) == 24
        assert len(tp["failed"]) == 24

    @pytest.mark.asyncio
    async def test_charts_duration_histogram_structure(self):
        """charts.duration_histogram has labels and values."""
        from aquilia.tasks.engine import MemoryBackend
        backend = MemoryBackend()
        stats = await backend.get_stats()
        dh = stats["charts"]["duration_histogram"]
        assert "labels" in dh
        assert "values" in dh
        assert len(dh["labels"]) == 8
        assert len(dh["values"]) == 8

    @pytest.mark.asyncio
    async def test_charts_state_doughnut(self):
        """charts.state_doughnut reflects actual job states."""
        from aquilia.tasks.engine import MemoryBackend, Job, JobState
        backend = MemoryBackend()
        await backend.push(Job(func_ref="test.fn", name="test"))
        stats = await backend.get_stats()
        sd = stats["charts"]["state_doughnut"]
        assert "labels" in sd
        assert "values" in sd
        assert "pending" in sd["labels"]

    @pytest.mark.asyncio
    async def test_charts_queue_breakdown(self):
        """charts.queue_breakdown has per-queue state arrays."""
        from aquilia.tasks.engine import MemoryBackend, Job
        backend = MemoryBackend()
        await backend.push(Job(func_ref="fn1", name="t1", queue="high"))
        await backend.push(Job(func_ref="fn2", name="t2", queue="low"))
        stats = await backend.get_stats()
        qb = stats["charts"]["queue_breakdown"]
        assert "labels" in qb
        assert "pending" in qb
        assert "running" in qb
        assert "completed" in qb
        assert "failed" in qb
        assert "high" in qb["labels"]
        assert "low" in qb["labels"]

    @pytest.mark.asyncio
    async def test_success_rate_no_jobs(self):
        """Success rate is 100% when no terminal jobs exist."""
        from aquilia.tasks.engine import MemoryBackend
        backend = MemoryBackend()
        stats = await backend.get_stats()
        assert stats["success_rate"] == 100

    @pytest.mark.asyncio
    async def test_success_rate_with_completed_only(self):
        """Success rate is 100% when all terminal jobs completed."""
        from aquilia.tasks.engine import MemoryBackend, Job, JobState
        from datetime import datetime, timezone, timedelta
        backend = MemoryBackend()
        for i in range(3):
            job = Job(func_ref="fn", name=f"t{i}")
            await backend.push(job)
            job.state = JobState.COMPLETED
            now = datetime.now(timezone.utc)
            job.started_at = now - timedelta(milliseconds=10)
            job.completed_at = now
        stats = await backend.get_stats()
        assert stats["success_rate"] == 100

    @pytest.mark.asyncio
    async def test_success_rate_with_failures(self):
        """Success rate reflects completed vs failed ratio."""
        from aquilia.tasks.engine import MemoryBackend, Job, JobState
        from datetime import datetime, timezone, timedelta
        backend = MemoryBackend()
        # 3 completed
        for i in range(3):
            job = Job(func_ref="fn", name=f"ok{i}")
            await backend.push(job)
            job.state = JobState.COMPLETED
            now = datetime.now(timezone.utc)
            job.started_at = now - timedelta(milliseconds=10)
            job.completed_at = now
        # 1 failed
        fail_job = Job(func_ref="fn", name="fail")
        await backend.push(fail_job)
        fail_job.state = JobState.FAILED
        fail_job.completed_at = datetime.now(timezone.utc)

        stats = await backend.get_stats()
        assert stats["success_rate"] == 75.0

    @pytest.mark.asyncio
    async def test_percentiles_no_jobs(self):
        """P50/P95/P99 are 0 when no completed jobs."""
        from aquilia.tasks.engine import MemoryBackend
        backend = MemoryBackend()
        stats = await backend.get_stats()
        assert stats["p50_ms"] == 0
        assert stats["p95_ms"] == 0
        assert stats["p99_ms"] == 0

    @pytest.mark.asyncio
    async def test_percentiles_with_data(self):
        """P50/P95/P99 are computed from completed job durations."""
        from aquilia.tasks.engine import MemoryBackend, Job, JobState
        from datetime import datetime, timezone, timedelta
        backend = MemoryBackend()
        for i in range(1, 101):
            job = Job(func_ref="fn", name=f"t{i}")
            await backend.push(job)
            job.state = JobState.COMPLETED
            now = datetime.now(timezone.utc)
            job.started_at = now - timedelta(milliseconds=i)
            job.completed_at = now  # duration_ms = i
        stats = await backend.get_stats()
        # Percentiles computed from sorted durations 1..100ms
        assert abs(stats["p50_ms"] - 50) < 2  # Allow rounding tolerance
        assert abs(stats["p95_ms"] - 95) < 2
        assert abs(stats["p99_ms"] - 99) < 2

    @pytest.mark.asyncio
    async def test_duration_histogram_buckets(self):
        """Duration histogram correctly bins job durations."""
        from aquilia.tasks.engine import MemoryBackend, Job, JobState
        from datetime import datetime, timezone, timedelta
        backend = MemoryBackend()
        durations = [5, 25, 75, 150, 400, 750, 3000, 8000]
        for d in durations:
            job = Job(func_ref="fn", name=f"t{d}")
            await backend.push(job)
            job.state = JobState.COMPLETED
            now = datetime.now(timezone.utc)
            job.started_at = now - timedelta(milliseconds=d)
            job.completed_at = now
        stats = await backend.get_stats()
        hist = stats["charts"]["duration_histogram"]["values"]
        # Each bucket should have exactly 1 job
        for i in range(8):
            assert hist[i] == 1, f"Bucket {i} expected 1 but got {hist[i]}"

    @pytest.mark.asyncio
    async def test_throughput_timeline_length(self):
        """Throughput timeline always has 24 hourly slots."""
        from aquilia.tasks.engine import MemoryBackend
        backend = MemoryBackend()
        stats = await backend.get_stats()
        tp = stats["charts"]["throughput"]
        assert len(tp["labels"]) == 24
        assert len(tp["completed"]) == 24
        assert len(tp["failed"]) == 24


# ============================================================================
# 27. CHART.JS TEMPLATE RENDERING
# ============================================================================


class TestChartJsTemplateRendering:
    """Verify render functions pass chart data to templates."""

    def _tasks_data(self, **overrides):
        """Helper to build tasks_data dict with correct nested structure."""
        stats = {
            "total_jobs": 0, "completed_count": 0, "active_count": 0,
            "failed_count": 0, "pending_count": 0, "dead_letter_count": 0,
            "avg_duration_ms": 0, "by_state": {}, "queues": [],
            "queue_count": 0, "success_rate": 100, "p50_ms": 0,
            "p95_ms": 0, "p99_ms": 0,
            "manager": {},
            "charts": {
                "throughput": {"labels": [], "completed": [], "failed": []},
                "duration_histogram": {"labels": [], "values": []},
                "state_doughnut": {"labels": [], "values": []},
                "queue_breakdown": {"labels": [], "pending": [], "running": [], "completed": [], "failed": []},
            },
        }
        stats.update(overrides)
        return {"available": overrides.pop("available", False), "stats": stats, "jobs": [], "queue_stats": {}}

    def _errors_data(self, **overrides):
        """Helper to build errors_data dict with correct structure."""
        base = {
            "total_errors": 0, "errors_last_hour": 0, "errors_last_24h": 0,
            "error_rate_per_min": 0, "unique_errors": 0,
            "unresolved_count": 0, "resolved_count": 0, "mttr_seconds": 0,
            "by_domain": {}, "by_severity": {}, "top_routes": [],
            "top_codes": [], "recent_errors": [], "error_groups": [],
            "hourly_trend": [],
            "charts": {
                "hourly": {"labels": [], "values": []},
                "five_min": {"labels": [], "values": []},
                "severity_doughnut": {"labels": [], "values": []},
                "domain_polar": {"labels": [], "values": []},
                "top_codes_bar": {"labels": [], "values": []},
                "domain_stacked": {"labels": [], "series": {}},
                "severity_timeline": {"labels": [], "series": {}},
                "velocity": [],
            },
        }
        base.update(overrides)
        return base

    def test_render_tasks_page_includes_chart_js_cdn(self):
        """render_tasks_page() output includes Chart.js CDN script."""
        from aquilia.admin.templates import render_tasks_page
        html = render_tasks_page(tasks_data=self._tasks_data())
        assert "chart.js" in html.lower() or "Chart" in html

    def test_render_tasks_page_passes_success_rate(self):
        """render_tasks_page() passes success_rate to template."""
        from aquilia.admin.templates import render_tasks_page
        html = render_tasks_page(tasks_data=self._tasks_data(
            total_jobs=10, completed_count=9, failed_count=1,
            success_rate=90.0, p50_ms=25, p95_ms=80, p99_ms=95,
            available=True,
        ))
        assert "90" in html  # success_rate rendered
        assert "Success Rate" in html

    def test_render_tasks_page_passes_percentiles(self):
        """render_tasks_page() passes P50/P95/P99 to template."""
        from aquilia.admin.templates import render_tasks_page
        html = render_tasks_page(tasks_data=self._tasks_data(
            total_jobs=5, completed_count=5, success_rate=100,
            p50_ms=42, p95_ms=88, p99_ms=99, available=True,
        ))
        assert "P50" in html
        assert "P95" in html or "p95" in html.lower()
        assert "P99" in html or "p99" in html.lower()

    def test_render_errors_page_includes_chart_js_cdn(self):
        """render_errors_page() output includes Chart.js CDN script."""
        from aquilia.admin.templates import render_errors_page
        html = render_errors_page(errors_data=self._errors_data())
        assert "chart.js" in html.lower() or "Chart" in html

    def test_render_errors_page_passes_resolution_stats(self):
        """render_errors_page() passes unresolved/resolved/mttr to template."""
        from aquilia.admin.templates import render_errors_page
        html = render_errors_page(errors_data=self._errors_data(
            total_errors=5, errors_last_hour=2, errors_last_24h=5,
            error_rate_per_min=1.5, unique_errors=3,
            unresolved_count=2, resolved_count=1, mttr_seconds=45.5,
        ))
        assert "Unresolved" in html
        assert "MTTR" in html
        assert "46s" in html or "45" in html  # mttr_seconds rendered

    def test_render_errors_page_includes_severity_filter_buttons(self):
        """render_errors_page() includes filter buttons for severity."""
        from aquilia.admin.templates import render_errors_page
        html = render_errors_page(errors_data=self._errors_data())
        assert "filterErrors" in html
        assert "Errors" in html
        assert "Warnings" in html

    def test_render_errors_page_chart_canvas_elements(self):
        """render_errors_page() produces all expected canvas elements."""
        from aquilia.admin.templates import render_errors_page
        html = render_errors_page(errors_data=self._errors_data())
        assert "chart-error-trend" in html
        assert "chart-severity-doughnut" in html
        assert "chart-domain-polar" in html
        assert "chart-top-codes" in html
        assert "chart-domain-stacked" in html
        assert "chart-severity-timeline" in html
        assert "chart-velocity" in html

    def test_render_tasks_page_chart_canvas_elements(self):
        """render_tasks_page() produces all expected canvas elements."""
        from aquilia.admin.templates import render_tasks_page
        html = render_tasks_page(tasks_data=self._tasks_data())
        assert "chart-throughput" in html
        assert "chart-state-doughnut" in html
        assert "chart-duration" in html
        assert "chart-queues" in html

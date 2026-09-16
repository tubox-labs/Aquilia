"""
Regression tests for the background-task subsystem forensic audit (v1.4.2).

Each test maps to a confirmed finding:

    F-TA-03  Dependents of failed/dead/cancelled/missing parents stayed
             WAITING forever; ``fail_orphaned_dependents`` existed only in
             a docstring. ``JobState.FAILED`` was never assigned anywhere.
    F-TA-04  The per-process scheduler duplicated periodic jobs under
             multi-process deployment (N processes → N copies per slot).
    F-TA-05  ``TaskManager.stop()`` hung forever on Python 3.12+ when a
             task swallowed ``CancelledError`` (unreachable TimeoutError
             branch under ``wait_for(gather(...))``).
    N-1      A task body raising ``CancelledError`` killed its worker loop
             permanently and froze the job in RUNNING.
    N-2      The per-job timeout was defeatable: a body that swallowed
             cancellation ran past its budget and was marked COMPLETED.
    N-3      Unsatisfiable cron expressions (Feb 30) fired hourly forever
             via the 48h-scan fallback instead of never.
    N-4      Non-retryable faults (TaskResolutionFault, …) burned the full
             retry budget before dead-lettering.
    N-5      Waiting orphans were never pruned by cleanup (terminal-only
             filters) — resolved by F-TA-03 turning them into FAILED.
    N-6      ``attempt_epoch`` was bumped and persisted but never read, so
             a zombie worker's late write clobbered the reclaiming
             worker's state.

Coverage uses the in-memory backend primarily and SQLBackend against real
SQLite for cross-backend lockstep; Redis-specific paths are unit-verified
at the source level only (no live Redis in the test environment).
"""

from __future__ import annotations

import asyncio
import contextlib
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from aquilia.tasks import MemoryBackend, TaskManager, cron, every, task
from aquilia.tasks.faults import TaskScheduleFault
from aquilia.tasks.job import Job, JobState
from aquilia.tasks.schedule import CronSchedule

# ════════════════════════════════════════════════════════════════════
# Shared fixtures
# ════════════════════════════════════════════════════════════════════


@pytest.fixture
def boom_task():
    """Register a task that always fails, and clean up after."""
    from aquilia.tasks.decorators import _task_registry

    @task(name="audit_fixes_boom")
    async def boom() -> None:
        raise RuntimeError("upstream failed")

    yield boom
    _task_registry.pop("audit_fixes_boom", None)


@pytest.fixture
def ok_task():
    """Register a trivially successful task, and clean up after."""
    from aquilia.tasks.decorators import _task_registry

    @task(name="audit_fixes_ok")
    async def ok() -> int:
        return 42

    yield ok
    _task_registry.pop("audit_fixes_ok", None)


@pytest.fixture
async def sqlite_db():
    from aquilia.db.engine import configure_database

    path = Path(tempfile.mkdtemp()) / "audit-fixes.db"
    db = configure_database(f"sqlite:///{path}")
    await db.connect()
    yield db
    await db.disconnect()
    path.unlink(missing_ok=True)


def _waiting_orphan(dep_id: str, *, queue: str = "default") -> Job:
    """A pre-existing WAITING job blocked on ``dep_id`` (never enqueued through a manager)."""
    return Job(
        name="orphan",
        func_ref="tests:orphan",
        queue=queue,
        state=JobState.WAITING,
        depends_on=[dep_id],
    )


# ════════════════════════════════════════════════════════════════════
# F-TA-03 — dependency failure propagation
# ════════════════════════════════════════════════════════════════════


class TestDependencyFailurePropagation:
    """A dependent whose parent can never complete must be FAILED, not WAITING forever."""

    async def test_dead_parent_fails_its_dependent(self, boom_task, ok_task):
        manager = TaskManager(backend=MemoryBackend(), num_workers=0)
        await manager.start()
        try:
            parent = await manager.enqueue(boom_task, max_retries=0)
            child = await manager.enqueue(ok_task, depends_on=[parent])

            await manager.drain_once("test")  # parent → DEAD, child swept

            child_job = await manager.get_job(child)
            assert child_job.state is JobState.FAILED
            assert child_job.result is not None
            assert child_job.result.error_type == "DependencyFailed"
            assert child_job.is_terminal
        finally:
            await manager.stop(timeout=2.0)

    async def test_cancelled_parent_fails_its_dependent(self, ok_task):
        manager = TaskManager(backend=MemoryBackend(), num_workers=0)
        await manager.start()
        try:
            parent = await manager.enqueue(ok_task)
            child = await manager.enqueue(ok_task, depends_on=[parent])

            assert await manager.cancel(parent) is True

            child_job = await manager.get_job(child)
            assert child_job.state is JobState.FAILED
            assert child_job.result.error_type == "DependencyFailed"
        finally:
            await manager.stop(timeout=2.0)

    async def test_pop_time_orphan_with_missing_dependency_is_failed(self):
        """Pre-existing orphans and typo'd dependency IDs are caught at pop time."""
        backend = MemoryBackend()
        orphan = _waiting_orphan("no-such-job-id")
        await backend.push(orphan)

        assert await backend.pop("default") is None  # nothing runnable

        assert orphan.state is JobState.FAILED
        assert orphan.result.error_type == "DependencyFailed"
        # Terminal, so it is never scanned again.
        assert await backend.pop("default") is None

    async def test_pop_time_orphan_with_dead_parent_is_failed(self, boom_task):
        manager = TaskManager(backend=MemoryBackend(), num_workers=0)
        await manager.start()
        try:
            parent = await manager.enqueue(boom_task, max_retries=0)
            await manager.drain_once("test")  # parent → DEAD (child not yet enqueued)

            orphan = _waiting_orphan(parent)
            await manager.backend.push(orphan)
            assert await manager.backend.pop("default") is None

            assert orphan.state is JobState.FAILED
            assert orphan.result.error_type == "DependencyFailed"
        finally:
            await manager.stop(timeout=2.0)

    async def test_pending_parent_leaves_dependent_waiting(self, ok_task):
        """Only uncompletable dependencies fail a dependent; unfinished ones still wait."""
        manager = TaskManager(backend=MemoryBackend(), num_workers=0)
        await manager.start()
        try:
            parent = await manager.enqueue(ok_task)
            child = await manager.enqueue(ok_task, depends_on=[parent])

            child_job = await manager.get_job(child)
            assert child_job.state is JobState.WAITING
            assert child_job.is_terminal is False
        finally:
            await manager.stop(timeout=2.0)

    async def test_orphans_are_failed_on_sql_backend(self, sqlite_db):
        from aquilia.tasks.backends import SQLBackend

        backend = SQLBackend(sqlite_db)
        manager = TaskManager(backend=backend, num_workers=0)
        await manager.start()
        try:
            # Dead-parent propagation through the manager path.
            dead = Job(name="dead", func_ref="tests:dead", queue="q1", max_retries=0)
            await backend.push(dead)
            child = Job(name="child", func_ref="tests:child", queue="q1", depends_on=[dead.id])
            await backend.push(child)

            # Children have no priority edge; the parent is claimed first.
            while True:
                job = await manager.backend.pop("q1")
                if job is None:
                    break
                if job.id == dead.id:
                    await manager._execute_job(job, "test")  # parent → DEAD + sweep
                else:
                    # A blocked child popped before its parent died:
                    # keep polling; the next claim happens after the sweep.
                    await asyncio.sleep(0)

            child_job = await backend.get(child.id)
            assert child_job.state is JobState.FAILED
            assert child_job.result.error_type == "DependencyFailed"

            # Pop-time sweep of a missing dependency.
            orphan = _waiting_orphan("no-such-job-id", queue="q2")
            await backend.push(orphan)
            assert await backend.pop("q2") is None
            orphan_job = await backend.get(orphan.id)
            assert orphan_job.state is JobState.FAILED
            assert orphan_job.result.error_type == "DependencyFailed"
        finally:
            await manager.stop(timeout=2.0)


class TestFailOrphanedDependentsSweep:
    """The public sweep the old docstring promised but never delivered."""

    async def test_sweep_fails_waiting_orphans(self, ok_task):
        manager = TaskManager(backend=MemoryBackend(), num_workers=0)
        await manager.start()
        try:
            parent = await manager.enqueue(ok_task, max_retries=0)
            orphan = _waiting_orphan(parent)
            await manager.backend.push(orphan)

            # Simulate the parent dying outside the manager's failure path.
            parent_job = await manager.get_job(parent)
            parent_job.state = JobState.DEAD
            parent_job.completed_at = datetime.now(timezone.utc)
            await manager.backend.update(parent_job)

            failed = await manager.fail_orphaned_dependents()
            assert failed == 1
            assert orphan.state is JobState.FAILED
            assert orphan.result.error_type == "DependencyFailed"

            # Idempotent: a second sweep finds nothing new.
            assert await manager.fail_orphaned_dependents() == 0
        finally:
            await manager.stop(timeout=2.0)

    async def test_sweep_is_scoped_by_only_job_id(self, ok_task):
        manager = TaskManager(backend=MemoryBackend(), num_workers=0)
        await manager.start()
        try:
            dead_parent = await manager.enqueue(ok_task, max_retries=0)
            live_parent = await manager.enqueue(ok_task, max_retries=0)
            orphan = _waiting_orphan(dead_parent)
            untouched = _waiting_orphan(live_parent)
            await manager.backend.push(orphan)
            await manager.backend.push(untouched)

            dead_job = await manager.get_job(dead_parent)
            dead_job.state = JobState.DEAD
            await manager.backend.update(dead_job)

            failed = await manager.fail_orphaned_dependents(only_job_id=dead_parent)
            assert failed == 1
            assert orphan.state is JobState.FAILED
            assert untouched.state is JobState.WAITING
        finally:
            await manager.stop(timeout=2.0)

    async def test_dependency_status_classifies_three_ways(self, ok_task):
        manager = TaskManager(backend=MemoryBackend(), num_workers=0)
        await manager.start()
        try:
            completed = await manager.enqueue(ok_task)
            await manager.drain_once("test")
            running = Job(name="r", func_ref="tests:r", queue="default", state=JobState.RUNNING)
            await manager.backend.push(running)

            assert await manager.backend.dependency_status(Job(depends_on=[])) == "satisfied"
            assert await manager.backend.dependency_status(Job(depends_on=[completed])) == "satisfied"
            assert await manager.backend.dependency_status(Job(depends_on=[running.id])) == "pending"
            assert await manager.backend.dependency_status(Job(depends_on=["missing"])) == "failed"
            assert await manager.backend.dependency_status(Job(depends_on=[completed, "missing"])) == "failed"
        finally:
            await manager.stop(timeout=2.0)

    async def test_stats_count_failed_and_cancelled_jobs(self, ok_task):
        """FAILED and CANCELLED jobs must appear in failed stats / success rate."""
        manager = TaskManager(backend=MemoryBackend(), num_workers=0)
        await manager.start()
        try:
            done = await manager.enqueue(ok_task)
            cancelled = await manager.enqueue(ok_task)
            await manager.drain_once("test")
            await manager.cancel(cancelled)
            orphan = _waiting_orphan("missing")
            orphan.state = JobState.FAILED
            await manager.backend.push(orphan)

            stats = await manager.get_stats()
            assert stats["by_state"].get("failed", 0) >= 1
            # 1 completed vs 1 cancelled + 1 failed → 33.3%
            assert stats["success_rate"] == pytest.approx(33.3)
        finally:
            await manager.stop(timeout=2.0)


# ════════════════════════════════════════════════════════════════════
# N-5 — orphans become prunable
# ════════════════════════════════════════════════════════════════════


class TestCleanupPrunesFailedOrphans:
    async def test_cleanup_removes_old_failed_jobs_memory(self):
        backend = MemoryBackend()
        orphan = _waiting_orphan("missing")
        orphan.state = JobState.FAILED
        orphan.completed_at = datetime.now(timezone.utc) - timedelta(hours=2)
        await backend.push(orphan)

        removed = await backend.cleanup(max_age_seconds=3600)
        assert removed == 1
        assert await backend.get(orphan.id) is None

    async def test_cleanup_removes_old_failed_jobs_sql(self, sqlite_db):
        from aquilia.tasks.backends import SQLBackend

        backend = SQLBackend(sqlite_db)
        await backend.initialize()
        orphan = _waiting_orphan("missing", queue="q")
        orphan.state = JobState.FAILED
        orphan.completed_at = datetime.now(timezone.utc) - timedelta(hours=2)
        await backend.push(orphan)

        removed = await backend.cleanup(max_age_seconds=3600)
        assert removed == 1
        assert await backend.get(orphan.id) is None


# ════════════════════════════════════════════════════════════════════
# F-TA-05 — stop() must be bounded
# ════════════════════════════════════════════════════════════════════


class TestStopBoundedShutdown:
    async def test_stop_returns_when_task_mid_execution_swallows_cancellation(self):
        """The original hang: a task already running that swallows CancelledError."""
        manager = TaskManager(num_workers=0)
        started = asyncio.Event()

        async def stubborn() -> None:
            started.set()
            # Swallow the first few cancellations — enough to defeat the
            # old single-shot wait_for(gather(...)) shutdown — then exit.
            swallows_left = 3
            while swallows_left:
                try:
                    await asyncio.sleep(3600)
                except asyncio.CancelledError:
                    swallows_left -= 1
                    continue

        manager._running = True
        stubborn_task = asyncio.create_task(stubborn(), name="stubborn")
        manager._workers.append(stubborn_task)
        await started.wait()  # the task is mid-execution, not merely scheduled

        loop = asyncio.get_running_loop()
        t0 = loop.time()
        await manager.stop(timeout=2.0)
        elapsed = loop.time() - t0

        assert elapsed < 3.0, f"stop() took {elapsed:.2f}s — cancellation swallow still blocks shutdown"
        # stop() re-delivers cancellation, so a bounded swallower finishes.
        assert stubborn_task.done()
        assert manager._workers == []

    async def test_stop_detaches_a_forever_swallowing_task(self):
        """A task that would swallow every cancellation forever is detached, not awaited."""
        manager = TaskManager(num_workers=0)
        started = asyncio.Event()
        release = asyncio.Event()

        async def immortal() -> None:
            started.set()
            # Swallows every cancellation until released — modelling a task
            # stuck in a CPU-bound or cancellation-hostile loop.
            while not release.is_set():
                try:
                    await asyncio.sleep(3600)
                except asyncio.CancelledError:
                    continue

        manager._running = True
        immortal_task = asyncio.create_task(immortal(), name="immortal")
        manager._workers.append(immortal_task)
        await started.wait()

        loop = asyncio.get_running_loop()
        t0 = loop.time()
        await manager.stop(timeout=0.3)
        elapsed = loop.time() - t0

        assert elapsed < 1.5, f"stop() took {elapsed:.2f}s — forever-swallower blocks shutdown"
        assert manager._workers == []
        assert not immortal_task.done(), "the task should have been detached, still running"

        # The test now owns the detached task. A cancellation-hostile body
        # can only be unwound from outside; release it and hand it one more
        # cancellation so the event loop shuts down cleanly.
        release.set()
        immortal_task.cancel()
        with contextlib.suppress(asyncio.CancelledError, Exception):
            await asyncio.wait_for(asyncio.shield(immortal_task), timeout=2.0)
        assert immortal_task.done()

    async def test_stop_returns_when_task_never_started(self):
        """Cancelling a scheduled (not yet running) task must also be bounded."""
        manager = TaskManager(num_workers=0)

        async def idle() -> None:
            await asyncio.sleep(3600)

        manager._running = True
        manager._workers.append(asyncio.create_task(idle(), name="idle"))

        loop = asyncio.get_running_loop()
        t0 = loop.time()
        await manager.stop(timeout=0.2)
        assert loop.time() - t0 < 2.0
        assert manager._workers == []


class TestWorkerShutdownDuringJob:
    """Scenario (b) of N-1: manager.stop() during a running job shuts down cleanly."""

    async def test_stop_mid_job_is_clean_and_reaps_the_runner(self):
        manager = TaskManager(backend=MemoryBackend(), num_workers=1)
        await manager.start()
        started = asyncio.Event()

        @task(name="audit_fixes_long")
        async def long_job() -> None:
            started.set()
            await asyncio.sleep(30)

        try:
            job_id = await manager.enqueue(long_job, timeout=60)
            await started.wait()

            await asyncio.wait_for(manager.stop(timeout=3.0), timeout=8.0)

            assert manager.is_running is False
            # No leaked child runner tasks.
            leftovers = [
                t for t in asyncio.all_tasks() if t is not asyncio.current_task() and not t.done()
            ]
            assert leftovers == []
            job = await manager.get_job(job_id)
            assert job.state is JobState.RUNNING  # lease reclaim owns recovery
        finally:
            from aquilia.tasks.decorators import _task_registry

            _task_registry.pop("audit_fixes_long", None)
            if manager.is_running:
                await manager.stop(timeout=3.0)


# ════════════════════════════════════════════════════════════════════
# N-1 — a task body raising CancelledError must not kill the worker
# ════════════════════════════════════════════════════════════════════


class TestTaskBodyCancelledError:
    async def test_body_raising_cancelled_error_is_a_failure_and_worker_survives(self):
        manager = TaskManager(backend=MemoryBackend(), num_workers=1)
        await manager.start()
        follow_up_ran = asyncio.Event()

        @task(name="audit_fixes_canceller")
        async def canceller() -> None:
            raise asyncio.CancelledError()

        @task(name="audit_fixes_followup")
        async def followup() -> None:
            follow_up_ran.set()

        try:
            bad = await manager.enqueue(canceller, max_retries=0)
            good = await manager.enqueue(followup)

            for _ in range(80):
                bad_job = await manager.get_job(bad)
                good_job = await manager.get_job(good)
                if bad_job and bad_job.is_terminal and good_job and good_job.is_terminal:
                    break
                await asyncio.sleep(0.05)

            assert bad_job.state is JobState.DEAD  # failed, not frozen RUNNING
            assert bad_job.result.error_type == "CancelledError"
            assert good_job.state is JobState.COMPLETED  # the worker survived
            assert follow_up_ran.is_set()
        finally:
            from aquilia.tasks.decorators import _task_registry

            _task_registry.pop("audit_fixes_canceller", None)
            _task_registry.pop("audit_fixes_followup", None)
            await manager.stop(timeout=3.0)

    async def test_body_raising_cancelled_error_follows_retry_policy(self):
        """With retries available, a CancelledError-raising body retries like any failure."""
        manager = TaskManager(backend=MemoryBackend(), num_workers=0)
        await manager.start()

        async def canceller() -> None:
            raise asyncio.CancelledError()

        try:
            job_id = await manager.enqueue(canceller, max_retries=2)
            job = await manager.drain_once("test")
            assert job.state is JobState.RETRYING
            assert job.result.error_type == "CancelledError"
            stored = await manager.get_job(job_id)
            assert stored.state is JobState.RETRYING
        finally:
            await manager.stop(timeout=2.0)


# ════════════════════════════════════════════════════════════════════
# N-2 — timeout must not be defeatable by swallowing cancellation
# ════════════════════════════════════════════════════════════════════


class TestTimeoutNotDefeatable:
    async def test_swallowed_timeout_cancellation_is_a_timeout_failure(self):
        """A body that suppresses CancelledError must not be recorded as a success."""
        manager = TaskManager(backend=MemoryBackend(), num_workers=0)
        await manager.start()

        async def stubborn() -> str:
            try:
                await asyncio.sleep(2.0)
            except asyncio.CancelledError:
                await asyncio.sleep(0.4)  # swallow the cancellation and overrun
            return "too late"

        try:
            await manager.enqueue(stubborn, timeout=0.2, max_retries=0)
            job = await manager.drain_once("test")

            assert job.state is JobState.DEAD
            assert job.result is not None
            assert job.result.success is False
            assert job.result.error_type == "TimeoutError"
            # The overrun is visible in the recorded duration.
            assert job.result.duration_ms > 200
        finally:
            await manager.stop(timeout=2.0)

    async def test_normal_timeout_still_fails_the_job(self):
        manager = TaskManager(backend=MemoryBackend(), num_workers=0)
        await manager.start()

        async def sleepy() -> None:
            await asyncio.sleep(5.0)

        try:
            await manager.enqueue(sleepy, timeout=0.1, max_retries=0)
            job = await manager.drain_once("test")
            assert job.state is JobState.DEAD
            assert job.result.error_type == "TimeoutError"
        finally:
            await manager.stop(timeout=2.0)

    async def test_fast_job_within_budget_still_completes(self):
        """The overrun check must not misfire on jobs that finish inside their budget."""
        manager = TaskManager(backend=MemoryBackend(), num_workers=0)
        await manager.start()

        async def quick() -> str:
            await asyncio.sleep(0.02)
            return "ok"

        try:
            await manager.enqueue(quick, timeout=5.0, max_retries=0)
            job = await manager.drain_once("test")
            assert job.state is JobState.COMPLETED
            assert job.result.value == "ok"
        finally:
            await manager.stop(timeout=2.0)


# ════════════════════════════════════════════════════════════════════
# N-3 — unsatisfiable cron expressions
# ════════════════════════════════════════════════════════════════════


class TestUnsatisfiableCron:
    def test_feb_30_raises_at_construction(self):
        with pytest.raises(TaskScheduleFault, match="can never match"):
            cron("0 0 30 2 *")

    def test_april_31_raises_at_construction(self):
        with pytest.raises(TaskScheduleFault, match="can never match"):
            cron("0 0 31 4 *")

    def test_unsatisfiable_day_in_the_only_selected_month_raises(self):
        # Only April is selected; April 31 does not exist.
        with pytest.raises(TaskScheduleFault):
            cron("0 0 31 4 *")

    def test_valid_day_in_some_selected_month_passes(self):
        # 30 exists in at least one of the selected months (any month but February).
        s = cron("0 0 30 2,4 *")
        assert s is not None

    def test_leap_day_is_valid(self):
        s = cron("0 0 29 2 *")
        base = datetime(2026, 9, 16, tzinfo=timezone.utc)
        nxt = s.next_run(base)
        assert (nxt.month, nxt.day) == (2, 29)
        assert nxt > base

    def test_rare_leap_day_with_weekday_resolves_to_a_real_date(self):
        """Feb 29 on a Monday: rare (28-year gaps) but satisfiable — must not fault."""
        s = cron("0 0 29 2 1")
        nxt = s.next_run(datetime(2026, 9, 16, tzinfo=timezone.utc))
        assert (nxt.month, nxt.day) == (2, 29)
        assert nxt.isoweekday() == 1  # Monday

    def test_next_run_no_longer_falls_back_hourly(self):
        """A hand-constructed never-matching schedule must fault, not fire hourly."""
        bad = CronSchedule(expression="0 0 30 2 *", _dom=(30,), _month=(2,))
        with pytest.raises(TaskScheduleFault):
            bad.next_run(datetime(2026, 9, 16, tzinfo=timezone.utc))

    def test_next_run_yearly_expression_finds_next_january(self):
        s = cron("0 0 1 1 *")
        base = datetime(2026, 9, 16, tzinfo=timezone.utc)
        nxt = s.next_run(base)
        assert (nxt.year, nxt.month, nxt.day, nxt.hour, nxt.minute) == (2027, 1, 1, 0, 0)


# ════════════════════════════════════════════════════════════════════
# N-4 — non-retryable faults skip the retry budget
# ════════════════════════════════════════════════════════════════════


class TestNonRetryableFaults:
    async def test_unresolvable_func_ref_dead_letters_immediately(self):
        manager = TaskManager(backend=MemoryBackend(), num_workers=0)
        await manager.start()
        try:
            bad = Job(name="bad", func_ref="never_registered:anything", queue="default", max_retries=3)
            await manager.backend.push(bad)
            job = await manager.drain_once("test")

            assert job.state is JobState.DEAD
            assert job.retry_count == 1  # first attempt, no budget burned
            assert job.result.error_type == "TaskResolutionFault"

            # Nothing was re-enqueued for a retry.
            assert await manager.backend.pop("default") is None
        finally:
            await manager.stop(timeout=2.0)

    async def test_retryable_errors_still_retry(self):
        manager = TaskManager(backend=MemoryBackend(), num_workers=0)
        await manager.start()

        async def flaky() -> None:
            raise RuntimeError("transient")

        try:
            await manager.enqueue(flaky, max_retries=2)
            job = await manager.drain_once("test")
            assert job.state is JobState.RETRYING
            assert job.retry_count == 1
        finally:
            await manager.stop(timeout=2.0)


# ════════════════════════════════════════════════════════════════════
# N-6 — attempt-epoch guard against zombie writes
# ════════════════════════════════════════════════════════════════════


class TestAttemptEpochGuard:
    async def test_memory_update_if_epoch_matching_epoch_writes(self):
        backend = MemoryBackend()
        stored_job = Job(name="m", func_ref="tests:m", queue="default")
        await backend.push(stored_job)

        # A distinct finishing copy, as a worker holding a claimed job would have.
        finisher = Job(id=stored_job.id, name="m", func_ref="tests:m", queue="default")
        finisher.state = JobState.COMPLETED
        assert await backend.update_if_epoch(finisher, stored_job.attempt_epoch) is True
        assert (await backend.get(stored_job.id)).state is JobState.COMPLETED

    async def test_memory_update_if_epoch_stale_epoch_skips(self):
        backend = MemoryBackend()
        stored_job = Job(name="m", func_ref="tests:m", queue="default")
        await backend.push(stored_job)

        finisher = Job(id=stored_job.id, name="m", func_ref="tests:m", queue="default")
        finisher.state = JobState.COMPLETED
        assert await backend.update_if_epoch(finisher, stored_job.attempt_epoch - 1) is False
        assert stored_job.state is JobState.PENDING  # the stored job was untouched

    async def test_sql_update_if_epoch_matching_and_stale(self, sqlite_db):
        from aquilia.tasks.backends import SQLBackend

        backend = SQLBackend(sqlite_db)
        await backend.initialize()

        fresh = Job(name="a", func_ref="tests:a", queue="q")
        await backend.push(fresh)
        stored = await backend.get(fresh.id)
        fresh.state = JobState.COMPLETED
        assert await backend.update_if_epoch(fresh, stored.attempt_epoch) is True
        assert (await backend.get(fresh.id)).state is JobState.COMPLETED

        stale = Job(name="b", func_ref="tests:b", queue="q")
        await backend.push(stale)
        stored_stale = await backend.get(stale.id)
        stale.state = JobState.COMPLETED
        assert await backend.update_if_epoch(stale, stored_stale.attempt_epoch - 3) is False
        assert (await backend.get(stale.id)).state is JobState.PENDING

    async def test_zombie_completion_cannot_clobber_a_reclaimed_job(self, sqlite_db):
        """End-to-end: reclaim bumps the epoch, and the zombie's finish is discarded."""
        from aquilia.tasks.backends import SQLBackend

        backend = SQLBackend(sqlite_db, lease_seconds=0.1)
        manager = TaskManager(backend=backend, num_workers=0)
        await manager.start()
        try:
            job = Job(name="z", func_ref="tests:z", queue="qz", max_retries=2)
            await backend.push(job)

            # Worker A claims the job (epoch 0)…
            claimed = await backend.pop("qz")
            assert claimed is not None
            claimed_epoch = claimed.attempt_epoch

            # …its lease lapses and another worker reclaims (epoch → 1,
            # state → PENDING in the store).
            await asyncio.sleep(0.25)
            assert await backend.reclaim_expired() == 1
            requeued = await backend.get(job.id)
            assert requeued.state is JobState.PENDING
            assert requeued.attempt_epoch == claimed_epoch + 1

            # Worker A finally finishes and tries to record its result.
            zombie_job = claimed
            zombie_job.state = JobState.COMPLETED
            zombie_job.result = None
            assert await manager._finalize_job(zombie_job, claimed_epoch) is False

            survivor = await backend.get(job.id)
            assert survivor.state is JobState.PENDING  # zombie write discarded
        finally:
            await manager.stop(timeout=2.0)

    async def test_stale_failure_retry_is_not_persisted(self, sqlite_db):
        """The retry path is epoch-guarded too: a zombie cannot re-enqueue its job."""
        from aquilia.tasks.backends import SQLBackend

        backend = SQLBackend(sqlite_db, lease_seconds=60.0)
        manager = TaskManager(backend=backend, num_workers=0)
        await manager.start()
        try:
            job = Job(name="z2", func_ref="tests:z2", queue="qz2", max_retries=2)
            await backend.push(job)
            claimed = await backend.pop("qz2")
            claimed_epoch = claimed.attempt_epoch

            # Reclaim under the claimant's nose (simulated epoch bump).
            reclaimed = await backend.get(job.id)
            reclaimed.attempt_epoch += 1
            await backend.update(reclaimed)

            await manager._handle_failure(
                claimed,
                "test",
                error="late failure",
                error_type="RuntimeError",
                traceback_str="",
                elapsed=1.0,
                claimed_epoch=claimed_epoch,
            )

            survivor = await backend.get(job.id)
            assert survivor.state is JobState.RUNNING  # zombie retry discarded
        finally:
            await manager.stop(timeout=2.0)


# ════════════════════════════════════════════════════════════════════
# F-TA-04 — multi-process scheduler deduplication
# ════════════════════════════════════════════════════════════════════


class TestSchedulerDedup:
    def test_slot_fingerprint_is_stable_within_a_slot(self):
        schedule = every(seconds=10)
        t0 = datetime(2026, 9, 16, 12, 0, 3, tzinfo=timezone.utc)
        t1 = datetime(2026, 9, 16, 12, 0, 9, tzinfo=timezone.utc)
        t2 = datetime(2026, 9, 16, 12, 0, 11, tzinfo=timezone.utc)

        assert TaskManager._schedule_slot_fingerprint("t", schedule, t0) == (
            TaskManager._schedule_slot_fingerprint("t", schedule, t1)
        )
        assert TaskManager._schedule_slot_fingerprint("t", schedule, t0) != (
            TaskManager._schedule_slot_fingerprint("t", schedule, t2)
        )
        # Different tasks never share a slot key.
        assert TaskManager._schedule_slot_fingerprint("a", schedule, t0) != (
            TaskManager._schedule_slot_fingerprint("b", schedule, t0)
        )

    def test_slot_fingerprint_floors_cron_to_minute_granularity(self):
        schedule = cron("*/5 * * * *")
        before = datetime(2026, 9, 16, 12, 4, 59, tzinfo=timezone.utc)
        after = datetime(2026, 9, 16, 12, 5, 1, tzinfo=timezone.utc)
        assert TaskManager._schedule_slot_fingerprint("t", schedule, before) != (
            TaskManager._schedule_slot_fingerprint("t", schedule, after)
        )

    async def test_two_schedulers_collapse_to_one_enqueue_per_slot(self):
        """Two managers over one backend must not double-enqueue a periodic task."""
        from aquilia.tasks.decorators import _task_registry

        @task(name="audit_fixes_periodic", schedule=every(seconds=30))
        async def periodic() -> None:
            return None

        try:
            backend = MemoryBackend()
            one = TaskManager(backend=backend, num_workers=0, scheduler_tick=0.2)
            two = TaskManager(backend=backend, num_workers=0, scheduler_tick=0.2)
            await one.start()
            await two.start()

            # The scheduler sleeps 1s before its first tick; 1.3s covers
            # the first tick of both schedulers, with the next slot still
            # 30s away — exactly one enqueue is due.
            await asyncio.sleep(1.3)
            await one.stop(timeout=1.0)
            await two.stop(timeout=1.0)

            jobs = await backend.list_jobs(limit=50)
            periodic_jobs = [j for j in jobs if j.name == "audit_fixes_periodic"]
            assert len(periodic_jobs) == 1, (
                f"expected exactly 1 job from 2 concurrent schedulers, got {len(periodic_jobs)}"
            )
            assert periodic_jobs[0].dedup_key is not None
            assert periodic_jobs[0].dedup_key.startswith("__schedule__:audit_fixes_periodic:")
        finally:
            _task_registry.pop("audit_fixes_periodic", None)

    async def test_consecutive_slots_each_enqueue_once(self):
        from aquilia.tasks.decorators import _task_registry

        @task(name="audit_fixes_fast_periodic", schedule=every(seconds=0.4))
        async def fast_periodic() -> None:
            return None

        try:
            backend = MemoryBackend()
            one = TaskManager(backend=backend, num_workers=0, scheduler_tick=0.1)
            two = TaskManager(backend=backend, num_workers=0, scheduler_tick=0.1)
            await one.start()
            await two.start()
            await asyncio.sleep(2.2)
            await one.stop(timeout=1.0)
            await two.stop(timeout=1.0)

            jobs = [j for j in await backend.list_jobs(limit=100) if j.name == "audit_fixes_fast_periodic"]
            # ~3 slots of 0.4s after the 1s startup delay; duplicated
            # scheduling would produce ~6.
            assert 2 <= len(jobs) <= 4
            dedup_keys = {j.dedup_key for j in jobs}
            assert len(dedup_keys) == len(jobs), "one job per slot, each with a distinct slot key"
        finally:
            _task_registry.pop("audit_fixes_fast_periodic", None)

    async def test_scheduler_dedup_is_atomic_on_sql_backend(self, sqlite_db):
        """The slot reservation must be cross-process on a durable backend."""
        from aquilia.tasks.backends import SQLBackend

        @task(name="audit_fixes_sql_periodic", schedule=every(seconds=30))
        async def sql_periodic() -> None:
            return None

        try:
            backend = SQLBackend(sqlite_db)
            one = TaskManager(backend=backend, num_workers=0, scheduler_tick=0.2)
            two = TaskManager(backend=backend, num_workers=0, scheduler_tick=0.2)
            await one.start()
            await two.start()
            await asyncio.sleep(1.3)
            await one.stop(timeout=1.0)
            await two.stop(timeout=1.0)

            jobs = [j for j in await backend.list_jobs(limit=50) if j.name == "audit_fixes_sql_periodic"]
            assert len(jobs) == 1, f"expected exactly 1 job from 2 SQL-backed schedulers, got {len(jobs)}"
        finally:
            from aquilia.tasks.decorators import _task_registry

            _task_registry.pop("audit_fixes_sql_periodic", None)

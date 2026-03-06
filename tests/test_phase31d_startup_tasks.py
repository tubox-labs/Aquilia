"""
Phase 31d Tests — Industry-Standard Task Scheduling, On-Demand Dispatch, SEO.

Tests cover:
1. Schedule helpers: every(), cron(), IntervalSchedule, CronSchedule
2. @task(schedule=...) decorator integration
3. _TaskDescriptor.delay() / .send() on-demand dispatch API
4. TaskManager scheduler loop (periodic auto-enqueue)
5. TaskManager._bind_task_descriptors()
6. Admin dashboard with periodic + on-demand task data
7. Chart.js data structures with actual job metrics
8. Auth task schedule/dispatch patterns
9. Integration.tasks() scheduler_tick parameter (no more run_on_startup)
10. SEO file validations (sitemap, robots, webmanifest, GA, JSON-LD)
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure repo root is on sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


# ═══════════════════════════════════════════════════════════════════════════
# 1. Schedule Helpers — every() and cron()
# ═══════════════════════════════════════════════════════════════════════════


class TestEverySchedule:
    """Verify every() creates correct IntervalSchedule instances."""

    def test_every_seconds(self):
        from aquilia.tasks.schedule import every, IntervalSchedule

        s = every(seconds=30)
        assert isinstance(s, IntervalSchedule)
        assert s.interval == 30

    def test_every_minutes(self):
        from aquilia.tasks.schedule import every

        s = every(minutes=5)
        assert s.interval == 300

    def test_every_hours(self):
        from aquilia.tasks.schedule import every

        s = every(hours=1)
        assert s.interval == 3600

    def test_every_days(self):
        from aquilia.tasks.schedule import every

        s = every(days=1)
        assert s.interval == 86400

    def test_every_combined(self):
        from aquilia.tasks.schedule import every

        s = every(hours=2, minutes=30)
        assert s.interval == 2 * 3600 + 30 * 60

    def test_every_zero_raises(self):
        from aquilia.tasks.schedule import every

        with pytest.raises(ValueError, match="must be > 0"):
            every()

    def test_every_negative_raises(self):
        from aquilia.tasks.schedule import every

        with pytest.raises(ValueError, match="must be > 0"):
            every(seconds=-10)

    def test_human_readable_seconds(self):
        from aquilia.tasks.schedule import every

        assert "30s" in every(seconds=30).human_readable

    def test_human_readable_minutes(self):
        from aquilia.tasks.schedule import every

        assert "5m" in every(minutes=5).human_readable

    def test_human_readable_hours(self):
        from aquilia.tasks.schedule import every

        assert "1h" in every(hours=1).human_readable

    def test_next_run(self):
        from aquilia.tasks.schedule import every

        now = datetime.now(timezone.utc)
        s = every(minutes=5)
        nxt = s.next_run(now)
        assert nxt == now + timedelta(seconds=300)

    def test_next_run_no_base(self):
        from aquilia.tasks.schedule import every

        s = every(seconds=10)
        nxt = s.next_run()
        assert nxt > datetime.now(timezone.utc) - timedelta(seconds=1)

    def test_frozen_dataclass(self):
        from aquilia.tasks.schedule import every

        s = every(seconds=30)
        with pytest.raises(AttributeError):
            s.interval = 60


class TestCronSchedule:
    """Verify cron() creates correct CronSchedule instances."""

    def test_every_5_minutes(self):
        from aquilia.tasks.schedule import cron

        s = cron("*/5 * * * *")
        assert s.expression == "*/5 * * * *"
        assert 0 in s._minute
        assert 5 in s._minute
        assert 10 in s._minute

    def test_hourly(self):
        from aquilia.tasks.schedule import cron

        s = cron("0 * * * *")
        assert s._minute == (0,)
        assert s._hour == ()  # wildcard

    def test_daily_midnight(self):
        from aquilia.tasks.schedule import cron

        s = cron("0 0 * * *")
        assert s._minute == (0,)
        assert s._hour == (0,)

    def test_specific_day(self):
        from aquilia.tasks.schedule import cron

        s = cron("30 2 * * 1")
        assert s._minute == (30,)
        assert s._hour == (2,)
        assert s._dow == (1,)

    def test_range(self):
        from aquilia.tasks.schedule import cron

        s = cron("1-5 * * * *")
        assert s._minute == (1, 2, 3, 4, 5)

    def test_list(self):
        from aquilia.tasks.schedule import cron

        s = cron("0,15,30,45 * * * *")
        assert s._minute == (0, 15, 30, 45)

    def test_human_readable(self):
        from aquilia.tasks.schedule import cron

        s = cron("*/5 * * * *")
        assert "cron(*/5 * * * *)" == s.human_readable

    def test_invalid_field_count(self):
        from aquilia.tasks.schedule import cron

        with pytest.raises(ValueError, match="5 fields"):
            cron("* * *")

    def test_matches_minute(self):
        from aquilia.tasks.schedule import cron

        s = cron("30 * * * *")
        dt_match = datetime(2026, 3, 6, 12, 30, 0, tzinfo=timezone.utc)
        dt_no = datetime(2026, 3, 6, 12, 15, 0, tzinfo=timezone.utc)
        assert s.matches(dt_match) is True
        assert s.matches(dt_no) is False

    def test_next_run(self):
        from aquilia.tasks.schedule import cron

        s = cron("0 * * * *")
        base = datetime(2026, 3, 6, 12, 30, 0, tzinfo=timezone.utc)
        nxt = s.next_run(base)
        assert nxt.minute == 0
        assert nxt > base


# ═══════════════════════════════════════════════════════════════════════════
# 2. @task(schedule=...) Decorator Integration
# ═══════════════════════════════════════════════════════════════════════════


class TestTaskScheduleDecorator:
    """Verify @task decorator accepts and stores schedule param."""

    def test_task_without_schedule(self):
        from aquilia.tasks.decorators import _TaskDescriptor
        from aquilia.tasks import task

        @task
        async def plain_task():
            pass

        assert isinstance(plain_task, _TaskDescriptor)
        assert plain_task.schedule is None
        assert plain_task.is_periodic is False

    def test_task_with_interval_schedule(self):
        from aquilia.tasks import task, every

        @task(schedule=every(minutes=10))
        async def periodic_task():
            pass

        assert periodic_task.is_periodic is True
        assert periodic_task.schedule.interval == 600

    def test_task_with_cron_schedule(self):
        from aquilia.tasks import task, cron

        @task(schedule=cron("0 */6 * * *"))
        async def cron_task():
            pass

        assert cron_task.is_periodic is True
        assert cron_task.schedule.expression == "0 */6 * * *"

    def test_get_periodic_tasks(self):
        from aquilia.tasks.decorators import get_periodic_tasks
        import myapp.modules.auth.tasks  # noqa: F401

        periodic = get_periodic_tasks()
        # cleanup_expired_sessions has schedule=every(hours=1)
        names = list(periodic.keys())
        assert any("cleanup_expired_sessions" in n for n in names)

    def test_on_demand_tasks_not_in_periodic(self):
        from aquilia.tasks.decorators import get_periodic_tasks

        periodic = get_periodic_tasks()
        names = list(periodic.keys())
        # record_login_attempt and check_account_lockout are on-demand
        assert not any("record_login_attempt" in n for n in names)
        assert not any("check_account_lockout" in n for n in names)


# ═══════════════════════════════════════════════════════════════════════════
# 3. _TaskDescriptor.delay() / .send() — On-Demand Dispatch
# ═══════════════════════════════════════════════════════════════════════════


class TestTaskDelayAndSend:
    """Verify .delay() and .send() dispatch API."""

    @pytest.mark.asyncio
    async def test_delay_requires_bound_manager(self):
        """delay() should raise if no TaskManager is bound."""
        from aquilia.tasks import task

        @task
        async def unbound_task():
            return 42

        with pytest.raises(RuntimeError, match="no bound TaskManager"):
            await unbound_task.delay()

    @pytest.mark.asyncio
    async def test_delay_dispatches_to_manager(self):
        """delay() should enqueue via bound TaskManager."""
        from aquilia.tasks import task
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        @task(queue="test")
        async def greet(name="world"):
            return f"hello {name}"

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=2)
        await manager.start()

        greet.bind(manager)
        job_id = await greet.delay(name="aquilia")

        assert isinstance(job_id, str)
        assert len(job_id) > 0

        # Wait for execution
        await asyncio.sleep(0.5)
        job = await manager.get_job(job_id)
        assert job is not None
        assert job.result is not None
        assert job.result.success is True

        await manager.stop()

    @pytest.mark.asyncio
    async def test_send_is_alias_for_delay(self):
        """send() should work identically to delay()."""
        from aquilia.tasks import task
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        @task(queue="test")
        async def ping():
            return "pong"

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=2)
        await manager.start()

        ping.bind(manager)
        job_id = await ping.send()

        assert isinstance(job_id, str)
        await asyncio.sleep(0.5)
        job = await manager.get_job(job_id)
        assert job.result.success is True

        await manager.stop()

    @pytest.mark.asyncio
    async def test_delay_with_args_and_kwargs(self):
        """delay() should pass arguments correctly."""
        from aquilia.tasks import task
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        @task
        async def add(a, b):
            return a + b

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=2)
        await manager.start()

        add.bind(manager)
        job_id = await add.delay(3, 7)

        await asyncio.sleep(0.5)
        job = await manager.get_job(job_id)
        assert job.result.success is True
        assert job.result.value == 10

        await manager.stop()

    @pytest.mark.asyncio
    async def test_bind_sets_manager(self):
        """bind() should set _manager on descriptor."""
        from aquilia.tasks import task
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        @task
        async def noop():
            pass

        assert noop._manager is None
        manager = TaskManager(backend=MemoryBackend(), num_workers=1)
        noop.bind(manager)
        assert noop._manager is manager


# ═══════════════════════════════════════════════════════════════════════════
# 4. TaskManager._bind_task_descriptors()
# ═══════════════════════════════════════════════════════════════════════════


class TestBindTaskDescriptors:
    """Verify TaskManager.start() binds all registered descriptors."""

    @pytest.mark.asyncio
    async def test_start_binds_descriptors(self):
        """After start(), registered tasks should have .delay() available."""
        from aquilia.tasks.engine import TaskManager, MemoryBackend
        from aquilia.tasks.decorators import get_registered_tasks

        import myapp.modules.auth.tasks  # noqa: F401

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=2)
        await manager.start()

        # All registered tasks should have manager bound
        for name, desc in get_registered_tasks().items():
            assert desc._manager is manager, f"{name} not bound"

        await manager.stop()

    @pytest.mark.asyncio
    async def test_delay_works_after_start(self):
        """After start(), .delay() should work on auth tasks."""
        from aquilia.tasks.engine import TaskManager, MemoryBackend
        import myapp.modules.auth.tasks as tasks

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=2)
        await manager.start()

        # Should NOT raise — manager is bound by start()
        job_id = await tasks.record_login_attempt.delay(
            username="admin",
            ip_address="192.168.1.1",
            success=True,
        )
        assert isinstance(job_id, str)

        await asyncio.sleep(0.5)
        job = await manager.get_job(job_id)
        assert job.result.success is True
        assert job.result.value["event"] == "login_attempt"
        assert job.result.value["success"] is True

        await manager.stop()


# ═══════════════════════════════════════════════════════════════════════════
# 5. Scheduler Loop — Periodic Task Auto-Enqueue
# ═══════════════════════════════════════════════════════════════════════════


class TestSchedulerLoop:
    """Verify the scheduler loop enqueues periodic tasks."""

    @pytest.mark.asyncio
    async def test_scheduler_enqueues_periodic_task_on_first_tick(self):
        """Periodic tasks should be enqueued on the first scheduler tick."""
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        import myapp.modules.auth.tasks  # noqa: F401

        backend = MemoryBackend()
        # Short scheduler tick for fast test
        manager = TaskManager(
            backend=backend,
            num_workers=4,
            scheduler_tick=0.5,
        )
        await manager.start()

        # Wait for scheduler to tick + workers to execute
        await asyncio.sleep(2.0)

        # cleanup_expired_sessions has schedule=every(hours=1)
        # It should have been enqueued once by the scheduler
        jobs = await manager.list_jobs()
        cleanup_jobs = [
            j for j in jobs
            if "cleanup_expired_sessions" in (j.name or j.func_ref)
        ]
        assert len(cleanup_jobs) >= 1

        await manager.stop()

    @pytest.mark.asyncio
    async def test_scheduler_does_not_enqueue_on_demand_tasks(self):
        """On-demand tasks (no schedule) should NOT be auto-enqueued."""
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        import myapp.modules.auth.tasks  # noqa: F401

        backend = MemoryBackend()
        manager = TaskManager(
            backend=backend,
            num_workers=4,
            scheduler_tick=0.5,
        )
        await manager.start()

        await asyncio.sleep(2.0)

        jobs = await manager.list_jobs()
        # record_login_attempt is on-demand — should NOT be auto-enqueued
        login_jobs = [
            j for j in jobs
            if "record_login_attempt" in (j.name or j.func_ref)
        ]
        assert len(login_jobs) == 0

        # check_account_lockout is on-demand too
        lockout_jobs = [
            j for j in jobs
            if "check_account_lockout" in (j.name or j.func_ref)
        ]
        assert len(lockout_jobs) == 0

        await manager.stop()

    @pytest.mark.asyncio
    async def test_scheduler_respects_interval(self):
        """Scheduler should not re-enqueue before the interval elapses."""
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        import myapp.modules.auth.tasks  # noqa: F401

        backend = MemoryBackend()
        manager = TaskManager(
            backend=backend,
            num_workers=4,
            scheduler_tick=0.3,
        )
        await manager.start()

        # Wait for several scheduler ticks (give enough time under load)
        await asyncio.sleep(3.0)

        jobs = await manager.list_jobs()
        # cleanup_expired_sessions has schedule=every(hours=1)
        # Each unique descriptor should only be enqueued once (interval=3600s)
        # Note: task may be registered under multiple import paths
        cleanup_jobs = [
            j for j in jobs
            if "cleanup_expired_sessions" in (j.name or j.func_ref)
        ]
        # Each registered descriptor enqueues once; we verify no duplicates
        # per registered name (multiple import paths = multiple descriptors)
        seen_refs = set()
        for j in cleanup_jobs:
            ref = j.name or j.func_ref
            assert ref not in seen_refs, f"Duplicate enqueue: {ref}"
            seen_refs.add(ref)

        await manager.stop()

    @pytest.mark.asyncio
    async def test_scheduler_tracks_last_run(self):
        """Scheduler should track last_run for each periodic task."""
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        import myapp.modules.auth.tasks  # noqa: F401

        backend = MemoryBackend()
        manager = TaskManager(
            backend=backend,
            num_workers=2,
            scheduler_tick=0.3,
        )
        await manager.start()
        await asyncio.sleep(1.5)

        # Should have recorded last run for cleanup_expired_sessions
        has_entry = any(
            "cleanup_expired_sessions" in name
            for name in manager._schedule_last_run
        )
        assert has_entry

        await manager.stop()


# ═══════════════════════════════════════════════════════════════════════════
# 6. Admin Dashboard With Real Periodic + On-Demand Data
# ═══════════════════════════════════════════════════════════════════════════


class TestAdminDashboardWithScheduledData:
    """Verify admin shows real data from scheduler + on-demand dispatch."""

    @pytest.mark.asyncio
    async def test_periodic_task_populates_dashboard(self):
        """Scheduled tasks should produce real admin dashboard data."""
        from aquilia.admin.site import AdminSite
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        import myapp.modules.auth.tasks  # noqa: F401

        backend = MemoryBackend()
        manager = TaskManager(
            backend=backend,
            num_workers=4,
            scheduler_tick=0.3,
        )
        await manager.start()
        await asyncio.sleep(2.0)

        site = AdminSite.__new__(AdminSite)
        site._task_manager = manager
        site._registry = {}

        data = await site.get_tasks_data()
        assert data["available"] is True
        assert data["stats"]["total_jobs"] >= 1
        assert data["stats"]["completed_count"] >= 1

        await manager.stop()

    @pytest.mark.asyncio
    async def test_on_demand_dispatch_populates_dashboard(self):
        """On-demand .delay() calls should populate admin dashboard."""
        from aquilia.admin.site import AdminSite
        from aquilia.tasks.engine import TaskManager, MemoryBackend
        import myapp.modules.auth.tasks as tasks

        backend = MemoryBackend()
        manager = TaskManager(
            backend=backend,
            num_workers=4,
            scheduler_tick=999,  # disable scheduler for this test
        )
        await manager.start()

        # Dispatch on-demand tasks via .delay()
        await tasks.record_login_attempt.delay(
            username="admin", ip_address="1.2.3.4", success=True,
        )
        await tasks.check_account_lockout.delay(username="admin")

        await asyncio.sleep(1.0)

        site = AdminSite.__new__(AdminSite)
        site._task_manager = manager
        site._registry = {}

        data = await site.get_tasks_data()
        assert data["stats"]["total_jobs"] >= 2
        assert data["stats"]["completed_count"] >= 2

        await manager.stop()

    @pytest.mark.asyncio
    async def test_registered_tasks_show_schedule_info(self):
        """Admin registered_tasks should display schedule/dispatch mode."""
        from aquilia.admin.site import AdminSite
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        import myapp.modules.auth.tasks  # noqa: F401 — ensure module is loaded

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=1)
        await manager.start()  # start binds descriptors

        site = AdminSite.__new__(AdminSite)
        site._task_manager = manager
        site._registry = {}

        data = await site.get_tasks_data()
        rt = data["registered_tasks"]

        # Find cleanup task — should be periodic
        cleanup = [t for t in rt if "cleanup_expired_sessions" in t["name"]]
        assert len(cleanup) >= 1
        assert cleanup[0]["dispatch"] == "periodic"
        assert "1h" in cleanup[0]["schedule"]

        # Find login audit — should be on-demand
        login = [t for t in rt if "record_login_attempt" in t["name"]]
        assert len(login) >= 1
        assert login[0]["dispatch"] == "on-demand"

        await manager.stop()

    @pytest.mark.asyncio
    async def test_charts_populated_after_mixed_dispatch(self):
        """Charts should show data from both periodic and on-demand tasks."""
        from aquilia.admin.site import AdminSite
        from aquilia.tasks.engine import TaskManager, MemoryBackend
        import myapp.modules.auth.tasks as tasks

        backend = MemoryBackend()
        manager = TaskManager(
            backend=backend,
            num_workers=4,
            scheduler_tick=0.3,
        )
        await manager.start()

        # On-demand dispatch
        await tasks.record_login_attempt.delay(
            username="test", success=False, failure_reason="bad password",
        )

        await asyncio.sleep(2.0)

        site = AdminSite.__new__(AdminSite)
        site._task_manager = manager
        site._registry = {}

        data = await site.get_tasks_data()
        charts = data["stats"].get("charts", {})

        assert sum(charts["throughput"]["completed"]) >= 2
        assert sum(charts["duration_histogram"]["values"]) >= 2
        assert sum(charts["state_doughnut"]["values"]) >= 2

        await manager.stop()

    @pytest.mark.asyncio
    async def test_tasks_data_json_serializable(self):
        """Full tasks_data dict should be JSON-serializable."""
        from aquilia.admin.site import AdminSite
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        import myapp.modules.auth.tasks  # noqa: F401

        backend = MemoryBackend()
        manager = TaskManager(
            backend=backend,
            num_workers=4,
            scheduler_tick=0.3,
        )
        await manager.start()
        await asyncio.sleep(2.0)

        site = AdminSite.__new__(AdminSite)
        site._task_manager = manager
        site._registry = {}

        data = await site.get_tasks_data()
        serialized = json.dumps(data, default=str)
        assert isinstance(serialized, str)
        parsed = json.loads(serialized)
        assert parsed["available"] is True

        await manager.stop()


# ═══════════════════════════════════════════════════════════════════════════
# 7. Auth Task Results — Validate Correct Output
# ═══════════════════════════════════════════════════════════════════════════


class TestAuthTaskResults:
    """Verify the 3 auth tasks produce correct result values via .delay()."""

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions_result(self):
        from aquilia.tasks.engine import TaskManager, MemoryBackend
        import myapp.modules.auth.tasks as tasks

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=2)
        await manager.start()

        job_id = await tasks.cleanup_expired_sessions.delay()
        await asyncio.sleep(0.5)

        job = await manager.get_job(job_id)
        assert job.result.success is True
        assert "purged" in job.result.value
        assert "elapsed_seconds" in job.result.value

        await manager.stop()

    @pytest.mark.asyncio
    async def test_record_login_attempt_result(self):
        from aquilia.tasks.engine import TaskManager, MemoryBackend
        import myapp.modules.auth.tasks as tasks

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=2)
        await manager.start()

        job_id = await tasks.record_login_attempt.delay(
            username="admin", ip_address="10.0.0.1", success=True,
        )
        await asyncio.sleep(0.5)

        job = await manager.get_job(job_id)
        assert job.result.success is True
        assert job.result.value["event"] == "login_attempt"
        assert job.result.value["success"] is True

        await manager.stop()

    @pytest.mark.asyncio
    async def test_check_account_lockout_result(self):
        from aquilia.tasks.engine import TaskManager, MemoryBackend
        import myapp.modules.auth.tasks as tasks

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=2)
        await manager.start()

        job_id = await tasks.check_account_lockout.delay(username="alice")
        await asyncio.sleep(0.5)

        job = await manager.get_job(job_id)
        assert job.result.success is True
        assert job.result.value["username"] == "alice"
        assert "locked" in job.result.value

        await manager.stop()


# ═══════════════════════════════════════════════════════════════════════════
# 8. Integration.tasks() — No More run_on_startup
# ═══════════════════════════════════════════════════════════════════════════


class TestIntegrationTasksConfig:
    """Verify Integration.tasks() uses scheduler_tick, not run_on_startup."""

    def test_no_run_on_startup_key(self):
        """run_on_startup should NOT exist in config dict."""
        from aquilia.config_builders import Integration

        config = Integration.tasks()
        assert "run_on_startup" not in config

    def test_scheduler_tick_default(self):
        """scheduler_tick should default to 15.0."""
        from aquilia.config_builders import Integration

        config = Integration.tasks()
        assert config["scheduler_tick"] == 15.0

    def test_scheduler_tick_custom(self):
        """Custom scheduler_tick should be preserved."""
        from aquilia.config_builders import Integration

        config = Integration.tasks(scheduler_tick=5.0)
        assert config["scheduler_tick"] == 5.0

    def test_all_config_keys(self):
        """All expected keys should be in the config dict."""
        from aquilia.config_builders import Integration

        config = Integration.tasks()
        expected = {
            "_integration_type", "enabled", "backend", "num_workers",
            "default_queue", "cleanup_interval", "cleanup_max_age",
            "max_retries", "retry_delay", "retry_backoff",
            "retry_max_delay", "default_timeout", "auto_start",
            "dead_letter_max", "scheduler_tick",
        }
        assert expected.issubset(set(config.keys()))

    def test_integration_type(self):
        from aquilia.config_builders import Integration

        config = Integration.tasks(scheduler_tick=10)
        assert config["_integration_type"] == "tasks"


# ═══════════════════════════════════════════════════════════════════════════
# 9. Workspace Configuration
# ═══════════════════════════════════════════════════════════════════════════


class TestWorkspaceNoRunOnStartup:
    """Verify workspace.py does NOT have run_on_startup."""

    def test_workspace_no_run_on_startup(self):
        filepath = os.path.join(REPO_ROOT, "myapp", "workspace.py")
        with open(filepath, "r") as f:
            content = f.read()
        assert "run_on_startup" not in content

    def test_workspace_has_tasks_config(self):
        filepath = os.path.join(REPO_ROOT, "myapp", "workspace.py")
        with open(filepath, "r") as f:
            content = f.read()
        assert 'backend="memory"' in content
        assert "num_workers=4" in content


# ═══════════════════════════════════════════════════════════════════════════
# 10. Full End-to-End Pipeline
# ═══════════════════════════════════════════════════════════════════════════


class TestEndToEndPipeline:
    """Full pipeline: scheduler → enqueue → execute → admin data → charts."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        """Complete pipeline with periodic + on-demand tasks."""
        from aquilia.admin.site import AdminSite
        from aquilia.tasks.engine import TaskManager, MemoryBackend
        import myapp.modules.auth.tasks as tasks

        backend = MemoryBackend()
        manager = TaskManager(
            backend=backend, num_workers=4, scheduler_tick=0.3,
        )
        await manager.start()

        # On-demand dispatch via .delay()
        job1 = await tasks.record_login_attempt.delay(
            username="admin", success=True,
        )
        job2 = await tasks.check_account_lockout.delay(username="admin")

        # Wait for scheduler tick + execution
        await asyncio.sleep(2.0)

        # Verify on-demand jobs completed
        j1 = await manager.get_job(job1)
        j2 = await manager.get_job(job2)
        assert j1.result.success is True
        assert j2.result.success is True

        # Verify periodic task was also enqueued by scheduler
        all_jobs = await manager.list_jobs()
        cleanup_jobs = [
            j for j in all_jobs
            if "cleanup_expired_sessions" in (j.name or j.func_ref)
        ]
        assert len(cleanup_jobs) >= 1

        # Verify admin data
        site = AdminSite.__new__(AdminSite)
        site._task_manager = manager
        site._registry = {}
        data = await site.get_tasks_data()

        assert data["available"] is True
        assert data["stats"]["total_jobs"] >= 3
        assert data["stats"]["completed_count"] >= 3
        assert data["stats"]["success_rate"] == 100.0

        # Charts
        charts = data["stats"]["charts"]
        assert sum(charts["throughput"]["completed"]) >= 3
        assert sum(charts["duration_histogram"]["values"]) >= 3

        # Manager stats
        mgr = data["stats"]["manager"]
        assert mgr["running"] is True
        assert mgr["total_enqueued"] >= 3
        assert mgr["total_completed"] >= 3
        assert mgr["backend"] == "MemoryBackend"

        # Registered tasks
        assert len(data["registered_tasks"]) >= 3

        await manager.stop()

    @pytest.mark.asyncio
    async def test_pipeline_queues_tracked(self):
        """Manager should track distinct queues from scheduled + on-demand."""
        from aquilia.tasks.engine import TaskManager, MemoryBackend
        import myapp.modules.auth.tasks as tasks

        backend = MemoryBackend()
        manager = TaskManager(
            backend=backend, num_workers=4, scheduler_tick=0.3,
        )
        await manager.start()

        await tasks.record_login_attempt.delay(username="x")
        await tasks.check_account_lockout.delay(username="x")
        await asyncio.sleep(2.0)

        stats = await manager.get_stats()
        queues = stats["manager"]["queues"]
        assert "maintenance" in queues  # periodic cleanup
        assert "audit" in queues       # on-demand login
        assert "security" in queues    # on-demand lockout

        await manager.stop()


# ═══════════════════════════════════════════════════════════════════════════
# 11. Auth Task Schedule Patterns
# ═══════════════════════════════════════════════════════════════════════════


class TestAuthTaskPatterns:
    """Verify auth tasks use correct dispatch patterns."""

    def test_cleanup_is_periodic(self):
        """cleanup_expired_sessions should have schedule=every(hours=1)."""
        import myapp.modules.auth.tasks as tasks

        assert tasks.cleanup_expired_sessions.is_periodic is True
        assert tasks.cleanup_expired_sessions.schedule.interval == 3600

    def test_record_login_is_on_demand(self):
        """record_login_attempt should be on-demand (no schedule)."""
        import myapp.modules.auth.tasks as tasks

        assert tasks.record_login_attempt.is_periodic is False
        assert tasks.record_login_attempt.schedule is None

    def test_check_lockout_is_on_demand(self):
        """check_account_lockout should be on-demand (no schedule)."""
        import myapp.modules.auth.tasks as tasks

        assert tasks.check_account_lockout.is_periodic is False
        assert tasks.check_account_lockout.schedule is None


# ═══════════════════════════════════════════════════════════════════════════
# 12. Server Has No _enqueue_startup_tasks
# ═══════════════════════════════════════════════════════════════════════════


class TestServerNoAutoEnqueue:
    """Verify server no longer has run_on_startup / _enqueue_startup_tasks."""

    def test_no_enqueue_startup_tasks_method(self):
        """AquiliaServer should NOT have _enqueue_startup_tasks."""
        from aquilia.server import AquiliaServer

        assert not hasattr(AquiliaServer, "_enqueue_startup_tasks")

    def test_server_source_no_run_on_startup(self):
        """server.py should not reference run_on_startup."""
        filepath = os.path.join(REPO_ROOT, "aquilia", "server.py")
        with open(filepath, "r") as f:
            content = f.read()
        assert "run_on_startup" not in content
        assert "_enqueue_startup_tasks" not in content


# ═══════════════════════════════════════════════════════════════════════════
# 13. SEO File Validations
# ═══════════════════════════════════════════════════════════════════════════


class TestSEOFiles:
    """Verify SEO enhancements in aqdocx/ files."""

    def _read_file(self, relpath):
        filepath = os.path.join(REPO_ROOT, relpath)
        with open(filepath, "r") as f:
            return f.read()

    # ── index.html ───────────────────────────────────────────────────

    def test_index_html_has_google_analytics(self):
        content = self._read_file("aqdocx/index.html")
        assert "googletagmanager.com/gtag" in content
        assert "G-63WX40QPFB" in content

    def test_index_html_has_json_ld(self):
        content = self._read_file("aqdocx/index.html")
        assert "application/ld+json" in content
        assert "SoftwareApplication" in content

    def test_index_html_has_og_tags(self):
        content = self._read_file("aqdocx/index.html")
        assert 'property="og:title"' in content
        assert 'property="og:description"' in content

    def test_index_html_has_twitter_tags(self):
        content = self._read_file("aqdocx/index.html")
        assert 'name="twitter:card"' in content

    def test_index_html_has_robots_meta(self):
        content = self._read_file("aqdocx/index.html")
        assert 'name="robots"' in content

    def test_index_html_has_preconnect(self):
        content = self._read_file("aqdocx/index.html")
        assert "preconnect" in content

    def test_index_html_has_noscript(self):
        content = self._read_file("aqdocx/index.html")
        assert "<noscript>" in content

    # ── robots.txt ───────────────────────────────────────────────────

    def test_robots_txt_has_sitemap(self):
        content = self._read_file("aqdocx/public/robots.txt")
        assert "Sitemap:" in content

    def test_robots_txt_has_crawl_delay(self):
        content = self._read_file("aqdocx/public/robots.txt")
        assert "Crawl-delay:" in content

    def test_robots_txt_has_allow_rules(self):
        content = self._read_file("aqdocx/public/robots.txt")
        assert "Allow:" in content

    # ── sitemap.xml ──────────────────────────────────────────────────

    def test_sitemap_is_valid_xml(self):
        import xml.etree.ElementTree as ET

        content = self._read_file("aqdocx/public/sitemap.xml")
        root = ET.fromstring(content)
        assert root is not None

    def test_sitemap_has_urls(self):
        content = self._read_file("aqdocx/public/sitemap.xml")
        assert content.count("<url>") >= 20

    def test_sitemap_has_doc_routes(self):
        content = self._read_file("aqdocx/public/sitemap.xml")
        for section in [
            "/docs/installation", "/docs/quickstart", "/docs/server",
            "/docs/controllers", "/docs/models", "/docs/database",
            "/docs/auth", "/docs/di", "/docs/middleware",
        ]:
            assert section in content, f"Missing: {section}"

    def test_sitemap_has_changefreq(self):
        content = self._read_file("aqdocx/public/sitemap.xml")
        assert "<changefreq>" in content

    # ── site.webmanifest ─────────────────────────────────────────────

    def test_webmanifest_is_valid_json(self):
        data = json.loads(self._read_file("aqdocx/public/site.webmanifest"))
        assert isinstance(data, dict)

    def test_webmanifest_has_description(self):
        data = json.loads(self._read_file("aqdocx/public/site.webmanifest"))
        assert "description" in data
        assert len(data["description"]) > 20

    def test_webmanifest_has_start_url(self):
        data = json.loads(self._read_file("aqdocx/public/site.webmanifest"))
        assert data.get("start_url") == "/"

    def test_webmanifest_has_categories(self):
        data = json.loads(self._read_file("aqdocx/public/site.webmanifest"))
        assert "categories" in data
        assert len(data["categories"]) >= 1

    def test_webmanifest_has_lang(self):
        data = json.loads(self._read_file("aqdocx/public/site.webmanifest"))
        assert data.get("lang") == "en"

    def test_webmanifest_name_descriptive(self):
        data = json.loads(self._read_file("aqdocx/public/site.webmanifest"))
        assert "Aquilia" in data["name"]
        assert len(data["name"]) > 10


# ═══════════════════════════════════════════════════════════════════════════
# 14. BackgroundTaskConfig Manifest
# ═══════════════════════════════════════════════════════════════════════════


class TestBackgroundTaskConfigManifest:
    """Verify BackgroundTaskConfig in manifest still works correctly."""

    def test_background_task_config_to_dict(self):
        from aquilia.manifest import BackgroundTaskConfig

        config = BackgroundTaskConfig(
            tasks=["mod.tasks:my_task"],
            default_queue="custom",
        )
        d = config.to_dict()
        assert d["tasks"] == ["mod.tasks:my_task"]
        assert d["default_queue"] == "custom"

    def test_background_task_config_defaults(self):
        from aquilia.manifest import BackgroundTaskConfig

        config = BackgroundTaskConfig()
        assert config.tasks == []
        assert config.default_queue == "default"
        assert config.auto_discover is True
        assert config.enabled is True

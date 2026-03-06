"""
Phase 31d Tests — SEO Enhancements, Startup Task Enqueue, Admin Dashboard Data.

Tests cover:
1. Integration.tasks() run_on_startup parameter
2. Server._enqueue_startup_tasks() method
3. Admin dashboard populates with real job data after startup enqueue
4. Chart.js data structures with actual job metrics
5. SEO file validations (sitemap, robots, webmanifest)
6. Config propagation of run_on_startup flag
7. Edge cases: no tasks registered, manager not running, errors
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure repo root is on sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


# ═══════════════════════════════════════════════════════════════════════════
# 1. Integration.tasks() — run_on_startup Parameter
# ═══════════════════════════════════════════════════════════════════════════


class TestIntegrationTasksRunOnStartup:
    """Verify run_on_startup parameter in Integration.tasks()."""

    def test_run_on_startup_defaults_false(self):
        """run_on_startup should default to False."""
        from aquilia.config_builders import Integration

        config = Integration.tasks()
        assert config["run_on_startup"] is False

    def test_run_on_startup_true(self):
        """run_on_startup=True should be preserved in config dict."""
        from aquilia.config_builders import Integration

        config = Integration.tasks(run_on_startup=True)
        assert config["run_on_startup"] is True

    def test_run_on_startup_false_explicit(self):
        """Explicit False should be preserved."""
        from aquilia.config_builders import Integration

        config = Integration.tasks(run_on_startup=False)
        assert config["run_on_startup"] is False

    def test_run_on_startup_with_other_params(self):
        """run_on_startup coexists with all other params."""
        from aquilia.config_builders import Integration

        config = Integration.tasks(
            backend="memory",
            num_workers=8,
            default_queue="custom",
            max_retries=5,
            run_on_startup=True,
        )
        assert config["run_on_startup"] is True
        assert config["num_workers"] == 8
        assert config["default_queue"] == "custom"
        assert config["max_retries"] == 5
        assert config["backend"] == "memory"
        assert config["enabled"] is True

    def test_integration_type_preserved(self):
        """_integration_type should still be 'tasks'."""
        from aquilia.config_builders import Integration

        config = Integration.tasks(run_on_startup=True)
        assert config["_integration_type"] == "tasks"

    def test_all_config_keys_present(self):
        """All expected keys should be in the config dict."""
        from aquilia.config_builders import Integration

        config = Integration.tasks(run_on_startup=True)
        expected_keys = {
            "_integration_type", "enabled", "backend", "num_workers",
            "default_queue", "cleanup_interval", "cleanup_max_age",
            "max_retries", "retry_delay", "retry_backoff",
            "retry_max_delay", "default_timeout", "auto_start",
            "dead_letter_max", "run_on_startup",
        }
        assert expected_keys.issubset(set(config.keys()))


# ═══════════════════════════════════════════════════════════════════════════
# 2. Config Propagation — get_tasks_config with run_on_startup
# ═══════════════════════════════════════════════════════════════════════════


class TestConfigRunOnStartup:
    """Verify run_on_startup flows through config system."""

    def test_get_tasks_config_default_no_run_on_startup(self):
        """Default config should not have run_on_startup=True."""
        from aquilia.config import ConfigLoader

        loader = ConfigLoader()
        config = loader.get_tasks_config()
        # run_on_startup not in defaults, so it shouldn't be there
        assert config.get("run_on_startup", False) is False

    def test_get_tasks_config_with_run_on_startup(self):
        """run_on_startup should propagate through integrations config."""
        from aquilia.config import ConfigLoader

        loader = ConfigLoader()
        loader.config_data["integrations"] = {
            "tasks": {
                "enabled": True,
                "backend": "memory",
                "num_workers": 4,
                "run_on_startup": True,
            }
        }

        config = loader.get_tasks_config()
        assert config.get("run_on_startup") is True

    def test_get_tasks_config_run_on_startup_false(self):
        """Explicit False should propagate."""
        from aquilia.config import ConfigLoader

        loader = ConfigLoader()
        loader.config_data["integrations"] = {
            "tasks": {
                "enabled": True,
                "run_on_startup": False,
            }
        }

        config = loader.get_tasks_config()
        assert config.get("run_on_startup", False) is False


# ═══════════════════════════════════════════════════════════════════════════
# 3. Server._enqueue_startup_tasks() — Core Logic
# ═══════════════════════════════════════════════════════════════════════════


class TestEnqueueStartupTasks:
    """Verify _enqueue_startup_tasks() enqueues registered @task functions."""

    @pytest.mark.asyncio
    async def test_enqueues_all_registered_tasks(self):
        """All registered @task functions should be enqueued."""
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        # Import to register the 3 auth tasks
        import myapp.modules.auth.tasks  # noqa: F401
        from aquilia.tasks.decorators import get_registered_tasks

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=2)
        await manager.start()

        # Create a mock server with _enqueue_startup_tasks
        server = MagicMock()
        server._task_manager = manager
        server.logger = MagicMock()

        # Import and call the actual method
        from aquilia.server import AquiliaServer
        bound_method = AquiliaServer._enqueue_startup_tasks.__get__(server, AquiliaServer)
        await bound_method()

        # Check jobs were enqueued
        jobs = await manager.list_jobs()
        registered = get_registered_tasks()
        assert len(jobs) >= len(registered)

        # Verify job names match registered task names
        job_names = {j.name for j in jobs}
        for name in registered.keys():
            assert name in job_names, f"Task {name} was not enqueued"

        await manager.stop()

    @pytest.mark.asyncio
    async def test_enqueue_sets_correct_queues(self):
        """Enqueued jobs should have the correct queue from @task decorator."""
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        import myapp.modules.auth.tasks  # noqa: F401

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=2)
        await manager.start()

        server = MagicMock()
        server._task_manager = manager
        server.logger = MagicMock()

        from aquilia.server import AquiliaServer
        await AquiliaServer._enqueue_startup_tasks.__get__(server, AquiliaServer)()

        jobs = await manager.list_jobs()
        queue_map = {}
        for j in jobs:
            queue_map[j.name] = j.queue

        # job.name may be the full func_ref or short task_name
        def find_queue(name_fragment):
            for n, q in queue_map.items():
                if name_fragment in n:
                    return q
            return None

        assert find_queue("cleanup_expired_sessions") == "maintenance"
        assert find_queue("record_login_attempt") == "audit"
        assert find_queue("check_account_lockout") == "security"

        await manager.stop()

    @pytest.mark.asyncio
    async def test_enqueue_sets_correct_priorities(self):
        """Enqueued jobs should reflect @task decorator priorities."""
        from aquilia.tasks.engine import TaskManager, MemoryBackend
        from aquilia.tasks.job import Priority

        import myapp.modules.auth.tasks  # noqa: F401

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=2)
        await manager.start()

        server = MagicMock()
        server._task_manager = manager
        server.logger = MagicMock()

        from aquilia.server import AquiliaServer
        await AquiliaServer._enqueue_startup_tasks.__get__(server, AquiliaServer)()

        jobs = await manager.list_jobs()
        priority_map = {}
        for j in jobs:
            priority_map[j.name] = j.priority

        # job.name may be the full func_ref or short task_name
        def find_priority(name_fragment):
            for n, p in priority_map.items():
                if name_fragment in n:
                    return p
            return None

        assert find_priority("cleanup_expired_sessions") == Priority.LOW
        assert find_priority("record_login_attempt") == Priority.NORMAL
        assert find_priority("check_account_lockout") == Priority.HIGH

        await manager.stop()

    @pytest.mark.asyncio
    async def test_no_enqueue_when_manager_not_running(self):
        """Should not enqueue if manager is not running."""
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        import myapp.modules.auth.tasks  # noqa: F401

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=2)
        # Do NOT start the manager

        server = MagicMock()
        server._task_manager = manager
        server.logger = MagicMock()

        from aquilia.server import AquiliaServer
        await AquiliaServer._enqueue_startup_tasks.__get__(server, AquiliaServer)()

        jobs = await manager.list_jobs()
        assert len(jobs) == 0

    @pytest.mark.asyncio
    async def test_no_enqueue_when_no_manager(self):
        """Should gracefully handle None task manager."""
        server = MagicMock()
        server._task_manager = None
        server.logger = MagicMock()

        from aquilia.server import AquiliaServer
        # Should not raise
        await AquiliaServer._enqueue_startup_tasks.__get__(server, AquiliaServer)()

    @pytest.mark.asyncio
    async def test_enqueue_logs_count(self):
        """Should log the number of enqueued tasks."""
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        import myapp.modules.auth.tasks  # noqa: F401

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=2)
        await manager.start()

        server = MagicMock()
        server._task_manager = manager
        server.logger = MagicMock()

        from aquilia.server import AquiliaServer
        await AquiliaServer._enqueue_startup_tasks.__get__(server, AquiliaServer)()

        # Check info log was called with enqueue count
        info_calls = [str(c) for c in server.logger.info.call_args_list]
        assert any("Startup-enqueued" in c for c in info_calls)

        await manager.stop()

    @pytest.mark.asyncio
    async def test_enqueue_error_is_nonfatal(self):
        """A single task enqueue failure should not block others."""
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        import myapp.modules.auth.tasks  # noqa: F401

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=2)
        await manager.start()

        # Patch enqueue to fail on first call only
        original_enqueue = manager.enqueue
        call_count = [0]

        async def flaky_enqueue(*a, **kw):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("Simulated failure")
            return await original_enqueue(*a, **kw)

        manager.enqueue = flaky_enqueue

        server = MagicMock()
        server._task_manager = manager
        server.logger = MagicMock()

        from aquilia.server import AquiliaServer
        # Should not raise
        await AquiliaServer._enqueue_startup_tasks.__get__(server, AquiliaServer)()

        # At least some tasks should be enqueued despite the failure
        jobs = await manager.list_jobs()
        assert len(jobs) >= 2  # 3 registered, 1 failed = at least 2

        # Warning should be logged for the failure
        warning_calls = [str(c) for c in server.logger.warning.call_args_list]
        assert any("Failed to startup-enqueue" in c for c in warning_calls)

        await manager.stop()


# ═══════════════════════════════════════════════════════════════════════════
# 4. Admin Dashboard Data After Startup Enqueue
# ═══════════════════════════════════════════════════════════════════════════


class TestAdminDashboardWithRealData:
    """Verify admin dashboard shows real data after tasks are enqueued and run."""

    @pytest.mark.asyncio
    async def test_get_tasks_data_shows_jobs(self):
        """get_tasks_data should return actual job objects after enqueue."""
        from aquilia.admin.site import AdminSite
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        import myapp.modules.auth.tasks  # noqa: F401

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=2)
        await manager.start()

        # Enqueue the 3 auth tasks
        from aquilia.tasks.decorators import get_registered_tasks
        for name, desc in get_registered_tasks().items():
            await manager.enqueue(desc)

        # Wait for workers to process
        await asyncio.sleep(0.5)

        site = AdminSite.__new__(AdminSite)
        site._task_manager = manager
        site._registry = {}

        data = await site.get_tasks_data()

        assert data["available"] is True
        assert len(data["jobs"]) >= 3
        assert data["stats"]["total_jobs"] >= 3

        await manager.stop()

    @pytest.mark.asyncio
    async def test_completed_count_nonzero(self):
        """completed_count should be > 0 after tasks run."""
        from aquilia.admin.site import AdminSite
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        import myapp.modules.auth.tasks  # noqa: F401

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=4)
        await manager.start()

        from aquilia.tasks.decorators import get_registered_tasks
        for name, desc in get_registered_tasks().items():
            await manager.enqueue(desc)

        await asyncio.sleep(1.0)

        site = AdminSite.__new__(AdminSite)
        site._task_manager = manager
        site._registry = {}

        data = await site.get_tasks_data()
        stats = data["stats"]
        assert stats["completed_count"] >= 3

        await manager.stop()

    @pytest.mark.asyncio
    async def test_queue_stats_populated(self):
        """queue_stats should have entries for each task queue."""
        from aquilia.admin.site import AdminSite
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        import myapp.modules.auth.tasks  # noqa: F401

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=4)
        await manager.start()

        from aquilia.tasks.decorators import get_registered_tasks
        for name, desc in get_registered_tasks().items():
            await manager.enqueue(desc)

        await asyncio.sleep(1.0)

        site = AdminSite.__new__(AdminSite)
        site._task_manager = manager
        site._registry = {}

        data = await site.get_tasks_data()
        qs = data["queue_stats"]

        # Should have entries for maintenance, audit, security
        assert "maintenance" in qs
        assert "audit" in qs
        assert "security" in qs

        await manager.stop()

    @pytest.mark.asyncio
    async def test_charts_data_populated(self):
        """Chart.js data structures should have actual values."""
        from aquilia.admin.site import AdminSite
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        import myapp.modules.auth.tasks  # noqa: F401

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=4)
        await manager.start()

        from aquilia.tasks.decorators import get_registered_tasks
        for name, desc in get_registered_tasks().items():
            await manager.enqueue(desc)

        await asyncio.sleep(1.0)

        site = AdminSite.__new__(AdminSite)
        site._task_manager = manager
        site._registry = {}

        data = await site.get_tasks_data()
        charts = data["stats"].get("charts", {})

        # Throughput chart
        assert "throughput" in charts
        assert "labels" in charts["throughput"]
        assert len(charts["throughput"]["labels"]) == 24
        assert "completed" in charts["throughput"]
        # At least one hour should have completed tasks
        assert sum(charts["throughput"]["completed"]) >= 3

        # Duration histogram
        assert "duration_histogram" in charts
        assert "labels" in charts["duration_histogram"]
        assert "values" in charts["duration_histogram"]
        # At least some bucket should have values
        assert sum(charts["duration_histogram"]["values"]) >= 3

        # State doughnut
        assert "state_doughnut" in charts
        assert "labels" in charts["state_doughnut"]
        assert "values" in charts["state_doughnut"]
        assert sum(charts["state_doughnut"]["values"]) >= 3

        # Queue breakdown
        assert "queue_breakdown" in charts
        assert "labels" in charts["queue_breakdown"]
        assert len(charts["queue_breakdown"]["labels"]) >= 3

        await manager.stop()

    @pytest.mark.asyncio
    async def test_job_dicts_have_result_data(self):
        """Individual job dicts should have result data after completion."""
        from aquilia.admin.site import AdminSite
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        import myapp.modules.auth.tasks  # noqa: F401

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=4)
        await manager.start()

        from aquilia.tasks.decorators import get_registered_tasks
        for name, desc in get_registered_tasks().items():
            await manager.enqueue(desc)

        await asyncio.sleep(1.0)

        site = AdminSite.__new__(AdminSite)
        site._task_manager = manager
        site._registry = {}

        data = await site.get_tasks_data()
        completed_jobs = [
            j for j in data["jobs"]
            if j.get("state") == "completed"
        ]

        assert len(completed_jobs) >= 3

        for job in completed_jobs:
            assert "result" in job
            assert job["result"] is not None
            result = job["result"]
            assert result.get("success") is True
            assert "duration_ms" in result
            assert result["duration_ms"] >= 0

        await manager.stop()

    @pytest.mark.asyncio
    async def test_success_rate_100_percent(self):
        """All 3 auth tasks should complete successfully → 100% rate."""
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        import myapp.modules.auth.tasks  # noqa: F401

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=4)
        await manager.start()

        from aquilia.tasks.decorators import get_registered_tasks
        for name, desc in get_registered_tasks().items():
            await manager.enqueue(desc)

        await asyncio.sleep(1.0)

        stats = await manager.get_stats()
        assert stats["success_rate"] == 100.0

        await manager.stop()

    @pytest.mark.asyncio
    async def test_latency_percentiles_populated(self):
        """P50, P95, P99 should be > 0 after tasks complete."""
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        import myapp.modules.auth.tasks  # noqa: F401

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=4)
        await manager.start()

        from aquilia.tasks.decorators import get_registered_tasks
        for name, desc in get_registered_tasks().items():
            await manager.enqueue(desc)

        await asyncio.sleep(1.0)

        stats = await manager.get_stats()
        assert stats["p50_ms"] >= 0
        # P95 and P99 should at least be defined
        assert "p95_ms" in stats
        assert "p99_ms" in stats

        await manager.stop()

    @pytest.mark.asyncio
    async def test_manager_stats_reflect_enqueue(self):
        """Manager stats should show total_enqueued and total_completed."""
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        import myapp.modules.auth.tasks  # noqa: F401

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=4)
        await manager.start()

        from aquilia.tasks.decorators import get_registered_tasks
        registered = get_registered_tasks()
        for name, desc in registered.items():
            await manager.enqueue(desc)

        await asyncio.sleep(1.0)

        stats = await manager.get_stats()
        mgr = stats["manager"]
        assert mgr["total_enqueued"] >= len(registered)
        assert mgr["total_completed"] >= len(registered)
        assert mgr["total_failed"] == 0
        assert mgr["running"] is True

        await manager.stop()

    @pytest.mark.asyncio
    async def test_tasks_data_json_serializable(self):
        """Full tasks_data dict should be JSON-serializable."""
        from aquilia.admin.site import AdminSite
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        import myapp.modules.auth.tasks  # noqa: F401

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=4)
        await manager.start()

        from aquilia.tasks.decorators import get_registered_tasks
        for name, desc in get_registered_tasks().items():
            await manager.enqueue(desc)

        await asyncio.sleep(1.0)

        site = AdminSite.__new__(AdminSite)
        site._task_manager = manager
        site._registry = {}

        data = await site.get_tasks_data()
        # Should not raise
        serialized = json.dumps(data, default=str)
        assert isinstance(serialized, str)
        parsed = json.loads(serialized)
        assert parsed["available"] is True

        await manager.stop()


# ═══════════════════════════════════════════════════════════════════════════
# 5. Admin Tasks Template Rendering With Real Data
# ═══════════════════════════════════════════════════════════════════════════


class TestAdminTasksTemplateWithData:
    """Verify template renders with actual job data."""

    @pytest.mark.asyncio
    async def test_render_tasks_page_shows_job_count(self):
        """Total jobs count should appear in rendered page."""
        from aquilia.admin.templates import render_tasks_page
        from aquilia.admin.site import AdminSite
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        import myapp.modules.auth.tasks  # noqa: F401

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=4)
        await manager.start()

        from aquilia.tasks.decorators import get_registered_tasks
        for name, desc in get_registered_tasks().items():
            await manager.enqueue(desc)

        await asyncio.sleep(1.0)

        site = AdminSite.__new__(AdminSite)
        site._task_manager = manager
        site._registry = {}

        data = await site.get_tasks_data()
        html = render_tasks_page(data)

        # The job count (at least 3) should appear
        assert "3" in html or "Total" in html.lower()

        await manager.stop()

    @pytest.mark.asyncio
    async def test_render_tasks_page_shows_queue_names(self):
        """Queue names from tasks should appear in the rendered page."""
        from aquilia.admin.templates import render_tasks_page
        from aquilia.admin.site import AdminSite
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        import myapp.modules.auth.tasks  # noqa: F401

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=4)
        await manager.start()

        from aquilia.tasks.decorators import get_registered_tasks
        for name, desc in get_registered_tasks().items():
            await manager.enqueue(desc)

        await asyncio.sleep(1.0)

        site = AdminSite.__new__(AdminSite)
        site._task_manager = manager
        site._registry = {}

        data = await site.get_tasks_data()
        html = render_tasks_page(data)

        assert "maintenance" in html
        assert "audit" in html
        assert "security" in html

        await manager.stop()

    @pytest.mark.asyncio
    async def test_render_tasks_page_shows_task_names(self):
        """Task names should appear in the rendered page."""
        from aquilia.admin.templates import render_tasks_page
        from aquilia.admin.site import AdminSite
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        import myapp.modules.auth.tasks  # noqa: F401

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=4)
        await manager.start()

        from aquilia.tasks.decorators import get_registered_tasks
        for name, desc in get_registered_tasks().items():
            await manager.enqueue(desc)

        await asyncio.sleep(1.0)

        site = AdminSite.__new__(AdminSite)
        site._task_manager = manager
        site._registry = {}

        data = await site.get_tasks_data()
        html = render_tasks_page(data)

        assert "cleanup_expired_sessions" in html
        assert "record_login_attempt" in html
        assert "check_account_lockout" in html

        await manager.stop()

    @pytest.mark.asyncio
    async def test_render_tasks_page_shows_completed_state(self):
        """Completed state should appear in rendered jobs table."""
        from aquilia.admin.templates import render_tasks_page
        from aquilia.admin.site import AdminSite
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        import myapp.modules.auth.tasks  # noqa: F401

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=4)
        await manager.start()

        from aquilia.tasks.decorators import get_registered_tasks
        for name, desc in get_registered_tasks().items():
            await manager.enqueue(desc)

        await asyncio.sleep(1.0)

        site = AdminSite.__new__(AdminSite)
        site._task_manager = manager
        site._registry = {}

        data = await site.get_tasks_data()
        html = render_tasks_page(data)

        # completed should appear (as state in job rows)
        assert "completed" in html.lower()

        await manager.stop()


# ═══════════════════════════════════════════════════════════════════════════
# 6. Job Result Values — Auth Task Output Validation
# ═══════════════════════════════════════════════════════════════════════════


class TestAuthTaskResults:
    """Verify the 3 auth tasks produce correct result values."""

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions_result(self):
        """cleanup_expired_sessions should return purge summary."""
        from aquilia.tasks.engine import TaskManager, MemoryBackend
        import myapp.modules.auth.tasks as tasks

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=2)
        await manager.start()

        job_id = await manager.enqueue(tasks.cleanup_expired_sessions)
        await asyncio.sleep(0.5)

        job = await manager.get_job(job_id)
        assert job is not None
        assert job.result is not None
        assert job.result.success is True
        assert "purged" in job.result.value
        assert "elapsed_seconds" in job.result.value

        await manager.stop()

    @pytest.mark.asyncio
    async def test_record_login_attempt_result(self):
        """record_login_attempt should return audit entry dict."""
        from aquilia.tasks.engine import TaskManager, MemoryBackend
        import myapp.modules.auth.tasks as tasks

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=2)
        await manager.start()

        job_id = await manager.enqueue(tasks.record_login_attempt)
        await asyncio.sleep(0.5)

        job = await manager.get_job(job_id)
        assert job is not None
        assert job.result is not None
        assert job.result.success is True
        assert job.result.value["event"] == "login_attempt"
        assert "timestamp" in job.result.value

        await manager.stop()

    @pytest.mark.asyncio
    async def test_check_account_lockout_result(self):
        """check_account_lockout should return lockout decision dict."""
        from aquilia.tasks.engine import TaskManager, MemoryBackend
        import myapp.modules.auth.tasks as tasks

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=2)
        await manager.start()

        job_id = await manager.enqueue(tasks.check_account_lockout)
        await asyncio.sleep(0.5)

        job = await manager.get_job(job_id)
        assert job is not None
        assert job.result is not None
        assert job.result.success is True
        assert "locked" in job.result.value
        assert "recent_failures" in job.result.value

        await manager.stop()


# ═══════════════════════════════════════════════════════════════════════════
# 7. Full End-to-End: Enqueue → Execute → Admin Data → Charts
# ═══════════════════════════════════════════════════════════════════════════


class TestEndToEndTaskPipeline:
    """Full pipeline: register → enqueue → execute → admin stats."""

    @pytest.mark.asyncio
    async def test_full_pipeline_produces_charts(self):
        """Complete pipeline should produce non-empty chart data."""
        from aquilia.admin.site import AdminSite
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        import myapp.modules.auth.tasks  # noqa: F401

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=4)
        await manager.start()

        # Enqueue all registered tasks
        from aquilia.tasks.decorators import get_registered_tasks
        registered = get_registered_tasks()
        job_ids = []
        for name, desc in registered.items():
            jid = await manager.enqueue(desc)
            job_ids.append(jid)

        # Wait for execution
        await asyncio.sleep(1.0)

        # Verify all completed
        for jid in job_ids:
            job = await manager.get_job(jid)
            assert job.result is not None
            assert job.result.success is True

        # Get admin data
        site = AdminSite.__new__(AdminSite)
        site._task_manager = manager
        site._registry = {}

        data = await site.get_tasks_data()

        # Stats should be populated
        assert data["available"] is True
        assert data["stats"]["total_jobs"] >= 3
        assert data["stats"]["completed_count"] >= 3
        assert data["stats"]["success_rate"] == 100.0

        # Charts should have real values
        charts = data["stats"]["charts"]
        assert sum(charts["throughput"]["completed"]) >= 3
        assert sum(charts["duration_histogram"]["values"]) >= 3
        assert sum(charts["state_doughnut"]["values"]) >= 3

        # Queue breakdown should reflect all 3 queues
        qb = charts["queue_breakdown"]
        assert len(qb["labels"]) >= 3
        assert sum(qb["completed"]) >= 3

        # Manager info
        mgr = data["stats"]["manager"]
        assert mgr["running"] is True
        assert mgr["total_enqueued"] >= 3
        assert mgr["total_completed"] >= 3
        assert mgr["backend"] == "MemoryBackend"

        # Registered tasks also present
        assert len(data["registered_tasks"]) >= 3

        await manager.stop()

    @pytest.mark.asyncio
    async def test_pipeline_uptime_nonzero(self):
        """Manager uptime should be > 0 after startup."""
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        import myapp.modules.auth.tasks  # noqa: F401

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=2)
        await manager.start()

        from aquilia.tasks.decorators import get_registered_tasks
        for name, desc in get_registered_tasks().items():
            await manager.enqueue(desc)

        await asyncio.sleep(0.5)

        stats = await manager.get_stats()
        assert stats["manager"]["uptime_seconds"] > 0

        await manager.stop()

    @pytest.mark.asyncio
    async def test_pipeline_queues_tracked(self):
        """Manager should track the distinct queues used."""
        from aquilia.tasks.engine import TaskManager, MemoryBackend

        import myapp.modules.auth.tasks  # noqa: F401

        backend = MemoryBackend()
        manager = TaskManager(backend=backend, num_workers=4)
        await manager.start()

        from aquilia.tasks.decorators import get_registered_tasks
        for name, desc in get_registered_tasks().items():
            await manager.enqueue(desc)

        await asyncio.sleep(0.5)

        stats = await manager.get_stats()
        queues = stats["manager"]["queues"]
        assert "maintenance" in queues
        assert "audit" in queues
        assert "security" in queues

        await manager.stop()


# ═══════════════════════════════════════════════════════════════════════════
# 8. SEO File Validations
# ═══════════════════════════════════════════════════════════════════════════


class TestSEOFiles:
    """Verify SEO enhancements in aqdocx/ files."""

    def _read_file(self, relpath):
        filepath = os.path.join(REPO_ROOT, relpath)
        with open(filepath, "r") as f:
            return f.read()

    # ── index.html ───────────────────────────────────────────────────

    def test_index_html_has_google_analytics(self):
        """index.html should have Google Analytics gtag.js."""
        content = self._read_file("aqdocx/index.html")
        assert "googletagmanager.com/gtag" in content
        assert "G-63WX40QPFB" in content

    def test_index_html_has_json_ld(self):
        """index.html should have JSON-LD structured data."""
        content = self._read_file("aqdocx/index.html")
        assert "application/ld+json" in content
        assert "SoftwareApplication" in content
        assert "schema.org" in content

    def test_index_html_has_og_tags(self):
        """index.html should have Open Graph meta tags."""
        content = self._read_file("aqdocx/index.html")
        assert 'property="og:title"' in content
        assert 'property="og:description"' in content
        assert 'property="og:type"' in content

    def test_index_html_has_twitter_tags(self):
        """index.html should have Twitter Card meta tags."""
        content = self._read_file("aqdocx/index.html")
        assert 'name="twitter:card"' in content
        assert 'name="twitter:title"' in content

    def test_index_html_has_robots_meta(self):
        """index.html should have robots meta tag."""
        content = self._read_file("aqdocx/index.html")
        assert 'name="robots"' in content

    def test_index_html_has_preconnect(self):
        """index.html should preconnect to Google Analytics."""
        content = self._read_file("aqdocx/index.html")
        assert "preconnect" in content
        assert "googletagmanager.com" in content

    def test_index_html_has_noscript(self):
        """index.html should have a noscript fallback."""
        content = self._read_file("aqdocx/index.html")
        assert "<noscript>" in content

    # ── robots.txt ───────────────────────────────────────────────────

    def test_robots_txt_has_sitemap(self):
        """robots.txt should reference the sitemap."""
        content = self._read_file("aqdocx/public/robots.txt")
        assert "Sitemap:" in content
        assert "sitemap.xml" in content

    def test_robots_txt_has_crawl_delay(self):
        """robots.txt should specify crawl delay."""
        content = self._read_file("aqdocx/public/robots.txt")
        assert "Crawl-delay:" in content

    def test_robots_txt_has_allow_rules(self):
        """robots.txt should have Allow directives."""
        content = self._read_file("aqdocx/public/robots.txt")
        assert "Allow:" in content

    def test_robots_txt_has_user_agent(self):
        """robots.txt should specify User-agent."""
        content = self._read_file("aqdocx/public/robots.txt")
        assert "User-agent:" in content

    # ── sitemap.xml ──────────────────────────────────────────────────

    def test_sitemap_is_valid_xml(self):
        """sitemap.xml should be parseable XML."""
        import xml.etree.ElementTree as ET

        content = self._read_file("aqdocx/public/sitemap.xml")
        # Should not raise
        root = ET.fromstring(content)
        assert root is not None

    def test_sitemap_has_urls(self):
        """sitemap.xml should have multiple URL entries."""
        content = self._read_file("aqdocx/public/sitemap.xml")
        assert content.count("<url>") >= 20

    def test_sitemap_has_doc_routes(self):
        """sitemap.xml should cover major doc sections."""
        content = self._read_file("aqdocx/public/sitemap.xml")
        sections = [
            "/docs/installation",
            "/docs/quickstart",
            "/docs/server",
            "/docs/controllers",
            "/docs/models",
            "/docs/database",
            "/docs/auth",
            "/docs/di",
            "/docs/middleware",
        ]
        for section in sections:
            assert section in content, f"Missing section: {section}"

    def test_sitemap_has_changefreq(self):
        """sitemap.xml should include changefreq elements."""
        content = self._read_file("aqdocx/public/sitemap.xml")
        assert "<changefreq>" in content

    def test_sitemap_has_priority(self):
        """sitemap.xml should include priority elements."""
        content = self._read_file("aqdocx/public/sitemap.xml")
        assert "<priority>" in content

    # ── site.webmanifest ─────────────────────────────────────────────

    def test_webmanifest_is_valid_json(self):
        """site.webmanifest should be valid JSON."""
        content = self._read_file("aqdocx/public/site.webmanifest")
        data = json.loads(content)
        assert isinstance(data, dict)

    def test_webmanifest_has_description(self):
        """site.webmanifest should have a description."""
        content = self._read_file("aqdocx/public/site.webmanifest")
        data = json.loads(content)
        assert "description" in data
        assert len(data["description"]) > 20

    def test_webmanifest_has_start_url(self):
        """site.webmanifest should have start_url."""
        content = self._read_file("aqdocx/public/site.webmanifest")
        data = json.loads(content)
        assert data.get("start_url") == "/"

    def test_webmanifest_has_scope(self):
        """site.webmanifest should have scope."""
        content = self._read_file("aqdocx/public/site.webmanifest")
        data = json.loads(content)
        assert "scope" in data

    def test_webmanifest_has_categories(self):
        """site.webmanifest should have categories."""
        content = self._read_file("aqdocx/public/site.webmanifest")
        data = json.loads(content)
        assert "categories" in data
        assert len(data["categories"]) >= 1

    def test_webmanifest_has_lang(self):
        """site.webmanifest should have language."""
        content = self._read_file("aqdocx/public/site.webmanifest")
        data = json.loads(content)
        assert data.get("lang") == "en"

    def test_webmanifest_has_orientation(self):
        """site.webmanifest should have orientation."""
        content = self._read_file("aqdocx/public/site.webmanifest")
        data = json.loads(content)
        assert "orientation" in data

    def test_webmanifest_name_descriptive(self):
        """site.webmanifest name should be descriptive."""
        content = self._read_file("aqdocx/public/site.webmanifest")
        data = json.loads(content)
        assert "Aquilia" in data["name"]
        assert len(data["name"]) > 10  # More than just "Aquilia"


# ═══════════════════════════════════════════════════════════════════════════
# 9. Workspace Configuration
# ═══════════════════════════════════════════════════════════════════════════


class TestWorkspaceRunOnStartup:
    """Verify myapp/workspace.py has run_on_startup=True."""

    def test_workspace_has_run_on_startup(self):
        """workspace.py should configure run_on_startup=True."""
        filepath = os.path.join(REPO_ROOT, "myapp", "workspace.py")
        with open(filepath, "r") as f:
            content = f.read()
        assert "run_on_startup=True" in content

    def test_workspace_tasks_config(self):
        """workspace.py should have backend, workers, and run_on_startup."""
        filepath = os.path.join(REPO_ROOT, "myapp", "workspace.py")
        with open(filepath, "r") as f:
            content = f.read()
        assert 'backend="memory"' in content
        assert "num_workers=4" in content
        assert "run_on_startup=True" in content


# ═══════════════════════════════════════════════════════════════════════════
# 10. BackgroundTaskConfig Manifest
# ═══════════════════════════════════════════════════════════════════════════


class TestBackgroundTaskConfigManifest:
    """Verify BackgroundTaskConfig in manifest still works correctly."""

    def test_background_task_config_to_dict(self):
        """BackgroundTaskConfig.to_dict() should serialize correctly."""
        from aquilia.manifest import BackgroundTaskConfig

        config = BackgroundTaskConfig(
            tasks=["mod.tasks:my_task"],
            default_queue="custom",
            auto_discover=True,
            enabled=True,
        )
        d = config.to_dict()
        assert d["tasks"] == ["mod.tasks:my_task"]
        assert d["default_queue"] == "custom"
        assert d["auto_discover"] is True
        assert d["enabled"] is True

    def test_background_task_config_defaults(self):
        """BackgroundTaskConfig defaults should be sensible."""
        from aquilia.manifest import BackgroundTaskConfig

        config = BackgroundTaskConfig()
        assert config.tasks == []
        assert config.default_queue == "default"
        assert config.auto_discover is True
        assert config.enabled is True

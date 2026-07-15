"""Integration tests for the ASGI lifespan manager and hot-reload subsystem."""

from __future__ import annotations

import asyncio

import pytest

from aquilia.devplatform.config import AquiliaDevelopmentConfig
from aquilia.devplatform.core.lifespan import ASGILifespanManager
from aquilia.devplatform.reload.analyzer import ReloadPlan, ReloadStrategy
from aquilia.devplatform.reload.executor import ModuleReloadExecutor
from aquilia.devplatform.reload.state_preservation import ResourceSnapshot, StateBridgeRegistry


async def _run_lifespan(manager, *, do_shutdown=True):
    events = []
    inbox = ["lifespan.startup"] + (["lifespan.shutdown"] if do_shutdown else [])

    async def receive():
        if inbox:
            return {"type": inbox.pop(0)}
        await asyncio.sleep(0.01)
        return {"type": "lifespan.shutdown"}

    async def send(msg):
        events.append(msg["type"])

    await manager({"type": "lifespan"}, receive, send)
    return events


class _AppWithLifespan:
    """Minimal ASGI app that completes startup and shutdown lifespan events."""

    async def __call__(self, scope, receive, send):
        while True:
            msg = await receive()
            if msg["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif msg["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                return


class TestLifespan:
    async def test_startup_and_shutdown_sequence(self, runtime):
        cfg = AquiliaDevelopmentConfig(port=8000, reload=False, inspector_enabled=False)
        mgr = ASGILifespanManager(_AppWithLifespan(), cfg, runtime)
        events = await _run_lifespan(mgr)
        assert "lifespan.startup.complete" in events
        assert "lifespan.shutdown.complete" in events

    async def test_telemetry_wired_on_startup(self, runtime):
        cfg = AquiliaDevelopmentConfig(port=8000, reload=False, inspector_enabled=True)
        mgr = ASGILifespanManager(_AppWithLifespan(), cfg, runtime)
        await _run_lifespan(mgr, do_shutdown=False)
        # A CPU/lag/task source should now be attached.
        s = runtime.snapshot()
        assert s.event_loop_lag_ms >= 0.0
        # cleanup: stop lag sampler
        if mgr._lag_sampler:
            mgr._lag_sampler.stop()

    async def test_idempotent_startup(self, runtime):
        cfg = AquiliaDevelopmentConfig(port=8000, reload=False, inspector_enabled=False)
        mgr = ASGILifespanManager(_AppWithLifespan(), cfg, runtime)
        await mgr._adp_startup()
        first = mgr._started
        await mgr._adp_startup()  # second call is a no-op
        assert first and mgr._started


class TestReloadAnalyzer:
    def test_empty_change_is_noop_strategy(self):
        from aquilia.devplatform.reload.analyzer import DependencyGraphAnalyzer

        analyzer = DependencyGraphAnalyzer()
        plan = analyzer.compute_strategy(set())
        assert isinstance(plan, ReloadPlan)
        assert plan.strategy == ReloadStrategy.NOOP

    def test_non_python_change_is_noop(self, tmp_path):
        """A generated/runtime artifact must never trigger a reload."""
        from aquilia.devplatform.reload.analyzer import DependencyGraphAnalyzer

        analyzer = DependencyGraphAnalyzer()
        surp = tmp_path / ".aquilia" / "audit.surp"
        surp.parent.mkdir(parents=True)
        surp.write_text("x")
        plan = analyzer.compute_strategy({surp})
        assert plan.strategy == ReloadStrategy.NOOP

    def test_unloaded_python_change_is_full(self, tmp_path):
        from aquilia.devplatform.reload.analyzer import DependencyGraphAnalyzer

        analyzer = DependencyGraphAnalyzer()
        newmod = tmp_path / "brand_new_module.py"
        newmod.write_text("x = 1")
        plan = analyzer.compute_strategy({newmod})
        assert plan.strategy == ReloadStrategy.FULL


class TestReloadExecutor:
    async def test_noop_plan_does_nothing(self, runtime, monkeypatch):
        """A NOOP plan must never touch execv or partial reload."""

        def boom(*a, **k):
            raise AssertionError("NOOP plan must not reload")

        monkeypatch.setattr("os.execv", boom)
        plan = ReloadPlan(strategy=ReloadStrategy.NOOP, reason="nothing")
        await ModuleReloadExecutor(plan, runtime).execute()  # no raise, no exit

    async def test_full_reload_calls_execv(self, runtime, monkeypatch):
        calls = {}

        def fake_execv(exe, argv):
            calls["exe"] = exe
            raise SystemExit(0)  # stop before actually replacing the process

        monkeypatch.setattr("os.execv", fake_execv)
        cleanup = {}
        monkeypatch.setattr(
            ModuleReloadExecutor, "_pre_execv_cleanup", staticmethod(lambda: cleanup.setdefault("ran", True))
        )
        plan = ReloadPlan(strategy=ReloadStrategy.FULL, reason="test")
        ex = ModuleReloadExecutor(plan, runtime)
        with pytest.raises(SystemExit):
            await ex.execute()
        assert "exe" in calls
        assert cleanup.get("ran") is True

    async def test_pre_execv_cleanup_stops_trackers(self, runtime, monkeypatch):
        from aquilia.devplatform.diagnostics.memory import MemoryUsageTracker

        MemoryUsageTracker.get_instance().start()
        ModuleReloadExecutor._pre_execv_cleanup()
        import tracemalloc

        assert not tracemalloc.is_tracing()

    async def test_partial_reload_no_modules(self, runtime):
        plan = ReloadPlan(strategy=ReloadStrategy.PARTIAL, reason="test", affected_modules=[])
        ex = ModuleReloadExecutor(plan, runtime)
        await ex.execute()  # must not raise with nothing to reload


class TestStateBridge:
    def test_snapshot_restore_roundtrip(self):
        reg = StateBridgeRegistry.get_instance()
        reg.register("db_connection_pool", object())
        snap = reg.snapshot()
        assert snap.has("db_connection_pool")
        reg.restore(snap)  # best-effort, must not raise

    def test_resource_snapshot_missing(self):
        snap = ResourceSnapshot()
        assert not snap.has("nope")
        assert snap.get("nope") is None

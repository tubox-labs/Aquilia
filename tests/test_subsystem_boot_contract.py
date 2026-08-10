"""
Boot-contract regression tests for the subsystem layer.

Each test here pins a fix from the 2026-08-09 subsystem audit and fails against
the pre-fix code:

- ``BootContext.di_containers()`` as the single DI resolution path (BUG-3/4)
- ``_timeout`` actually enforced in ``BaseSubsystem.initialize`` (ARCH-2)
- ``EffectSubsystem.health_check`` constructing a valid ``HealthStatus`` (BUG-2)
- ``HealthRegistry.register_check`` wiring for live ``/health`` (ISSUE-2/Gap 3)
- ``AdminRateLimiter.force_cleanup`` as public API (ISSUE-5)
"""

from __future__ import annotations

import asyncio

import pytest

from aquilia.health import HealthStatus, SubsystemStatus
from aquilia.subsystems import DI_CONTAINER_KEY, BaseSubsystem, BootContext


class _FakeContainer:
    """Minimal DI container double -- records what was registered."""

    def __init__(self) -> None:
        self.registered: list = []

    def register(self, provider) -> None:
        self.registered.append(provider)


class _FakeRuntimeRegistry:
    def __init__(self, containers: dict) -> None:
        self.di_containers = containers


# ---------------------------------------------------------------------------
# BootContext.di_containers -- BUG-3 / BUG-4
# ---------------------------------------------------------------------------


def test_di_containers_empty_without_registry_or_shared_container():
    ctx = BootContext(config={}, manifests=[])
    assert ctx.di_containers() == []


def test_di_containers_prefers_explicit_shared_container():
    explicit = _FakeContainer()
    other = _FakeContainer()
    ctx = BootContext(
        config={},
        manifests=[],
        registry=_FakeRuntimeRegistry({"app": other}),
        shared_state={DI_CONTAINER_KEY: explicit},
    )
    assert ctx.di_containers() == [explicit]


def test_di_containers_falls_back_to_every_runtime_container():
    a, b = _FakeContainer(), _FakeContainer()
    ctx = BootContext(config={}, manifests=[], registry=_FakeRuntimeRegistry({"a": a, "b": b}))
    assert set(map(id, ctx.di_containers())) == {id(a), id(b)}


def test_di_containers_ignores_objects_without_register():
    ctx = BootContext(config={}, manifests=[], shared_state={DI_CONTAINER_KEY: object()})
    assert ctx.di_containers() == []


async def test_storage_subsystem_registers_registry_into_di(tmp_path):
    """The canonical key must actually reach DI -- the old '_di_registry' never did."""
    from aquilia.storage.registry import StorageRegistry
    from aquilia.subsystems import StorageSubsystem

    container = _FakeContainer()
    ctx = BootContext(
        config={"storage": {"backends": [{"alias": "default", "backend": "local", "root": str(tmp_path)}]}},
        manifests=[],
        shared_state={DI_CONTAINER_KEY: container},
    )

    sub = StorageSubsystem()
    status = await sub.initialize(ctx)
    try:
        assert status.status is SubsystemStatus.HEALTHY, status.message
        # ValueProvider stringifies the token as "<module>.<qualname>".
        tokens = [p._meta.token for p in container.registered]
        assert f"{StorageRegistry.__module__}.{StorageRegistry.__qualname__}" in tokens
        assert ctx.shared_state["storage_registry"] is not None
    finally:
        await sub.shutdown()


async def test_storage_subsystem_registers_live_health_check(tmp_path):
    """/health must be able to re-run the check, not just read the boot snapshot."""
    from aquilia.subsystems import StorageSubsystem

    ctx = BootContext(
        config={"storage": {"backends": [{"alias": "default", "backend": "local", "root": str(tmp_path)}]}},
        manifests=[],
    )
    sub = StorageSubsystem()
    await sub.initialize(ctx)
    try:
        assert "storage" in ctx.health._checks
        results = await ctx.health.run_checks()
        assert results["storage"].status is SubsystemStatus.HEALTHY
    finally:
        await sub.shutdown()


# ---------------------------------------------------------------------------
# Timeout enforcement -- ARCH-2
# ---------------------------------------------------------------------------


class _HangingSubsystem(BaseSubsystem):
    _name = "hanging"
    _timeout = 0.05

    async def _do_initialize(self, ctx: BootContext) -> None:
        await asyncio.sleep(30)

    async def _do_shutdown(self) -> None:
        return None


class _UnboundedSubsystem(_HangingSubsystem):
    _name = "unbounded"
    _timeout = 0.0


async def test_initialize_enforces_timeout():
    sub = _HangingSubsystem()
    status = await asyncio.wait_for(sub.initialize(BootContext(config={}, manifests=[])), timeout=5)

    assert status.status is SubsystemStatus.UNHEALTHY
    assert "timed out" in status.message
    assert sub._initialized is False


async def test_zero_timeout_disables_the_bound():
    sub = _UnboundedSubsystem()
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(sub.initialize(BootContext(config={}, manifests=[])), timeout=0.1)


async def test_timeout_is_exposed_as_a_property():
    assert _HangingSubsystem().timeout == pytest.approx(0.05)


# ---------------------------------------------------------------------------
# EffectSubsystem.health_check -- BUG-1 / BUG-2 / ISSUE-4
# ---------------------------------------------------------------------------


class _FakeEffectRegistry:
    def __init__(self, report: dict) -> None:
        self._report = report

    async def health_check(self) -> dict:
        return self._report


async def test_effect_health_check_uses_details_not_metadata():
    """``metadata=`` raised TypeError; the payload belongs in ``details``."""
    from aquilia.subsystems import EffectSubsystem

    report = {"healthy": True, "provider_count": 3, "providers": {"a": {}}}
    sub = EffectSubsystem()
    sub._initialized = True
    sub._registry = _FakeEffectRegistry(report)

    status = await sub.health_check()

    assert isinstance(status, HealthStatus)
    assert status.status is SubsystemStatus.HEALTHY
    assert status.details == report
    assert "3 providers" in status.message


async def test_effect_health_check_degrades_when_registry_unhealthy():
    from aquilia.subsystems import EffectSubsystem

    sub = EffectSubsystem()
    sub._initialized = True
    sub._registry = _FakeEffectRegistry({"healthy": False, "provider_count": 1})

    assert (await sub.health_check()).status is SubsystemStatus.DEGRADED


async def test_effect_health_check_reports_stopped_before_init():
    from aquilia.subsystems import EffectSubsystem

    assert (await EffectSubsystem().health_check()).status is SubsystemStatus.STOPPED


# ---------------------------------------------------------------------------
# AdminRateLimiter.force_cleanup -- ISSUE-5
# ---------------------------------------------------------------------------


def test_force_cleanup_is_public_and_reports_counts():
    from aquilia.admin.security import AdminRateLimiter

    limiter = AdminRateLimiter()
    limiter.record_login_failure("10.0.0.1")
    limiter._login_records["login:10.0.0.1"].attempts = [0.0]  # ancient attempt
    limiter._login_records["login:10.0.0.1"].lockout_until = 0.0

    cleaned_login, cleaned_sensitive = limiter.force_cleanup()

    assert cleaned_login == 1
    assert cleaned_sensitive == 0
    assert "login:10.0.0.1" not in limiter._login_records


def test_force_cleanup_preserves_active_lockouts():
    import time

    from aquilia.admin.security import AdminRateLimiter

    limiter = AdminRateLimiter()
    limiter.record_login_failure("10.0.0.2")
    limiter._login_records["login:10.0.0.2"].lockout_until = time.monotonic() + 300

    assert limiter.force_cleanup() == (0, 0)
    assert "login:10.0.0.2" in limiter._login_records


# ---------------------------------------------------------------------------
# Live health refresh -- ISSUE-2 / Gap 3
# ---------------------------------------------------------------------------


async def test_run_checks_supersedes_stale_boot_snapshot():
    """A backend that dies after boot must surface, not stay HEALTHY forever."""
    from aquilia.health import HealthRegistry

    registry = HealthRegistry()
    alive = {"ok": True}

    def live_check() -> HealthStatus:
        return HealthStatus(
            name="storage",
            status=SubsystemStatus.HEALTHY if alive["ok"] else SubsystemStatus.UNHEALTHY,
            message="live",
        )

    registry.register("storage", live_check())
    registry.register_check("storage", live_check)

    assert registry.to_dict()["status"] == "healthy"

    alive["ok"] = False
    # Without the refresh the snapshot still claims healthy -- the audited bug.
    assert registry.to_dict()["status"] == "healthy"

    await registry.run_checks()
    assert registry.to_dict()["status"] == "unhealthy"


async def test_run_checks_is_safe_when_nothing_registered_a_check():
    """The /health refresh must be a no-op, not an error, with no live checks."""
    from aquilia.health import HealthRegistry

    registry = HealthRegistry()
    registry.register("cache", HealthStatus(name="cache", status=SubsystemStatus.HEALTHY))

    assert await registry.run_checks() == {}
    assert registry.to_dict()["status"] == "healthy"


# ---------------------------------------------------------------------------
# Workspace declaration detection -- Gap 4
# ---------------------------------------------------------------------------


class _WsShim:
    def __init__(self, obj) -> None:
        self.workspace_obj = obj
        self.root = None


def test_integration_lookup_ignores_builder_methods():
    """``Workspace.storage``/``vectordb`` are methods; they are not declarations."""
    from aquilia.cli.checks.subsystems import _integration
    from aquilia.workspace import Workspace

    bare = _WsShim(Workspace("demo"))

    for name in ("storage", "vectordb", "i18n", "tasks"):
        assert _integration(bare, name) is None, f"{name} falsely reported as declared"


def test_integration_lookup_finds_real_declaration():
    from aquilia.cli.checks.subsystems import _integration
    from aquilia.workspace import Workspace

    ws = Workspace("demo").storage(default="d", backends={})
    assert _integration(_WsShim(ws), "storage") is not None


def test_vectordb_driver_check_flags_missing_elips():
    """vectordb enabled without the ``elips`` driver is a hard boot failure."""
    import importlib.util
    from unittest.mock import patch

    from aquilia.cli.checks.subsystems import check_vectordb_driver
    from aquilia.workspace import Workspace

    ws = Workspace("demo")
    ws._integrations["vectordb"] = {"enabled": True, "stores": [{"alias": "main"}]}

    class _Ctx:
        workspace = _WsShim(ws)

    real_find_spec = importlib.util.find_spec

    def fake_find_spec(name, *args, **kwargs):
        return None if name == "elips" else real_find_spec(name, *args, **kwargs)

    with patch("aquilia.cli.checks.subsystems.importlib.util.find_spec", fake_find_spec):
        findings = list(check_vectordb_driver(_Ctx()))

    assert [f.code for f in findings] == ["AQ_VECTORDB_DRIVER_MISSING"]


def test_vectordb_driver_check_silent_when_not_declared():
    from aquilia.cli.checks.subsystems import check_vectordb_driver
    from aquilia.workspace import Workspace

    class _Ctx:
        workspace = _WsShim(Workspace("demo"))

    assert list(check_vectordb_driver(_Ctx())) == []


# ---------------------------------------------------------------------------
# Admin lifecycle wiring -- Gap 6
# ---------------------------------------------------------------------------


def _server(**integrations):
    from aquilia.config import ConfigLoader
    from aquilia.manifest import AppManifest
    from aquilia.server import AquiliaServer
    from aquilia.workspace import Workspace

    config = Workspace("admin-ws").to_dict()
    config.setdefault("integrations", {}).update(integrations)

    loader = ConfigLoader()
    loader.config_data = config
    loader._build_apps_namespace()

    return AquiliaServer(manifests=[AppManifest(name="app", version="0.0.1")], config=loader)


async def test_admin_lifecycle_starts_when_admin_is_configured():
    """``_wire_admin_integration`` wires routes only; the hooks must also run."""
    from aquilia.admin import get_admin_subsystems

    get_admin_subsystems().lifecycle._started = False

    server = _server(admin={"enabled": True})
    await server.startup()
    try:
        assert server._admin_subsystems is not None
        assert server._admin_subsystems.lifecycle._started is True
    finally:
        await server.shutdown()


async def test_admin_lifecycle_untouched_when_admin_absent():
    server = _server()
    await server.startup()
    try:
        assert server._admin_subsystems is None
    finally:
        await server.shutdown()

"""Regression tests for module-level manifest lifecycle hook resolution."""

import sys
import types
from types import SimpleNamespace

from aquilia.aquilary.core import AppContext, Aquilary, RuntimeRegistry
from aquilia.manifest import AppManifest, LifecycleConfig


def _make_modules_auth_lifecycle(on_startup, on_shutdown):
    modules_pkg = types.ModuleType("modules")
    modules_pkg.__path__ = []

    auth_pkg = types.ModuleType("modules.auth")
    auth_pkg.__path__ = []

    lifecycle_mod = types.ModuleType("modules.auth.lifecycle")
    lifecycle_mod.on_startup = on_startup
    lifecycle_mod.on_shutdown = on_shutdown

    return modules_pkg, auth_pkg, lifecycle_mod


def test_manifest_lifecycle_config_populates_app_context_hooks():
    """AppContext should take hooks from manifest.lifecycle config."""
    manifest = AppManifest(
        name="auth",
        version="1.0.0",
        lifecycle=LifecycleConfig(
            on_startup="lifecycle:on_startup",
            on_shutdown="lifecycle:on_shutdown",
        ),
    )

    config = SimpleNamespace(apps=SimpleNamespace())
    registry = Aquilary.from_manifests([manifest], config=config, mode="test")

    ctx = registry.app_contexts[0]
    assert ctx.on_startup == "lifecycle:on_startup"
    assert ctx.on_shutdown == "lifecycle:on_shutdown"


def test_runtime_resolves_module_relative_lifecycle_paths(monkeypatch):
    """Relative lifecycle hooks should resolve against the module package."""

    def startup(*_args, **_kwargs):
        return "startup"

    def shutdown(*_args, **_kwargs):
        return "shutdown"

    modules_pkg, auth_pkg, lifecycle_mod = _make_modules_auth_lifecycle(startup, shutdown)
    monkeypatch.setitem(sys.modules, "modules", modules_pkg)
    monkeypatch.setitem(sys.modules, "modules.auth", auth_pkg)
    monkeypatch.setitem(sys.modules, "modules.auth.lifecycle", lifecycle_mod)

    manifest_stub = SimpleNamespace(__module__="modules.auth.manifest")
    ctx = AppContext(
        name="auth",
        version="1.0.0",
        manifest=manifest_stub,
        config_namespace={},
        on_startup="lifecycle:on_startup",
        on_shutdown="lifecycle:on_shutdown",
    )

    runtime = RuntimeRegistry.from_metadata(SimpleNamespace(app_contexts=[ctx]), config=SimpleNamespace())
    runtime._resolve_lifecycle_hooks()

    assert ctx.on_startup is startup
    assert ctx.on_shutdown is shutdown


def test_runtime_resolves_explicit_module_lifecycle_paths(monkeypatch):
    """Explicit module paths should continue to resolve unchanged."""

    def startup(*_args, **_kwargs):
        return "startup"

    def shutdown(*_args, **_kwargs):
        return "shutdown"

    modules_pkg, auth_pkg, lifecycle_mod = _make_modules_auth_lifecycle(startup, shutdown)
    monkeypatch.setitem(sys.modules, "modules", modules_pkg)
    monkeypatch.setitem(sys.modules, "modules.auth", auth_pkg)
    monkeypatch.setitem(sys.modules, "modules.auth.lifecycle", lifecycle_mod)

    manifest_stub = SimpleNamespace(__module__="modules.auth.manifest")
    ctx = AppContext(
        name="auth",
        version="1.0.0",
        manifest=manifest_stub,
        config_namespace={},
        on_startup="modules.auth.lifecycle:on_startup",
        on_shutdown="modules.auth.lifecycle:on_shutdown",
    )

    runtime = RuntimeRegistry.from_metadata(SimpleNamespace(app_contexts=[ctx]), config=SimpleNamespace())
    runtime._resolve_lifecycle_hooks()

    assert ctx.on_startup is startup
    assert ctx.on_shutdown is shutdown

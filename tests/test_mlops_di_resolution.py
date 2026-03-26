"""Regression tests for MLOps DI resolution and lifecycle wiring."""

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Annotated, Any

import pytest

from aquilia.di.core import Container
from aquilia.di.decorators import Inject
from aquilia.di.errors import ProviderNotFoundError
from aquilia.di.providers import ClassProvider
from aquilia.faults.domains import ProviderNotFoundFault
from aquilia.lifecycle import LifecycleCoordinator
from aquilia.mlops.di.providers import register_mlops_providers
from aquilia.mlops.engine.lifecycle import mlops_on_startup
from aquilia.mlops.orchestrator.loader import ModelLoader
from aquilia.mlops.orchestrator.orchestrator import ModelOrchestrator
from aquilia.mlops.orchestrator.registry import ModelRegistry
from aquilia.mlops.orchestrator.router import VersionRouter


@pytest.mark.asyncio
async def test_register_mlops_providers_registers_orchestrator_stack() -> None:
    """MLOps DI wiring should register and resolve the full orchestrator stack."""
    container = Container(scope="app")

    register_mlops_providers(
        container,
        {
            "enabled": True,
            "plugin_auto_discover": False,
            "registry_db": ":memory:",
        },
    )

    assert container.is_registered(ModelRegistry)
    assert container.is_registered(VersionRouter)
    assert container.is_registered(ModelLoader)
    assert container.is_registered(ModelOrchestrator)

    orchestrator = await container.resolve_async(ModelOrchestrator)
    assert isinstance(orchestrator, ModelOrchestrator)
    assert isinstance(orchestrator._registry, ModelRegistry)
    assert isinstance(orchestrator._router, VersionRouter)
    assert isinstance(orchestrator._loader, ModelLoader)


@pytest.mark.asyncio
async def test_model_orchestrator_injection_requires_no_manual_fallback() -> None:
    """A class that depends on ModelOrchestrator should resolve directly via DI."""

    class InferenceConsumer:
        def __init__(
            self,
            orchestrator: Annotated[ModelOrchestrator, Inject(token=ModelOrchestrator)],
        ):
            self.orchestrator = orchestrator

    container = Container(scope="app")
    register_mlops_providers(container, {"enabled": True, "plugin_auto_discover": False})
    container.register(ClassProvider(InferenceConsumer, scope="singleton"))

    consumer = await container.resolve_async(InferenceConsumer)
    assert isinstance(consumer.orchestrator, ModelOrchestrator)


@pytest.mark.asyncio
async def test_register_mlops_providers_is_idempotent() -> None:
    """Repeated registration should not fail or duplicate orchestrator bindings."""
    container = Container(scope="app")

    register_mlops_providers(container, {"enabled": True, "plugin_auto_discover": False})
    first = await container.resolve_async(ModelOrchestrator)

    register_mlops_providers(container, {"enabled": True, "plugin_auto_discover": False})
    second = await container.resolve_async(ModelOrchestrator)

    assert first is second


@dataclass
class _LifecycleTestConfig:
    """Small Config-like object for lifecycle tests."""

    startup_hook: str
    payload: dict[str, Any]

    def get(self, key: str, default: Any = None) -> Any:
        if key == "on_startup":
            return self.startup_hook
        if key == "on_shutdown":
            return None
        return default

    def to_dict(self) -> dict[str, Any]:
        return self.payload


@pytest.mark.asyncio
async def test_global_startup_registers_orchestrator_before_app_startup() -> None:
    """Global startup hook should receive a DI container and wire providers first."""
    container = Container(scope="app")
    seen = {"registered_before_app_hook": False}

    async def app_startup(_config_ns: dict[str, Any], di_container: Container | None) -> None:
        seen["registered_before_app_hook"] = bool(
            di_container is not None and di_container.is_registered(ModelOrchestrator)
        )

    ctx = SimpleNamespace(
        name="app",
        on_startup=app_startup,
        on_shutdown=None,
        config_namespace={},
    )
    runtime = SimpleNamespace(
        meta=SimpleNamespace(app_contexts=[ctx]),
        di_containers={"app": container},
    )
    config = _LifecycleTestConfig(
        startup_hook="aquilia.mlops.engine.lifecycle:mlops_on_startup",
        payload={"enabled": True, "plugins": {"auto_discover": False}},
    )

    coordinator = LifecycleCoordinator(runtime, config)
    await coordinator.startup()

    assert seen["registered_before_app_hook"] is True


@pytest.mark.asyncio
async def test_mlops_startup_hook_registers_orchestrator_integration_path() -> None:
    """Integration lifecycle hook should register ModelOrchestrator in DI."""
    container = Container(scope="app")

    await mlops_on_startup(
        config={
            "enabled": True,
            "plugins": {"auto_discover": False},
            "registry": {"db_path": ":memory:"},
        },
        di_container=container,
    )

    orchestrator = await container.resolve_async(ModelOrchestrator)
    assert isinstance(orchestrator, ModelOrchestrator)


@pytest.mark.asyncio
async def test_missing_orchestrator_provider_raises_clear_error() -> None:
    """Unwired DI should fail explicitly (no hidden fallback construction)."""
    container = Container(scope="app")

    with pytest.raises(ProviderNotFoundError) as exc_info:
        await container.resolve_async(ModelOrchestrator)

    assert "aquilia.mlops.orchestrator.orchestrator.ModelOrchestrator" in str(exc_info.value)


@pytest.mark.asyncio
async def test_missing_orchestrator_maps_to_provider_not_found_fault() -> None:
    """Regression for expected PROVIDER_NOT_FOUND fault payload semantics."""
    # Save originals to avoid leaking monkey patches across tests.
    from aquilia.di.core import Container as DIContainer
    from aquilia.faults.integrations.di import patch_di_container

    original_resolve = DIContainer.resolve
    original_resolve_async = DIContainer.resolve_async
    original_register = DIContainer.register

    patch_di_container()
    try:
        container = Container(scope="app")
        with pytest.raises(ProviderNotFoundFault) as exc_info:
            await container.resolve_async(ModelOrchestrator)

        fault = exc_info.value
        assert fault.code == "PROVIDER_NOT_FOUND"
        assert "ModelOrchestrator" in fault.message
        assert fault.domain.name.lower() == "di"
    finally:
        DIContainer.resolve = original_resolve
        DIContainer.resolve_async = original_resolve_async
        DIContainer.register = original_register

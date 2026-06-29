import pytest

from aquilia.inspector.middleware import InspectorMiddleware
from aquilia.manifest import AppManifest
from aquilia.server import AquiliaServer
from aquilia.workspace import Workspace


def test_workspace_fluent_config():
    ws = Workspace("test-ws")
    ws.inspector(enabled=True, ring_buffer_size=42)
    cfg = ws.to_dict()
    assert cfg["inspector"]["enabled"] is True
    assert cfg["inspector"]["ring_buffer_size"] == 42
    assert cfg["integrations"]["inspector"]["ring_buffer_size"] == 42


@pytest.mark.asyncio
async def test_server_wires_inspector_when_enabled():
    manifest = AppManifest(name="test_app", version="0.0.1")
    ws = Workspace("test-ws").inspector(enabled=True)

    # Load config loader
    from aquilia.config import ConfigLoader

    config_loader = ConfigLoader()
    config_loader.config_data = ws.to_dict()
    config_loader._build_apps_namespace()

    server = AquiliaServer(manifests=[manifest], config=config_loader)

    # Check if InspectorMiddleware is in the middleware stack at priority 11
    middlewares = [mw for mw in server.middleware_stack.middlewares if isinstance(mw.middleware, InspectorMiddleware)]
    assert len(middlewares) == 1
    assert middlewares[0].priority == 11

    # Check if DI diagnostic listeners were added to app containers
    for container in server.runtime.di_containers.values():
        assert len(container._diagnostics._listeners) > 0

    # Check if fault listener was registered on FaultEngine
    assert len(server.fault_engine._event_listeners) > 0


@pytest.mark.asyncio
async def test_server_does_not_wire_inspector_when_disabled():
    manifest = AppManifest(name="test_app", version="0.0.1")
    ws = Workspace("test-ws").inspector(enabled=False)

    from aquilia.config import ConfigLoader

    config_loader = ConfigLoader()
    config_loader.config_data = ws.to_dict()
    config_loader._build_apps_namespace()

    server = AquiliaServer(manifests=[manifest], config=config_loader)

    # Check that InspectorMiddleware is NOT registered
    middlewares = [mw for mw in server.middleware_stack.middlewares if isinstance(mw.middleware, InspectorMiddleware)]
    assert len(middlewares) == 0

    # Check that DI diagnostics is empty
    for container in server.runtime.di_containers.values():
        assert len(container._diagnostics._listeners) == 0

    # Fault engine listeners should not contain our listener (though other listeners like error tracker might exist)
    for listener in server.fault_engine._event_listeners:
        assert "fault_listener" not in str(listener)

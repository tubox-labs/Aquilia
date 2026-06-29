import pytest

from aquilia.manifest import AppManifest
from aquilia.testing import TestClient, TestServer
from aquilia.workspace import Workspace


def make_manifest():
    return AppManifest(
        name="test_ui_app",
        version="0.0.1",
    )


@pytest.mark.asyncio
async def test_standalone_ui_accessible_in_debug_without_auth():
    manifest = make_manifest()
    ws = Workspace("test-ws").inspector(enabled=True)

    from aquilia.config import ConfigLoader

    config_loader = ConfigLoader()
    config_loader.config_data = ws.to_dict()
    config_loader.config_data["debug"] = True
    config_loader._build_apps_namespace()

    async with TestServer(manifests=[manifest], config=config_loader, debug=True) as server:
        client = TestClient(server.app)
        response = await client.get("/__aquilia__/inspector/")
        assert response.status_code == 200
        assert b"Request Inspector" in response.body


@pytest.mark.asyncio
async def test_standalone_ui_forbidden_in_prod_without_auth(monkeypatch):
    # Ensure AQUILIA_ENV is NOT dev
    monkeypatch.setenv("AQUILIA_ENV", "production")

    manifest = make_manifest()
    ws = Workspace("test-ws").inspector(enabled=True)

    from aquilia.config import ConfigLoader

    config_loader = ConfigLoader()
    config_loader.config_data = ws.to_dict()
    config_loader.config_data["debug"] = False
    config_loader.config_data["reload"] = False
    config_loader._build_apps_namespace()

    # Pass debug=False to TestServer to prevent debug override
    async with TestServer(manifests=[manifest], config=config_loader, debug=False) as server:
        client = TestClient(server.app)
        response = await client.get("/__aquilia__/inspector/")
        assert response.status_code == 403

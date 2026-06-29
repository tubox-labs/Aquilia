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


@pytest.mark.asyncio
async def test_admin_panel_inspector_view_rendering():
    from unittest.mock import MagicMock

    from aquilia.admin.controller import AdminController
    from aquilia.admin.site import AdminSite
    from aquilia.response import Response

    site = AdminSite(title="Custom Title Portal")
    site.admin_config = MagicMock()
    site.admin_config.is_module_enabled.return_value = True

    ctrl = AdminController(site=site)
    ctrl._ensure_csrf = MagicMock()
    ctrl._ensure_initialized = MagicMock()

    # Mock identity and permission checks
    import aquilia.admin.controller as ctrl_mod

    # Temporarily mock helper functions
    original_require = ctrl_mod._require_identity
    original_has_perm = ctrl_mod.has_admin_permission
    original_secure_html = ctrl_mod._secure_html_response
    original_get_name = ctrl_mod._get_identity_name
    original_get_avatar = ctrl_mod._get_identity_avatar

    mock_identity = MagicMock()
    ctrl_mod._require_identity = lambda ctx: (mock_identity, None)
    ctrl_mod.has_admin_permission = lambda identity, perm: True
    ctrl_mod._get_identity_name = lambda identity: "Developer"
    ctrl_mod._get_identity_avatar = lambda identity: ""
    ctrl_mod._secure_html_response = lambda html, site_obj: Response(html.encode("utf-8"), status=200)

    try:
        request = MagicMock()
        request.path = "/admin/inspector/"
        ctx = MagicMock()

        res = await ctrl.inspector_view(request, ctx)
        assert res.status == 200
        # Verify the custom title got passed and rendered in the HTML
        assert b"Custom Title Portal" in res._content
    finally:
        ctrl_mod._require_identity = original_require
        ctrl_mod.has_admin_permission = original_has_perm
        ctrl_mod._secure_html_response = original_secure_html
        ctrl_mod._get_identity_name = original_get_name
        ctrl_mod._get_identity_avatar = original_get_avatar

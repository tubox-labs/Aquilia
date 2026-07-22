from __future__ import annotations

import tempfile
import shutil
from pathlib import Path
import pytest

from aquilia import Workspace, Controller, GET, RequestCtx, Response, AppManifest
from aquilia.testing import TestClient
from aquilia.runtime import AquiliaRuntime
from aquilia.integrations import TemplatesIntegration


@pytest.mark.asyncio
async def test_issue59_controller_render_resolution(tmp_path):
    """
    Verify issue #59: self.render() works in controller route handlers
    both with explicit TemplatesIntegration and auto-detected template directory.
    """
    mod_dir = tmp_path / "modules" / "web"
    mod_dir.mkdir(parents=True, exist_ok=True)
    (mod_dir / "__init__.py").write_text("", encoding="utf-8")
    (mod_dir / "manifest.py").write_text("""
from aquilia import AppManifest
manifest = AppManifest(
    name="web",
    version="1.0.0",
    controllers=["modules.web.controllers:StarterController"]
)
""", encoding="utf-8")
    (mod_dir / "controllers.py").write_text("""
from aquilia import Controller, GET, RequestCtx, Response
class StarterController(Controller):
    prefix = ""
    @GET("/")
    async def welcome(self, ctx: RequestCtx):
        return await self.render("issue59_welcome.html", {"title": "Aquilia App"})
""", encoding="utf-8")

    (tmp_path / "templates").mkdir(exist_ok=True)
    (tmp_path / "templates" / "issue59_welcome.html").write_text("<h1>{{ title }}</h1>", encoding="utf-8")

    ws_code = """
from aquilia import Workspace, Module, AquilaConfig
from aquilia.integrations import (
    MiddlewareChain,
    DiIntegration,
    RoutingIntegration,
    FaultHandlingIntegration,
    PatternsIntegration,
    DatabaseIntegration,
    TemplatesIntegration,
)

class BaseEnv(AquilaConfig):
    env = "dev"
    class server(AquilaConfig.Server):
        host = "127.0.0.1"
        port = 8000

workspace = (
    Workspace("app", version="1.0.0")
    .env_config(BaseEnv)
    .module(Module("web", version="1.0.0").route_prefix(""))
    .middleware(MiddlewareChain.minimal())
    .integrate(DiIntegration(auto_wire=True))
    .integrate(RoutingIntegration(strict_matching=True))
    .integrate(FaultHandlingIntegration(default_strategy="propagate"))
    .integrate(PatternsIntegration())
    .integrate(DatabaseIntegration(url="sqlite:///:memory:"))
    .integrate(
        TemplatesIntegration.builder()
        .source("templates")
        .scan_modules()
        .cached("memory")
        .secure()
    )
)
"""
    (tmp_path / "workspace.py").write_text(ws_code, encoding="utf-8")

    import sys
    for mod_name in list(sys.modules.keys()):
        if "web" in mod_name or mod_name.startswith("modules"):
            sys.modules.pop(mod_name, None)

    sys.path.insert(0, str(tmp_path))

    try:
        runtime = AquiliaRuntime.from_workspace(workspace_root=tmp_path, mode="dev")
        await runtime.server.startup()
        if getattr(runtime.server, "template_engine", None):
            print("LOADER SEARCH PATHS:", runtime.server.template_engine.loader.search_paths)
        client = TestClient(runtime.server)
        response = await client.get("/web/")
        assert response.status_code == 200
        assert "<h1>Aquilia App</h1>" in response.text
    finally:
        if str(tmp_path) in sys.path:
            sys.path.remove(str(tmp_path))

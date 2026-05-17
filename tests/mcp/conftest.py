from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def mcp_repo(tmp_path: Path) -> Path:
    root = tmp_path
    (root / "aquilia" / "cli").mkdir(parents=True)
    (root / "aquilia" / "aquilary").mkdir(parents=True)
    (root / "docs").mkdir()
    (root / "examples" / "crud_app" / "modules" / "projects").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "aquilia" / "__init__.py").write_text("__version__ = '0.1.0'\n", encoding="utf-8")
    (root / "aquilia" / "runtime.py").write_text(
        """
class AquiliaRuntime:
    def configure(self): pass
    def discover(self): pass
    def bootstrap(self): pass
""",
        encoding="utf-8",
    )
    (root / "aquilia" / "entrypoint.py").write_text(
        "from .runtime import AquiliaRuntime\napp = AquiliaRuntime.from_workspace() if False else None\n",
        encoding="utf-8",
    )
    (root / "aquilia" / "config.py").write_text(
        "class ConfigLoader:\n    def _load_yaml_file(self, path):\n        'YAML configuration is no longer supported'\n",
        encoding="utf-8",
    )
    (root / "aquilia" / "manifest.py").write_text(
        """
class AppManifest:
    controllers = []
    services = []
    socket_controllers = []
    # AppManifest.database is deprecated and ignored at runtime.
    # AppManifest.route_prefix is deprecated.
class DatabaseConfig: pass
""",
        encoding="utf-8",
    )
    (root / "aquilia" / "config_builders.py").write_text(
        """
class Workspace: pass
class Module:
    def route_prefix(self, prefix): return self
    def register_controllers(self): 'deprecated'
""",
        encoding="utf-8",
    )
    (root / "aquilia" / "asgi.py").write_text(
        "class ASGIAdapter:\n    def handle_http(self): pass\n    def handle_websocket(self): pass\n    def handle_lifespan(self): pass\n",
        encoding="utf-8",
    )
    (root / "aquilia" / "server.py").write_text("class AquiliaServer: pass\n", encoding="utf-8")
    (root / "aquilia" / "aquilary" / "core.py").write_text(
        "# workspace prefix AppManifest.route_prefix\nclass Aquilary: pass\n",
        encoding="utf-8",
    )
    (root / "aquilia" / "cli" / "__main__.py").write_text(
        """
import click
@click.group()
def cli(): pass
@cli.command("validate")
def validate(): '''Validate workspace.'''
@cli.group("mcp")
def mcp(): '''MCP commands.'''
@mcp.command("list-tools")
def list_tools(): pass
""",
        encoding="utf-8",
    )
    (root / "docs" / "README.md").write_text("# Docs\nAquilia runtime docs\n", encoding="utf-8")
    (root / "examples" / "crud_app" / "README.md").write_text("# CRUD\n", encoding="utf-8")
    (root / "examples" / "crud_app" / "workspace.py").write_text(
        'from aquilia import Workspace, Module\nworkspace = Workspace("crud").module(Module("projects").route_prefix("/projects"))\n',
        encoding="utf-8",
    )
    (root / "examples" / "crud_app" / "modules" / "projects" / "manifest.py").write_text(
        'from aquilia import AppManifest\nmanifest = AppManifest(name="projects", version="0.1.0")\n',
        encoding="utf-8",
    )
    (root / "tests" / "test_runtime.py").write_text("def test_smoke(): assert True\n", encoding="utf-8")
    return root

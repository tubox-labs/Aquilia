from __future__ import annotations

import os
import tempfile
from pathlib import Path

from aquilia import AquilaConfig, Env, Module, Workspace
from aquilia.config import ConfigLoader
from aquilia.integrations import DiIntegration, FaultHandlingIntegration, RoutingIntegration
from aquilia.runtime import AquiliaRuntime, RuntimeConfig, RuntimePhase


class BaseEnv(AquilaConfig):
    env = Env("AQ_ENV", default="dev")
    signing_key = Env("AQ_SIGNING_KEY", default="dev-secret-key-that-is-long-enough-for-examples")


def build_workspace() -> Workspace:
    return (
        Workspace("reference-runtime", version="1.0.0", description="Runtime lifecycle reference")
        .env_config(BaseEnv)
        .runtime(mode="test", host="127.0.0.1", port=8123, reload=False)
        .module(Module("health", version="1.0.0").route_prefix("/health").tags("core", "runtime"))
        .integrate(DiIntegration(auto_wire=True))
        .integrate(RoutingIntegration(strict_matching=True))
        .integrate(FaultHandlingIntegration(default_strategy="propagate"))
    )


def _write_runtime_workspace(root: Path) -> None:
    (root / "modules" / "health").mkdir(parents=True)
    (root / "modules" / "__init__.py").write_text("", encoding="utf-8")
    (root / "modules" / "health" / "__init__.py").write_text("", encoding="utf-8")
    (root / "workspace.py").write_text(
        """
from aquilia import Module, Workspace
from aquilia.integrations import DiIntegration, RoutingIntegration

workspace = (
    Workspace("reference-runtime", version="1.0.0")
    .runtime(mode="test", host="127.0.0.1", port=8123, reload=False)
    .module(Module("health", version="1.0.0").route_prefix("/health"))
    .integrate(DiIntegration(auto_wire=True))
    .integrate(RoutingIntegration(strict_matching=True))
)
""".lstrip(),
        encoding="utf-8",
    )
    (root / "modules" / "health" / "controllers.py").write_text(
        """
from aquilia import Controller, GET, RequestCtx, Response


class HealthController(Controller):
    prefix = "/"

    @GET("/")
    async def index(self, ctx: RequestCtx):
        return Response.json({"status": "ok"})
""".lstrip(),
        encoding="utf-8",
    )
    (root / "modules" / "health" / "manifest.py").write_text(
        """
from aquilia import AppManifest

manifest = AppManifest(
    name="health",
    version="1.0.0",
    controllers=["modules.health.controllers:HealthController"],
)
""".lstrip(),
        encoding="utf-8",
    )


async def run() -> dict:
    previous_env = os.environ.get("AQ_ENV")
    previous_secret = os.environ.get("AQ_SECRET_KEY")
    os.environ["AQ_ENV"] = "test"
    os.environ["AQ_SECRET_KEY"] = "reference-suite-secret-key-32-bytes-minimum"
    try:
        workspace = build_workspace()
        workspace_config = workspace.to_dict()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_runtime_workspace(root)
            loader = ConfigLoader.load(paths=[str(root / "workspace.py")])
            runtime = AquiliaRuntime(RuntimeConfig(workspace_root=root, mode="test", debug=True))
            runtime.configure().discover().bootstrap()
            return {
                "workspace": workspace_config["workspace"]["name"],
                "modules": runtime.module_names,
                "runtime_phase": runtime.phase.value,
                "loader_runtime_mode": loader.get("runtime.mode"),
                "app_is_ready": runtime.phase == RuntimePhase.READY and callable(runtime.app),
            }
    finally:
        if previous_env is None:
            os.environ.pop("AQ_ENV", None)
        else:
            os.environ["AQ_ENV"] = previous_env
        if previous_secret is None:
            os.environ.pop("AQ_SECRET_KEY", None)
        else:
            os.environ["AQ_SECRET_KEY"] = previous_secret
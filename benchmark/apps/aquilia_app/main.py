from __future__ import annotations

from pathlib import Path

from aquilia.runtime import AquiliaRuntime

WORKSPACE_ROOT = Path(__file__).resolve().parent
runtime = AquiliaRuntime.from_workspace(workspace_root=WORKSPACE_ROOT, mode="prod")
server = runtime.server
app = server.app

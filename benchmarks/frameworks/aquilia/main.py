from __future__ import annotations

from pathlib import Path
from aquilia.runtime import AquiliaRuntime

from aquilia.db.engine import configure_database

WORKSPACE_ROOT = Path(__file__).resolve().parent
DB_FILE = WORKSPACE_ROOT.parents[2] / "benchmarks" / "techempower" / "techempower.db"
configure_database(f"sqlite:///{DB_FILE.resolve()}")

runtime = AquiliaRuntime.from_workspace(workspace_root=WORKSPACE_ROOT, mode="prod")
server = runtime.server
app = server.app

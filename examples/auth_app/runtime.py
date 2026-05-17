from pathlib import Path

from aquilia.runtime import AquiliaRuntime, RuntimeConfig

runtime = AquiliaRuntime(
    RuntimeConfig(workspace_root=Path(__file__).parent, mode="dev", debug=True)
).configure().discover().bootstrap()

app = runtime.app

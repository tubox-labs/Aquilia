from pathlib import Path

from aquilia.runtime import AquiliaRuntime

runtime = AquiliaRuntime.from_workspace(Path(__file__).parent, mode="dev")
app = runtime.app

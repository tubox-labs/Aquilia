# Sqlite Examples

Native async SQLite compatibility layer, connection pool, transactions, cursors, rows, PRAGMAs, backup, metrics, and errors.

Examples here use public symbols and checked patterns from the repository. When a module has no safe standalone constructor example, the example focuses on importing and wiring the actual source-backed API.

## Source-Backed Import Examples

```python
from aquilia.sqlite._backup import backup_database
from aquilia.sqlite._compat import CompatConnection
from aquilia.sqlite._compat import connect
from aquilia.sqlite._config import SqlitePoolConfig
from aquilia.sqlite._connection import AsyncConnection
from aquilia.sqlite._cursor import AsyncCursor
```

## Workspace/Manifest Wiring Example

```python
from aquilia import AppManifest, Integration, Module, Workspace

workspace = (
    Workspace("example", version="1.0.0")
    .runtime(mode="dev", port=8000)
    .module(Module("example").route_prefix("/example"))
    .integrate(Integration.di(auto_wire=True))
)

manifest = AppManifest(
    name="example",
    version="1.0.0",
    controllers=["modules.example.controllers:ExampleController"],
    services=["modules.example.services:ExampleService"],
)
```

## Verification

- Run `python -m aquilia.cli.__main__ --help` to confirm CLI availability.
- Run `aq validate` in a workspace to validate manifest paths.
- Run related tests under `tests/` or `examples/*/tests/` for executable behavior.

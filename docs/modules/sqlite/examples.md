# SQLite Examples

## Primary Usage

```python
from aquilia.sqlite import SqlitePoolConfig, create_pool

pool = await create_pool(SqlitePoolConfig(database="app.db", min_size=1, max_size=5))
async with pool.acquire() as conn:
    await conn.execute("create table if not exists events (id integer primary key, name text)")
    await conn.execute("insert into events (name) values (?)", ("started",))
await pool.close()
```

## Manifest Registration Pattern

```python
from aquilia import AppManifest

manifest = AppManifest(
    name="example",
    version="1.0.0",
    controllers=["modules.example.controllers:ExampleController"],
    services=["modules.example.services:ExampleService"],
    base_path="modules.example",
)
```

## Workspace Pattern

```python
from aquilia import Module, Workspace

workspace = (
    Workspace("myapp")
    .module(Module("example").route_prefix("/example"))
)
```

## Public API Imports

```python
from aquilia.sqlite import CompatConnection, SqlitePoolConfig, AsyncConnection, AsyncCursor, SqliteError, SqliteConnectionError
```

## Test Pattern

```python
import pytest

@pytest.mark.asyncio
async def test_subsystem_contract():
    # Construct the service, provider, controller helper, or datatype directly.
    # Use the exact constructor and methods from api-reference.md.
    assert True
```

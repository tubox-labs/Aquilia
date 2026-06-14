# Dotenv

> `aquilia.dotenv` — Zero-dependency `.env` file loader

The dotenv module provides automatic loading of environment variables from `.env` files without external dependencies. It integrates seamlessly with the Aquilia configuration system and respects existing environment variables.

## Architecture

```
.env file → DotEnv.parse() → dict → os.environ (optional)
                                      → AquiliaConfig (typed)
```

## Key Classes

| Class | Purpose |
|---|---|
| `DotEnv` | Core parser with `parse()`, `load()`, and `values()` |
| `DotEnvLoader` | Configuration-aware loader with workspace integration |

## Quick Start

```python
from aquilia.dotenv import load_dotenv

# Load .env from current directory
load_dotenv()

# Now os.environ has your values
import os
print(os.environ.get("DATABASE_URL"))
```

## Supported Syntax

```bash
# Comments
SIMPLE=value
QUOTED="value with spaces"
SINGLE='value with spaces'
EXPORT=exported value
export EXPORTED=also works

# Variable interpolation
BASE_URL=http://localhost
API_URL=${BASE_URL}/api
ALT_SYNTAX=$BASE_URL/alt

# Multiline values (with quotes)
MULTILINE="line1
line2
line3"
```

## API Reference

### `load_dotenv()`

```python
def load_dotenv(
    dotenv_path: str | Path | None = None,
    override: bool = False,
    encoding: str = "utf-8",
    verbose: bool = False,
) -> bool:
    """Load .env file into os.environ. Returns True if loaded."""
```

```python
from aquilia.dotenv import load_dotenv

# Load default .env
load_dotenv()

# Load specific file with override
load_dotenv("/path/to/.env.production", override=True)

# Returns False if no .env found
if not load_dotenv():
    print("No .env file found, using existing environment")
```

### `dotenv_values()`

```python
def dotenv_values(
    dotenv_path: str | Path | None = None,
    encoding: str = "utf-8",
    interpolate: bool = True,
) -> dict[str, str]:
    """Parse .env file and return dict WITHOUT modifying os.environ."""
```

```python
from aquilia.dotenv import dotenv_values

# Just read values
settings = dotenv_values(".env.test")
print(settings["DATABASE_URL"])
```

### `find_dotenv()`

```python
def find_dotenv(
    filename: str = ".env",
    raise_error_if_not_found: bool = False,
    usecwd: bool = False,
) -> str:
    """Search for .env file in parent directories."""
```

```python
from aquilia.dotenv import find_dotenv

# Auto-discover .env file
path = find_dotenv()
# Searches from cwd up to root

# Find specific env file
path = find_dotenv(".env.staging")
```

### `DotEnv.parse()`

```python
from aquilia.dotenv import DotEnv

# Parse without loading
env = DotEnv.parse(".env")
print(env)  # {"DATABASE_URL": "...", "SECRET_KEY": "..."}
```

### `DotEnv.load()`

```python
# Load with options
DotEnv.load(".env", override=True, encoding="utf-8")
```

## State Management

```python
from aquilia.dotenv import (
    is_dotenv_loaded,
    ensure_dotenv_loaded,
    reset_dotenv_state,
)

# Check if .env was already loaded
if not is_dotenv_loaded():
    load_dotenv()

# Ensure it's loaded exactly once (idempotent)
ensure_dotenv_loaded()

# Reset for testing
reset_dotenv_state()
```

## Integration with AquiliaConfig

```python
from aquilia.dotenv import load_dotenv
from aquilia.config import AquilaConfig, Env, Secret

# Load .env first
load_dotenv()

# Then use typed config
config = AquilaConfig(
    database_url=Env("DATABASE_URL"),
    api_key=Secret("API_KEY"),
    debug=Env("DEBUG", cast=bool, default=False),
)
```

## Security

- **No shell execution** — Values are parsed, not evaluated
- **No pickle or eval** — Purely string parsing
- **Strips BOM** — Handles UTF-8 with byte order marks
- **Validates variable names** — Only alphanumeric + underscore allowed
- **Respects existing** — Does not overwrite variables already in the environment
- **Singleton pattern** — Files loaded exactly once to prevent race conditions

## Error Handling

```python
from aquilia.dotenv import load_dotenv, find_dotenv

try:
    path = find_dotenv(raise_error_if_not_found=True)
    load_dotenv(path)
except FileNotFoundError:
    logger.warning("No .env file found")
    # Fall back to existing environment
```

## Related

- [Entrypoint](entrypoint.md) — Dotenv is loaded before the runtime configures
- [Runtime](runtime.md) — RuntimeConfig can specify custom `.env` file paths
- [integrations](../integrations/index.md) — Type-safe configuration via `Env` and `Secret`
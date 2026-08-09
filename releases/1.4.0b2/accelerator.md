# Accelerator Configuration — v1.4.0b2

## Overview

Aquilia v1.4.0b2 adds a coherent, layered configuration system for the two native C++ engine accelerators introduced in v1.4.0b1. The fail-soft behavior is unchanged — absent native extensions degrade to pure Python automatically. This release adds explicit control for teams that need deterministic engine selection in CI pipelines, debugging sessions, and restricted environments.

---

## `AquilaConfig.Accelerator`

A new `AquilaConfig.Accelerator` inner class in `aquilia/pyconfig.py`:

```python
class AquilaConfig:
    class Accelerator:
        """Native C++ engine configuration."""
        
        #: Enable the C++ request engine (router + RequestContext).
        #: Maps to AQUILIA_ENGINE environment variable.
        engine: bool = True
        
        #: Enable the C++ data engine (ORM FieldPlan + Contract hydration).
        #: Maps to AQUILIA_DATAENGINE environment variable.
        dataengine: bool = True
```

### Engine Descriptions

**`engine` (`AQUILIA_ENGINE`)**
The *request* engine — C++ radix-trie router and `RequestContext`. Active on every HTTP request. Disabling it trades throughput for pure-Python reproducibility.

**`dataengine` (`AQUILIA_DATAENGINE`)**
The *data* engine — C++ `FieldPlan`/`TypeCode` used by the ORM query compiler and the Contract hydration path. Only active when an app touches the ORM or contracts.

The two engines are **independent**: you can disable one while keeping the other.

---

## Workspace Configuration

```python
# workspace.py
from aquilia.pyconfig import AquilaConfig
from aquilia.integrations import Env

class BaseEnv(AquilaConfig):
    class accelerator(AquilaConfig.Accelerator):
        engine = True      # default: C++ router enabled
        dataengine = True  # default: C++ ORM enabled

# CI / integration-test environment forcing pure Python
class CIEnv(BaseEnv):
    env = "ci"
    class accelerator(BaseEnv.accelerator):
        engine = Env("AQUILIA_ENGINE", default=False, cast=bool)
        dataengine = Env("AQUILIA_DATAENGINE", default=False, cast=bool)

# Debugging: disable C++ router, keep C++ ORM
class DebugEnv(BaseEnv):
    env = "debug"
    class accelerator(BaseEnv.accelerator):
        engine = False
        dataengine = True
```

---

## Environment Variable Override

```bash
# Force pure-Python router
export AQUILIA_ENGINE=0

# Force pure-Python ORM compiler
export AQUILIA_DATAENGINE=0

# Both
export AQUILIA_ENGINE=0 AQUILIA_DATAENGINE=0
```

**Important**: A pre-existing environment variable is **never** overwritten by `workspace.py`. Setting `AQUILIA_ENGINE=0` in CI before launching the server guarantees pure-Python mode regardless of what `workspace.py` configures.

---

## CLI Flags

New flag pairs added to `aq run` and `aq dev`:

```bash
# Disable C++ router for this run
aq run --no-engine

# Disable C++ ORM compiler for this run
aq run --no-dataengine

# Both disabled — full pure-Python mode
aq run --no-engine --no-dataengine

# Explicitly enable (overrides env var that disabled them)
aq run --engine --dataengine

# Mixed mode: pure-Python router, native ORM
aq run --no-engine --dataengine
```

### Flag behavior

| Flag | Sets env var | Before workspace loading |
|---|---|---|
| `--engine` | `AQUILIA_ENGINE=1` | Yes — hot-reload workers inherit |
| `--no-engine` | `AQUILIA_ENGINE=0` | Yes — hot-reload workers inherit |
| `--dataengine` | `AQUILIA_DATAENGINE=1` | Yes |
| `--no-dataengine` | `AQUILIA_DATAENGINE=0` | Yes |

CLI flags write to `os.environ` **before** workspace loading so all reload worker subprocesses inherit the correct value.

---

## Priority Chain

Highest wins:

| Priority | Source | Example |
|---|---|---|
| 1 (highest) | CLI flag | `aq run --no-engine` |
| 2 | Process environment | `AQUILIA_ENGINE=0` set by CI shell |
| 3 | workspace.py `AquilaConfig.Accelerator` | `engine = False` |
| 4 (lowest) | Framework default | Enabled |

### Rule: no CI overwrite

`AquilaConfig.to_loader()` propagates resolved accelerator values into `os.environ` so hot-reload workers inherit the setting. But it only writes when the env var is **not already present**:

```python
# From pyconfig.py
if env_key in os.environ:
    continue  # honour CI pin, never overwrite
val = accel_data.get(field)
if val is not None:
    os.environ[env_key] = "1" if val else "0"
```

This means `AQUILIA_ENGINE=0 aq run` is guaranteed to use pure Python even if `workspace.py` sets `engine = True`.

---

## `run_dev_server()` API

`aquilia.cli.commands.run.run_dev_server()` gained two keyword-only parameters:

```python
def run_dev_server(
    ...,
    *,
    engine: bool | None = None,
    dataengine: bool | None = None,
) -> None:
    """
    engine: Override C++ request-engine state.
        True = enable, False = disable, None = read from workspace or env.
    dataengine: Override C++ data-engine state.
        True = enable, False = disable, None = read from workspace or env.
    """
```

These are for programmatic use (test harnesses, deployment scripts) that invoke `run_dev_server()` directly.

---

## `aq init workspace` Template Updates

The workspace generator now includes the `accelerator` section with inline documentation:

```python
# workspace.py (generated by aq init workspace)
class BaseEnv(AquilaConfig):
    # Native C++ engine configuration.
    # Both engines are fail-soft: absent extensions fall back to pure Python.
    # Set to False or Env("AQUILIA_ENGINE", default=True, cast=bool) to control via env var.
    class accelerator(AquilaConfig.Accelerator):
        engine = True      # C++ router + RequestContext (AQUILIA_ENGINE)
        dataengine = True  # C++ ORM FieldPlan + contracts (AQUILIA_DATAENGINE)
```

The generated `.env.example` now documents these variables:

```bash
# Native C++ engine accelerators
# Set to 0 to force pure-Python fallbacks (useful for debugging or CI parity)
# Use 'aq run --no-engine' / 'aq run --no-dataengine' for per-run override
AQUILIA_ENGINE=1
AQUILIA_DATAENGINE=1
```

---

## Verifying Engine State

```python
# Check which engines are active
import aquilia.engines
print(aquilia.engines.engine_info())
print(aquilia.engines.dataengine_info())
import aquilia.json
print(aquilia.json.backend())
```

Output with all native engines active:
```
{'backend': 'native', 'version': '...', 'engine': 'c++'}
{'backend': 'native', 'dataengine': 'c++'}
aquilia._json
```

Output with pure-Python fallbacks:
```
{'backend': 'python', 'engine': 'pure-python'}
{'backend': 'python', 'dataengine': 'pure-python'}
stdlib
```

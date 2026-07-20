# DI Settings & Configuration

In Aquilia v1.3.2, every runtime knob for the dependency-injection container lives in a single typed, immutable object: `DISettings`. The subsystem historically read a couple of loose `os.environ` flags (e.g. strict-scope enforcement); those are gone. You now configure the container the same way you configure every other subsystem — through a config block in `workspace.py`.

## The `DISettings` Object

`DISettings` is a frozen, slotted dataclass defined in `aquilia.di.settings`. Every field maps 1:1 to a key under the `di` config section.

```python
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class DISettings:
    scope_enforcement: str = "warn"          # "warn" | "raise" | "off"
    parallel_resolution: bool = False
    diagnostics_enabled: bool = False
    disposal_strategy: str = "lifo"          # "lifo" | "fifo" | "parallel"
    hook_timeout_seconds: float = 30.0
    pool_acquire_timeout_seconds: float = 30.0
    pool_max_waiters: int | None = None      # None = unbounded
    type_key_cache_max: int = 8192
    enable_conditional_providers: bool = True
    enable_plugins: bool = True
    strict_service_registration: bool = False
```

| Field | Default | Purpose |
|---|---|---|
| `scope_enforcement` | `"warn"` | Captive-dependency handling: `"warn"` logs, `"raise"` raises `ScopeViolationError`, `"off"` skips the check. |
| `parallel_resolution` | `False` | Resolve independent constructor dependencies concurrently via `asyncio.gather`. |
| `diagnostics_enabled` | `False` | Emit `RESOLUTION_START/SUCCESS/FAILURE` diagnostic events per resolve. |
| `disposal_strategy` | `"lifo"` | Finalizer ordering: `"lifo"`, `"fifo"`, or `"parallel"`. |
| `hook_timeout_seconds` | `30.0` | Per-hook timeout for startup/shutdown lifecycle hooks. |
| `pool_acquire_timeout_seconds` | `30.0` | Default pool acquire timeout. |
| `pool_max_waiters` | `None` | Cap on concurrent waiters against an exhausted pool (fast-fail). `None` = unbounded. |
| `type_key_cache_max` | `8192` | Upper bound on the global type→key cache before a wholesale flush. |
| `enable_conditional_providers` | `True` | Honour `@conditional` / `when=` predicates during registration. |
| `enable_plugins` | `True` | Run registered `DIPlugin` hooks during registry build. |
| `strict_service_registration` | `False` | Fail-fast at boot when a service fails to register, instead of logging and continuing. |

Two derived properties support hot-path checks: `strict_scopes` (True when `scope_enforcement == "raise"`) and `scope_check_enabled` (True unless `"off"`).

---

## Configuring DI in `workspace.py`

Add a `di` block to your environment config. It subclasses `AquilaConfig.DI`, and the server reads it at boot and installs it via `configure_di()` automatically.

```python
from aquilia import AquilaConfig

class BaseEnv(AquilaConfig):
    class di(AquilaConfig.DI):
        scope_enforcement   = "warn"     # "warn" | "raise" | "off"
        parallel_resolution = False

class DevEnv(BaseEnv):
    class di(BaseEnv.di):
        diagnostics_enabled = True       # trace every resolution in dev

class ProdEnv(BaseEnv):
    class di(BaseEnv.di):
        scope_enforcement   = "raise"    # fail-fast on captive deps
        parallel_resolution = True       # resolve independent deps concurrently
        pool_max_waiters    = 256        # fast-fail an exhausted pool
```

`aq init` now scaffolds these blocks in generated projects: `DevEnv` enables diagnostics, `ProdEnv` sets `scope_enforcement="raise"` and `parallel_resolution=True`.

---

## Programmatic Configuration

In tests or scripts, configure the container directly. Until `configure_di()` runs, a permissive default applies, so importing the DI system in isolation needs no setup.

```python
from aquilia.di import DISettings, configure_di, get_di_settings, reset_di_settings

configure_di(DISettings(scope_enforcement="raise", parallel_resolution=True))

assert get_di_settings().strict_scopes is True

# Test teardown — restore permissive defaults
reset_di_settings()
```

`configure_di()` is last-call-wins and also propagates `type_key_cache_max` into the core module's cache bound.

---

## Validation & `DIConfigFault`

Invalid values raise `DIConfigFault` (code `DI_CONFIG_INVALID`) at construction, so bad configuration surfaces at boot rather than at first resolution:

```python
DISettings(scope_enforcement="bogus")   # DIConfigFault: must be one of ['off','raise','warn']
DISettings(disposal_strategy="nope")    # DIConfigFault: must be one of ['fifo','lifo','parallel']
DISettings(pool_max_waiters=0)          # DIConfigFault: must be >= 1 or None
DISettings(hook_timeout_seconds=0)      # DIConfigFault: must be > 0
```

`DISettings.from_mapping(data)` builds settings from a `di` config dict (or attribute object, or `None`) and ignores unknown keys for forward compatibility.

---

## New Boot-Time Faults

Two configuration-driven faults now surface at service registration:

* **`INVALID_SERVICE_SCOPE`** — a manifest declares an unknown scope (e.g. `"singelton"`). Always fatal; the message lists the valid scopes.
* **`SERVICE_REGISTRATION_FAILED`** — a service fails to import/construct. Fatal only when `strict_service_registration=True`; otherwise logged and skipped so the app still boots.

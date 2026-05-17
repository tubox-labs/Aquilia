# Subsystems API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/subsystems/__init__.py` | 34 | 0 | 0 | Subsystem Initializers -- Protocol and base classes for server decomposition. |
| `aquilia/subsystems/base.py` | 216 | 3 | 0 | Subsystem Initializer -- Protocol and base implementation. |
| `aquilia/subsystems/effects.py` | 313 | 1 | 0 | Effect Subsystem -- Subsystem initializer for the effect system. |

## Public Exports

`BaseSubsystem`, `BootContext`, `EffectSubsystem`, `StorageSubsystem`, `SubsystemInitializer`

## Public Class Summary

| Class | Source | Bases | Summary |
| --- | --- | --- | --- |
| `BootContext` | `aquilia/subsystems/base.py` | object | Shared context passed to all subsystem initializers during boot. |
| `SubsystemInitializer` | `aquilia/subsystems/base.py` | Protocol | Protocol for subsystem lifecycle management. |
| `BaseSubsystem` | `aquilia/subsystems/base.py` | ABC | Base class for subsystem initializers with common lifecycle patterns. |
| `EffectSubsystem` | `aquilia/subsystems/effects.py` | BaseSubsystem | Subsystem initializer for the Aquilia effect system. |

## Detailed Classes And Methods

### `BootContext`

- Source: `aquilia/subsystems/base.py`
- Bases: `object`
- Summary: Shared context passed to all subsystem initializers during boot.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `config` | `dict[str, Any]` | `` |
| `manifests` | `list[AppManifest]` | `` |
| `registry` | `Any` | `None` |
| `middleware_stack` | `Any` | `None` |
| `health` | `HealthRegistry` | `field(default_factory=HealthRegistry)` |
| `shared_state` | `dict[str, Any]` | `field(default_factory=dict)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get_config` | `def get_config(self, key: str, default: Any=None)` | Get a configuration value by dotted key path. |
| `get_manifest` | `def get_manifest(self, module_name: str)` | Get a manifest by module name. |

### `SubsystemInitializer`

- Source: `aquilia/subsystems/base.py`
- Bases: `Protocol`
- Summary: Protocol for subsystem lifecycle management.
- Decorators: `runtime_checkable`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `name` | `def name(self)` | Unique subsystem name. |
| `priority` | `def priority(self)` | Boot priority (lower = earlier). Range: 0-1000. |
| `required` | `def required(self)` | If True, initialization failure stops the entire server startup. |
| `initialize` | `async def initialize(self, ctx: BootContext)` | Initialize the subsystem. |
| `health_check` | `async def health_check(self)` | Report current health status. |
| `shutdown` | `async def shutdown(self)` | Graceful shutdown with resource cleanup. |

### `BaseSubsystem`

- Source: `aquilia/subsystems/base.py`
- Bases: `ABC`
- Summary: Base class for subsystem initializers with common lifecycle patterns.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `name` | `def name(self)` |  |
| `priority` | `def priority(self)` |  |
| `required` | `def required(self)` |  |
| `timeout` | `def timeout(self)` |  |
| `initialize` | `async def initialize(self, ctx: BootContext)` | Initialize with timing and error handling. |
| `health_check` | `async def health_check(self)` | Default health check -- reports based on init status. |
| `shutdown` | `async def shutdown(self)` | Shutdown with logging. |

### `EffectSubsystem`

- Source: `aquilia/subsystems/effects.py`
- Bases: `BaseSubsystem`
- Summary: Subsystem initializer for the Aquilia effect system.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `health_check` | `async def health_check(self)` | Report effect system health. |
| `registry` | `def registry(self)` | Access the EffectRegistry. |

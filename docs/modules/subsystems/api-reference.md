# Subsystems API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
| --- | --- | --- | --- |
| `BootContext` | `aquilia/subsystems/base.py` | object | Shared context passed to all subsystem initializers during boot. |
| `SubsystemInitializer` | `aquilia/subsystems/base.py` | Protocol | Protocol for subsystem lifecycle management. |
| `BaseSubsystem` | `aquilia/subsystems/base.py` | ABC | Base class for subsystem initializers with common lifecycle patterns. |
| `EffectSubsystem` | `aquilia/subsystems/effects.py` | BaseSubsystem | Subsystem initializer for the Aquilia effect system. |

## Public Function Summary

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| None detected |  |  |  |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| None detected |  |  |

## Detailed Classes And Methods

### Class: `BootContext`

- Source: `aquilia/subsystems/base.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Shared context passed to all subsystem initializers during boot.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `config` | `dict[str, Any]` |  |
| `manifests` | `list[AppManifest]` |  |
| `registry` | `Any` | `None` |
| `middleware_stack` | `Any` | `None` |
| `health` | `HealthRegistry` | `field(default_factory=HealthRegistry)` |
| `shared_state` | `dict[str, Any]` | `field(default_factory=dict)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_config` | `def get_config(self, key: str, default: Any = None) -> Any` |  | Get a configuration value by dotted key path. |
| `get_manifest` | `def get_manifest(self, module_name: str) -> AppManifest &#124; None` |  | Get a manifest by module name. |

### Class: `SubsystemInitializer`

- Source: `aquilia/subsystems/base.py`
- Bases: `Protocol`
- Decorators: `runtime_checkable`
- Summary: Protocol for subsystem lifecycle management.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `name` | `def name(self) -> str` | property | Unique subsystem name. |
| `priority` | `def priority(self) -> int` | property | Boot priority (lower = earlier). Range: 0-1000. |
| `required` | `def required(self) -> bool` | property | If True, initialization failure stops the entire server startup. |
| `initialize` | `async def initialize(self, ctx: BootContext) -> HealthStatus` |  | Initialize the subsystem. |
| `health_check` | `async def health_check(self) -> HealthStatus` |  | Report current health status. |
| `shutdown` | `async def shutdown(self) -> None` |  | Graceful shutdown with resource cleanup. |

### Class: `BaseSubsystem`

- Source: `aquilia/subsystems/base.py`
- Bases: `ABC`
- Summary: Base class for subsystem initializers with common lifecycle patterns.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `name` | `def name(self) -> str` | property | Method. |
| `priority` | `def priority(self) -> int` | property | Method. |
| `required` | `def required(self) -> bool` | property | Method. |
| `timeout` | `def timeout(self) -> float` | property | Method. |
| `initialize` | `async def initialize(self, ctx: BootContext) -> HealthStatus` |  | Initialize with timing and error handling. |
| `health_check` | `async def health_check(self) -> HealthStatus` |  | Default health check -- reports based on init status. |
| `shutdown` | `async def shutdown(self) -> None` |  | Shutdown with logging. |

### Class: `EffectSubsystem`

- Source: `aquilia/subsystems/effects.py`
- Bases: `BaseSubsystem`
- Summary: Subsystem initializer for the Aquilia effect system.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `health_check` | `async def health_check(self)` |  | Report effect system health. |
| `registry` | `def registry(self) -> EffectRegistry &#124; None` | property | Access the EffectRegistry. |

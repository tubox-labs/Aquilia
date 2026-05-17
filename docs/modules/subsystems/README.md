# subsystems Module

## Purpose

Subsystem initializer contracts. Use this module when adding startup units that plug into server boot using a small common protocol.

## Source Coverage

- Python files: 3
- Public classes: 4
- Dataclasses: 1
- Enums: 0
- Public functions: 0

## How It Fits In Aquilia

1. Import the package from `aquilia.subsystems` or its concrete submodules.
2. Configure it through workspace integrations, manifests, or direct service construction depending on the subsystem.
3. Keep business logic outside transport and framework glue so the subsystem stays testable.

## Practical Guidance

- Prefer typed configuration objects and framework helpers over ad hoc dictionaries when they exist.
- Use the tests in `tests/` as behavioral examples when changing this subsystem.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `BootContext` | `aquilia/subsystems/base.py` | Shared context passed to all subsystem initializers during boot. |
| `SubsystemInitializer` | `aquilia/subsystems/base.py` | Protocol for subsystem lifecycle management. |
| `BaseSubsystem` | `aquilia/subsystems/base.py` | Base class for subsystem initializers with common lifecycle patterns. |
| `EffectSubsystem` | `aquilia/subsystems/effects.py` | Subsystem initializer for the Aquilia effect system. |

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| None detected |  |  |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/subsystems/__init__.py` | Subsystem Initializers -- Protocol and base classes for server decomposition. |
| `aquilia/subsystems/base.py` | Subsystem Initializer -- Protocol and base implementation. |
| `aquilia/subsystems/effects.py` | Effect Subsystem -- Subsystem initializer for the effect system. |

## Testing Pointers

Search `tests/` for `subsystems` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.

# Subsystems Documentation

This directory is the professional documentation set for `subsystems`. It is implementation-driven and aligned with the current source files under `aquilia/subsystems`.

## What This Covers

Small contracts for server boot decomposition and subsystem initialization.

## Source Files Read

- `aquilia/subsystems/__init__.py`: Subsystem Initializers -- Protocol and base classes for server decomposition.
- `aquilia/subsystems/base.py`: Subsystem Initializer -- Protocol and base implementation.
- `aquilia/subsystems/effects.py`: Effect Subsystem -- Subsystem initializer for the effect system.

## Document Map

- `architecture.md`: Runtime architecture and module boundaries
- `configuration.md`: Configuration entry points, datatypes, and precedence
- `api-reference.md`: Classes, methods, functions, constants, and data fields extracted from source
- `integration-guide.md`: How to wire the module into a real Aquilia application
- `cli-reference.md`: Command line surface and operational commands
- `edge-cases-and-limitations.md`: Known edge cases and implementation limits
- `troubleshooting.md`: Common failures and diagnosis steps
- `examples.md`: Code examples and usage patterns

## Public Surface Snapshot

- Python files: 3
- Public classes: 4
- Configuration or dataclass-like types: 1
- Public functions: 0
- Constants detected: 0

## Fast Start

```python
from aquilia.subsystems import annotations, BaseSubsystem, BootContext, SubsystemInitializer, EffectSubsystem

# The imported symbols above are public exports from this module.
# See api-reference.md for constructor signatures, methods, and data fields.
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.

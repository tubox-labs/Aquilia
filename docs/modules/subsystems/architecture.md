# Subsystems Architecture

Subsystem initializer contracts and boot context abstractions for decomposing server setup.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/subsystems/__init__.py` | 34 | 0 | 0 | Subsystem Initializers -- Protocol and base classes for server decomposition. |
| `aquilia/subsystems/base.py` | 216 | 3 | 0 | Subsystem Initializer -- Protocol and base implementation. |
| `aquilia/subsystems/effects.py` | 313 | 1 | 0 | Effect Subsystem -- Subsystem initializer for the effect system. |

## Internal Shape

`subsystems` has 3 Python files, 4 public classes, 0 public module-level functions, and 1 constants or module flags detected by AST.

## Runtime Responsibilities

- No mounted `aq` command group maps directly to this module; it is used through Python APIs, manifests, workspace integrations, or server startup wiring.

## Internal Imports

| Import | Count |
| --- | ---: |
| `.base` | 2 |
| `..health` | 1 |
| `..manifest` | 1 |
| `.effects` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `__future__` | 3 |
| `logging` | 2 |
| `typing` | 2 |
| `abc` | 1 |
| `dataclasses` | 1 |
| `time` | 1 |

## Lifecycle And Extension Points

No dedicated extension classes were detected by naming convention; inspect `api-reference.md` for all public classes and functions.

## Error Handling

This module does not define public `Fault` or `Error` classes in its own files. Errors are usually raised through shared `aquilia.faults` domains or consuming subsystems.

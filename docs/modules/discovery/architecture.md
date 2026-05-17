# Discovery Architecture

AST-based component discovery and manifest synchronization support.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/discovery/__init__.py` | 51 | 0 | 0 | Aquilia Discovery - Component auto-discovery subsystem. |
| `aquilia/discovery/engine.py` | 696 | 9 | 0 | Auto-Discovery Engine -- AST-based component classification and manifest sync. |

## Internal Shape

`discovery` has 2 Python files, 9 public classes, 0 public module-level functions, and 1 constants or module flags detected by AST.

## Runtime Responsibilities

- This module has `aq` command coverage documented in `cli-reference.md`; 1 commands map to this subsystem.

## Internal Imports

| Import | Count |
| --- | ---: |
| `..manifest` | 1 |
| `.engine` | 1 |
| `aquilia.utils.scanner` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `__future__` | 1 |
| `ast` | 1 |
| `dataclasses` | 1 |
| `logging` | 1 |
| `pathlib` | 1 |
| `re` | 1 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `AutoDiscoveryEngine` | `aquilia/discovery/engine.py` | Scans module directories for components and syncs manifest.py files. |

## Error Handling

This module does not define public `Fault` or `Error` classes in its own files. Errors are usually raised through shared `aquilia.faults` domains or consuming subsystems.

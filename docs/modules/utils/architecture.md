# Utils Architecture

Small shared helpers for URL joining, data objects, and package scanning.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/utils/__init__.py` | 16 | 0 | 0 | Aquilia Utils Package |
| `aquilia/utils/data.py` | 42 | 1 | 0 | Data Utilities - Provides flexible data structures for the framework. |
| `aquilia/utils/scanner.py` | 218 | 1 | 0 | Package Scanner Utility. |
| `aquilia/utils/urls.py` | 50 | 0 | 2 | URL Utilities for Aquilia. |

## Internal Shape

`utils` has 4 Python files, 2 public classes, 2 public module-level functions, and 1 constants or module flags detected by AST.

## Runtime Responsibilities

- No mounted `aq` command group maps directly to this module; it is used through Python APIs, manifests, workspace integrations, or server startup wiring.

## Internal Imports

| Import | Count |
| --- | ---: |
| `.scanner` | 1 |
| `.urls` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `typing` | 2 |
| `collections` | 1 |
| `importlib` | 1 |
| `inspect` | 1 |
| `logging` | 1 |
| `pkgutil` | 1 |
| `types` | 1 |

## Lifecycle And Extension Points

No dedicated extension classes were detected by naming convention; inspect `api-reference.md` for all public classes and functions.

## Error Handling

This module does not define public `Fault` or `Error` classes in its own files. Errors are usually raised through shared `aquilia.faults` domains or consuming subsystems.

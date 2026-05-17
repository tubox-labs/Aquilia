# Debug Architecture

Development-mode welcome, HTTP error, version error, and exception pages.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/debug/__init__.py` | 31 | 0 | 0 | Aquilia Debug - Beautiful development-mode error and welcome pages. |
| `aquilia/debug/pages.py` | 1269 | 1 | 4 | Aquilia Debug Pages -- Tubox Themed (Premium). |

## Internal Shape

`debug` has 2 Python files, 1 public classes, 4 public module-level functions, and 6 constants or module flags detected by AST.

## Runtime Responsibilities

- No mounted `aq` command group maps directly to this module; it is used through Python APIs, manifests, workspace integrations, or server startup wiring.

## Internal Imports

| Import | Count |
| --- | ---: |
| `.pages` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `__future__` | 1 |
| `html` | 1 |
| `linecache` | 1 |
| `logging` | 1 |
| `os` | 1 |
| `traceback` | 1 |
| `typing` | 1 |

## Lifecycle And Extension Points

No dedicated extension classes were detected by naming convention; inspect `api-reference.md` for all public classes and functions.

## Error Handling

This module does not define public `Fault` or `Error` classes in its own files. Errors are usually raised through shared `aquilia.faults` domains or consuming subsystems.

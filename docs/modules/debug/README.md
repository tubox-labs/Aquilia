# debug Module

## Purpose

Development error and welcome pages. Use this module for HTML diagnostics in development, including exception, HTTP error, versioning, and welcome pages.

## Source Coverage

- Python files: 2
- Public classes: 1
- Dataclasses: 0
- Enums: 0
- Public functions: 4

## How It Fits In Aquilia

1. Import the package from `aquilia.debug` or its concrete submodules.
2. Configure it through workspace integrations, manifests, or direct service construction depending on the subsystem.
3. Keep business logic outside transport and framework glue so the subsystem stays testable.

## Practical Guidance

- Prefer typed configuration objects and framework helpers over ad hoc dictionaries when they exist.
- Use the tests in `tests/` as behavioral examples when changing this subsystem.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `DebugPageRenderer` | `aquilia/debug/pages.py` | Public class. |

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| `render_debug_exception_page` | `aquilia/debug/pages.py` | Public function. |
| `render_http_error_page` | `aquilia/debug/pages.py` | Public function. |
| `render_version_error_page` | `aquilia/debug/pages.py` | Render a themed HTML page for API versioning errors. |
| `render_welcome_page` | `aquilia/debug/pages.py` | Public function. |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/debug/__init__.py` | Aquilia Debug - Beautiful development-mode error and welcome pages. |
| `aquilia/debug/pages.py` | Aquilia Debug Pages -- Tubox Themed (Premium). |

## Testing Pointers

Search `tests/` for `debug` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.

# Debug Pages Documentation

This directory is the professional documentation set for `debug`. It is implementation-driven and aligned with the current source files under `aquilia/debug`.

## What This Covers

Development-mode HTML pages for welcome, HTTP errors, version errors, and exception diagnostics.

## Source Files Read

- `aquilia/debug/__init__.py`: Aquilia Debug - Beautiful development-mode error and welcome pages.
- `aquilia/debug/pages.py`: Aquilia Debug Pages -- Tubox Themed (Premium).

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

- Python files: 2
- Public classes: 1
- Configuration or dataclass-like types: 0
- Public functions: 4
- Constants detected: 5

## Fast Start

```python
from aquilia.debug import DebugPageRenderer, render_debug_exception_page, render_http_error_page, render_version_error_page, render_welcome_page

# The imported symbols above are public exports from this module.
# See api-reference.md for constructor signatures, methods, and data fields.
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.

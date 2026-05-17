# Utilities Documentation

This directory is the professional documentation set for `utils`. It is implementation-driven and aligned with the current source files under `aquilia/utils`.

## What This Covers

Small utilities for package scanning, URL path normalization, joining, and data helper objects.

## Source Files Read

- `aquilia/utils/__init__.py`: Aquilia Utils Package
- `aquilia/utils/data.py`: Data Utilities - Provides flexible data structures for the framework.
- `aquilia/utils/scanner.py`: Package Scanner Utility.
- `aquilia/utils/urls.py`: URL Utilities for Aquilia.

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

- Python files: 4
- Public classes: 2
- Configuration or dataclass-like types: 0
- Public functions: 2
- Constants detected: 0

## Fast Start

```python
from aquilia.utils import PackageScanner, join_paths, normalize_path

# The imported symbols above are public exports from this module.
# See api-reference.md for constructor signatures, methods, and data fields.
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.

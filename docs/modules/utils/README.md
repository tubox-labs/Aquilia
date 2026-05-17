# utils Module

## Purpose

Small shared utilities. Use this module for package scanning, path joining, path normalization, and data helper objects.

## Source Coverage

- Python files: 4
- Public classes: 2
- Dataclasses: 0
- Enums: 0
- Public functions: 2

## How It Fits In Aquilia

1. Import the package from `aquilia.utils` or its concrete submodules.
2. Configure it through workspace integrations, manifests, or direct service construction depending on the subsystem.
3. Keep business logic outside transport and framework glue so the subsystem stays testable.

## Practical Guidance

- Prefer typed configuration objects and framework helpers over ad hoc dictionaries when they exist.
- Use the tests in `tests/` as behavioral examples when changing this subsystem.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `DataObject` | `aquilia/utils/data.py` | A dictionary subclass that supports dot-notation access to its keys. |
| `PackageScanner` | `aquilia/utils/scanner.py` | Enhanced scanner for discovering classes in Python packages. |

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| `join_paths` | `aquilia/utils/urls.py` | Robustly join URL path segments. |
| `normalize_path` | `aquilia/utils/urls.py` | Normalize a URL path. |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/utils/__init__.py` | Aquilia Utils Package |
| `aquilia/utils/data.py` | Data Utilities - Provides flexible data structures for the framework. |
| `aquilia/utils/scanner.py` | Package Scanner Utility. |
| `aquilia/utils/urls.py` | URL Utilities for Aquilia. |

## Testing Pointers

Search `tests/` for `utils` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.

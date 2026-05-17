# discovery Module

## Purpose

AST-based component discovery. Use this module to scan module directories, classify controllers and services, compare manifests, and write sync reports.

## Source Coverage

- Python files: 2
- Public classes: 9
- Dataclasses: 4
- Enums: 0
- Public functions: 0

## How It Fits In Aquilia

1. Import the package from `aquilia.discovery` or its concrete submodules.
2. Configure it through workspace integrations, manifests, or direct service construction depending on the subsystem.
3. Keep business logic outside transport and framework glue so the subsystem stays testable.

## Practical Guidance

- Prefer typed configuration objects and framework helpers over ad hoc dictionaries when they exist.
- Use the tests in `tests/` as behavioral examples when changing this subsystem.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `ClassifiedComponent` | `aquilia/discovery/engine.py` | A component discovered by the AST classifier. |
| `DiscoveryResult` | `aquilia/discovery/engine.py` | Result of scanning a single module. |
| `SyncAction` | `aquilia/discovery/engine.py` | Describes a change to make to a manifest file. |
| `SyncReport` | `aquilia/discovery/engine.py` | Report from a manifest sync operation. |
| `ASTClassifier` | `aquilia/discovery/engine.py` | Classifies Python classes using AST analysis -- no imports needed. |
| `FileScanner` | `aquilia/discovery/engine.py` | Scans module directories for Python files matching discovery patterns. |
| `ManifestDiffer` | `aquilia/discovery/engine.py` | Compares discovered components against declared manifest components. |
| `ManifestWriter` | `aquilia/discovery/engine.py` | Safely updates manifest.py files using text manipulation. |
| `AutoDiscoveryEngine` | `aquilia/discovery/engine.py` | Scans module directories for components and syncs manifest.py files. |

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| None detected |  |  |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/discovery/__init__.py` | Aquilia Discovery - Component auto-discovery subsystem. |
| `aquilia/discovery/engine.py` | Auto-Discovery Engine -- AST-based component classification and manifest sync. |

## Testing Pointers

Search `tests/` for `discovery` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.

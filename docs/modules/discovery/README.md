# Discovery Documentation

This directory is the professional documentation set for `discovery`. It is implementation-driven and aligned with the current source files under `aquilia/discovery`.

## What This Covers

The AST-based scanner and manifest sync tooling used to find controllers, services, middleware, models, tasks, and other module components.

## Source Files Read

- `aquilia/discovery/__init__.py`: Aquilia Discovery - Component auto-discovery subsystem.
- `aquilia/discovery/engine.py`: Auto-Discovery Engine -- AST-based component classification and manifest sync.

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
- Public classes: 9
- Configuration or dataclass-like types: 4
- Public functions: 0
- Constants detected: 0

## Fast Start

```python
from aquilia.discovery import PackageScanner, ASTClassifier, AutoDiscoveryEngine, ClassifiedComponent, DiscoveryResult, FileScanner

# The imported symbols above are public exports from this module.
# See api-reference.md for constructor signatures, methods, and data fields.
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.

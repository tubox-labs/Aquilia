# Typing Contracts Documentation

This directory is the professional documentation set for `typing`. It is implementation-driven and aligned with the current source files under `aquilia/typing`.

## What This Covers

Shared type aliases and protocols for ASGI, config, containers, controllers, request state, effects, manifests, middleware, and JSON-like values.

## Source Files Read

- `aquilia/typing/__init__.py`: Implementation file.
- `aquilia/typing/asgi.py`: Implementation file.
- `aquilia/typing/common.py`: Implementation file.
- `aquilia/typing/config.py`: Configuration type definitions for Aquilia.
- `aquilia/typing/container.py`: Implementation file.
- `aquilia/typing/controller.py`: Implementation file.
- `aquilia/typing/effects.py`: Implementation file.
- `aquilia/typing/manifest.py`: Implementation file.
- `aquilia/typing/middleware.py`: Implementation file.
- `aquilia/typing/request_state.py`: Implementation file.

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

- Python files: 10
- Public classes: 37
- Configuration or dataclass-like types: 1
- Public functions: 0
- Constants detected: 2

## Fast Start

```python
from aquilia.typing import ASGIApplication, ASGIReceive, ASGIReceiveEvent, ASGIScope, ASGISend, ASGISendEvent

# The imported symbols above are public exports from this module.
# See api-reference.md for constructor signatures, methods, and data fields.
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.

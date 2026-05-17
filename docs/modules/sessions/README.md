# Sessions Documentation

This directory is the professional documentation set for `sessions`. It is implementation-driven and aligned with the current source files under `aquilia/sessions`.

## What This Covers

The session subsystem with policy builders, stores, transports, guards, decorators, state objects, session engine, lifecycle rules, and typed session faults.

## Source Files Read

- `aquilia/sessions/__init__.py`: AquilaSessions - Production-grade session management for Aquilia.
- `aquilia/sessions/core.py`: AquilaSessions - Core types.
- `aquilia/sessions/decorators.py`: Unique Session Decorators for Aquilia.
- `aquilia/sessions/engine.py`: AquilaSessions - Session Engine.
- `aquilia/sessions/faults.py`: AquilaSessions - Fault definitions.
- `aquilia/sessions/policy.py`: AquilaSessions - Policy types.
- `aquilia/sessions/state.py`: Typed Session State for Aquilia.
- `aquilia/sessions/store.py`: AquilaSessions - Session storage abstraction.
- `aquilia/sessions/transport.py`: AquilaSessions - Transport adapters.

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

- Python files: 9
- Public classes: 41
- Configuration or dataclass-like types: 6
- Public functions: 3
- Constants detected: 6

## Fast Start

```python
from datetime import timedelta
from aquilia.sessions import SessionPolicy, PersistencePolicy, TransportPolicy

user_sessions = SessionPolicy(
    name="user",
    ttl=timedelta(days=7),
    idle_timeout=timedelta(hours=1),
    persistence=PersistencePolicy(enabled=True, store_name="memory"),
    transport=TransportPolicy(adapter="cookie", cookie_httponly=True),
    scope="user",
)
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.

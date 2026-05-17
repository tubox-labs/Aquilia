# Core Runtime Documentation

This directory is the professional documentation set for `core`. It is implementation-driven and aligned with the current source files under `aquilia`.

## What This Covers

The root framework layer that exposes workspace builders, ASGI bootstrap, request and response primitives, runtime phases, middleware stack behavior, configuration loading, signing, uploads, and shared data structures.

## Source Files Read

- `aquilia/__init__.py`: Aquilia - Production-ready async Python web framework
- `aquilia/_datastructures.py`: Core data structures for Aquilia Request handling.
- `aquilia/_uploads.py`: Upload file handling for Aquilia Request.
- `aquilia/_version.py`: Single source of truth for the Aquilia framework version.
- `aquilia/asgi.py`: ASGI adapter -- Bridges the ASGI protocol to Aquilia's request / response system.
- `aquilia/config.py`: Config system - Layered typed configuration with validation.
- `aquilia/config_builders.py`: Fluent Configuration Builders for Aquilia.
- `aquilia/dotenv.py`: Aquilia Native Dotenv Loader (``aquilia.dotenv``)
- `aquilia/effects.py`: Effect System -- Typed Capabilities with Providers and Layers.
- `aquilia/engine.py`: Engine -- Core runtime primitives for the Aquilia request lifecycle.
- `aquilia/entrypoint.py`: Aquilia ASGI Entrypoint - Zero-Config Production Application Factory.
- `aquilia/flow.py`: Aquilia Flow -- Typed Pipeline System with Effect Integration.
- `aquilia/health.py`: Health Registry -- Centralized subsystem health tracking.
- `aquilia/lifecycle.py`: Lifecycle Coordinator - Orchestrates startup and shutdown hooks.
- `aquilia/manifest.py`: AppManifest - Production-grade, data-driven application manifest system.
- `aquilia/middleware.py`: Middleware system - Composable, async-first middleware with effect awareness.
- `aquilia/pyconfig.py`: Aquilia Python-Native Configuration System  (``aquilia.pyconfig``)
- `aquilia/request.py`: Request - Production-grade ASGI request wrapper.
- `aquilia/response.py`: Response - Production-grade HTTP response builder with streaming support.
- `aquilia/runtime.py`: AquiliaRuntime - Structured ASGI Bootstrap Lifecycle Manager.
- `aquilia/server.py`: AquiliaServer - Main server orchestrating all components with lifecycle management.
- `aquilia/signing.py`: Aquilia Signing Engine  (``aquilia.signing``)

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

- Python files: 22
- Public classes: 132
- Configuration or dataclass-like types: 38
- Public functions: 46
- Constants detected: 55

## Fast Start

```python
from aquilia import __version__, URL, Headers, MultiDict, ParsedContentType, Range

# The imported symbols above are public exports from this module.
# See api-reference.md for constructor signatures, methods, and data fields.
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.

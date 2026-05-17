# Core Runtime Architecture

## Runtime Role

The root framework layer that exposes workspace builders, ASGI bootstrap, request and response primitives, runtime phases, middleware stack behavior, configuration loading, signing, uploads, and shared data structures.

The implementation is split across 22 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

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

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `typing` | 29 |
| `auth` | 16 |
| `logging` | 15 |
| `__future__` | 14 |
| `dataclasses` | 13 |
| `collections` | 12 |
| `os` | 8 |
| `pathlib` | 8 |
| `enum` | 7 |
| `faults` | 7 |
| `contextlib` | 5 |
| `controller` | 5 |
| `datetime` | 5 |
| `json` | 5 |
| `time` | 5 |
| `asyncio` | 4 |
| `hashlib` | 4 |
| `inspect` | 4 |
| `middleware_ext` | 4 |
| `response` | 4 |
| `_datastructures` | 3 |
| `aquilia` | 3 |
| `importlib` | 3 |
| `middleware` | 3 |
| `re` | 3 |
| `request` | 3 |
| `sessions` | 3 |
| `sockets` | 3 |
| `templates` | 3 |
| `urllib` | 3 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.

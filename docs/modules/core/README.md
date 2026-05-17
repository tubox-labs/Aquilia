# Core Documentation

Root framework runtime files: ASGI adapter, server, runtime bootstrap, config, pyconfig, request/response, middleware, lifecycle, signing, effects, dotenv, uploads, and data structures.

## Coverage Snapshot

- Source files: 22
- Source lines: 27322
- Public classes: 132
- Public module functions: 46
- Constants/module flags: 63
- Public exports in `__all__`: 606

## Source Files Read

- `aquilia/__init__.py`: Aquilia - Production-ready async Python web framework
- `aquilia/_datastructures.py`: Core data structures for Aquilia Request handling.
- `aquilia/_uploads.py`: Upload file handling for Aquilia Request.
- `aquilia/_version.py`: Single source of truth for the Aquilia framework version.
- `aquilia/asgi.py`: ASGI adapter -- Bridges the ASGI protocol to Aquilia's request / response system. Supports HTTP, WebSocket, and Lifespan events.
- `aquilia/config.py`: Config system - Layered typed configuration with validation. Supports dataclass/pydantic-like behavior with merge precedence.
- `aquilia/config_builders.py`: Fluent Configuration Builders for Aquilia.
- `aquilia/dotenv.py`: Aquilia Native Dotenv Loader (``aquilia.dotenv``) =================================================
- `aquilia/effects.py`: Effect System -- Typed Capabilities with Providers and Layers.
- `aquilia/engine.py`: Engine -- Core runtime primitives for the Aquilia request lifecycle.
- `aquilia/entrypoint.py`: Aquilia ASGI Entrypoint — Zero-Config Production Application Factory.
- `aquilia/flow.py`: Aquilia Flow -- Typed Pipeline System with Effect Integration.
- `aquilia/health.py`: Health Registry -- Centralized subsystem health tracking.
- `aquilia/lifecycle.py`: Lifecycle Coordinator - Orchestrates startup and shutdown hooks.
- `aquilia/manifest.py`: AppManifest - Production-grade, data-driven application manifest system.
- `aquilia/middleware.py`: Middleware system - Composable, async-first middleware with effect awareness.
- `aquilia/pyconfig.py`: Aquilia Python-Native Configuration System  (``aquilia.pyconfig``) ==================================================================
- `aquilia/request.py`: Request - Production-grade ASGI request wrapper.
- `aquilia/response.py`: Response - Production-grade HTTP response builder with streaming support.
- `aquilia/runtime.py`: AquiliaRuntime — Structured ASGI Bootstrap Lifecycle Manager.
- `aquilia/server.py`: AquiliaServer - Main server orchestrating all components with lifecycle management.
- `aquilia/signing.py`: Aquilia Signing Engine  (``aquilia.signing``) =============================================

## Document Map

- `architecture.md`: module boundaries, dependencies, lifecycle, and extension points.
- `configuration.md`: configuration classes, builders, server wiring, and precedence.
- `api-reference.md`: source-extracted classes, methods, functions, constants, exports, and signatures.
- `integration-guide.md`: how to wire the module into an Aquilia app.
- `cli-reference.md`: mounted `aq` commands for this module, if any.
- `examples.md`: usage examples derived from source and checked example apps.
- `edge-cases-and-limitations.md`: implementation limits and compatibility behavior.
- `troubleshooting.md`: diagnostic commands and common failure patterns.

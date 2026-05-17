# Core Runtime Edge Cases And Limitations

## Fault And Error Types

The following error-oriented classes are present in the implementation and should guide defensive usage.

| Type | Source | Meaning |
| --- | --- | --- |
| `ConfigError` | `aquilia/config.py` | Raised when configuration validation fails. |
| `FlowError` | `aquilia/flow.py` | Raised when a flow pipeline encounters an unrecoverable error. |
| `LifecycleError` | `aquilia/lifecycle.py` | Raised when lifecycle operation fails. |
| `FaultHandlerConfig` | `aquilia/manifest.py` | Fault handler configuration. |
| `FaultHandlingConfig` | `aquilia/manifest.py` | Fault/error handling configuration. |
| `RequestFault` | `aquilia/request.py` | Base class for request-related faults. |
| `MultipartParseError` | `aquilia/request.py` | Multipart parsing failed (400). |
| `ResponseStreamError` | `aquilia/response.py` | Error during response streaming. |
| `TemplateRenderError` | `aquilia/response.py` | Template rendering error during response. |
| `InvalidHeaderError` | `aquilia/response.py` | Invalid header name or value (injection attempt). |
| `ClientDisconnectError` | `aquilia/response.py` | Client disconnected during response send. |
| `RangeNotSatisfiableError` | `aquilia/response.py` | Invalid Range header (416 response). |
| `HLSManifestError` | `aquilia/response.py` | Invalid HLS manifest payload or helper usage. |

## Common Edge Cases

- Optional dependencies may change behavior. Check imports and constructor docs before enabling production features.
- In-memory stores, queues, caches, adapters, and registries are usually process-local. Use durable backends when state must survive restarts or scale across workers.
- Request-scoped data must not be cached globally. Use request state, DI request scopes, or explicit parameters.
- Decorators in Aquilia generally attach metadata at import time. Runtime behavior happens later during compilation, routing, middleware execution, or service startup.
- Many subsystems intentionally convert invalid states into typed faults. Catch the specific fault type when application code can recover.

## Source-Level Limits To Review

Review these files before changing behavior:

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

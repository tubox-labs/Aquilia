# Core Architecture

Root framework runtime files: ASGI adapter, server, runtime bootstrap, config, pyconfig, request/response, middleware, lifecycle, signing, effects, dotenv, uploads, and data structures.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/__init__.py` | 1581 | 0 | 0 | Aquilia - Production-ready async Python web framework |
| `aquilia/_datastructures.py` | 440 | 5 | 2 | Core data structures for Aquilia Request handling. |
| `aquilia/_uploads.py` | 431 | 4 | 2 | Upload file handling for Aquilia Request. |
| `aquilia/_version.py` | 26 | 0 | 0 | Single source of truth for the Aquilia framework version. |
| `aquilia/asgi.py` | 641 | 1 | 0 | ASGI adapter -- Bridges the ASGI protocol to Aquilia's request / response system. Supports HTTP, WebSocket, and Lifespan events. |
| `aquilia/config.py` | 969 | 4 | 0 | Config system - Layered typed configuration with validation. Supports dataclass/pydantic-like behavior with merge precedence. |
| `aquilia/config_builders.py` | 5650 | 6 | 0 | Fluent Configuration Builders for Aquilia. |
| `aquilia/dotenv.py` | 898 | 2 | 6 | Aquilia Native Dotenv Loader (``aquilia.dotenv``) ================================================= |
| `aquilia/effects.py` | 794 | 21 | 0 | Effect System -- Typed Capabilities with Providers and Layers. |
| `aquilia/engine.py` | 295 | 3 | 1 | Engine -- Core runtime primitives for the Aquilia request lifecycle. |
| `aquilia/entrypoint.py` | 206 | 0 | 1 | Aquilia ASGI Entrypoint — Zero-Config Production Application Factory. |
| `aquilia/flow.py` | 1622 | 10 | 8 | Aquilia Flow -- Typed Pipeline System with Effect Integration. |
| `aquilia/health.py` | 162 | 3 | 0 | Health Registry -- Centralized subsystem health tracking. |
| `aquilia/lifecycle.py` | 363 | 5 | 1 | Lifecycle Coordinator - Orchestrates startup and shutdown hooks. |
| `aquilia/manifest.py` | 663 | 14 | 0 | AppManifest - Production-grade, data-driven application manifest system. |
| `aquilia/middleware.py` | 648 | 8 | 0 | Middleware system - Composable, async-first middleware with effect awareness. |
| `aquilia/pyconfig.py` | 1644 | 4 | 2 | Aquilia Python-Native Configuration System  (``aquilia.pyconfig``) ================================================================== |
| `aquilia/request.py` | 1998 | 11 | 0 | Request - Production-grade ASGI request wrapper. |
| `aquilia/response.py` | 2037 | 14 | 14 | Response - Production-grade HTTP response builder with streaming support. |
| `aquilia/runtime.py` | 721 | 3 | 0 | AquiliaRuntime — Structured ASGI Bootstrap Lifecycle Manager. |
| `aquilia/server.py` | 4001 | 1 | 0 | AquiliaServer - Main server orchestrating all components with lifecycle management. |
| `aquilia/signing.py` | 1532 | 13 | 9 | Aquilia Signing Engine  (``aquilia.signing``) ============================================= |

## Internal Shape

`core` has 22 Python files, 132 public classes, 46 public module-level functions, and 63 constants or module flags detected by AST.

## Runtime Responsibilities

- `AquiliaRuntime` owns configure, discover, bootstrap, and ASGI app access phases.
- `AquiliaServer` builds Aquilary metadata, runtime registries, DI containers, middleware, controllers, sockets, OpenAPI docs, admin routes, models, and subsystem services.
- `ASGIAdapter` handles HTTP, WebSocket, and lifespan scopes, performs route matching, creates request contexts, runs middleware, serves `/_health`, and maps fallback responses.
- `ConfigLoader` loads `workspace.py`, optional legacy `config/env.py`, dotenv files, `AQ_` environment variables, and manual overrides.

## Internal Imports

| Import | Count |
| --- | ---: |
| `.di` | 5 |
| `.faults` | 4 |
| `.response` | 4 |
| `.signing` | 4 |
| `._datastructures` | 3 |
| `.middleware` | 3 |
| `.request` | 3 |
| `.typing` | 3 |
| `.typing.manifest` | 3 |
| `._uploads` | 2 |
| `.aquilary` | 2 |
| `.auth.integration.middleware` | 2 |
| `.auth.manager` | 2 |
| `.auth.tokens` | 2 |
| `.config` | 2 |
| `.controller.router` | 2 |
| `.faults.domains` | 2 |
| `.filesystem` | 2 |
| `.health` | 2 |
| `.lifecycle` | 2 |
| `.models` | 2 |
| `.patterns` | 2 |
| `.sessions` | 2 |
| `.sessions.state` | 2 |
| `.tasks` | 2 |
| `.typing.container` | 2 |
| `.typing.effects` | 2 |
| `aquilia.faults.domains` | 2 |
| `.admin` | 1 |
| `.artifacts` | 1 |
| `.asgi` | 1 |
| `.auth` | 1 |
| `.auth.audit` | 1 |
| `.auth.authz` | 1 |
| `.auth.clearance` | 1 |
| `.auth.core` | 1 |
| `.auth.hardening` | 1 |
| `.auth.hashing` | 1 |
| `.auth.integration.aquila_sessions` | 1 |
| `.auth.integration.di_providers` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `typing` | 20 |
| `logging` | 15 |
| `__future__` | 14 |
| `dataclasses` | 13 |
| `collections` | 12 |
| `os` | 8 |
| `pathlib` | 8 |
| `enum` | 7 |
| `contextlib` | 5 |
| `datetime` | 5 |
| `json` | 5 |
| `time` | 5 |
| `asyncio` | 4 |
| `hashlib` | 4 |
| `inspect` | 4 |
| `importlib` | 3 |
| `re` | 3 |
| `urllib` | 3 |
| `abc` | 2 |
| `base64` | 2 |
| `email` | 2 |
| `hmac` | 2 |
| `tempfile` | 2 |
| `threading` | 2 |
| `warnings` | 2 |
| `http` | 1 |
| `ipaddress` | 1 |
| `mimetypes` | 1 |
| `struct` | 1 |
| `sys` | 1 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `UploadStore` | `aquilia/_uploads.py` | Protocol for upload storage backends. |
| `LocalUploadStore` | `aquilia/_uploads.py` | Local filesystem upload store. |
| `ASGIAdapter` | `aquilia/asgi.py` | ASGI application adapter. Converts ASGI events to Aquilia Request/Response. Uses controller-based routing exclusively. |
| `Config` | `aquilia/config.py` | Base class for typed configuration classes. |
| `ConfigError` | `aquilia/config.py` | Raised when configuration validation fails. |
| `ConfigLoader` | `aquilia/config.py` | Loads and merges configuration from multiple sources with precedence: CLI args > Environment variables > .env files > config files > defaults |
| `RuntimeConfig` | `aquilia/config_builders.py` | Runtime configuration. |
| `ModuleConfig` | `aquilia/config_builders.py` | Module configuration -- workspace-level orchestration metadata. |
| `AuthConfig` | `aquilia/config_builders.py` | Authentication configuration. |
| `Integration` | `aquilia/config_builders.py` | Integration configuration builders. |
| `DotEnvLoader` | `aquilia/dotenv.py` | Singleton loader that ensures .env files are loaded exactly once. |
| `EffectProvider` | `aquilia/effects.py` | Base class for effect providers. |
| `DBTxProvider` | `aquilia/effects.py` | Database transaction provider. |
| `CacheProvider` | `aquilia/effects.py` | Cache effect provider backed by the real CacheService. |
| `QueueProvider` | `aquilia/effects.py` | Queue/message publish effect provider. |
| `TaskQueueProvider` | `aquilia/effects.py` | Task queue effect provider backed by AquilaTasks TaskManager. |
| `HTTPProvider` | `aquilia/effects.py` | HTTP client effect provider for outbound requests. |
| `StorageProvider` | `aquilia/effects.py` | File/blob storage effect provider. |
| `EffectRegistry` | `aquilia/effects.py` | Registry for effect providers. |
| `LifecycleHook` | `aquilia/engine.py` | Named lifecycle points that subsystems can subscribe to. |
| `EngineMetrics` | `aquilia/engine.py` | Lightweight in-process metrics for the Aquilia engine. |
| `HealthRegistry` | `aquilia/health.py` | Centralized health tracking for all subsystems. |
| `LifecycleManager` | `aquilia/lifecycle.py` | High-level lifecycle manager with context manager support. |
| `LifecycleConfig` | `aquilia/manifest.py` | Lifecycle hook configuration. |
| `ServiceConfig` | `aquilia/manifest.py` | Service registration configuration with complete DI support. |
| `MiddlewareConfig` | `aquilia/manifest.py` | Middleware registration configuration. |
| `SessionConfig` | `aquilia/manifest.py` | Session management configuration. |
| `FaultHandlerConfig` | `aquilia/manifest.py` | Fault handler configuration. |
| `FaultHandlingConfig` | `aquilia/manifest.py` | Fault/error handling configuration. |
| `FeatureConfig` | `aquilia/manifest.py` | Feature flag configuration. |
| `BackgroundTaskConfig` | `aquilia/manifest.py` | Per-module background task configuration. |
| `TemplateConfig` | `aquilia/manifest.py` | Template engine configuration. |
| `DatabaseConfig` | `aquilia/manifest.py` | DEPRECATED: Manifest-level database configuration. |
| `MiddlewareDescriptor` | `aquilia/middleware.py` | Descriptor for middleware registration. |
| `MiddlewareStack` | `aquilia/middleware.py` | Manages middleware stack with deterministic ordering. Order: Global < App < Controller < Route, then by priority. |
| `RequestIdMiddleware` | `aquilia/middleware.py` | Adds unique request ID to each request. |
| `ExceptionMiddleware` | `aquilia/middleware.py` | Catches exceptions and converts them to error responses. |
| `LoggingMiddleware` | `aquilia/middleware.py` | Logs request/response with timing. |
| `TimeoutMiddleware` | `aquilia/middleware.py` | Enforces request timeout. |
| `CORSMiddleware` | `aquilia/middleware.py` | Handles CORS headers. |
| `CompressionMiddleware` | `aquilia/middleware.py` | Compresses response bodies. |
| `AquilaConfig` | `aquilia/pyconfig.py` | Base class for Aquilia Python-native configuration. |
| `PyConfigLoader` | `aquilia/pyconfig.py` | Load an ``AquilaConfig`` subclass from a Python source file. |
| `RuntimeConfig` | `aquilia/runtime.py` | Immutable configuration for an :class:`AquiliaRuntime` instance. |
| `SignerBackend` | `aquilia/signing.py` | Abstract backend that produces and verifies raw byte signatures. |
| `HmacSignerBackend` | `aquilia/signing.py` | Default signing backend — HMAC with a configurable digest. |
| `AsymmetricSignerBackend` | `aquilia/signing.py` | Asymmetric signing backend using the ``cryptography`` package. |
| `SigningConfig` | `aquilia/signing.py` | Runtime signing configuration. |

## Error Handling

Fault/error classes defined here:

`ConfigError`, `FlowError`, `LifecycleError`, `FaultHandlerConfig`, `FaultHandlingConfig`, `RequestFault`, `MultipartParseError`, `ResponseStreamError`, `TemplateRenderError`, `InvalidHeaderError`, `ClientDisconnectError`, `RangeNotSatisfiableError`, `HLSManifestError`

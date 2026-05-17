# Core Configuration

Root framework runtime files: ASGI adapter, server, runtime bootstrap, config, pyconfig, request/response, middleware, lifecycle, signing, effects, dotenv, uploads, and data structures.

This page distinguishes direct configuration APIs from indirect runtime wiring. All class names and source files below are extracted from the current source tree.

## Configuration Model

`ConfigLoader.load()` merges workspace files, legacy Python env config, explicit dotenv, native dotenv auto-load, `AQ_` environment variables, and manual overrides. YAML loading raises `ConfigInvalidFault`.

## Source Inventory

| File | Lines | Public classes | Public functions | Purpose |
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

## Detected Config-Oriented Classes

| Class | Source | Methods | Summary |
| --- | --- | --- | --- |
| `Config` | `aquilia/config.py` |  | Base class for typed configuration classes. |
| `ConfigError` | `aquilia/config.py` |  | Raised when configuration validation fails. |
| `ConfigLoader` | `aquilia/config.py` | `load`, `get`, `get_app_config`, `to_dict`, `get_session_config`, `get_auth_config`, `get_template_config`, `get_security_config`, `get_static_config`, `get_cache_config`, `get_i18n_config`, `get_mail_config`, `get_tasks_config`, `get_storage_config`, `get_middleware_config`, `get_versioning_config` | Loads and merges configuration from multiple sources with precedence: CLI args > Environment variables > .env files > config files > defaults |
| `RuntimeConfig` | `aquilia/config_builders.py` |  | Runtime configuration. |
| `ModuleConfig` | `aquilia/config_builders.py` | `to_dict` | Module configuration -- workspace-level orchestration metadata. |
| `AuthConfig` | `aquilia/config_builders.py` | `to_dict` | Authentication configuration. |
| `Integration` | `aquilia/config_builders.py` | `auth`, `sessions`, `di`, `database`, `storage`, `registry`, `routing`, `fault_handling`, `cache`, `tasks`, `admin`, `patterns`, `static_files`, `cors`, `csp`, `rate_limit`, `openapi`, `csrf`, `logging`, `mail` | Integration configuration builders. |
| `EffectProvider` | `aquilia/effects.py` | `initialize`, `acquire`, `release`, `finalize`, `health_check` | Base class for effect providers. |
| `DBTxProvider` | `aquilia/effects.py` | `initialize`, `acquire`, `release`, `health_check` | Database transaction provider. |
| `CacheProvider` | `aquilia/effects.py` | `initialize`, `acquire`, `release`, `finalize`, `health_check` | Cache effect provider backed by the real CacheService. |
| `QueueProvider` | `aquilia/effects.py` | `initialize`, `acquire`, `release`, `finalize`, `health_check` | Queue/message publish effect provider. |
| `TaskQueueProvider` | `aquilia/effects.py` | `initialize`, `acquire`, `release`, `finalize`, `health_check` | Task queue effect provider backed by AquilaTasks TaskManager. |
| `HTTPProvider` | `aquilia/effects.py` | `initialize`, `acquire`, `release`, `finalize` | HTTP client effect provider for outbound requests. |
| `StorageProvider` | `aquilia/effects.py` | `initialize`, `acquire`, `release`, `health_check` | File/blob storage effect provider. |
| `LifecycleConfig` | `aquilia/manifest.py` | `to_dict` | Lifecycle hook configuration. |
| `ServiceConfig` | `aquilia/manifest.py` | `to_dict` | Service registration configuration with complete DI support. |
| `MiddlewareConfig` | `aquilia/manifest.py` | `to_dict` | Middleware registration configuration. |
| `SessionConfig` | `aquilia/manifest.py` | `to_dict` | Session management configuration. |
| `FaultHandlerConfig` | `aquilia/manifest.py` |  | Fault handler configuration. |
| `FaultHandlingConfig` | `aquilia/manifest.py` | `to_dict` | Fault/error handling configuration. |
| `FeatureConfig` | `aquilia/manifest.py` | `to_dict` | Feature flag configuration. |
| `BackgroundTaskConfig` | `aquilia/manifest.py` | `to_dict` | Per-module background task configuration. |
| `TemplateConfig` | `aquilia/manifest.py` | `to_dict` | Template engine configuration. |
| `DatabaseConfig` | `aquilia/manifest.py` | `to_dict` | DEPRECATED: Manifest-level database configuration. |
| `MiddlewareDescriptor` | `aquilia/middleware.py` |  | Descriptor for middleware registration. |
| `MiddlewareStack` | `aquilia/middleware.py` | `add`, `build_handler`, `build_fast_handler` | Manages middleware stack with deterministic ordering. Order: Global < App < Controller < Route, then by priority. |
| `RequestIdMiddleware` | `aquilia/middleware.py` |  | Adds unique request ID to each request. |
| `ExceptionMiddleware` | `aquilia/middleware.py` |  | Catches exceptions and converts them to error responses. |
| `LoggingMiddleware` | `aquilia/middleware.py` |  | Logs request/response with timing. |
| `TimeoutMiddleware` | `aquilia/middleware.py` |  | Enforces request timeout. |
| `CORSMiddleware` | `aquilia/middleware.py` |  | Handles CORS headers. |
| `CompressionMiddleware` | `aquilia/middleware.py` |  | Compresses response bodies. |
| `AquilaConfig` | `aquilia/pyconfig.py` | `to_dict`, `invalidate_cache`, `clear_all_caches`, `to_loader`, `get`, `for_env`, `from_env_var` | Base class for Aquilia Python-native configuration. |
| `PyConfigLoader` | `aquilia/pyconfig.py` | `from_file`, `to_aquilia_loader`, `config_class` | Load an ``AquilaConfig`` subclass from a Python source file. |
| `RuntimeConfig` | `aquilia/runtime.py` | `is_dev`, `workspace_file`, `modules_dir` | Immutable configuration for an :class:`AquiliaRuntime` instance. |
| `SigningConfig` | `aquilia/signing.py` | `apply`, `make_session_signer`, `make_csrf_signer`, `make_activation_signer`, `make_cache_signer`, `make_cookie_signer`, `make_api_key_signer` | Runtime signing configuration. |

## Runtime Wiring Paths

- `workspace.py` defines workspace-level structure with `Workspace`, `Module`, and `Integration` builders.
- `modules/<name>/manifest.py` defines module internals with `AppManifest`.
- `ConfigLoader.get(...)` resolves dotted configuration paths at runtime.
- `AquiliaServer` consumes resolved config during middleware and subsystem setup.
- Subsystems with optional providers only require optional dependencies when their backend/provider is configured.

## Verification Checklist

1. Run `aq validate` to verify manifests.
2. Run `aq inspect config` to inspect resolved configuration.
3. Run `aq doctor` for workspace and integration diagnostics.
4. For server-only wiring, start via `aq run` and check startup logs plus `GET /_health`.

## Related Pages

- `api-reference.md` for exact class fields, methods, constants, and signatures.
- `integration-guide.md` for the workspace/manifest wiring pattern.
- `edge-cases-and-limitations.md` for fallback and compatibility behavior.

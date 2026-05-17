# core Module

## Purpose

Core runtime and public package surface. Use this material when you need to understand request and response primitives, workspace builders, runtime bootstrapping, ASGI handling, middleware composition, signing, configuration, and package-level exports.

## Source Coverage

- Python files: 22
- Public classes: 132
- Dataclasses: 35
- Enums: 9
- Public functions: 46

## How It Fits In Aquilia

1. Define workspace.py with Workspace and Module builders.
2. The runtime reads workspace.py, discovers module manifests, builds AquiliaServer, then exposes runtime.app as ASGI.
3. ASGIAdapter turns scopes into Request objects, matches controllers, builds RequestCtx, executes middleware, and sends Response objects.

## Practical Guidance

- Do not put component internals into workspace.py. Workspace modules are pointers, while module manifests own controllers, services, models, middleware, and socket controllers.
- Use Response factory methods instead of returning raw bytes when you need headers, cookies, streaming, cache headers, SSE, or background tasks.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `MultiDict` | `aquilia/_datastructures.py` | Dictionary that supports multiple values per key. |
| `Headers` | `aquilia/_datastructures.py` | Case-insensitive header access with raw preservation. |
| `URL` | `aquilia/_datastructures.py` | Parsed URL representation. |
| `ParsedContentType` | `aquilia/_datastructures.py` | Parsed Content-Type header. |
| `Range` | `aquilia/_datastructures.py` | Parsed HTTP Range header. |
| `UploadFile` | `aquilia/_uploads.py` | Uploaded file representation. |
| `FormData` | `aquilia/_uploads.py` | Parsed form data containing both fields and files. |
| `UploadStore` | `aquilia/_uploads.py` | Protocol for upload storage backends. |
| `LocalUploadStore` | `aquilia/_uploads.py` | Local filesystem upload store. |
| `ASGIAdapter` | `aquilia/asgi.py` | ASGI application adapter. |
| `NestedNamespace` | `aquilia/config.py` | A namespace that supports nested attribute access for app configs. |
| `Config` | `aquilia/config.py` | Base class for typed configuration classes. |
| `ConfigError` | `aquilia/config.py` | Raised when configuration validation fails. |
| `ConfigLoader` | `aquilia/config.py` | Loads and merges configuration from multiple sources with precedence: |
| `RuntimeConfig` | `aquilia/config_builders.py` | Runtime configuration. |
| `ModuleConfig` | `aquilia/config_builders.py` | Module configuration -- workspace-level orchestration metadata. |
| `Module` | `aquilia/config_builders.py` | Fluent module builder -- workspace-level orchestration only. |
| `AuthConfig` | `aquilia/config_builders.py` | Authentication configuration. |
| `Integration` | `aquilia/config_builders.py` | Integration configuration builders. |
| `Workspace` | `aquilia/config_builders.py` | Fluent workspace builder. |
| `DotEnv` | `aquilia/dotenv.py` | Native dotenv file parser and loader. |
| `DotEnvLoader` | `aquilia/dotenv.py` | Singleton loader that ensures .env files are loaded exactly once. |
| `EffectKind` | `aquilia/effects.py` | Categories of effects. |
| `Effect` | `aquilia/effects.py` | Effect token representing a capability. |
| `EffectProvider` | `aquilia/effects.py` | Base class for effect providers. |
| `DBTx` | `aquilia/effects.py` | Database transaction effect. |
| `CacheEffect` | `aquilia/effects.py` | Cache effect. |
| `QueueEffect` | `aquilia/effects.py` | Queue/message publish effect. |
| `HTTPEffect` | `aquilia/effects.py` | HTTP client effect for outbound requests. |
| `StorageEffect` | `aquilia/effects.py` | File/blob storage effect. |
| `DBTxProvider` | `aquilia/effects.py` | Database transaction provider. |
| `CacheProvider` | `aquilia/effects.py` | Cache effect provider backed by the real CacheService. |
| `QueueProvider` | `aquilia/effects.py` | Queue/message publish effect provider. |
| `TaskQueueProvider` | `aquilia/effects.py` | Task queue effect provider backed by AquilaTasks TaskManager. |
| `HTTPProvider` | `aquilia/effects.py` | HTTP client effect provider for outbound requests. |
| `StorageProvider` | `aquilia/effects.py` | File/blob storage effect provider. |
| `CacheServiceHandle` | `aquilia/effects.py` | Handle wrapping real CacheService for a given namespace. |
| `CacheHandle` | `aquilia/effects.py` | Handle for cache operations in a namespace. |
| `QueueHandle` | `aquilia/effects.py` | Handle for queue operations on a topic. |
| `TaskQueueHandle` | `aquilia/effects.py` | Handle for enqueuing background tasks via the TaskManager. |
| `HTTPHandle` | `aquilia/effects.py` | Handle for outbound HTTP requests. |
| `StorageHandle` | `aquilia/effects.py` | Handle for file/blob storage operations. |
| `EffectRegistry` | `aquilia/effects.py` | Registry for effect providers. |
| `LifecycleHook` | `aquilia/engine.py` | Named lifecycle points that subsystems can subscribe to. |
| `EngineMetrics` | `aquilia/engine.py` | Lightweight in-process metrics for the Aquilia engine. |
| `RequestCtx` | `aquilia/engine.py` | Per-request execution context. |
| `FlowNodeType` | `aquilia/flow.py` | Types of nodes in a flow pipeline. |
| `FlowStatus` | `aquilia/flow.py` | Pipeline execution outcome. |
| `FlowContext` | `aquilia/flow.py` | Typed execution context threaded through the entire flow pipeline. |
| `FlowNode` | `aquilia/flow.py` | A typed unit in a flow pipeline. |
| `FlowResult` | `aquilia/flow.py` | Result of a flow pipeline execution. |
| `FlowError` | `aquilia/flow.py` | Raised when a flow pipeline encounters an unrecoverable error. |
| `Layer` | `aquilia/flow.py` | Composable effect layer -- separates effect construction from usage. |
| `LayerComposition` | `aquilia/flow.py` | A composition of multiple layers, resolved in dependency order. |
| `FlowPipeline` | `aquilia/flow.py` | Composable, typed request pipeline with automatic effect management. |
| `EffectScope` | `aquilia/flow.py` | Async context manager that acquires and releases effects. |
| `SubsystemStatus` | `aquilia/health.py` | Status of a subsystem. |
| `HealthStatus` | `aquilia/health.py` | Health status for a single subsystem. |
| `HealthRegistry` | `aquilia/health.py` | Centralized health tracking for all subsystems. |
| `LifecyclePhase` | `aquilia/lifecycle.py` | Lifecycle phases. |
| `LifecycleEvent` | `aquilia/lifecycle.py` | Event emitted during lifecycle transitions. |
| `LifecycleError` | `aquilia/lifecycle.py` | Raised when lifecycle operation fails. |
| `LifecycleCoordinator` | `aquilia/lifecycle.py` | Coordinates application lifecycle across multiple apps. |
| `LifecycleManager` | `aquilia/lifecycle.py` | High-level lifecycle manager with context manager support. |
| `ComponentKind` | `aquilia/manifest.py` | Classification of framework components for auto-discovery. |
| `ComponentRef` | `aquilia/manifest.py` | Universal typed reference to any framework component. |
| `ServiceScope` | `aquilia/manifest.py` | Service lifecycle scope. |
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
| `AppManifest` | `aquilia/manifest.py` | Production-grade application manifest for complete app configuration. |
| `MiddlewareDescriptor` | `aquilia/middleware.py` | Descriptor for middleware registration. |
| `MiddlewareStack` | `aquilia/middleware.py` | Manages middleware stack with deterministic ordering. |

Only the first 80 classes are shown here. See the file inventory for the rest of the package.

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| `parse_date_header` | `aquilia/_datastructures.py` | Parse HTTP date header. |
| `parse_authorization_header` | `aquilia/_datastructures.py` | Parse Authorization header. |
| `create_upload_file_from_bytes` | `aquilia/_uploads.py` | Create an UploadFile from bytes (in-memory). |
| `create_upload_file_from_path` | `aquilia/_uploads.py` | Create an UploadFile from a disk path. |
| `find_dotenv` | `aquilia/dotenv.py` | Search for a .env file. |
| `load_dotenv` | `aquilia/dotenv.py` | Load a .env file into os.environ. |
| `dotenv_values` | `aquilia/dotenv.py` | Parse a .env file and return values WITHOUT loading into os.environ. |
| `ensure_dotenv_loaded` | `aquilia/dotenv.py` | Ensure dotenv is loaded (idempotent). |
| `is_dotenv_loaded` | `aquilia/dotenv.py` | Check if dotenv has been loaded. |
| `reset_dotenv_state` | `aquilia/dotenv.py` | Reset dotenv loaded state. |
| `get_engine_metrics` | `aquilia/engine.py` | Return the process-level engine metrics singleton. |
| `create_app` | `aquilia/entrypoint.py` | Create the ASGI application from workspace configuration. |
| `requires` | `aquilia/flow.py` | Decorator declaring effect dependencies on a handler or flow node. |
| `get_required_effects` | `aquilia/flow.py` | Extract declared effect requirements from a callable. |
| `pipeline` | `aquilia/flow.py` | Create a new FlowPipeline. |
| `guard` | `aquilia/flow.py` | Create a guard FlowNode. |
| `transform` | `aquilia/flow.py` | Create a transform FlowNode. |
| `handler` | `aquilia/flow.py` | Create a handler FlowNode. |
| `hook` | `aquilia/flow.py` | Create a hook FlowNode. |
| `from_pipeline_list` | `aquilia/flow.py` | Convert a controller-style pipeline list to a FlowPipeline. |
| `create_lifecycle_coordinator` | `aquilia/lifecycle.py` | Factory function to create lifecycle coordinator. |
| `reset_dotenv_state` | `aquilia/pyconfig.py` | Reset the dotenv loading state. |
| `section` | `aquilia/pyconfig.py` | Mark a nested class as a config *section*. |
| `has_crous` | `aquilia/response.py` | Return ``True`` if the ``crous`` library is importable. |
| `Ok` | `aquilia/response.py` | 200 OK response. |
| `Created` | `aquilia/response.py` | 201 Created response. |
| `NoContent` | `aquilia/response.py` | 204 No Content response. |
| `BadRequest` | `aquilia/response.py` | 400 Bad Request response. |
| `Unauthorized` | `aquilia/response.py` | 401 Unauthorized response. |
| `Forbidden` | `aquilia/response.py` | 403 Forbidden response. |
| `NotFound` | `aquilia/response.py` | 404 Not Found response. |
| `InternalError` | `aquilia/response.py` | 500 Internal Server Error response. |
| `generate_etag` | `aquilia/response.py` | Generate ETag from content. |
| `generate_etag_from_file` | `aquilia/response.py` | Generate ETag from file metadata. |
| `check_not_modified` | `aquilia/response.py` | Check if response should be 304 Not Modified. |
| `not_modified_response` | `aquilia/response.py` | Create 304 Not Modified response. |
| `requires_crous` | `aquilia/response.py` | Mark a handler as preferring CROUS binary responses. |
| `b64_encode` | `aquilia/signing.py` | URL-safe, no-padding Base64 encode. |
| `b64_decode` | `aquilia/signing.py` | URL-safe, no-padding Base64 decode. |
| `constant_time_compare` | `aquilia/signing.py` | Compare two values in constant time to prevent timing attacks. |
| `derive_key` | `aquilia/signing.py` | Derive a signing sub-key from *secret* and *salt* using HKDF-lite. |
| `dumps` | `aquilia/signing.py` | Serialise *obj* to a signed URL-safe string. |
| `loads` | `aquilia/signing.py` | Verify and deserialise a token produced by :func:`dumps`. |
| `configure` | `aquilia/signing.py` | Configure the global signing secret used by module-level helpers. |
| `make_signer` | `aquilia/signing.py` | Create a :class:`Signer` with the given (or global) settings. |
| `make_timestamp_signer` | `aquilia/signing.py` | Create a :class:`TimestampSigner` with the given (or global) settings. |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/__init__.py` | Aquilia - Production-ready async Python web framework |
| `aquilia/_datastructures.py` | Core data structures for Aquilia Request handling. |
| `aquilia/_uploads.py` | Upload file handling for Aquilia Request. |
| `aquilia/_version.py` | Single source of truth for the Aquilia framework version. |
| `aquilia/asgi.py` | ASGI adapter -- Bridges the ASGI protocol to Aquilia's request / response system. |
| `aquilia/config.py` | Config system - Layered typed configuration with validation. |
| `aquilia/config_builders.py` | Fluent Configuration Builders for Aquilia. |
| `aquilia/dotenv.py` | Aquilia Native Dotenv Loader (``aquilia.dotenv``) |
| `aquilia/effects.py` | Effect System -- Typed Capabilities with Providers and Layers. |
| `aquilia/engine.py` | Engine -- Core runtime primitives for the Aquilia request lifecycle. |
| `aquilia/entrypoint.py` | Aquilia ASGI Entrypoint - Zero-Config Production Application Factory. |
| `aquilia/flow.py` | Aquilia Flow -- Typed Pipeline System with Effect Integration. |
| `aquilia/health.py` | Health Registry -- Centralized subsystem health tracking. |
| `aquilia/lifecycle.py` | Lifecycle Coordinator - Orchestrates startup and shutdown hooks. |
| `aquilia/manifest.py` | AppManifest - Production-grade, data-driven application manifest system. |
| `aquilia/middleware.py` | Middleware system - Composable, async-first middleware with effect awareness. |
| `aquilia/pyconfig.py` | Aquilia Python-Native Configuration System  (``aquilia.pyconfig``) |
| `aquilia/request.py` | Request - Production-grade ASGI request wrapper. |
| `aquilia/response.py` | Response - Production-grade HTTP response builder with streaming support. |
| `aquilia/runtime.py` | AquiliaRuntime - Structured ASGI Bootstrap Lifecycle Manager. |
| `aquilia/server.py` | AquiliaServer - Main server orchestrating all components with lifecycle management. |
| `aquilia/signing.py` | Aquilia Signing Engine  (``aquilia.signing``) |

## Testing Pointers

Search `tests/` for `runtime|response|request|crous` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.

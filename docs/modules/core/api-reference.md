# Core Runtime API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
| --- | --- | --- | --- |
| `MultiDict` | `aquilia/_datastructures.py` | MutableMapping[str, list[str]] | Dictionary that supports multiple values per key. |
| `Headers` | `aquilia/_datastructures.py` | object | Case-insensitive header access with raw preservation. |
| `URL` | `aquilia/_datastructures.py` | object | Parsed URL representation. |
| `ParsedContentType` | `aquilia/_datastructures.py` | object | Parsed Content-Type header. |
| `Range` | `aquilia/_datastructures.py` | object | Parsed HTTP Range header. |
| `UploadFile` | `aquilia/_uploads.py` | object | Uploaded file representation. |
| `FormData` | `aquilia/_uploads.py` | object | Parsed form data containing both fields and files. |
| `UploadStore` | `aquilia/_uploads.py` | Protocol | Protocol for upload storage backends. |
| `LocalUploadStore` | `aquilia/_uploads.py` | object | Local filesystem upload store. |
| `ASGIAdapter` | `aquilia/asgi.py` | object | ASGI application adapter. |
| `NestedNamespace` | `aquilia/config.py` | object | A namespace that supports nested attribute access for app configs. |
| `Config` | `aquilia/config.py` | object | Base class for typed configuration classes. |
| `ConfigError` | `aquilia/config.py` | Exception | Raised when configuration validation fails. |
| `ConfigLoader` | `aquilia/config.py` | object | Loads and merges configuration from multiple sources with precedence: |
| `RuntimeConfig` | `aquilia/config_builders.py` | object | Runtime configuration. |
| `ModuleConfig` | `aquilia/config_builders.py` | object | Module configuration -- workspace-level orchestration metadata. |
| `Module` | `aquilia/config_builders.py` | object | Fluent module builder -- workspace-level orchestration only. |
| `AuthConfig` | `aquilia/config_builders.py` | object | Authentication configuration. |
| `Integration` | `aquilia/config_builders.py` | object | Integration configuration builders. |
| `Workspace` | `aquilia/config_builders.py` | object | Fluent workspace builder. |
| `DotEnv` | `aquilia/dotenv.py` | object | Native dotenv file parser and loader. |
| `DotEnvLoader` | `aquilia/dotenv.py` | object | Singleton loader that ensures .env files are loaded exactly once. |
| `EffectKind` | `aquilia/effects.py` | Enum | Categories of effects. |
| `Effect` | `aquilia/effects.py` | Generic[T] | Effect token representing a capability. |
| `EffectProvider` | `aquilia/effects.py` | ABC | Base class for effect providers. |
| `DBTx` | `aquilia/effects.py` | Effect | Database transaction effect. |
| `CacheEffect` | `aquilia/effects.py` | Effect | Cache effect. |
| `QueueEffect` | `aquilia/effects.py` | Effect | Queue/message publish effect. |
| `HTTPEffect` | `aquilia/effects.py` | Effect | HTTP client effect for outbound requests. |
| `StorageEffect` | `aquilia/effects.py` | Effect | File/blob storage effect. |
| `DBTxProvider` | `aquilia/effects.py` | EffectProvider | Database transaction provider. |
| `CacheProvider` | `aquilia/effects.py` | EffectProvider | Cache effect provider backed by the real CacheService. |
| `QueueProvider` | `aquilia/effects.py` | EffectProvider | Queue/message publish effect provider. |
| `TaskQueueProvider` | `aquilia/effects.py` | EffectProvider | Task queue effect provider backed by AquilaTasks TaskManager. |
| `HTTPProvider` | `aquilia/effects.py` | EffectProvider | HTTP client effect provider for outbound requests. |
| `StorageProvider` | `aquilia/effects.py` | EffectProvider | File/blob storage effect provider. |
| `CacheServiceHandle` | `aquilia/effects.py` | object | Handle wrapping real CacheService for a given namespace. |
| `CacheHandle` | `aquilia/effects.py` | object | Handle for cache operations in a namespace. |
| `QueueHandle` | `aquilia/effects.py` | object | Handle for queue operations on a topic. |
| `TaskQueueHandle` | `aquilia/effects.py` | object | Handle for enqueuing background tasks via the TaskManager. |
| `HTTPHandle` | `aquilia/effects.py` | object | Handle for outbound HTTP requests. |
| `StorageHandle` | `aquilia/effects.py` | object | Handle for file/blob storage operations. |
| `EffectRegistry` | `aquilia/effects.py` | object | Registry for effect providers. |
| `LifecycleHook` | `aquilia/engine.py` | Enum | Named lifecycle points that subsystems can subscribe to. |
| `EngineMetrics` | `aquilia/engine.py` | object | Lightweight in-process metrics for the Aquilia engine. |
| `RequestCtx` | `aquilia/engine.py` | object | Per-request execution context. |
| `FlowNodeType` | `aquilia/flow.py` | str, Enum | Types of nodes in a flow pipeline. |
| `FlowStatus` | `aquilia/flow.py` | str, Enum | Pipeline execution outcome. |
| `FlowContext` | `aquilia/flow.py` | object | Typed execution context threaded through the entire flow pipeline. |
| `FlowNode` | `aquilia/flow.py` | object | A typed unit in a flow pipeline. |
| `FlowResult` | `aquilia/flow.py` | object | Result of a flow pipeline execution. |
| `FlowError` | `aquilia/flow.py` | Exception | Raised when a flow pipeline encounters an unrecoverable error. |
| `Layer` | `aquilia/flow.py` | object | Composable effect layer -- separates effect construction from usage. |
| `LayerComposition` | `aquilia/flow.py` | object | A composition of multiple layers, resolved in dependency order. |
| `FlowPipeline` | `aquilia/flow.py` | object | Composable, typed request pipeline with automatic effect management. |
| `EffectScope` | `aquilia/flow.py` | object | Async context manager that acquires and releases effects. |
| `SubsystemStatus` | `aquilia/health.py` | str, Enum | Status of a subsystem. |
| `HealthStatus` | `aquilia/health.py` | object | Health status for a single subsystem. |
| `HealthRegistry` | `aquilia/health.py` | object | Centralized health tracking for all subsystems. |
| `LifecyclePhase` | `aquilia/lifecycle.py` | Enum | Lifecycle phases. |
| `LifecycleEvent` | `aquilia/lifecycle.py` | object | Event emitted during lifecycle transitions. |
| `LifecycleError` | `aquilia/lifecycle.py` | Exception | Raised when lifecycle operation fails. |
| `LifecycleCoordinator` | `aquilia/lifecycle.py` | object | Coordinates application lifecycle across multiple apps. |
| `LifecycleManager` | `aquilia/lifecycle.py` | object | High-level lifecycle manager with context manager support. |
| `ComponentKind` | `aquilia/manifest.py` | str, Enum | Classification of framework components for auto-discovery. |
| `ComponentRef` | `aquilia/manifest.py` | object | Universal typed reference to any framework component. |
| `ServiceScope` | `aquilia/manifest.py` | str, Enum | Service lifecycle scope. |
| `LifecycleConfig` | `aquilia/manifest.py` | object | Lifecycle hook configuration. |
| `ServiceConfig` | `aquilia/manifest.py` | object | Service registration configuration with complete DI support. |
| `MiddlewareConfig` | `aquilia/manifest.py` | object | Middleware registration configuration. |
| `SessionConfig` | `aquilia/manifest.py` | object | Session management configuration. |
| `FaultHandlerConfig` | `aquilia/manifest.py` | object | Fault handler configuration. |
| `FaultHandlingConfig` | `aquilia/manifest.py` | object | Fault/error handling configuration. |
| `FeatureConfig` | `aquilia/manifest.py` | object | Feature flag configuration. |
| `BackgroundTaskConfig` | `aquilia/manifest.py` | object | Per-module background task configuration. |
| `TemplateConfig` | `aquilia/manifest.py` | object | Template engine configuration. |
| `DatabaseConfig` | `aquilia/manifest.py` | object | DEPRECATED: Manifest-level database configuration. |
| `AppManifest` | `aquilia/manifest.py` | object | Production-grade application manifest for complete app configuration. |
| `MiddlewareDescriptor` | `aquilia/middleware.py` | object | Descriptor for middleware registration. |
| `MiddlewareStack` | `aquilia/middleware.py` | object | Manages middleware stack with deterministic ordering. |
| `RequestIdMiddleware` | `aquilia/middleware.py` | object | Adds unique request ID to each request. |
| `ExceptionMiddleware` | `aquilia/middleware.py` | object | Catches exceptions and converts them to error responses. |
| `LoggingMiddleware` | `aquilia/middleware.py` | object | Logs request/response with timing. |
| `TimeoutMiddleware` | `aquilia/middleware.py` | object | Enforces request timeout. |
| `CORSMiddleware` | `aquilia/middleware.py` | object | Handles CORS headers. |
| `CompressionMiddleware` | `aquilia/middleware.py` | object | Compresses response bodies. |
| `Secret` | `aquilia/pyconfig.py` | object | A configuration field that holds a sensitive value (password, API key ...). |
| `Env` | `aquilia/pyconfig.py` | object | Bind a configuration field to an environment variable. |
| `AquilaConfig` | `aquilia/pyconfig.py` | object | Base class for Aquilia Python-native configuration. |
| `PyConfigLoader` | `aquilia/pyconfig.py` | object | Load an ``AquilaConfig`` subclass from a Python source file. |
| `RequestFault` | `aquilia/request.py` | Fault | Base class for request-related faults. |
| `BadRequest` | `aquilia/request.py` | RequestFault | Malformed request (400). |
| `PayloadTooLarge` | `aquilia/request.py` | RequestFault | Request payload exceeds limits (413). |
| `UnsupportedMediaType` | `aquilia/request.py` | RequestFault | Unsupported Content-Type (415). |
| `ClientDisconnect` | `aquilia/request.py` | RequestFault | Client disconnected during request (499). |
| `InvalidJSON` | `aquilia/request.py` | RequestFault | Invalid JSON payload (400). |
| `InvalidCrous` | `aquilia/request.py` | RequestFault | Invalid CROUS binary payload (400). |
| `CrousUnavailable` | `aquilia/request.py` | RequestFault | CROUS library not installed (500-level). |
| `InvalidHeader` | `aquilia/request.py` | RequestFault | Invalid header format (400). |
| `MultipartParseError` | `aquilia/request.py` | RequestFault | Multipart parsing failed (400). |
| `Request` | `aquilia/request.py` | object | Production-grade request object for Aquilia. |
| `BackgroundTask` | `aquilia/response.py` | Protocol | Protocol for background tasks executed after response is sent. |
| `CallableBackgroundTask` | `aquilia/response.py` | object | Simple callable-based background task. |
| `ServerSentEvent` | `aquilia/response.py` | object | Server-Sent Event data structure. |
| `MediaChunk` | `aquilia/response.py` | object | Type-safe media chunk container for streaming payloads. |
| `HLSSegment` | `aquilia/response.py` | object | Single media segment entry in an HLS media playlist. |
| `HLSVariant` | `aquilia/response.py` | object | Variant stream descriptor for an HLS master playlist. |
| `CookieSigner` | `aquilia/response.py` | object | Cookie signer with HMAC-based signing and key rotation support. |
| `ResponseStreamError` | `aquilia/response.py` | Fault | Error during response streaming. |
| `TemplateRenderError` | `aquilia/response.py` | Fault | Template rendering error during response. |
| `InvalidHeaderError` | `aquilia/response.py` | Fault | Invalid header name or value (injection attempt). |
| `ClientDisconnectError` | `aquilia/response.py` | Fault | Client disconnected during response send. |
| `RangeNotSatisfiableError` | `aquilia/response.py` | Fault | Invalid Range header (416 response). |
| `HLSManifestError` | `aquilia/response.py` | Fault | Invalid HLS manifest payload or helper usage. |
| `Response` | `aquilia/response.py` | object | Production-grade HTTP response with ASGI 3 streaming support. |
| `RuntimePhase` | `aquilia/runtime.py` | str, Enum | Lifecycle phase of an :class:`AquiliaRuntime` instance. |
| `RuntimeConfig` | `aquilia/runtime.py` | object | Immutable configuration for an :class:`AquiliaRuntime` instance. |
| `AquiliaRuntime` | `aquilia/runtime.py` | object | Structured ASGI bootstrap lifecycle manager. |
| `AquiliaServer` | `aquilia/server.py` | object | Main Aquilia server that orchestrates all components with lifecycle management. |
| `SignerBackend` | `aquilia/signing.py` | ABC | Abstract backend that produces and verifies raw byte signatures. |
| `HmacSignerBackend` | `aquilia/signing.py` | SignerBackend | Default signing backend - HMAC with a configurable digest. |
| `AsymmetricSignerBackend` | `aquilia/signing.py` | SignerBackend | Asymmetric signing backend using the ``cryptography`` package. |
| `Signer` | `aquilia/signing.py` | object | Simple HMAC-based data signer. |
| `TimestampSigner` | `aquilia/signing.py` | Signer | Signer that embeds a UTC timestamp in the signed value. |
| `RotatingSigner` | `aquilia/signing.py` | object | A signer that supports transparent key rotation. |
| `SessionSigner` | `aquilia/signing.py` | TimestampSigner | Timestamped signer for Aquilia session cookies. |
| `CSRFSigner` | `aquilia/signing.py` | Signer | Signer for CSRF tokens. |
| `ActivationLinkSigner` | `aquilia/signing.py` | TimestampSigner | Timestamped signer for one-time activation / password-reset URLs. |
| `CacheKeySigner` | `aquilia/signing.py` | Signer | Signer for cache key integrity verification. |
| `CookieSigner` | `aquilia/signing.py` | TimestampSigner | Timestamped signer for signed HTTP cookies (non-session). |
| `APIKeySigner` | `aquilia/signing.py` | TimestampSigner | Timestamped signer for short-lived API access keys / signed URLs. |
| `SigningConfig` | `aquilia/signing.py` | object | Runtime signing configuration. |

## Public Function Summary

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `parse_date_header` | `aquilia/_datastructures.py` | `def parse_date_header(date_str: str &#124; None) -> datetime &#124; None` | Parse HTTP date header. |
| `parse_authorization_header` | `aquilia/_datastructures.py` | `def parse_authorization_header(auth_header: str &#124; None) -> tuple[str, str] &#124; None` | Parse Authorization header. |
| `create_upload_file_from_bytes` | `aquilia/_uploads.py` | `def create_upload_file_from_bytes(filename: str, content: bytes, content_type: str = 'application/octet-stream') -> UploadFile` | Create an UploadFile from bytes (in-memory). |
| `create_upload_file_from_path` | `aquilia/_uploads.py` | `def create_upload_file_from_path(filename: str, file_path: Path, content_type: str = 'application/octet-stream') -> UploadFile` | Create an UploadFile from a disk path. |
| `find_dotenv` | `aquilia/dotenv.py` | `def find_dotenv(filename: str = '.env', raise_error: bool = False, usecwd: bool = False) -> Path &#124; None` | Search for a .env file. |
| `load_dotenv` | `aquilia/dotenv.py` | `def load_dotenv(dotenv_path: str &#124; Path &#124; None = None, *, override: bool = False, interpolate: bool = True, encoding: str = 'utf-8') -> bool` | Load a .env file into os.environ. |
| `dotenv_values` | `aquilia/dotenv.py` | `def dotenv_values(dotenv_path: str &#124; Path &#124; None = None, *, interpolate: bool = True, encoding: str = 'utf-8') -> dict[str, str]` | Parse a .env file and return values WITHOUT loading into os.environ. |
| `ensure_dotenv_loaded` | `aquilia/dotenv.py` | `def ensure_dotenv_loaded(path: str &#124; Path &#124; None = None, *, auto_load: bool &#124; None = None) -> None` | Ensure dotenv is loaded (idempotent). |
| `is_dotenv_loaded` | `aquilia/dotenv.py` | `def is_dotenv_loaded() -> bool` | Check if dotenv has been loaded. |
| `reset_dotenv_state` | `aquilia/dotenv.py` | `def reset_dotenv_state() -> None` | Reset dotenv loaded state. |
| `get_engine_metrics` | `aquilia/engine.py` | `def get_engine_metrics() -> EngineMetrics` | Return the process-level engine metrics singleton. |
| `create_app` | `aquilia/entrypoint.py` | `def create_app(workspace_root: Path &#124; None = None, mode: str &#124; None = None) -> Any` | Create the ASGI application from workspace configuration. |
| `requires` | `aquilia/flow.py` | `def requires(*effect_names: str) -> Callable` | Decorator declaring effect dependencies on a handler or flow node. |
| `get_required_effects` | `aquilia/flow.py` | `def get_required_effects(func: Callable) -> list[str]` | Extract declared effect requirements from a callable. |
| `pipeline` | `aquilia/flow.py` | `def pipeline(name: str = 'pipeline', *, timeout: float &#124; None = None) -> FlowPipeline` | Create a new FlowPipeline. |
| `guard` | `aquilia/flow.py` | `def guard(fn: Callable, *, name: str &#124; None = None, priority: int = PRIORITY_AUTH, effects: list[str] &#124; None = None) -> FlowNode` | Create a guard FlowNode. |
| `transform` | `aquilia/flow.py` | `def transform(fn: Callable, *, name: str &#124; None = None, priority: int = PRIORITY_TRANSFORM, effects: list[str] &#124; None = None) -> FlowNode` | Create a transform FlowNode. |
| `handler` | `aquilia/flow.py` | `def handler(fn: Callable, *, name: str &#124; None = None, priority: int = PRIORITY_DEFAULT, effects: list[str] &#124; None = None) -> FlowNode` | Create a handler FlowNode. |
| `hook` | `aquilia/flow.py` | `def hook(fn: Callable, *, name: str &#124; None = None, priority: int = PRIORITY_LOG, effects: list[str] &#124; None = None) -> FlowNode` | Create a hook FlowNode. |
| `from_pipeline_list` | `aquilia/flow.py` | `def from_pipeline_list(nodes: Sequence[Any], *, name: str = 'controller_pipeline') -> FlowPipeline` | Convert a controller-style pipeline list to a FlowPipeline. |
| `create_lifecycle_coordinator` | `aquilia/lifecycle.py` | `def create_lifecycle_coordinator(runtime: Any, config: Any = None) -> LifecycleCoordinator` | Factory function to create lifecycle coordinator. |
| `reset_dotenv_state` | `aquilia/pyconfig.py` | `def reset_dotenv_state() -> None` | Reset the dotenv loading state. |
| `section` | `aquilia/pyconfig.py` | `def section(cls: type) -> type` | Mark a nested class as a config *section*. |
| `has_crous` | `aquilia/response.py` | `def has_crous() -> bool` | Return ``True`` if the ``crous`` library is importable. |
| `Ok` | `aquilia/response.py` | `def Ok(content: Any = None, **kwargs) -> Response` | 200 OK response. |
| `Created` | `aquilia/response.py` | `def Created(content: Any = None, location: str &#124; None = None, **kwargs) -> Response` | 201 Created response. |
| `NoContent` | `aquilia/response.py` | `def NoContent() -> Response` | 204 No Content response. |
| `BadRequest` | `aquilia/response.py` | `def BadRequest(message: str = 'Bad Request', **kwargs) -> Response` | 400 Bad Request response. |
| `Unauthorized` | `aquilia/response.py` | `def Unauthorized(message: str = 'Unauthorized', **kwargs) -> Response` | 401 Unauthorized response. |
| `Forbidden` | `aquilia/response.py` | `def Forbidden(message: str = 'Forbidden', **kwargs) -> Response` | 403 Forbidden response. |
| `NotFound` | `aquilia/response.py` | `def NotFound(message: str = 'Not Found', **kwargs) -> Response` | 404 Not Found response. |
| `InternalError` | `aquilia/response.py` | `def InternalError(message: str = 'Internal Server Error', **kwargs) -> Response` | 500 Internal Server Error response. |
| `generate_etag` | `aquilia/response.py` | `def generate_etag(content: bytes, weak: bool = False) -> str` | Generate ETag from content. |
| `generate_etag_from_file` | `aquilia/response.py` | `def generate_etag_from_file(path: PathLike, weak: bool = True) -> str` | Generate ETag from file metadata. |
| `check_not_modified` | `aquilia/response.py` | `def check_not_modified(request: Any, etag: str &#124; None = None, last_modified: datetime &#124; None = None) -> bool` | Check if response should be 304 Not Modified. |
| `not_modified_response` | `aquilia/response.py` | `def not_modified_response(etag: str &#124; None = None) -> Response` | Create 304 Not Modified response. |
| `requires_crous` | `aquilia/response.py` | `def requires_crous(func: Callable) -> Callable` | Mark a handler as preferring CROUS binary responses. |
| `b64_encode` | `aquilia/signing.py` | `def b64_encode(data: bytes) -> str` | URL-safe, no-padding Base64 encode. |
| `b64_decode` | `aquilia/signing.py` | `def b64_decode(data: str &#124; bytes) -> bytes` | URL-safe, no-padding Base64 decode. |
| `constant_time_compare` | `aquilia/signing.py` | `def constant_time_compare(a: bytes &#124; str, b: bytes &#124; str) -> bool` | Compare two values in constant time to prevent timing attacks. |
| `derive_key` | `aquilia/signing.py` | `def derive_key(secret: str &#124; bytes, salt: str, algorithm: str = 'HS256') -> bytes` | Derive a signing sub-key from *secret* and *salt* using HKDF-lite. |
| `dumps` | `aquilia/signing.py` | `def dumps(obj: Any, *, secret: str &#124; bytes &#124; None = None, salt: str = 'aquilia.signing.dumps', algorithm: str = 'HS256', compress: bool = False, max_age: float &#124; int &#124; timedelta &#124; None = None, timestamp: bool = True) -> str` | Serialise *obj* to a signed URL-safe string. |
| `loads` | `aquilia/signing.py` | `def loads(token: str, *, secret: str &#124; bytes &#124; None = None, salt: str = 'aquilia.signing.dumps', algorithm: str = 'HS256', max_age: float &#124; int &#124; timedelta &#124; None = None) -> Any` | Verify and deserialise a token produced by :func:`dumps`. |
| `configure` | `aquilia/signing.py` | `def configure(secret: str &#124; bytes, *, fallback_secrets: Sequence[str &#124; bytes] &#124; None = None, algorithm: str = 'HS256', salt: str = 'aquilia.signing') -> None` | Configure the global signing secret used by module-level helpers. |
| `make_signer` | `aquilia/signing.py` | `def make_signer(secret: str &#124; bytes &#124; None = None, *, salt: str = 'aquilia.signing', algorithm: str &#124; None = None) -> Signer` | Create a :class:`Signer` with the given (or global) settings. |
| `make_timestamp_signer` | `aquilia/signing.py` | `def make_timestamp_signer(secret: str &#124; bytes &#124; None = None, *, salt: str = 'aquilia.signing.ts', algorithm: str &#124; None = None) -> TimestampSigner` | Create a :class:`TimestampSigner` with the given (or global) settings. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `VERSION` | `aquilia/_version.py` | `tuple[int, int, int]` |
| `WORKSPACE_VERSION` | `aquilia/_version.py` | `str` |
| `_VAR_NAME_PATTERN` | `aquilia/dotenv.py` | `Final` |
| `_INTERPOLATE_BRACES` | `aquilia/dotenv.py` | `Final` |
| `_INTERPOLATE_SIMPLE` | `aquilia/dotenv.py` | `Final` |
| `T` | `aquilia/effects.py` | `TypeVar('T')` |
| `T` | `aquilia/flow.py` | `TypeVar('T')` |
| `R` | `aquilia/flow.py` | `TypeVar('R')` |
| `E` | `aquilia/flow.py` | `TypeVar('E')` |
| `PRIORITY_CRITICAL` | `aquilia/flow.py` | `10` |
| `PRIORITY_AUTH` | `aquilia/flow.py` | `20` |
| `PRIORITY_VALIDATE` | `aquilia/flow.py` | `30` |
| `PRIORITY_TRANSFORM` | `aquilia/flow.py` | `40` |
| `PRIORITY_DEFAULT` | `aquilia/flow.py` | `50` |
| `PRIORITY_ENRICH` | `aquilia/flow.py` | `60` |
| `PRIORITY_LOG` | `aquilia/flow.py` | `70` |
| `PRIORITY_CLEANUP` | `aquilia/flow.py` | `80` |
| `_FD_SECURITY` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.SECURITY)` |
| `_FD_IO` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.IO)` |
| `_FD_ROUTING` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.ROUTING)` |
| `_FD_EFFECT` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.EFFECT)` |
| `_FD_MODEL` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.MODEL)` |
| `_FD_CACHE` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.CACHE)` |
| `_FD_CONFIG` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.CONFIG)` |
| `_FD_REGISTRY` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.REGISTRY)` |
| `_FD_DI` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.DI)` |
| `_FD_FLOW` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.FLOW)` |
| `_FD_SYSTEM` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.SYSTEM)` |
| `_FD_STORAGE` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.STORAGE)` |
| `_FD_TASKS` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.TASKS)` |
| `_FD_TEMPLATE` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.TEMPLATE)` |
| `_FD_HTTP` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.HTTP)` |
| `_FAST_SKIP_NAMES` | `aquilia/middleware.py` | `frozenset({'LoggingMiddleware', 'TimeoutMiddleware'})` |
| `_FALLBACK_500_HTML` | `aquilia/middleware.py` | `'<!DOCTYPE html><html><head><meta charset="utf-8"><title>500 Internal Server Error</title><style>body{font-family:system-ui,sans-serif;background:#000;color:#ed` |
| `T` | `aquilia/pyconfig.py` | `TypeVar('T')` |
| `CROUS_MEDIA_TYPE` | `aquilia/request.py` | `'application/x-crous'` |
| `CROUS_MEDIA_TYPES` | `aquilia/request.py` | `frozenset({'application/x-crous', 'application/crous', 'application/vnd.crous'})` |
| `CROUS_MAGIC` | `aquilia/request.py` | `b'CROUSv1'` |
| `T` | `aquilia/request.py` | `TypeVar('T')` |
| `_FD_IO` | `aquilia/request.py` | `cast(FaultDomain, FaultDomain.IO)` |
| `_FD_SECURITY` | `aquilia/request.py` | `cast(FaultDomain, FaultDomain.SECURITY)` |
| `CROUS_MEDIA_TYPE` | `aquilia/response.py` | `'application/x-crous'` |
| `CROUS_MAGIC` | `aquilia/response.py` | `b'CROUSv1'` |
| `_PHASE_ORDER` | `aquilia/runtime.py` | `dict[RuntimePhase, int]` |
| `_HMAC_ALGORITHMS` | `aquilia/signing.py` | `frozenset[str]` |
| `_ASYMMETRIC_ALGORITHMS` | `aquilia/signing.py` | `frozenset[str]` |
| `_ALL_ALGORITHMS` | `aquilia/signing.py` | `frozenset[str]` |
| `_HMAC_DIGEST_MAP` | `aquilia/signing.py` | `dict[str, str]` |
| `_SEP` | `aquilia/signing.py` | `':'` |
| `_MIN_KEY_BYTES` | `aquilia/signing.py` | `32` |
| `_EPOCH` | `aquilia/signing.py` | `int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp() * 1000000)` |
| `_TS_FORMAT_V1` | `aquilia/signing.py` | `1` |
| `_GLOBAL_SECRETS` | `aquilia/signing.py` | `list[str &#124; bytes]` |
| `_GLOBAL_ALGORITHM` | `aquilia/signing.py` | `str` |
| `_GLOBAL_SALT` | `aquilia/signing.py` | `str` |

## Detailed Classes And Methods

### Class: `MultiDict`

- Source: `aquilia/_datastructures.py`
- Bases: `MutableMapping[str, list[str]]`
- Summary: Dictionary that supports multiple values per key.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get` | `def get(self, key: str, default: Any = None) -> Any` |  | Get first value for a key. |
| `get_all` | `def get_all(self, key: str) -> list[str]` |  | Get all values for a key. |
| `add` | `def add(self, key: str, value: str) -> None` |  | Add a value to a key (appends to list). |
| `items_list` | `def items_list(self) -> list[tuple[str, str]]` |  | Return all items as flat list of tuples. |
| `to_dict` | `def to_dict(self, multi: bool = False) -> dict[str, str &#124; list[str]]` |  | Convert to regular dict. |

### Class: `Headers`

- Source: `aquilia/_datastructures.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Case-insensitive header access with raw preservation.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `raw` | `list[tuple[bytes, bytes]]` | `field(default_factory=list)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get` | `def get(self, name: str, default: str &#124; None = None) -> str &#124; None` |  | Get first value for header (case-insensitive). |
| `get_all` | `def get_all(self, name: str) -> list[str]` |  | Get all values for header (case-insensitive). |
| `has` | `def has(self, name: str) -> bool` |  | Check if header exists. |
| `items` | `def items(self) -> Iterator[tuple[str, str]]` |  | Iterate over all headers. |
| `keys` | `def keys(self) -> Iterator[str]` |  | Iterate over header names. |
| `values` | `def values(self) -> Iterator[str]` |  | Iterate over header values. |

### Class: `URL`

- Source: `aquilia/_datastructures.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Parsed URL representation.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `scheme` | `str` |  |
| `host` | `str` |  |
| `port` | `int &#124; None` | `None` |
| `path` | `str` | `'/'` |
| `query` | `str` | `''` |
| `fragment` | `str` | `''` |
| `username` | `str &#124; None` | `None` |
| `password` | `str &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `parse` | `def parse(cls, url: str) -> URL` | classmethod | Parse URL string into components. |
| `netloc` | `def netloc(self) -> str` | property | Build netloc string. |
| `replace` | `def replace(self, **kwargs) -> URL` |  | Create new URL with replaced components. |
| `with_query` | `def with_query(self, **params) -> URL` |  | Create new URL with updated query parameters. |

### Class: `ParsedContentType`

- Source: `aquilia/_datastructures.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Parsed Content-Type header.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `media_type` | `str` |  |
| `params` | `dict[str, str]` | `field(default_factory=dict)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `parse` | `def parse(cls, content_type: str &#124; None) -> ParsedContentType &#124; None` | classmethod | Parse Content-Type header. |
| `charset` | `def charset(self) -> str` | property | Get charset parameter (default: utf-8). |
| `boundary` | `def boundary(self) -> str &#124; None` | property | Get boundary parameter (for multipart). |

### Class: `Range`

- Source: `aquilia/_datastructures.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Parsed HTTP Range header.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `unit` | `str` | `'bytes'` |
| `ranges` | `list[tuple[int &#124; None, int &#124; None]]` | `field(default_factory=list)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `parse` | `def parse(cls, range_header: str &#124; None) -> Range &#124; None` | classmethod | Parse Range header. |

### Class: `UploadFile`

- Source: `aquilia/_uploads.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Uploaded file representation.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `filename` | `str` |  |
| `content_type` | `str` |  |
| `size` | `int &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `read` | `async def read(self, size: int = -1) -> bytes` |  | Read file content. |
| `stream` | `async def stream(self, chunk_size: int &#124; None = None) -> AsyncIterator[bytes]` |  | Stream file content in chunks. |
| `save` | `async def save(self, path: str &#124; Path, overwrite: bool = False) -> Path` |  | Save uploaded file to disk. |
| `close` | `async def close(self) -> None` |  | Clean up temporary file if exists. |

### Class: `FormData`

- Source: `aquilia/_uploads.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Parsed form data containing both fields and files.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `fields` | `MultiDict` | `field(default_factory=MultiDict)` |
| `files` | `dict[str, list[UploadFile]]` | `field(default_factory=dict)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get` | `def get(self, name: str, default: FormValue &#124; None = None) -> FormValue &#124; None` |  | Get field or file by name. |
| `get_field` | `def get_field(self, name: str, default: str &#124; None = None) -> str &#124; None` |  | Get form field value. |
| `get_all_fields` | `def get_all_fields(self, name: str) -> list[str]` |  | Get all values for a form field. |
| `get_file` | `def get_file(self, name: str) -> UploadFile &#124; None` |  | Get first uploaded file by name. |
| `get_all_files` | `def get_all_files(self, name: str) -> list[UploadFile]` |  | Get all uploaded files by name. |
| `cleanup` | `async def cleanup(self) -> None` |  | Clean up all temporary upload files. |

### Class: `UploadStore`

- Source: `aquilia/_uploads.py`
- Bases: `Protocol`
- Summary: Protocol for upload storage backends.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `write_chunk` | `async def write_chunk(self, upload_id: str, chunk: bytes) -> None` |  | Write a chunk of uploaded data. |
| `finalize` | `async def finalize(self, upload_id: str, metadata: dict[str, Any] &#124; None = None) -> Path` |  | Finalize upload and return final path/identifier. |
| `abort` | `async def abort(self, upload_id: str) -> None` |  | Abort upload and clean up partial data. |

### Class: `LocalUploadStore`

- Source: `aquilia/_uploads.py`
- Bases: `object`
- Summary: Local filesystem upload store.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `write_chunk` | `async def write_chunk(self, upload_id: str, chunk: bytes) -> None` |  | Write chunk to temporary file. |
| `finalize` | `async def finalize(self, upload_id: str, metadata: dict[str, Any] &#124; None = None) -> Path` |  | Finalize upload and move to final location. |
| `abort` | `async def abort(self, upload_id: str) -> None` |  | Abort upload and remove temp file. |

### Class: `ASGIAdapter`

- Source: `aquilia/asgi.py`
- Bases: `object`
- Summary: ASGI application adapter.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `handle_http` | `async def handle_http(self, scope: ASGIScope, receive: ASGIReceive, send: ASGISend) -> None` |  | Handle HTTP request with optimized hot path. |
| `handle_websocket` | `async def handle_websocket(self, scope: ASGIScope, receive: ASGIReceive, send: ASGISend) -> None` |  | Handle WebSocket connection. |
| `handle_lifespan` | `async def handle_lifespan(self, scope: ASGIScope, receive: ASGIReceive, send: ASGISend) -> None` |  | Handle ASGI lifespan events. |

### Class: `NestedNamespace`

- Source: `aquilia/config.py`
- Bases: `object`
- Summary: A namespace that supports nested attribute access for app configs.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict` |  | Return the underlying data dictionary. |
| `get` | `def get(self, key: str, default: Any = None) -> Any` |  | Method. |

### Class: `Config`

- Source: `aquilia/config.py`
- Bases: `object`
- Summary: Base class for typed configuration classes.

### Class: `ConfigError`

- Source: `aquilia/config.py`
- Bases: `Exception`
- Summary: Raised when configuration validation fails.

### Class: `ConfigLoader`

- Source: `aquilia/config.py`
- Bases: `object`
- Summary: Loads and merges configuration from multiple sources with precedence:

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `load` | `def load(cls, paths: list[str] &#124; None = None, env_prefix: str = 'AQ_', env_file: str &#124; None = None, overrides: dict[str, Any] &#124; None = None) -> 'ConfigLoader'` | classmethod | Load configuration from multiple sources with proper merge strategy. |
| `get` | `def get(self, path: str, default: Any = None) -> Any` |  | Get config value by dot-separated path. |
| `get_app_config` | `def get_app_config(self, app_name: str, config_class: type[Config]) -> Config` |  | Get and validate configuration for a specific app. |
| `to_dict` | `def to_dict(self) -> dict` |  | Export all config as dictionary. |
| `get_session_config` | `def get_session_config(self) -> dict` |  | Get session configuration with defaults. |
| `get_auth_config` | `def get_auth_config(self) -> dict` |  | Get auth configuration with defaults. |
| `get_template_config` | `def get_template_config(self) -> dict` |  | Get template configuration with defaults. |
| `get_security_config` | `def get_security_config(self) -> dict` |  | Get security configuration with defaults. |
| `get_static_config` | `def get_static_config(self) -> dict` |  | Get static files configuration with defaults. |
| `get_cache_config` | `def get_cache_config(self) -> dict` |  | Get cache configuration with defaults. |
| `get_i18n_config` | `def get_i18n_config(self) -> dict` |  | Get i18n (internationalization) configuration with defaults. |
| `get_mail_config` | `def get_mail_config(self) -> dict` |  | Get mail configuration with defaults. |
| `get_tasks_config` | `def get_tasks_config(self) -> dict` |  | Get background tasks configuration with defaults. |
| `get_storage_config` | `def get_storage_config(self) -> dict` |  | Get storage configuration with defaults. |
| `get_middleware_config` | `def get_middleware_config(self) -> list` |  | Get middleware chain configuration. |
| `get_versioning_config` | `def get_versioning_config(self) -> dict` |  | Get API versioning configuration with defaults. |

### Class: `RuntimeConfig`

- Source: `aquilia/config_builders.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Runtime configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `mode` | `str` | `'dev'` |
| `host` | `str` | `'127.0.0.1'` |
| `port` | `int` | `8000` |
| `reload` | `bool` | `True` |
| `workers` | `int` | `1` |

### Class: `ModuleConfig`

- Source: `aquilia/config_builders.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Module configuration -- workspace-level orchestration metadata.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `version` | `str` | `'0.1.0'` |
| `description` | `str` | `''` |
| `fault_domain` | `str &#124; None` | `None` |
| `route_prefix` | `str &#124; None` | `None` |
| `depends_on` | `list[str]` | `field(default_factory=list)` |
| `tags` | `list[str]` | `field(default_factory=list)` |
| `imports` | `list[str]` | `field(default_factory=list)` |
| `exports` | `list[str]` | `field(default_factory=list)` |
| `on_startup` | `str &#124; None` | `None` |
| `on_shutdown` | `str &#124; None` | `None` |
| `database` | `dict[str, Any] &#124; None` | `None` |
| `auto_discover` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Convert to dictionary format. |

### Class: `Module`

- Source: `aquilia/config_builders.py`
- Bases: `object`
- Summary: Fluent module builder -- workspace-level orchestration only.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `auto_discover` | `def auto_discover(self, enabled: bool = True) -> 'Module'` |  | Configure auto-discovery behavior. |
| `fault_domain` | `def fault_domain(self, domain: str) -> 'Module'` |  | Set fault domain. |
| `route_prefix` | `def route_prefix(self, prefix: str) -> 'Module'` |  | Set route prefix. |
| `depends_on` | `def depends_on(self, *modules: str) -> 'Module'` |  | Set module dependencies (legacy -- prefer imports()). |
| `imports` | `def imports(self, *modules: str) -> 'Module'` |  | Declare module imports (v2 encapsulation). |
| `exports` | `def exports(self, *components: str) -> 'Module'` |  | Declare exported components (v2 encapsulation). |
| `tags` | `def tags(self, *module_tags: str) -> 'Module'` |  | Set module tags for organization and filtering. |
| `register_controllers` | `def register_controllers(self, *controllers: str) -> 'Module'` |  | DEPRECATED -- declare controllers in modules/*/manifest.py instead. |
| `register_services` | `def register_services(self, *services: str) -> 'Module'` |  | DEPRECATED -- declare services in modules/*/manifest.py instead. |
| `register_providers` | `def register_providers(self, *providers: dict[str, Any]) -> 'Module'` |  | DEPRECATED -- declare providers in modules/*/manifest.py instead. |
| `register_routes` | `def register_routes(self, *routes: dict[str, Any]) -> 'Module'` |  | DEPRECATED -- declare routes via controllers in modules/*/manifest.py instead. |
| `register_sockets` | `def register_sockets(self, *sockets: str) -> 'Module'` |  | DEPRECATED -- declare socket controllers in modules/*/manifest.py instead. |
| `register_middlewares` | `def register_middlewares(self, *middlewares: str) -> 'Module'` |  | DEPRECATED -- declare middleware in modules/*/manifest.py instead. |
| `register_models` | `def register_models(self, *models: str) -> 'Module'` |  | DEPRECATED -- declare models in modules/*/manifest.py instead. |
| `register_serializers` | `def register_serializers(self, *serializers: str) -> 'Module'` |  | DEPRECATED -- declare serializers in modules/*/manifest.py instead. |
| `on_startup` | `def on_startup(self, hook: str) -> 'Module'` |  | Register a startup hook for this module. |
| `on_shutdown` | `def on_shutdown(self, hook: str) -> 'Module'` |  | Register a shutdown hook for this module. |
| `database` | `def database(self, url: str &#124; None = None, *, config: Any &#124; None = None, auto_connect: bool = True, auto_create: bool = True, auto_migrate: bool = False, migrations_dir: str = 'migrations', **kwargs) -> 'Module'` |  | Configure database for this module. |
| `build` | `def build(self) -> ModuleConfig` |  | Build module configuration. |

### Class: `AuthConfig`

- Source: `aquilia/config_builders.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Authentication configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `enabled` | `bool` | `True` |
| `store_type` | `str` | `'memory'` |
| `secret_key` | `str &#124; None` | `None` |
| `algorithm` | `str` | `'HS256'` |
| `issuer` | `str` | `'aquilia'` |
| `audience` | `str` | `'aquilia-app'` |
| `access_token_ttl_minutes` | `int` | `60` |
| `refresh_token_ttl_days` | `int` | `30` |
| `require_auth_by_default` | `bool` | `False` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Convert to dictionary format. |

### Class: `Integration`

- Source: `aquilia/config_builders.py`
- Bases: `object`
- Summary: Integration configuration builders.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `auth` | `def auth(config: AuthConfig &#124; None = None, enabled: bool = True, store_type: str = 'memory', secret_key: str &#124; None = None, **kwargs) -> dict[str, Any]` | staticmethod | Configure authentication. |
| `sessions` | `def sessions(policy: Any &#124; None = None, store: Any &#124; None = None, transport: Any &#124; None = None, **kwargs) -> dict[str, Any]` | staticmethod | Configure session integration with Aquilia's unique fluent syntax. |
| `di` | `def di(auto_wire: bool = True, **kwargs) -> dict[str, Any]` | staticmethod | Configure dependency injection. |
| `database` | `def database(url: str &#124; None = None, *, config: Any &#124; None = None, auto_connect: bool = True, auto_create: bool = True, auto_migrate: bool = False, migrations_dir: str = 'migrations', pool_size: int = 5, echo: bool = False, model_paths: list[str] &#124; None = None, scan_dirs: list[str] &#124; None = None, **kwargs) -> dict[str, Any]` | staticmethod | Configure database and AMDL model integration. |
| `storage` | `def storage(default: str = 'default', backends: dict[str, Any] &#124; None = None, **kwargs) -> dict[str, Any]` | staticmethod | Configure file storage backends. |
| `registry` | `def registry(**kwargs) -> dict[str, Any]` | staticmethod | Configure registry. |
| `routing` | `def routing(strict_matching: bool = True, **kwargs) -> dict[str, Any]` | staticmethod | Configure routing. |
| `fault_handling` | `def fault_handling(default_strategy: str = 'propagate', **kwargs) -> dict[str, Any]` | staticmethod | Configure fault handling. |
| `cache` | `def cache(backend: str = 'memory', default_ttl: int = 300, max_size: int = 10000, eviction_policy: str = 'lru', namespace: str = 'default', key_prefix: str = 'aq:', serializer: str = 'json', redis_url: str = 'redis://localhost:6379/0', redis_max_connections: int = 10, l1_max_size: int = 1000, l1_ttl: int = 60, l2_backend: str = 'redis', middleware_enabled: bool = False, middleware_default_ttl: int = 60, **kwargs) -> dict[str, Any]` | staticmethod | Configure the caching subsystem. |
| `tasks` | `def tasks(backend: str = 'memory', num_workers: int = 4, default_queue: str = 'default', cleanup_interval: float = 300.0, cleanup_max_age: float = 3600.0, max_retries: int = 3, retry_delay: float = 1.0, retry_backoff: float = 2.0, retry_max_delay: float = 300.0, default_timeout: float = 300.0, auto_start: bool = True, dead_letter_max: int = 1000, scheduler_tick: float = 15.0, **kwargs) -> dict[str, Any]` | staticmethod | Configure the background task subsystem. |
| `admin` | `def admin(url_prefix: str = '/admin', site_title: str = 'Aquilia Admin', site_header: str = 'Aquilia Administration', auto_discover: bool = True, login_url: str &#124; None = None, list_per_page: int = 25, theme: str = 'auto', modules: Optional['Integration.AdminModules'] = None, audit: Optional['Integration.AdminAudit'] = None, monitoring: Optional['Integration.AdminMonitoring'] = None, sidebar: Optional['Integration.AdminSidebar'] = None, containers: Optional['Integration.AdminContainers'] = None, pods: Optional['Integration.AdminPods'] = None, security: Optional['Integration.AdminSecurity'] = None, enable_audit: bool &#124; None = None, audit_max_entries: int = 10000, enable_dashboard: bool &#124; None = None, enable_orm: bool &#124; None = None, enable_migrations: bool &#124; None = None, enable_config: bool &#124; None = None, enable_workspace: bool &#124; None = None, enable_permissions: bool &#124; None = None, enable_monitoring: bool &#124; None = None, enable_admin_users: bool &#124; None = None, enable_containers: bool &#124; None = None, enable_pods: bool &#124; None = None, enable_profile: bool &#124; None = None, audit_log_logins: bool &#124; None = None, audit_log_views: bool &#124; None = None, audit_log_searches: bool &#124; None = None, enable_api_keys: bool &#124; None = None, enable_preferences: bool &#124; None = None, audit_excluded_actions: list[str] &#124; None = None, monitoring_metrics: list[str] &#124; None = None, monitoring_refresh_interval: int &#124; None = None, sidebar_sections: dict[str, bool] &#124; None = None, **kwargs) -> dict[str, Any]` | staticmethod | Configure the admin dashboard integration. |
| `patterns` | `def patterns(**kwargs) -> dict[str, Any]` | staticmethod | Configure patterns. |
| `static_files` | `def static_files(directories: dict[str, str] &#124; None = None, cache_max_age: int = 86400, immutable: bool = False, etag: bool = True, gzip: bool = True, brotli: bool = True, memory_cache: bool = True, html5_history: bool = False, **kwargs) -> dict[str, Any]` | staticmethod | Configure static file serving middleware. |
| `cors` | `def cors(allow_origins: list[str] &#124; None = None, allow_methods: list[str] &#124; None = None, allow_headers: list[str] &#124; None = None, expose_headers: list[str] &#124; None = None, allow_credentials: bool = False, max_age: int = 600, allow_origin_regex: str &#124; None = None, **kwargs) -> dict[str, Any]` | staticmethod | Configure CORS middleware. |
| `csp` | `def csp(policy: dict[str, list[str]] &#124; None = None, report_only: bool = False, nonce: bool = True, preset: str = 'strict', **kwargs) -> dict[str, Any]` | staticmethod | Configure Content-Security-Policy middleware. |
| `rate_limit` | `def rate_limit(limit: int = 100, window: int = 60, algorithm: str = 'sliding_window', per_user: bool = False, burst: int &#124; None = None, exempt_paths: list[str] &#124; None = None, **kwargs) -> dict[str, Any]` | staticmethod | Configure rate limiting middleware. |
| `openapi` | `def openapi(title: str = 'Aquilia API', version: str = '1.0.0', description: str = '', terms_of_service: str = '', contact_name: str = '', contact_email: str = '', contact_url: str = '', license_name: str = '', license_url: str = '', servers: list[dict[str, str]] &#124; None = None, docs_path: str = '/docs', openapi_json_path: str = '/openapi.json', redoc_path: str = '/redoc', include_internal: bool = False, group_by_module: bool = True, infer_request_body: bool = True, infer_responses: bool = True, detect_security: bool = True, external_docs_url: str = '', external_docs_description: str = '', swagger_ui_theme: str = '', swagger_ui_config: dict[str, Any] &#124; None = None, enabled: bool = True, **kwargs) -> dict[str, Any]` | staticmethod | Configure OpenAPI specification generation and interactive documentation. |
| `csrf` | `def csrf(secret_key: str = '', token_length: int = 32, header_name: str = 'X-CSRF-Token', field_name: str = '_csrf_token', cookie_name: str = '_csrf_cookie', cookie_path: str = '/', cookie_domain: str &#124; None = None, cookie_secure: bool = True, cookie_samesite: str = 'Lax', cookie_httponly: bool = False, cookie_max_age: int = 3600, safe_methods: list[str] &#124; None = None, exempt_paths: list[str] &#124; None = None, exempt_content_types: list[str] &#124; None = None, trust_ajax: bool = True, rotate_token: bool = False, failure_status: int = 403, enabled: bool = True, **kwargs) -> dict[str, Any]` | staticmethod | Configure CSRF (Cross-Site Request Forgery) protection integration. |
| `logging` | `def logging(format: str = '%(method)s %(path)s %(status)s %(duration_ms).1fms', level: str = 'INFO', slow_threshold_ms: float = 1000.0, skip_paths: list[str] &#124; None = None, include_headers: bool = False, include_query: bool = True, include_user_agent: bool = False, log_request_body: bool = False, log_response_body: bool = False, colorize: bool = True, enabled: bool = True, **kwargs) -> dict[str, Any]` | staticmethod | Configure request/response logging integration. |
| `mail` | `def mail(default_from: str = 'noreply@localhost', default_reply_to: str &#124; None = None, subject_prefix: str = '', providers: list[dict[str, Any]] &#124; None = None, auth: Any &#124; None = None, console_backend: bool = False, preview_mode: bool = False, template_dirs: list[str] &#124; None = None, retry_max_attempts: int = 5, retry_base_delay: float = 1.0, rate_limit_global: int = 1000, rate_limit_per_domain: int = 100, dkim_enabled: bool = False, dkim_domain: str &#124; None = None, dkim_selector: str = 'aquilia', require_tls: bool = True, pii_redaction: bool = False, metrics_enabled: bool = True, tracing_enabled: bool = False, enabled: bool = True, **kwargs) -> dict[str, Any]` | staticmethod | Configure AquilaMail -- the production-ready async mail subsystem. |
| `mlops` | `def mlops(*, enabled: bool = True, registry_db: str = 'registry.db', blob_root: str = '.aquilia-store', storage_backend: str = 'filesystem', drift_method: str = 'psi', drift_threshold: float = 0.2, drift_num_bins: int = 10, max_batch_size: int = 16, max_latency_ms: float = 50.0, batching_strategy: str = 'hybrid', sample_rate: float = 0.01, log_dir: str = 'prediction_logs', hmac_secret: str &#124; None = None, signing_private_key: str &#124; None = None, signing_public_key: str &#124; None = None, encryption_key: Any &#124; None = None, plugin_auto_discover: bool = True, scaling_policy: dict[str, Any] &#124; None = None, rollout_default_strategy: str = 'canary', auto_rollback: bool = True, metrics_model_name: str = '', metrics_model_version: str = '', cache_enabled: bool = True, cache_ttl: int = 60, cache_namespace: str = 'mlops', artifact_store_dir: str = 'artifacts', fault_engine_debug: bool = False, **kwargs) -> dict[str, Any]` | staticmethod | Configure MLOps platform integration. |
| `i18n` | `def i18n(*, default_locale: str = 'en', available_locales: list[str] &#124; None = None, fallback_locale: str = 'en', catalog_dirs: list[str] &#124; None = None, catalog_format: str = 'json', missing_key_strategy: str = 'log_and_key', auto_reload: bool = False, auto_detect: bool = True, cookie_name: str = 'aq_locale', query_param: str = 'lang', path_prefix: bool = False, resolver_order: list[str] &#124; None = None, enabled: bool = True, **kwargs) -> dict[str, Any]` | staticmethod | Configure the i18n (internationalization) subsystem. |
| `serializers` | `def serializers(*, auto_discover: bool = True, strict_validation: bool = True, raise_on_error: bool = False, date_format: str = 'iso-8601', datetime_format: str = 'iso-8601', coerce_decimal_to_string: bool = True, compact_json: bool = True, enabled: bool = True, **kwargs) -> dict[str, Any]` | staticmethod | Configure global serializer settings. |
| `render` | `def render(service_name: str &#124; None = None, region: str = 'oregon', plan: str = 'starter', num_instances: int = 1, image: str &#124; None = None, health_path: str = '/_health', auto_deploy: str = 'no', **kwargs) -> dict[str, Any]` | staticmethod | Configure Render PaaS deployment. |
| `versioning` | `def versioning(strategy: str = 'header', versions: list[str] &#124; None = None, default_version: str &#124; None = None, require_version: bool = False, header_name: str = 'X-API-Version', query_param: str = 'api_version', url_prefix: str = 'v', url_segment_index: int = 0, strip_version_from_path: bool = True, media_type_param: str = 'version', channels: dict[str, str] &#124; None = None, channel_header: str = 'X-API-Channel', channel_query_param: str = 'api_channel', negotiation_mode: str = 'exact', sunset_policy: Any &#124; None = None, sunset_schedules: dict[str, dict[str, Any]] &#124; None = None, include_version_header: bool = True, response_header_name: str = 'X-API-Version', include_supported_versions_header: bool = True, neutral_paths: list[str] &#124; None = None, enabled: bool = True, **kwargs) -> dict[str, Any]` | staticmethod | Configure API versioning integration. |

### Class: `Workspace`

- Source: `aquilia/config_builders.py`
- Bases: `object`
- Summary: Fluent workspace builder.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `on_startup` | `def on_startup(self, hook: str) -> 'Workspace'` |  | Register a workspace-level startup hook. |
| `on_shutdown` | `def on_shutdown(self, hook: str) -> 'Workspace'` |  | Register a workspace-level shutdown hook. |
| `env_config` | `def env_config(self, config_cls: 'type &#124; AquilaConfig') -> 'Workspace'` |  | Attach a :class:`~aquilia.pyconfig.AquilaConfig` subclass |
| `starter` | `def starter(self, module_name: str) -> 'Workspace'` |  | Register the starter controller module. |
| `middleware` | `def middleware(self, chain: 'Integration.middleware.Chain') -> 'Workspace'` |  | Configure the middleware chain for this workspace. |
| `runtime` | `def runtime(self, mode: str = 'dev', host: str = '127.0.0.1', port: int = 8000, reload: bool = True, workers: int = 1) -> 'Workspace'` |  | Configure runtime settings. |
| `module` | `def module(self, module: Module) -> 'Workspace'` |  | Add a module to the workspace. |
| `integrate` | `def integrate(self, integration: 'dict[str, Any] &#124; Any') -> 'Workspace'` |  | Add an integration. |
| `sessions` | `def sessions(self, policies: list[Any] &#124; None = None, **kwargs) -> 'Workspace'` |  | Configure session management. |
| `i18n` | `def i18n(self, default_locale: str = 'en', available_locales: list[str] &#124; None = None, **kwargs) -> 'Workspace'` |  | Configure internationalization (shorthand for ``integrate(Integration.i18n(...))``). |
| `tasks` | `def tasks(self, num_workers: int = 4, backend: str = 'memory', **kwargs) -> 'Workspace'` |  | Configure background tasks (shorthand for ``integrate(Integration.tasks(...))``). |
| `storage` | `def storage(self, default: str = 'default', backends: dict[str, Any] &#124; None = None, **kwargs) -> 'Workspace'` |  | Configure file storage for the workspace. |
| `security` | `def security(self, cors_enabled: bool = False, csrf_protection: bool = False, helmet_enabled: bool = True, rate_limiting: bool = False, https_redirect: bool = False, hsts: bool = True, proxy_fix: bool = False, **kwargs) -> 'Workspace'` |  | Configure security features. |
| `telemetry` | `def telemetry(self, tracing_enabled: bool = False, metrics_enabled: bool = True, logging_enabled: bool = True, **kwargs) -> 'Workspace'` |  | Configure telemetry and observability. |
| `database` | `def database(self, url: str &#124; None = None, *, config: Any &#124; None = None, auto_connect: bool = True, auto_create: bool = True, auto_migrate: bool = False, migrations_dir: str = 'migrations', **kwargs) -> 'Workspace'` |  | Configure global database for the workspace. |
| `mlops` | `def mlops(self, enabled: bool = True, registry_db: str = 'registry.db', blob_root: str = '.aquilia-store', drift_method: str = 'psi', drift_threshold: float = 0.2, max_batch_size: int = 16, max_latency_ms: float = 50.0, plugin_auto_discover: bool = True, **kwargs) -> 'Workspace'` |  | Configure MLOps platform for this workspace. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Convert workspace to dictionary format compatible with ConfigLoader. |

### Class: `DotEnv`

- Source: `aquilia/dotenv.py`
- Bases: `object`
- Summary: Native dotenv file parser and loader.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `parse` | `def parse(cls, path: str &#124; Path, *, encoding: str = 'utf-8', interpolate: bool = True) -> dict[str, str]` | classmethod | Parse a .env file and return a dictionary of values. |
| `parse_string` | `def parse_string(cls, content: str, *, interpolate: bool = True) -> dict[str, str]` | classmethod | Parse dotenv-formatted string content. |
| `load` | `def load(cls, path: str &#124; Path &#124; None = None, *, override: bool = False, encoding: str = 'utf-8', interpolate: bool = True) -> dict[str, str]` | classmethod | Load environment variables from a .env file into os.environ. |

### Class: `DotEnvLoader`

- Source: `aquilia/dotenv.py`
- Bases: `object`
- Summary: Singleton loader that ensures .env files are loaded exactly once.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `configure` | `def configure(cls, *, search_paths: list[str] &#124; None = None, auto_load: bool = True, override: bool = False, interpolate: bool = True) -> None` | classmethod | Configure the loader before loading. |
| `ensure_loaded` | `def ensure_loaded(cls, *, path: str &#124; Path &#124; None = None, search_paths: list[str] &#124; None = None) -> dict[str, str]` | classmethod | Ensure dotenv files are loaded (idempotent). |
| `is_loaded` | `def is_loaded(cls) -> bool` | classmethod | Check if dotenv files have been loaded. |
| `loaded_files` | `def loaded_files(cls) -> list[Path]` | classmethod | Return list of files that were loaded. |
| `loaded_values` | `def loaded_values(cls) -> dict[str, str]` | classmethod | Return copy of all loaded values. |
| `reset` | `def reset(cls) -> None` | classmethod | Reset the loader state. |

### Class: `EffectKind`

- Source: `aquilia/effects.py`
- Bases: `Enum`
- Summary: Categories of effects.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `DB` |  | `'db'` |
| `CACHE` |  | `'cache'` |
| `QUEUE` |  | `'queue'` |
| `HTTP` |  | `'http'` |
| `STORAGE` |  | `'storage'` |
| `CUSTOM` |  | `'custom'` |

### Class: `Effect`

- Source: `aquilia/effects.py`
- Bases: `Generic[T]`
- Summary: Effect token representing a capability.

### Class: `EffectProvider`

- Source: `aquilia/effects.py`
- Bases: `ABC`
- Summary: Base class for effect providers.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `initialize` | `async def initialize(self)` | abstractmethod | Initialize the provider (called once at startup). |
| `acquire` | `async def acquire(self, mode: str &#124; None = None) -> Any` | abstractmethod | Acquire a resource for this effect (called per-request). |
| `release` | `async def release(self, resource: Any, success: bool = True)` | abstractmethod | Release the resource (called at end of request). |
| `finalize` | `async def finalize(self)` |  | Finalize provider (called at shutdown). |
| `health_check` | `async def health_check(self) -> dict[str, Any]` |  | Check provider health. Override for custom health reporting. |

### Class: `DBTx`

- Source: `aquilia/effects.py`
- Bases: `Effect`
- Summary: Database transaction effect.

### Class: `CacheEffect`

- Source: `aquilia/effects.py`
- Bases: `Effect`
- Summary: Cache effect.

### Class: `QueueEffect`

- Source: `aquilia/effects.py`
- Bases: `Effect`
- Summary: Queue/message publish effect.

### Class: `HTTPEffect`

- Source: `aquilia/effects.py`
- Bases: `Effect`
- Summary: HTTP client effect for outbound requests.

### Class: `StorageEffect`

- Source: `aquilia/effects.py`
- Bases: `Effect`
- Summary: File/blob storage effect.

### Class: `DBTxProvider`

- Source: `aquilia/effects.py`
- Bases: `EffectProvider`
- Summary: Database transaction provider.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `initialize` | `async def initialize(self)` |  | Initialize connection pool. |
| `acquire` | `async def acquire(self, mode: str &#124; None = None)` |  | Acquire database connection. |
| `release` | `async def release(self, resource: Any, success: bool = True)` |  | Release connection and commit/rollback transaction. |
| `health_check` | `async def health_check(self) -> dict[str, Any]` |  | Method. |

### Class: `CacheProvider`

- Source: `aquilia/effects.py`
- Bases: `EffectProvider`
- Summary: Cache effect provider backed by the real CacheService.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `initialize` | `async def initialize(self)` |  | Initialize cache backend. |
| `acquire` | `async def acquire(self, mode: str &#124; None = None)` |  | Get cache handle for namespace. |
| `release` | `async def release(self, resource: Any, success: bool = True)` |  | Nothing to release for cache. |
| `finalize` | `async def finalize(self)` |  | Shutdown underlying cache service. |
| `health_check` | `async def health_check(self) -> dict[str, Any]` |  | Method. |

### Class: `QueueProvider`

- Source: `aquilia/effects.py`
- Bases: `EffectProvider`
- Summary: Queue/message publish effect provider.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `initialize` | `async def initialize(self)` |  | Method. |
| `acquire` | `async def acquire(self, mode: str &#124; None = None)` |  | Return a queue handle for a topic/channel. |
| `release` | `async def release(self, resource: Any, success: bool = True)` |  | Method. |
| `finalize` | `async def finalize(self)` |  | Method. |
| `health_check` | `async def health_check(self) -> dict[str, Any]` |  | Method. |

### Class: `TaskQueueProvider`

- Source: `aquilia/effects.py`
- Bases: `EffectProvider`
- Summary: Task queue effect provider backed by AquilaTasks TaskManager.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `initialize` | `async def initialize(self)` |  | Method. |
| `acquire` | `async def acquire(self, mode: str &#124; None = None)` |  | Method. |
| `release` | `async def release(self, resource: Any, success: bool = True)` |  | Method. |
| `finalize` | `async def finalize(self)` |  | Method. |
| `health_check` | `async def health_check(self) -> dict[str, Any]` |  | Method. |

### Class: `HTTPProvider`

- Source: `aquilia/effects.py`
- Bases: `EffectProvider`
- Summary: HTTP client effect provider for outbound requests.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `initialize` | `async def initialize(self)` |  | Create HTTP client session. |
| `acquire` | `async def acquire(self, mode: str &#124; None = None)` |  | Return HTTP client handle. |
| `release` | `async def release(self, resource: Any, success: bool = True)` |  | Method. |
| `finalize` | `async def finalize(self)` |  | Method. |

### Class: `StorageProvider`

- Source: `aquilia/effects.py`
- Bases: `EffectProvider`
- Summary: File/blob storage effect provider.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `initialize` | `async def initialize(self)` |  | Method. |
| `acquire` | `async def acquire(self, mode: str &#124; None = None)` |  | Method. |
| `release` | `async def release(self, resource: Any, success: bool = True)` |  | Method. |
| `health_check` | `async def health_check(self) -> dict[str, Any]` |  | Method. |

### Class: `CacheServiceHandle`

- Source: `aquilia/effects.py`
- Bases: `object`
- Summary: Handle wrapping real CacheService for a given namespace.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get` | `async def get(self, key: str) -> Any &#124; None` |  | Method. |
| `set` | `async def set(self, key: str, value: Any, ttl: int &#124; None = None)` |  | Method. |
| `delete` | `async def delete(self, key: str)` |  | Method. |

### Class: `CacheHandle`

- Source: `aquilia/effects.py`
- Bases: `object`
- Summary: Handle for cache operations in a namespace.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get` | `async def get(self, key: str) -> Any &#124; None` |  | Get value from cache. |
| `set` | `async def set(self, key: str, value: Any, ttl: int &#124; None = None)` |  | Set value in cache. |
| `delete` | `async def delete(self, key: str)` |  | Delete value from cache. |

### Class: `QueueHandle`

- Source: `aquilia/effects.py`
- Bases: `object`
- Summary: Handle for queue operations on a topic.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `publish` | `async def publish(self, payload: Any, *, headers: dict[str, str] &#124; None = None)` |  | Publish a message to the topic. |
| `publish_batch` | `async def publish_batch(self, payloads: Sequence[Any])` |  | Publish multiple messages. |

### Class: `TaskQueueHandle`

- Source: `aquilia/effects.py`
- Bases: `object`
- Summary: Handle for enqueuing background tasks via the TaskManager.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `enqueue` | `async def enqueue(self, func, *args, **kwargs) -> str` |  | Enqueue a task for background execution. |
| `publish` | `async def publish(self, payload: Any, *, headers: dict[str, str] &#124; None = None)` |  | Compatibility with QueueHandle -- enqueue payload as a task. |
| `publish_batch` | `async def publish_batch(self, payloads: Sequence[Any])` |  | Compatibility with QueueHandle. |

### Class: `HTTPHandle`

- Source: `aquilia/effects.py`
- Bases: `object`
- Summary: Handle for outbound HTTP requests.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get` | `async def get(self, url: str, **kwargs) -> Any` |  | Method. |
| `post` | `async def post(self, url: str, *, json: Any = None, **kwargs) -> Any` |  | Method. |
| `put` | `async def put(self, url: str, *, json: Any = None, **kwargs) -> Any` |  | Method. |
| `delete` | `async def delete(self, url: str, **kwargs) -> Any` |  | Method. |

### Class: `StorageHandle`

- Source: `aquilia/effects.py`
- Bases: `object`
- Summary: Handle for file/blob storage operations.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `read` | `async def read(self, key: str) -> bytes &#124; None` |  | Method. |
| `write` | `async def write(self, key: str, data: bytes) -> None` |  | Method. |
| `delete` | `async def delete(self, key: str) -> bool` |  | Method. |
| `exists` | `async def exists(self, key: str) -> bool` |  | Method. |

### Class: `EffectRegistry`

- Source: `aquilia/effects.py`
- Bases: `object`
- Summary: Registry for effect providers.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `register` | `def register(self, effect_name: str, provider: EffectProvider)` |  | Register an effect provider. |
| `unregister` | `def unregister(self, effect_name: str) -> EffectProvider &#124; None` |  | Unregister and return an effect provider. |
| `initialize_all` | `async def initialize_all(self)` |  | Initialize all registered providers (lifecycle startup hook). |
| `finalize_all` | `async def finalize_all(self)` |  | Finalize all providers (lifecycle shutdown hook). |
| `acquire` | `async def acquire(self, effect_name: str, mode: str &#124; None = None) -> Any` |  | Acquire a resource for the named effect. |
| `release` | `async def release(self, effect_name: str, resource: Any, *, success: bool = True) -> None` |  | Release a resource for the named effect. |
| `startup` | `async def startup(self)` |  | DI lifecycle startup hook. |
| `shutdown` | `async def shutdown(self)` |  | DI lifecycle shutdown hook. |
| `has_effect` | `def has_effect(self, effect_name: str) -> bool` |  | Check if effect is available. |
| `get_provider` | `def get_provider(self, effect_name: str) -> EffectProvider` |  | Get provider for effect. |
| `health_check` | `async def health_check(self) -> dict[str, Any]` |  | Aggregate health from all providers. |
| `register_with_container` | `def register_with_container(self, container: 'Any')` |  | Register this EffectRegistry and all effect providers with a DI container. |
| `list_effects` | `def list_effects(self) -> list[str]` |  | Return all registered effect names. |
| `get_metrics` | `def get_metrics(self) -> dict[str, dict[str, int]]` |  | Return per-effect metrics. |

### Class: `LifecycleHook`

- Source: `aquilia/engine.py`
- Bases: `Enum`
- Summary: Named lifecycle points that subsystems can subscribe to.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `BEFORE_REQUEST` |  | `auto()` |
| `AFTER_REQUEST` |  | `auto()` |
| `ON_ERROR` |  | `auto()` |
| `ON_STARTUP` |  | `auto()` |
| `ON_SHUTDOWN` |  | `auto()` |

### Class: `EngineMetrics`

- Source: `aquilia/engine.py`
- Bases: `object`
- Summary: Lightweight in-process metrics for the Aquilia engine.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `request_started` | `def request_started(self) -> None` |  | Method. |
| `request_finished` | `def request_finished(self, latency_ms: float) -> None` |  | Method. |
| `request_errored` | `def request_errored(self) -> None` |  | Method. |
| `mean_latency_ms` | `def mean_latency_ms(self) -> float` | property | Method. |
| `snapshot` | `def snapshot(self) -> dict[str, Any]` |  | Return a JSON-serialisable snapshot of current metrics. |

### Class: `RequestCtx`

- Source: `aquilia/engine.py`
- Bases: `object`
- Summary: Per-request execution context.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `resolve` | `async def resolve(self, name: str, optional: bool = False) -> Any` |  | Resolve a dependency from the request-scoped container. |
| `resolve_sync` | `def resolve_sync(self, name: str, optional: bool = False) -> Any` |  | Synchronous resolution -- only for sync-safe providers. |
| `get` | `def get(self, key: str, default: Any = None) -> Any` |  | Shorthand for ``ctx.state.get(key, default)``. |
| `set` | `def set(self, key: str, value: Any) -> None` |  | Shorthand for ``ctx.state[key] = value``. |
| `elapsed_ms` | `def elapsed_ms(self) -> float` | property | Milliseconds elapsed since this context was created. |
| `add_cleanup` | `def add_cleanup(self, callback: CleanupCallback) -> None` |  | Register an async or sync callable to run on ``dispose()``. |
| `dispose` | `async def dispose(self) -> None` |  | Dispose of the request context. |

### Class: `FlowNodeType`

- Source: `aquilia/flow.py`
- Bases: `str, Enum`
- Summary: Types of nodes in a flow pipeline.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `GUARD` |  | `'guard'` |
| `TRANSFORM` |  | `'transform'` |
| `HANDLER` |  | `'handler'` |
| `HOOK` |  | `'hook'` |
| `EFFECT` |  | `'effect'` |
| `MIDDLEWARE` |  | `'middleware'` |

### Class: `FlowStatus`

- Source: `aquilia/flow.py`
- Bases: `str, Enum`
- Summary: Pipeline execution outcome.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `SUCCESS` |  | `'success'` |
| `GUARDED` |  | `'guarded'` |
| `ERROR` |  | `'error'` |
| `TIMEOUT` |  | `'timeout'` |
| `CANCELLED` |  | `'cancelled'` |

### Class: `FlowContext`

- Source: `aquilia/flow.py`
- Bases: `object`
- Summary: Typed execution context threaded through the entire flow pipeline.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_effect` | `def get_effect(self, name: str) -> Any` |  | Get an acquired effect resource by name. |
| `has_effect` | `def has_effect(self, name: str) -> bool` |  | Check if an effect resource is currently acquired. |
| `get` | `def get(self, key: str, default: Any = None) -> Any` |  | Method. |
| `set` | `def set(self, key: str, value: Any) -> None` |  | Method. |
| `add_cleanup` | `def add_cleanup(self, callback: Callable[[], Awaitable[None]]) -> None` |  | Register a cleanup callback (LIFO execution order). |
| `dispose` | `async def dispose(self) -> None` |  | Run all cleanup callbacks in LIFO order. |
| `elapsed_ms` | `def elapsed_ms(self) -> float` | property | Method. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Convert to dict for legacy FlowGuard compatibility. |

### Class: `FlowNode`

- Source: `aquilia/flow.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A typed unit in a flow pipeline.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `type` | `FlowNodeType` |  |
| `callable` | `Callable[..., Any]` |  |
| `name` | `str` |  |
| `priority` | `int` | `PRIORITY_DEFAULT` |
| `effects` | `list[str]` | `field(default_factory=list)` |
| `condition` | `Callable[[FlowContext], bool] &#124; None` | `None` |
| `timeout` | `float &#124; None` | `None` |

### Class: `FlowResult`

- Source: `aquilia/flow.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Result of a flow pipeline execution.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `status` | `FlowStatus` |  |
| `value` | `Any` | `None` |
| `context` | `FlowContext &#124; None` | `None` |
| `error` | `Exception &#124; None` | `None` |
| `guard` | `FlowNode &#124; None` | `None` |
| `timings` | `dict[str, float]` | `field(default_factory=dict)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_success` | `def is_success(self) -> bool` | property | Method. |
| `is_guarded` | `def is_guarded(self) -> bool` | property | Method. |

### Class: `FlowError`

- Source: `aquilia/flow.py`
- Bases: `Exception`
- Summary: Raised when a flow pipeline encounters an unrecoverable error.

### Class: `Layer`

- Source: `aquilia/flow.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Composable effect layer -- separates effect construction from usage.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `factory` | `Callable[..., Any]` |  |
| `deps` | `list[str]` | `field(default_factory=list)` |
| `scope` | `str` | `'app'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `build` | `async def build(self, resolved_deps: dict[str, Any]) -> Any` |  | Build the effect provider using resolved dependencies. |
| `merge` | `def merge(*layers: Layer) -> LayerComposition` | staticmethod | Merge multiple layers into a single composition. |
| `provide` | `def provide(layer: Layer, *providers: Layer) -> LayerComposition` | staticmethod | Provide dependencies for a layer from other layers. |

### Class: `LayerComposition`

- Source: `aquilia/flow.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A composition of multiple layers, resolved in dependency order.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `layers` | `list[Layer]` |  |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `build_all` | `async def build_all(self, initial_deps: dict[str, Any] &#124; None = None) -> dict[str, Any]` |  | Build all layers in dependency order. |
| `register_with` | `async def register_with(self, registry: EffectRegistry, initial_deps: dict[str, Any] &#124; None = None) -> None` |  | Build all layers and register providers with the registry. |

### Class: `FlowPipeline`

- Source: `aquilia/flow.py`
- Bases: `object`
- Summary: Composable, typed request pipeline with automatic effect management.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `guard` | `def guard(self, callable_or_node: Callable &#124; FlowNode, *, name: str &#124; None = None, priority: int = PRIORITY_AUTH, effects: list[str] &#124; None = None, condition: Callable &#124; None = None) -> FlowPipeline` |  | Add a guard node. Guards can short-circuit the pipeline. |
| `transform` | `def transform(self, callable_or_node: Callable &#124; FlowNode, *, name: str &#124; None = None, priority: int = PRIORITY_TRANSFORM, effects: list[str] &#124; None = None) -> FlowPipeline` |  | Add a transform node. Transforms modify the context/request data. |
| `handler` | `def handler(self, callable_or_node: Callable &#124; FlowNode, *, name: str &#124; None = None, priority: int = PRIORITY_DEFAULT, effects: list[str] &#124; None = None) -> FlowPipeline` |  | Set the handler node. The handler is the core business logic. |
| `hook` | `def hook(self, callable_or_node: Callable &#124; FlowNode, *, name: str &#124; None = None, priority: int = PRIORITY_LOG, effects: list[str] &#124; None = None) -> FlowPipeline` |  | Add a post-handler hook. Hooks run after the handler. |
| `effect` | `def effect(self, callable_or_node: Callable &#124; FlowNode, *, name: str &#124; None = None, priority: int = PRIORITY_DEFAULT - 5, effects: list[str] &#124; None = None) -> FlowPipeline` |  | Add an effect node. Effect nodes manage resource acquisition. |
| `middleware` | `def middleware(self, callable_or_node: Callable &#124; FlowNode, *, name: str &#124; None = None, priority: int = PRIORITY_CRITICAL) -> FlowPipeline` |  | Add a middleware node. Middleware wraps the entire pipeline. |
| `add_node` | `def add_node(self, node: FlowNode) -> FlowPipeline` |  | Add a pre-built FlowNode. |
| `add_nodes` | `def add_nodes(self, nodes: Sequence[FlowNode]) -> FlowPipeline` |  | Add multiple pre-built FlowNodes. |
| `compose` | `def compose(self, *other: FlowPipeline) -> FlowPipeline` |  | Compose this pipeline with others. |
| `execute` | `async def execute(self, context: FlowContext, effect_registry: EffectRegistry &#124; None = None) -> FlowResult` |  | Execute the pipeline. |
| `execute_with_timeout` | `async def execute_with_timeout(self, context: FlowContext, effect_registry: EffectRegistry &#124; None = None, timeout: float &#124; None = None) -> FlowResult` |  | Execute pipeline with optional timeout. |
| `nodes` | `def nodes(self) -> list[FlowNode]` | property | Return a copy of the node list. |
| `required_effects` | `def required_effects(self) -> set[str]` | property | All effects required by this pipeline. |

### Class: `EffectScope`

- Source: `aquilia/flow.py`
- Bases: `object`
- Summary: Async context manager that acquires and releases effects.

### Class: `SubsystemStatus`

- Source: `aquilia/health.py`
- Bases: `str, Enum`
- Summary: Status of a subsystem.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `HEALTHY` |  | `'healthy'` |
| `DEGRADED` |  | `'degraded'` |
| `UNHEALTHY` |  | `'unhealthy'` |
| `UNKNOWN` |  | `'unknown'` |
| `STARTING` |  | `'starting'` |
| `STOPPED` |  | `'stopped'` |

### Class: `HealthStatus`

- Source: `aquilia/health.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Health status for a single subsystem.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `status` | `SubsystemStatus` | `SubsystemStatus.UNKNOWN` |
| `latency_ms` | `float` | `0.0` |
| `message` | `str` | `''` |
| `details` | `dict[str, Any]` | `field(default_factory=dict)` |
| `checked_at` | `datetime` | `field(default_factory=lambda: datetime.now(timezone.utc))` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict` |  | Serialize for JSON response. |

### Class: `HealthRegistry`

- Source: `aquilia/health.py`
- Bases: `object`
- Summary: Centralized health tracking for all subsystems.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `register` | `def register(self, name: str, status: HealthStatus) -> None` |  | Register or update a subsystem's health status. |
| `register_check` | `def register_check(self, name: str, check: Callable[[], HealthStatus]) -> None` |  | Register a health check function for periodic evaluation. |
| `update` | `def update(self, name: str, status: SubsystemStatus, message: str = '') -> None` |  | Update an existing subsystem's status. |
| `get` | `def get(self, name: str) -> HealthStatus &#124; None` |  | Get a specific subsystem's health status. |
| `all_statuses` | `def all_statuses(self) -> dict[str, HealthStatus]` | property | Get all registered health statuses. |
| `overall` | `def overall(self) -> HealthStatus` |  | Compute aggregate health across all subsystems. |
| `to_dict` | `def to_dict(self) -> dict` |  | Serialize full health report for /health endpoint. |
| `run_checks` | `async def run_checks(self) -> dict[str, HealthStatus]` |  | Run all registered health checks and update statuses. |

### Class: `LifecyclePhase`

- Source: `aquilia/lifecycle.py`
- Bases: `Enum`
- Summary: Lifecycle phases.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `INIT` |  | `'init'` |
| `STARTING` |  | `'starting'` |
| `READY` |  | `'ready'` |
| `STOPPING` |  | `'stopping'` |
| `STOPPED` |  | `'stopped'` |
| `ERROR` |  | `'error'` |

### Class: `LifecycleEvent`

- Source: `aquilia/lifecycle.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Event emitted during lifecycle transitions.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `phase` | `LifecyclePhase` |  |
| `app_name` | `str &#124; None` | `None` |
| `message` | `str &#124; None` | `None` |
| `error` | `Exception &#124; None` | `None` |

### Class: `LifecycleError`

- Source: `aquilia/lifecycle.py`
- Bases: `Exception`
- Summary: Raised when lifecycle operation fails.

### Class: `LifecycleCoordinator`

- Source: `aquilia/lifecycle.py`
- Bases: `object`
- Summary: Coordinates application lifecycle across multiple apps.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `on_event` | `def on_event(self, handler: Callable[[LifecycleEvent], None])` |  | Register event handler. |
| `startup` | `async def startup(self)` |  | Execute startup hooks for all apps in dependency order. |
| `shutdown` | `async def shutdown(self)` |  | Execute shutdown hooks for all started apps in reverse order. |
| `restart` | `async def restart(self)` |  | Restart the application (shutdown then startup). |
| `get_status` | `def get_status(self) -> dict[str, Any]` |  | Get current lifecycle status. |

### Class: `LifecycleManager`

- Source: `aquilia/lifecycle.py`
- Bases: `object`
- Summary: High-level lifecycle manager with context manager support.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `on_event` | `def on_event(self, handler: Callable[[LifecycleEvent], None])` |  | Register event handler. |

### Class: `ComponentKind`

- Source: `aquilia/manifest.py`
- Bases: `str, Enum`
- Summary: Classification of framework components for auto-discovery.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `CONTROLLER` |  | `'controller'` |
| `SERVICE` |  | `'service'` |
| `MIDDLEWARE` |  | `'middleware'` |
| `GUARD` |  | `'guard'` |
| `PIPE` |  | `'pipe'` |
| `INTERCEPTOR` |  | `'interceptor'` |
| `EFFECT` |  | `'effect'` |
| `MODEL` |  | `'model'` |
| `FAULT_HANDLER` |  | `'fault_handler'` |
| `SOCKET_CONTROLLER` |  | `'socket_controller'` |
| `SERIALIZER` |  | `'serializer'` |

### Class: `ComponentRef`

- Source: `aquilia/manifest.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Universal typed reference to any framework component.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `class_path` | `str` |  |
| `kind` | `ComponentKind` |  |
| `metadata` | `ManifestMetadata` | `field(default_factory=dict)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `module_path` | `def module_path(self) -> str` | property | Extract the module path (before ':'). |
| `class_name` | `def class_name(self) -> str` | property | Extract the class name (after ':'). |
| `to_dict` | `def to_dict(self) -> dict` |  | Serialize to dictionary. |

### Class: `ServiceScope`

- Source: `aquilia/manifest.py`
- Bases: `str, Enum`
- Summary: Service lifecycle scope.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `SINGLETON` |  | `'singleton'` |
| `APP` |  | `'app'` |
| `REQUEST` |  | `'request'` |
| `TRANSIENT` |  | `'transient'` |
| `POOLED` |  | `'pooled'` |
| `EPHEMERAL` |  | `'ephemeral'` |

### Class: `LifecycleConfig`

- Source: `aquilia/manifest.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Lifecycle hook configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `on_startup` | `str &#124; None` | `None` |
| `on_shutdown` | `str &#124; None` | `None` |
| `depends_on` | `list[str]` | `field(default_factory=list)` |
| `startup_timeout` | `float` | `30.0` |
| `shutdown_timeout` | `float` | `30.0` |
| `error_strategy` | `str` | `'propagate'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict` |  | Serialize to dictionary. |

### Class: `ServiceConfig`

- Source: `aquilia/manifest.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Service registration configuration with complete DI support.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `class_path` | `str` |  |
| `scope` | `ServiceScope` | `ServiceScope.APP` |
| `auto_discover` | `bool` | `True` |
| `lifecycle` | `LifecycleConfig &#124; None` | `None` |
| `feature_flags` | `list[str]` | `field(default_factory=list)` |
| `aliases` | `list[str]` | `field(default_factory=list)` |
| `factory` | `str &#124; None` | `None` |
| `factory_args` | `dict[str, Any] &#124; None` | `None` |
| `config` | `dict[str, Any] &#124; None` | `None` |
| `observable` | `bool` | `True` |
| `required` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict` |  | Serialize to dictionary. |

### Class: `MiddlewareConfig`

- Source: `aquilia/manifest.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Middleware registration configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `class_path` | `str` |  |
| `scope` | `str` | `'global'` |
| `scope_target` | `str &#124; None` | `None` |
| `priority` | `int` | `50` |
| `condition` | `Callable &#124; None` | `None` |
| `config` | `dict[str, Any] &#124; None` | `None` |
| `on_error` | `str` | `'propagate'` |
| `fallback` | `str &#124; None` | `None` |
| `observable` | `bool` | `True` |
| `log_requests` | `bool` | `False` |
| `log_responses` | `bool` | `False` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict` |  | Serialize to dictionary. |

### Class: `SessionConfig`

- Source: `aquilia/manifest.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Session management configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `enabled` | `bool` | `True` |
| `ttl` | `timedelta` | `field(default_factory=lambda: timedelta(days=7))` |
| `idle_timeout` | `timedelta &#124; None` | `None` |
| `renewal` | `timedelta &#124; None` | `None` |
| `transport` | `str` | `'cookie'` |
| `transport_config` | `dict[str, Any] &#124; None` | `None` |
| `cookie_name` | `str` | `'session_id'` |
| `cookie_domain` | `str &#124; None` | `None` |
| `cookie_path` | `str` | `'/'` |
| `cookie_secure` | `bool` | `True` |
| `cookie_httponly` | `bool` | `True` |
| `cookie_samesite` | `str` | `'Strict'` |
| `store` | `str` | `'memory'` |
| `store_config` | `dict[str, Any] &#124; None` | `None` |
| `encryption_enabled` | `bool` | `True` |
| `encryption_key_env` | `str` | `'SESSION_ENCRYPTION_KEY'` |
| `serializer` | `str` | `'json'` |
| `log_lifecycle` | `bool` | `False` |
| `metrics_enabled` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict` |  | Serialize to dictionary. |

### Class: `FaultHandlerConfig`

- Source: `aquilia/manifest.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Fault handler configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` | `str` |  |
| `handler_path` | `str` |  |
| `recovery_strategy` | `str` | `'propagate'` |
| `fallback_response` | `dict[str, Any] &#124; None` | `None` |

### Class: `FaultHandlingConfig`

- Source: `aquilia/manifest.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Fault/error handling configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `default_domain` | `str` | `'APP'` |
| `strategy` | `str` | `'propagate'` |
| `handlers` | `list[FaultHandlerConfig]` | `field(default_factory=list)` |
| `middlewares` | `list[MiddlewareConfig]` | `field(default_factory=list)` |
| `metrics_enabled` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict` |  | Serialize to dictionary. |

### Class: `FeatureConfig`

- Source: `aquilia/manifest.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Feature flag configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `enabled` | `bool` | `False` |
| `conditions` | `dict[str, Any] &#124; None` | `None` |
| `services` | `list[str]` | `field(default_factory=list)` |
| `controllers` | `list[str]` | `field(default_factory=list)` |
| `middleware` | `list[MiddlewareConfig]` | `field(default_factory=list)` |
| `routes` | `list[str]` | `field(default_factory=list)` |
| `log_usage` | `bool` | `True` |
| `metrics_enabled` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict` |  | Serialize to dictionary. |

### Class: `BackgroundTaskConfig`

- Source: `aquilia/manifest.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Per-module background task configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `tasks` | `list[str]` | `field(default_factory=list)` |
| `default_queue` | `str` | `'default'` |
| `auto_discover` | `bool` | `True` |
| `enabled` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict` |  | Method. |

### Class: `TemplateConfig`

- Source: `aquilia/manifest.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Template engine configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `enabled` | `bool` | `True` |
| `search_paths` | `list[str]` | `field(default_factory=list)` |
| `precompile` | `bool` | `False` |
| `cache` | `str` | `'memory'` |
| `sandbox` | `bool` | `True` |
| `context_processors` | `list[str]` | `field(default_factory=list)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict` |  | Method. |

### Class: `DatabaseConfig`

- Source: `aquilia/manifest.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: DEPRECATED: Manifest-level database configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `url` | `str` | `'sqlite:///db.sqlite3'` |
| `auto_connect` | `bool` | `True` |
| `auto_create` | `bool` | `True` |
| `auto_migrate` | `bool` | `False` |
| `migrations_dir` | `str` | `'migrations'` |
| `pool_size` | `int` | `5` |
| `echo` | `bool` | `False` |
| `model_paths` | `list[str]` | `field(default_factory=list)` |
| `scan_dirs` | `list[str]` | `field(default_factory=lambda: ['models'])` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict` |  | Serialize to dictionary. |

### Class: `AppManifest`

- Source: `aquilia/manifest.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Production-grade application manifest for complete app configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `version` | `str` |  |
| `description` | `str` | `''` |
| `author` | `str` | `''` |
| `services` | `list[str &#124; ServiceConfig &#124; ComponentRef]` | `field(default_factory=list)` |
| `controllers` | `list[str &#124; ComponentRef]` | `field(default_factory=list)` |
| `socket_controllers` | `list[str &#124; ComponentRef]` | `field(default_factory=list)` |
| `models` | `list[str &#124; ComponentRef]` | `field(default_factory=list)` |
| `serializers` | `list[str &#124; ComponentRef]` | `field(default_factory=list)` |
| `guards` | `list[str &#124; ComponentRef]` | `field(default_factory=list)` |
| `pipes` | `list[str &#124; ComponentRef]` | `field(default_factory=list)` |
| `interceptors` | `list[str &#124; ComponentRef]` | `field(default_factory=list)` |
| `middleware` | `list[str &#124; MiddlewareConfig &#124; ComponentRef]` | `field(default_factory=list)` |
| `route_prefix` | `str` | `'/'` |
| `base_path` | `str &#124; None` | `None` |
| `lifecycle` | `LifecycleConfig &#124; None` | `None` |
| `sessions` | `list[SessionConfig]` | `field(default_factory=list)` |
| `templates` | `TemplateConfig &#124; None` | `None` |
| `database` | `DatabaseConfig &#124; None` | `None` |
| `faults` | `FaultHandlingConfig &#124; None` | `None` |
| `background_tasks` | `BackgroundTaskConfig &#124; None` | `None` |
| `features` | `list[FeatureConfig]` | `field(default_factory=list)` |
| `exports` | `list[str]` | `field(default_factory=list)` |
| `imports` | `list[str]` | `field(default_factory=list)` |
| `depends_on` | `list[str]` | `field(default_factory=list)` |
| `tags` | `list[str]` | `field(default_factory=list)` |
| `config_schema` | `dict[str, Any] &#124; None` | `None` |
| `auto_discover` | `bool` | `True` |
| `discover_patterns` | `list[str]` | `field(default_factory=lambda: ['controllers', 'services', 'middleware', 'guards', 'models', 'tasks'])` |
| `middlewares` | `list[tuple[str, dict]]` | `field(default_factory=list)` |
| `default_fault_domain` | `str &#124; None` | `None` |
| `on_startup` | `Callable &#124; None` | `None` |
| `on_shutdown` | `Callable &#124; None` | `None` |
| `config` | `type &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict` |  | Serialize manifest to dictionary (for fingerprinting and inspection). |
| `fingerprint` | `def fingerprint(self) -> str` |  | Generate stable hash of manifest for reproducible deploys. |

### Class: `MiddlewareDescriptor`

- Source: `aquilia/middleware.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Descriptor for middleware registration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `middleware` | `Middleware` |  |
| `scope` | `str` |  |
| `priority` | `int` |  |
| `name` | `str` |  |

### Class: `MiddlewareStack`

- Source: `aquilia/middleware.py`
- Bases: `object`
- Summary: Manages middleware stack with deterministic ordering.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `add` | `def add(self, middleware: Middleware, scope: str = 'global', priority: int = 50, name: str &#124; None = None)` |  | Add middleware to stack. |
| `build_handler` | `def build_handler(self, final_handler: Handler) -> Handler` |  | Build middleware chain wrapping the final handler. |
| `build_fast_handler` | `def build_fast_handler(self, final_handler: Handler) -> Handler` |  | Build a *minimal* middleware chain for latency-sensitive routes. |

### Class: `RequestIdMiddleware`

- Source: `aquilia/middleware.py`
- Bases: `object`
- Summary: Adds unique request ID to each request.

### Class: `ExceptionMiddleware`

- Source: `aquilia/middleware.py`
- Bases: `object`
- Summary: Catches exceptions and converts them to error responses.

### Class: `LoggingMiddleware`

- Source: `aquilia/middleware.py`
- Bases: `object`
- Summary: Logs request/response with timing.

### Class: `TimeoutMiddleware`

- Source: `aquilia/middleware.py`
- Bases: `object`
- Summary: Enforces request timeout.

### Class: `CORSMiddleware`

- Source: `aquilia/middleware.py`
- Bases: `object`
- Summary: Handles CORS headers.

### Class: `CompressionMiddleware`

- Source: `aquilia/middleware.py`
- Bases: `object`
- Summary: Compresses response bodies.

### Class: `Secret`

- Source: `aquilia/pyconfig.py`
- Bases: `object`
- Summary: A configuration field that holds a sensitive value (password, API key ...).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `reveal` | `def reveal(self) -> str &#124; None` |  | Return the actual secret value (use deliberately). |
| `env_name` | `def env_name(self) -> str &#124; None` | property | Return the environment variable name, if any. |
| `is_required` | `def is_required(self) -> bool` | property | Return whether this secret is required. |

### Class: `Env`

- Source: `aquilia/pyconfig.py`
- Bases: `object`
- Summary: Bind a configuration field to an environment variable.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `name` | `def name(self) -> str` | property | Return the environment variable name. |
| `default` | `def default(self) -> ConfigValue` | property | Return the default value. |
| `is_required` | `def is_required(self) -> bool` | property | Return whether this env var is required. |
| `resolve` | `def resolve(self, *, use_cache: bool = False) -> ConfigValue` |  | Return the resolved value from the environment or default. |
| `invalidate_cache` | `def invalidate_cache(self) -> None` |  | Invalidate the cached resolved value. |
| `disable_auto_load` | `def disable_auto_load(cls) -> None` | classmethod | Disable automatic .env loading. |
| `enable_auto_load` | `def enable_auto_load(cls) -> None` | classmethod | Enable automatic .env loading (default behavior). |

### Class: `AquilaConfig`

- Source: `aquilia/pyconfig.py`
- Bases: `object`
- Summary: Base class for Aquilia Python-native configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `env` | `str` | `'dev'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(cls, *, use_cache: bool = True) -> dict[str, Any]` | classmethod | Serialise this config class into a plain nested dict. |
| `invalidate_cache` | `def invalidate_cache(cls) -> None` | classmethod | Invalidate the cached config dict for this class. |
| `clear_all_caches` | `def clear_all_caches(cls) -> None` | classmethod | Clear all config class caches. |
| `to_loader` | `def to_loader(cls) -> ConfigLoader` | classmethod | Convert this Python config into a :class:`~aquilia.config.ConfigLoader`. |
| `get` | `def get(cls, path: str, default: Any = None) -> Any` | classmethod | Dot-path accessor on the serialised config dict. |
| `for_env` | `def for_env(cls, env_name: str) -> type[AquilaConfig]` | classmethod | Resolve the correct subclass for *env_name* from the subclass tree. |
| `from_env_var` | `def from_env_var(cls, var: str = 'AQ_ENV', default: str = 'dev') -> type[AquilaConfig]` | classmethod | Read ``var`` from the environment and return the matching subclass. |

### Class: `PyConfigLoader`

- Source: `aquilia/pyconfig.py`
- Bases: `object`
- Summary: Load an ``AquilaConfig`` subclass from a Python source file.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `from_file` | `def from_file(cls, path: str &#124; Path, *, env: str &#124; None = None, var: str = 'AQ_ENV', default_env: str = 'dev') -> PyConfigLoader` | classmethod | Import a Python config file and resolve the right subclass. |
| `to_aquilia_loader` | `def to_aquilia_loader(self)` |  | Return a fully populated :class:`~aquilia.config.ConfigLoader`. |
| `config_class` | `def config_class(self) -> type[AquilaConfig]` | property | The resolved :class:`AquilaConfig` subclass. |

### Class: `RequestFault`

- Source: `aquilia/request.py`
- Bases: `Fault`
- Summary: Base class for request-related faults.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `_FD_IO` |
| `severity` |  | `Severity.ERROR` |
| `public` |  | `True` |

### Class: `BadRequest`

- Source: `aquilia/request.py`
- Bases: `RequestFault`
- Summary: Malformed request (400).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'BAD_REQUEST'` |
| `message` |  | `'Bad request'` |

### Class: `PayloadTooLarge`

- Source: `aquilia/request.py`
- Bases: `RequestFault`
- Summary: Request payload exceeds limits (413).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'PAYLOAD_TOO_LARGE'` |
| `message` |  | `'Payload too large'` |

### Class: `UnsupportedMediaType`

- Source: `aquilia/request.py`
- Bases: `RequestFault`
- Summary: Unsupported Content-Type (415).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'UNSUPPORTED_MEDIA_TYPE'` |
| `message` |  | `'Unsupported media type'` |

### Class: `ClientDisconnect`

- Source: `aquilia/request.py`
- Bases: `RequestFault`
- Summary: Client disconnected during request (499).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'CLIENT_DISCONNECT'` |
| `message` |  | `'Client disconnected'` |
| `severity` |  | `Severity.WARN` |

### Class: `InvalidJSON`

- Source: `aquilia/request.py`
- Bases: `RequestFault`
- Summary: Invalid JSON payload (400).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'INVALID_JSON'` |
| `message` |  | `'Invalid JSON'` |

### Class: `InvalidCrous`

- Source: `aquilia/request.py`
- Bases: `RequestFault`
- Summary: Invalid CROUS binary payload (400).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'INVALID_CROUS'` |
| `message` |  | `'Invalid CROUS payload'` |

### Class: `CrousUnavailable`

- Source: `aquilia/request.py`
- Bases: `RequestFault`
- Summary: CROUS library not installed (500-level).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'CROUS_UNAVAILABLE'` |
| `message` |  | `'CROUS serializer not available'` |
| `severity` |  | `Severity.ERROR` |
| `public` |  | `False` |

### Class: `InvalidHeader`

- Source: `aquilia/request.py`
- Bases: `RequestFault`
- Summary: Invalid header format (400).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'INVALID_HEADER'` |
| `message` |  | `'Invalid header'` |

### Class: `MultipartParseError`

- Source: `aquilia/request.py`
- Bases: `RequestFault`
- Summary: Multipart parsing failed (400).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'MULTIPART_PARSE_ERROR'` |
| `message` |  | `'Multipart parsing failed'` |

### Class: `Request`

- Source: `aquilia/request.py`
- Bases: `object`
- Summary: Production-grade request object for Aquilia.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `method` | `def method(self) -> str` | property | HTTP method (GET, POST, etc.). |
| `http_version` | `def http_version(self) -> str` | property | HTTP version (e.g., '1.1', '2'). |
| `path` | `def path(self) -> str` | property | Request path (decoded). |
| `raw_path` | `def raw_path(self) -> bytes` | property | Raw request path (as bytes from ASGI). |
| `query_string` | `def query_string(self) -> str` | property | Raw query string. |
| `client` | `def client(self) -> tuple &#124; None` | property | Client address (host, port). |
| `query_params` | `def query_params(self) -> MultiDict` | property | Get parsed query parameters as MultiDict. |
| `query_param` | `def query_param(self, name: str, default: str &#124; None = None) -> str &#124; None` |  | Get single query parameter. |
| `headers` | `def headers(self) -> Headers` | property | Get parsed headers. |
| `header` | `def header(self, name: str, default: str &#124; None = None) -> str &#124; None` |  | Get single header (case-insensitive). |
| `has_header` | `def has_header(self, name: str) -> bool` |  | Check if header exists. |
| `cookies` | `def cookies(self) -> Mapping[str, str]` | property | Get parsed cookies. |
| `cookie` | `def cookie(self, name: str, default: str &#124; None = None) -> str &#124; None` |  | Get single cookie value. |
| `url` | `def url(self) -> URL` |  | Get full request URL. |
| `base_url` | `def base_url(self) -> URL` |  | Get base URL (scheme + host + root_path). |
| `url_for` | `def url_for(self, route_name: str, **params) -> str` |  | Build URL for named route. |
| `client_ip` | `def client_ip(self) -> str` |  | Get client IP address. |
| `content_type` | `def content_type(self) -> str &#124; None` |  | Get Content-Type header. |
| `content_length` | `def content_length(self) -> int &#124; None` |  | Get Content-Length header as int. |
| `is_json` | `def is_json(self) -> bool` |  | Check if request content type is JSON. |
| `is_crous` | `def is_crous(self) -> bool` |  | Check if request content type is CROUS binary. |
| `accepts` | `def accepts(self, *media_types: str) -> bool` |  | Check if client accepts any of the given media types. |
| `accepts_crous` | `def accepts_crous(self) -> bool` |  | Check if the client accepts CROUS binary responses. |
| `prefers_crous` | `def prefers_crous(self) -> bool` |  | Check if the client prefers CROUS over JSON. |
| `best_response_format` | `def best_response_format(self) -> str` |  | Negotiate the best response format between CROUS and JSON. |
| `range` | `def range(self) -> Range &#124; None` |  | Parse Range header. |
| `if_modified_since` | `def if_modified_since(self) -> Any &#124; None` |  | Parse If-Modified-Since header. |
| `if_none_match` | `def if_none_match(self) -> str &#124; None` |  | Get If-None-Match header (ETag). |
| `auth_scheme` | `def auth_scheme(self) -> str &#124; None` |  | Get authorization scheme (e.g., 'Bearer', 'Basic'). |
| `auth_credentials` | `def auth_credentials(self) -> str &#124; None` |  | Get authorization credentials. |
| `is_disconnected` | `def is_disconnected(self) -> bool` |  | Check if client has disconnected. |
| `iter_bytes` | `async def iter_bytes(self, chunk_size: int &#124; None = None) -> AsyncIterator[bytes]` |  | Stream request body in chunks. |
| `iter_text` | `async def iter_text(self, encoding: str = 'utf-8', chunk_size: int &#124; None = None) -> AsyncIterator[str]` |  | Stream request body as text chunks. |
| `body` | `async def body(self) -> bytes` |  | Read full request body (idempotent). |
| `text` | `async def text(self, encoding: str &#124; None = None) -> str` |  | Read request body as text. |
| `readexactly` | `async def readexactly(self, n: int) -> bytes` |  | Read exactly n bytes from request body. |
| `json` | `async def json(self, model: type[T] &#124; None = None, *, strict: bool = True) -> Any &#124; T` |  | Parse request body as JSON. |
| `crous` | `async def crous(self, model: type[T] &#124; None = None, *, strict: bool = True) -> Any &#124; T` |  | Parse request body as CROUS binary format. |
| `data` | `async def data(self, model: type[T] &#124; None = None, *, strict: bool = True) -> Any &#124; T` |  | Parse request body as JSON **or** CROUS, auto-detected. |
| `form` | `async def form(self) -> FormData` |  | Parse application/x-www-form-urlencoded form data. |
| `multipart` | `async def multipart(self) -> FormData` |  | Parse multipart/form-data. |
| `files` | `async def files(self) -> Mapping[str, list[UploadFile]]` |  | Get uploaded files from multipart request. |
| `save_upload` | `async def save_upload(self, upload: UploadFile, dest: str &#124; PathLike, *, overwrite: bool = False) -> Path` |  | Save uploaded file to destination. |
| `stream_upload_to_store` | `async def stream_upload_to_store(self, upload: UploadFile, store: UploadStore) -> Path` |  | Stream upload to custom storage backend. |
| `identity` | `def identity(self) -> Any &#124; None` | property | Get authenticated identity (set by AuthMiddleware). |
| `authenticated` | `def authenticated(self) -> bool` | property | Check if request is authenticated. |
| `require_identity` | `def require_identity(self) -> Any` |  | Get identity or raise AUTH_REQUIRED fault. |
| `has_role` | `def has_role(self, role: str) -> bool` |  | Check if identity has specific role. |
| `has_scope` | `def has_scope(self, scope: str) -> bool` |  | Check if identity has OAuth scope. |
| `session` | `def session(self) -> Any &#124; None` | property | Get session (set by SessionMiddleware). |
| `session` | `def session(self, value)` | session.setter | Set session in request state. |
| `require_session` | `def require_session(self) -> Any` |  | Get session or raise SESSION_REQUIRED fault. |
| `session_id` | `def session_id(self) -> str &#124; None` | property | Get session ID. |
| `container` | `def container(self) -> AsyncResolvableContainer &#124; SyncResolvableContainer &#124; None` | property | Get request-scoped DI container. |
| `resolve` | `async def resolve(self, service_type: type[T], *, optional: bool = False) -> T &#124; None` |  | Resolve service from DI container. |
| `inject` | `async def inject(self, **services) -> dict[str, Any]` |  | Inject multiple services by name. |
| `flash_messages` | `def flash_messages(self) -> list[dict[str, Any]]` |  | Get and clear flash messages from session. |
| `is_authenticated` | `def is_authenticated(self) -> bool` |  | Check if request is authenticated. |
| `template_context` | `def template_context(self) -> dict[str, Any]` | property | Get template rendering context with auto-injected variables. |
| `add_template_context` | `def add_template_context(self, **kwargs) -> None` |  | Add variables to template context. |
| `emit_effect` | `async def emit_effect(self, effect_name: str, **data) -> None` |  | Emit effect for lifecycle hooks. |
| `get_effect` | `def get_effect(self, name: str) -> Any` |  | Get an acquired effect resource by name. |
| `has_effect` | `def has_effect(self, name: str) -> bool` |  | Check if an effect resource is currently acquired. |
| `effects` | `def effects(self) -> dict[str, Any]` | property | All currently acquired effect resources. |
| `flow_context` | `def flow_context(self) -> Any` | property | Get the FlowContext for this request, if available. |
| `before_response` | `async def before_response(self, callback: Callable[..., Awaitable[None]]) -> None` |  | Register callback to run before response is sent. |
| `after_response` | `async def after_response(self, callback: Callable[..., Awaitable[None]]) -> None` |  | Register callback to run after response is sent. |
| `fault_context` | `def fault_context(self) -> dict[str, Any]` |  | Get context for fault reporting. |
| `report_fault` | `async def report_fault(self, fault: Fault) -> None` |  | Report fault through FaultEngine with request context. |
| `trace_id` | `def trace_id(self) -> str &#124; None` | property | Get trace ID for distributed tracing. |
| `request_id` | `def request_id(self) -> str &#124; None` | property | Get unique request ID. |
| `record_metric` | `def record_metric(self, name: str, value: float, **tags) -> None` |  | Record metric for this request. |
| `cleanup` | `async def cleanup(self) -> None` |  | Clean up temporary resources. |
| `path_params` | `def path_params(self) -> dict[str, Any]` |  | Get path parameters (set by router via state). |

### Class: `BackgroundTask`

- Source: `aquilia/response.py`
- Bases: `Protocol`
- Summary: Protocol for background tasks executed after response is sent.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `run` | `async def run(self) -> None` |  | Execute the background task. |

### Class: `CallableBackgroundTask`

- Source: `aquilia/response.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Simple callable-based background task.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `func` | `Callable[[], Awaitable[None]]` |  |
| `run_on_disconnect` | `bool` | `False` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `run` | `async def run(self) -> None` |  | Method. |

### Class: `ServerSentEvent`

- Source: `aquilia/response.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Server-Sent Event data structure.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `data` | `str` |  |
| `id` | `str &#124; None` | `None` |
| `event` | `str &#124; None` | `None` |
| `retry` | `int &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `encode` | `def encode(self) -> bytes` |  | Encode SSE event according to spec. |

### Class: `MediaChunk`

- Source: `aquilia/response.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Type-safe media chunk container for streaming payloads.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `data` | `bytes &#124; str` |  |
| `content_type` | `str &#124; None` | `None` |
| `is_final` | `bool` | `False` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `encode` | `def encode(self, encoding: str = 'utf-8') -> bytes` |  | Method. |

### Class: `HLSSegment`

- Source: `aquilia/response.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Single media segment entry in an HLS media playlist.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `uri` | `str` |  |
| `duration` | `float` |  |
| `title` | `str &#124; None` | `None` |
| `byte_range` | `str &#124; None` | `None` |
| `discontinuity` | `bool` | `False` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `render` | `def render(self) -> list[str]` |  | Method. |

### Class: `HLSVariant`

- Source: `aquilia/response.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Variant stream descriptor for an HLS master playlist.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `uri` | `str` |  |
| `bandwidth` | `int` |  |
| `resolution` | `str &#124; None` | `None` |
| `codecs` | `str &#124; None` | `None` |
| `frame_rate` | `float &#124; None` | `None` |
| `audio` | `str &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `render` | `def render(self) -> list[str]` |  | Method. |

### Class: `CookieSigner`

- Source: `aquilia/response.py`
- Bases: `object`
- Summary: Cookie signer with HMAC-based signing and key rotation support.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `sign` | `def sign(self, value: str) -> str` |  | Sign a cookie value. |
| `unsign` | `def unsign(self, signed_value: str) -> str &#124; None` |  | Verify and unsign a cookie value. |

### Class: `ResponseStreamError`

- Source: `aquilia/response.py`
- Bases: `Fault`
- Summary: Error during response streaming.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'RESPONSE_STREAM_ERROR'` |
| `domain` |  | `FaultDomain.RESPONSE` |
| `severity` |  | `Severity.ERROR` |

### Class: `TemplateRenderError`

- Source: `aquilia/response.py`
- Bases: `Fault`
- Summary: Template rendering error during response.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'TEMPLATE_RENDER_ERROR'` |
| `domain` |  | `FaultDomain.RESPONSE` |
| `severity` |  | `Severity.ERROR` |
| `message` |  | `'Template rendering failed'` |

### Class: `InvalidHeaderError`

- Source: `aquilia/response.py`
- Bases: `Fault`
- Summary: Invalid header name or value (injection attempt).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'INVALID_HEADER'` |
| `domain` |  | `FaultDomain.SECURITY` |
| `severity` |  | `Severity.WARN` |

### Class: `ClientDisconnectError`

- Source: `aquilia/response.py`
- Bases: `Fault`
- Summary: Client disconnected during response send.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'CLIENT_DISCONNECT'` |
| `domain` |  | `FaultDomain.IO` |
| `severity` |  | `Severity.INFO` |

### Class: `RangeNotSatisfiableError`

- Source: `aquilia/response.py`
- Bases: `Fault`
- Summary: Invalid Range header (416 response).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'RANGE_NOT_SATISFIABLE'` |
| `domain` |  | `FaultDomain.RESPONSE` |
| `severity` |  | `Severity.WARN` |

### Class: `HLSManifestError`

- Source: `aquilia/response.py`
- Bases: `Fault`
- Summary: Invalid HLS manifest payload or helper usage.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'HLS_MANIFEST_ERROR'` |
| `domain` |  | `FaultDomain.RESPONSE` |
| `severity` |  | `Severity.ERROR` |

### Class: `Response`

- Source: `aquilia/response.py`
- Bases: `object`
- Summary: Production-grade HTTP response with ASGI 3 streaming support.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `headers` | `def headers(self) -> dict[str, str &#124; list[str]]` | property | Get response headers. |
| `json` | `def json(cls, obj: Any, status: int = 200, *, encoder: Callable[[Any], str] &#124; None = None, headers: Mapping[str, str] &#124; None = None, **kwargs) -> Response` | classmethod | Create JSON response. |
| `html` | `def html(cls, content: str, status: int = 200, **kwargs) -> Response` | classmethod | Create HTML response. |
| `text` | `def text(cls, content: str, status: int = 200, **kwargs) -> Response` | classmethod | Create plain text response. |
| `redirect` | `def redirect(cls, url: str, status: int = 307, *, headers: dict[str, str] &#124; None = None) -> Response` | classmethod | Create redirect response. |
| `stream` | `def stream(cls, iterator: AsyncIterator[bytes] &#124; Iterator[bytes], status: int = 200, media_type: str = 'application/octet-stream', **kwargs) -> Response` | classmethod | Create streaming response. |
| `media_stream` | `def media_stream(cls, chunks: AsyncIterator[MediaChunk] &#124; Iterator[MediaChunk], status: int = 200, media_type: str = 'application/octet-stream', **kwargs) -> Response` | classmethod | Create a type-safe media chunk streaming response. |
| `sse` | `def sse(cls, event_iter: AsyncIterator[ServerSentEvent], status: int = 200, **kwargs) -> Response` | classmethod | Create Server-Sent Events (SSE) response. |
| `crous` | `def crous(cls, obj: Any, status: int = 200, *, headers: Mapping[str, str] &#124; None = None, compression: str &#124; None = None, dedup: bool = True, **kwargs) -> Response` | classmethod | Create a CROUS binary response. |
| `negotiated` | `def negotiated(cls, obj: Any, request: Any, status: int = 200, *, headers: Mapping[str, str] &#124; None = None, **kwargs) -> Response` | classmethod | Create a response with automatic content negotiation. |
| `file` | `def file(cls, path: PathLike, *, filename: str &#124; None = None, media_type: str &#124; None = None, status: int = 200, use_sendfile: bool = True, chunk_size: int = 64 * 1024, **kwargs) -> Response` | classmethod | Create file download response. |
| `hls_playlist` | `def hls_playlist(cls, segments: Sequence[HLSSegment], *, target_duration: int &#124; None = None, media_sequence: int = 0, version: int = 3, endlist: bool = True, status: int = 200, headers: Mapping[str, str] &#124; None = None) -> Response` | classmethod | Create an HLS media playlist (.m3u8) response. |
| `hls_master_playlist` | `def hls_master_playlist(cls, variants: Sequence[HLSVariant], *, version: int = 3, status: int = 200, headers: Mapping[str, str] &#124; None = None) -> Response` | classmethod | Create an HLS master playlist response. |
| `hls_segment` | `def hls_segment(cls, path: PathLike, *, status: int = 200, chunk_size: int = 64 * 1024, headers: Mapping[str, str] &#124; None = None) -> Response` | classmethod | Create an HLS segment file response with media-aware defaults. |
| `render` | `async def render(cls, template_name: str, context: Mapping[str, Any] &#124; None = None, *, request: Any &#124; None = None, request_ctx: Any &#124; None = None, engine: Any &#124; None = None, status: int = 200, headers: Mapping &#124; None = None, **response_kwargs) -> Response` | classmethod | Render template with automatic context injection. |
| `commit_session` | `async def commit_session(self, request: Any) -> None` |  | Commit session changes after response. |
| `execute_before_send_hooks` | `async def execute_before_send_hooks(self, request: Any) -> None` |  | Execute before-response callbacks registered on request. |
| `execute_after_send_hooks` | `async def execute_after_send_hooks(self, request: Any) -> None` |  | Execute after-response callbacks registered on request. |
| `record_response_metrics` | `def record_response_metrics(self, request: Any, duration_ms: float) -> None` |  | Record response metrics. |
| `from_fault` | `def from_fault(cls, fault: Fault, *, include_details: bool = False, request: Any &#124; None = None) -> Response` | classmethod | Create Response from Fault with appropriate status code. |
| `set_cookie` | `def set_cookie(self, name: str, value: str, *, max_age: int &#124; None = None, expires: datetime &#124; None = None, path: str = '/', domain: str &#124; None = None, secure: bool = True, httponly: bool = True, samesite: str &#124; None = 'Lax', same_site_policy: str &#124; None = None, signed: bool = False, signer: CookieSigner &#124; None = None) -> None` |  | Set a cookie. |
| `delete_cookie` | `def delete_cookie(self, name: str, path: str = '/', domain: str &#124; None = None) -> None` |  | Delete a cookie by setting Max-Age=0. |
| `set_header` | `def set_header(self, name: str, value: str) -> None` |  | Set header (replaces existing). |
| `add_header` | `def add_header(self, name: str, value: str) -> None` |  | Add header (supports multiple values). |
| `unset_header` | `def unset_header(self, name: str) -> None` |  | Remove header. |
| `set_etag` | `def set_etag(self, etag: str, weak: bool = False) -> None` |  | Set ETag header. |
| `set_last_modified` | `def set_last_modified(self, dt: datetime) -> None` |  | Set Last-Modified header. |
| `cache_control` | `def cache_control(self, **directives) -> None` |  | Set Cache-Control header. |
| `secure_headers` | `def secure_headers(self, *, hsts: bool = True, hsts_max_age: int = 31536000, csp: str &#124; None = None, frame_options: str = 'DENY', content_type_options: bool = True, xss_protection: bool = True, referrer_policy: str = 'strict-origin-when-cross-origin') -> None` |  | Set recommended security headers. |
| `send_asgi` | `async def send_asgi(self, send: Callable[[dict], Awaitable[None]], request: Any &#124; None = None) -> None` |  | Send response via ASGI. |

### Class: `RuntimePhase`

- Source: `aquilia/runtime.py`
- Bases: `str, Enum`
- Summary: Lifecycle phase of an :class:`AquiliaRuntime` instance.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `CREATED` |  | `'created'` |
| `CONFIGURING` |  | `'configuring'` |
| `DISCOVERING` |  | `'discovering'` |
| `BOOTSTRAPPING` |  | `'bootstrapping'` |
| `READY` |  | `'ready'` |
| `RUNNING` |  | `'running'` |
| `SHUTTING_DOWN` |  | `'shutting_down'` |
| `STOPPED` |  | `'stopped'` |
| `FAILED` |  | `'failed'` |

### Class: `RuntimeConfig`

- Source: `aquilia/runtime.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Immutable configuration for an :class:`AquiliaRuntime` instance.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `workspace_root` | `Path` |  |
| `mode` | `Literal['dev', 'test', 'prod']` | `'prod'` |
| `debug` | `bool &#124; None` | `None` |
| `config_overrides` | `dict[str, Any]` | `field(default_factory=dict)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_dev` | `def is_dev(self) -> bool` | property | Whether the runtime is in development mode. |
| `workspace_file` | `def workspace_file(self) -> Path` | property | Path to ``workspace.py``. |
| `modules_dir` | `def modules_dir(self) -> Path` | property | Path to the ``modules/`` directory. |

### Class: `AquiliaRuntime`

- Source: `aquilia/runtime.py`
- Bases: `object`
- Summary: Structured ASGI bootstrap lifecycle manager.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `phase` | `def phase(self) -> RuntimePhase` | property | Current lifecycle phase. |
| `app` | `def app(self) -> ASGIApplication` | property | The ASGI application callable. |
| `server` | `def server(self) -> Any` | property | The :class:`~aquilia.server.AquiliaServer` instance. |
| `workspace_name` | `def workspace_name(self) -> str` | property | Workspace name extracted from ``workspace.py``. |
| `module_names` | `def module_names(self) -> list[str]` | property | List of discovered module names. |
| `configure` | `def configure(self) -> AquiliaRuntime` |  | Bootstrap paths, environment variables, logging, and config. |
| `discover` | `def discover(self) -> AquiliaRuntime` |  | Discover workspace name, module manifests, and workspace module configs. |
| `bootstrap` | `def bootstrap(self) -> AquiliaRuntime` |  | Construct the :class:`~aquilia.server.AquiliaServer`. |
| `from_workspace` | `def from_workspace(cls, workspace_root: Path &#124; str &#124; None = None, mode: str &#124; None = None, *, config_overrides: dict[str, Any] &#124; None = None) -> AquiliaRuntime` | classmethod | Create a fully bootstrapped runtime from workspace configuration. |
| `create_app` | `def create_app(cls, workspace_root: Path &#124; str &#124; None = None, mode: str &#124; None = None, *, config_overrides: dict[str, Any] &#124; None = None) -> ASGIApplication` | classmethod | One-liner factory returning just the ASGI callable. |

### Class: `AquiliaServer`

- Source: `aquilia/server.py`
- Bases: `object`
- Summary: Main Aquilia server that orchestrates all components with lifecycle management.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `startup` | `async def startup(self)` |  | Execute startup sequence with Aquilary lifecycle management. |
| `shutdown` | `async def shutdown(self)` |  | Execute shutdown sequence with Aquilary lifecycle management. |
| `get_health` | `def get_health(self) -> dict` |  | Get current server health status (v2). |
| `graceful_shutdown` | `async def graceful_shutdown(self, timeout: float = 30.0)` |  | Graceful shutdown sequence (v2). |
| `run` | `def run(self, host: str &#124; None = None, port: int &#124; None = None, reload: bool &#124; None = None, log_level: str = 'info', graceful_timeout: float = 30.0)` |  | Run the development server with graceful shutdown support. |
| `get_asgi_app` | `def get_asgi_app(self)` |  | Get the ASGI application for external servers. |
| `lifespan` | `def lifespan(self)` |  | ASGI lifespan context manager. |

### Class: `SignerBackend`

- Source: `aquilia/signing.py`
- Bases: `ABC`
- Summary: Abstract backend that produces and verifies raw byte signatures.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `sign` | `def sign(self, message: bytes) -> bytes` | abstractmethod | Return the signature for *message*. |
| `verify` | `def verify(self, message: bytes, signature: bytes) -> bool` | abstractmethod | Return ``True`` if *signature* is valid for *message*. |
| `algorithm` | `def algorithm(self) -> str` | property, abstractmethod | The algorithm name (e.g. ``"HS256"``). |

### Class: `HmacSignerBackend`

- Source: `aquilia/signing.py`
- Bases: `SignerBackend`
- Summary: Default signing backend - HMAC with a configurable digest.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `algorithm` | `def algorithm(self) -> str` | property | Method. |
| `sign` | `def sign(self, message: bytes) -> bytes` |  | Return HMAC-{digest} signature of *message*. |
| `verify` | `def verify(self, message: bytes, signature: bytes) -> bool` |  | Return ``True`` iff *signature* equals HMAC of *message* (constant-time). |

### Class: `AsymmetricSignerBackend`

- Source: `aquilia/signing.py`
- Bases: `SignerBackend`
- Summary: Asymmetric signing backend using the ``cryptography`` package.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `algorithm` | `def algorithm(self) -> str` | property | Method. |
| `sign` | `def sign(self, message: bytes) -> bytes` |  | Method. |
| `verify` | `def verify(self, message: bytes, signature: bytes) -> bool` |  | Method. |

### Class: `Signer`

- Source: `aquilia/signing.py`
- Bases: `object`
- Summary: Simple HMAC-based data signer.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `sign` | `def sign(self, value: str, **kwargs: Any) -> str` |  | Sign *value* and return ``"<value><sep><b64sig>"``. |
| `unsign` | `def unsign(self, signed_value: str, **kwargs: Any) -> str` |  | Verify and return the original value from a signed token. |
| `sign_bytes` | `def sign_bytes(self, data: bytes) -> bytes` |  | Sign raw *data* and return ``data + sep_byte + b64sig`` as bytes. |
| `unsign_bytes` | `def unsign_bytes(self, signed_data: bytes) -> bytes` |  | Verify and return the original bytes from signed byte data. |
| `sign_object` | `def sign_object(self, obj: Any, **kwargs: Any) -> str` |  | Serialise *obj* to JSON, sign, and return a URL-safe token. |
| `unsign_object` | `def unsign_object(self, token: str, **kwargs: Any) -> Any` |  | Verify *token* and deserialise the embedded JSON payload. |

### Class: `TimestampSigner`

- Source: `aquilia/signing.py`
- Bases: `Signer`
- Summary: Signer that embeds a UTC timestamp in the signed value.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `sign` | `def sign(self, value: str, *, timestamp: datetime &#124; None = None, **kwargs: Any) -> str` |  | Sign *value* with an embedded UTC timestamp. |
| `unsign` | `def unsign(self, signed_value: str, max_age: float &#124; int &#124; timedelta &#124; None = None, **kwargs: Any) -> str` |  | Verify signature, optionally enforce ``max_age``, and return value. |
| `unsign_with_timestamp` | `def unsign_with_timestamp(self, signed_value: str, max_age: float &#124; int &#124; timedelta &#124; None = None) -> tuple[str, datetime]` |  | Verify signature and return ``(value, timestamp)`` tuple. |
| `sign_object` | `def sign_object(self, obj: Any, *, timestamp: datetime &#124; None = None, **kwargs: Any) -> str` |  | Sign a JSON-serialisable object with an embedded timestamp. |
| `unsign_object` | `def unsign_object(self, token: str, max_age: float &#124; int &#124; timedelta &#124; None = None, **kwargs: Any) -> Any` |  | Verify and deserialise a JSON object from a timestamped token. |

### Class: `RotatingSigner`

- Source: `aquilia/signing.py`
- Bases: `object`
- Summary: A signer that supports transparent key rotation.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `current_signer` | `def current_signer(self) -> Signer` | property | The active signer (used for new :meth:`sign` calls). |
| `sign` | `def sign(self, value: str, **kwargs: Any) -> str` |  | Sign *value* with the current (first) secret. |
| `unsign` | `def unsign(self, signed_value: str, max_age: float &#124; int &#124; timedelta &#124; None = None, **kwargs: Any) -> str` |  | Try each secret in order; return the value verified by the first match. |
| `sign_object` | `def sign_object(self, obj: Any, **kwargs: Any) -> str` |  | Sign a JSON-serialisable object with the current secret. |
| `unsign_object` | `def unsign_object(self, token: str, max_age: float &#124; int &#124; timedelta &#124; None = None) -> Any` |  | Verify and deserialise using each secret in order. |

### Class: `SessionSigner`

- Source: `aquilia/signing.py`
- Bases: `TimestampSigner`
- Summary: Timestamped signer for Aquilia session cookies.

### Class: `CSRFSigner`

- Source: `aquilia/signing.py`
- Bases: `Signer`
- Summary: Signer for CSRF tokens.

### Class: `ActivationLinkSigner`

- Source: `aquilia/signing.py`
- Bases: `TimestampSigner`
- Summary: Timestamped signer for one-time activation / password-reset URLs.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `unsign` | `def unsign(self, signed_value: str, max_age: float &#124; int &#124; timedelta &#124; None = None, **kwargs: Any) -> str` |  | Unsign with a default 24-hour max_age unless overridden. |

### Class: `CacheKeySigner`

- Source: `aquilia/signing.py`
- Bases: `Signer`
- Summary: Signer for cache key integrity verification.

### Class: `CookieSigner`

- Source: `aquilia/signing.py`
- Bases: `TimestampSigner`
- Summary: Timestamped signer for signed HTTP cookies (non-session).

### Class: `APIKeySigner`

- Source: `aquilia/signing.py`
- Bases: `TimestampSigner`
- Summary: Timestamped signer for short-lived API access keys / signed URLs.

### Class: `SigningConfig`

- Source: `aquilia/signing.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Runtime signing configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `secret` | `str` | `''` |
| `fallback_secrets` | `list[str]` | `field(default_factory=list)` |
| `algorithm` | `str` | `'HS256'` |
| `salt` | `str` | `'aquilia.signing'` |
| `session_salt` | `str` | `'aquilia.sessions'` |
| `csrf_salt` | `str` | `'aquilia.csrf'` |
| `activation_salt` | `str` | `'aquilia.activation'` |
| `cache_salt` | `str` | `'aquilia.cache'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `apply` | `def apply(self) -> None` |  | Apply this config to the global signing registry. |
| `make_session_signer` | `def make_session_signer(self) -> SessionSigner` |  | Method. |
| `make_csrf_signer` | `def make_csrf_signer(self) -> CSRFSigner` |  | Method. |
| `make_activation_signer` | `def make_activation_signer(self) -> ActivationLinkSigner` |  | Method. |
| `make_cache_signer` | `def make_cache_signer(self) -> CacheKeySigner` |  | Method. |
| `make_cookie_signer` | `def make_cookie_signer(self) -> CookieSigner` |  | Method. |
| `make_api_key_signer` | `def make_api_key_signer(self) -> APIKeySigner` |  | Method. |

## Functions

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `parse_date_header` | `aquilia/_datastructures.py` | `def parse_date_header(date_str: str &#124; None) -> datetime &#124; None` | Parse HTTP date header. |
| `parse_authorization_header` | `aquilia/_datastructures.py` | `def parse_authorization_header(auth_header: str &#124; None) -> tuple[str, str] &#124; None` | Parse Authorization header. |
| `create_upload_file_from_bytes` | `aquilia/_uploads.py` | `def create_upload_file_from_bytes(filename: str, content: bytes, content_type: str = 'application/octet-stream') -> UploadFile` | Create an UploadFile from bytes (in-memory). |
| `create_upload_file_from_path` | `aquilia/_uploads.py` | `def create_upload_file_from_path(filename: str, file_path: Path, content_type: str = 'application/octet-stream') -> UploadFile` | Create an UploadFile from a disk path. |
| `find_dotenv` | `aquilia/dotenv.py` | `def find_dotenv(filename: str = '.env', raise_error: bool = False, usecwd: bool = False) -> Path &#124; None` | Search for a .env file. |
| `load_dotenv` | `aquilia/dotenv.py` | `def load_dotenv(dotenv_path: str &#124; Path &#124; None = None, *, override: bool = False, interpolate: bool = True, encoding: str = 'utf-8') -> bool` | Load a .env file into os.environ. |
| `dotenv_values` | `aquilia/dotenv.py` | `def dotenv_values(dotenv_path: str &#124; Path &#124; None = None, *, interpolate: bool = True, encoding: str = 'utf-8') -> dict[str, str]` | Parse a .env file and return values WITHOUT loading into os.environ. |
| `ensure_dotenv_loaded` | `aquilia/dotenv.py` | `def ensure_dotenv_loaded(path: str &#124; Path &#124; None = None, *, auto_load: bool &#124; None = None) -> None` | Ensure dotenv is loaded (idempotent). |
| `is_dotenv_loaded` | `aquilia/dotenv.py` | `def is_dotenv_loaded() -> bool` | Check if dotenv has been loaded. |
| `reset_dotenv_state` | `aquilia/dotenv.py` | `def reset_dotenv_state() -> None` | Reset dotenv loaded state. |
| `get_engine_metrics` | `aquilia/engine.py` | `def get_engine_metrics() -> EngineMetrics` | Return the process-level engine metrics singleton. |
| `create_app` | `aquilia/entrypoint.py` | `def create_app(workspace_root: Path &#124; None = None, mode: str &#124; None = None) -> Any` | Create the ASGI application from workspace configuration. |
| `requires` | `aquilia/flow.py` | `def requires(*effect_names: str) -> Callable` | Decorator declaring effect dependencies on a handler or flow node. |
| `get_required_effects` | `aquilia/flow.py` | `def get_required_effects(func: Callable) -> list[str]` | Extract declared effect requirements from a callable. |
| `pipeline` | `aquilia/flow.py` | `def pipeline(name: str = 'pipeline', *, timeout: float &#124; None = None) -> FlowPipeline` | Create a new FlowPipeline. |
| `guard` | `aquilia/flow.py` | `def guard(fn: Callable, *, name: str &#124; None = None, priority: int = PRIORITY_AUTH, effects: list[str] &#124; None = None) -> FlowNode` | Create a guard FlowNode. |
| `transform` | `aquilia/flow.py` | `def transform(fn: Callable, *, name: str &#124; None = None, priority: int = PRIORITY_TRANSFORM, effects: list[str] &#124; None = None) -> FlowNode` | Create a transform FlowNode. |
| `handler` | `aquilia/flow.py` | `def handler(fn: Callable, *, name: str &#124; None = None, priority: int = PRIORITY_DEFAULT, effects: list[str] &#124; None = None) -> FlowNode` | Create a handler FlowNode. |
| `hook` | `aquilia/flow.py` | `def hook(fn: Callable, *, name: str &#124; None = None, priority: int = PRIORITY_LOG, effects: list[str] &#124; None = None) -> FlowNode` | Create a hook FlowNode. |
| `from_pipeline_list` | `aquilia/flow.py` | `def from_pipeline_list(nodes: Sequence[Any], *, name: str = 'controller_pipeline') -> FlowPipeline` | Convert a controller-style pipeline list to a FlowPipeline. |
| `create_lifecycle_coordinator` | `aquilia/lifecycle.py` | `def create_lifecycle_coordinator(runtime: Any, config: Any = None) -> LifecycleCoordinator` | Factory function to create lifecycle coordinator. |
| `reset_dotenv_state` | `aquilia/pyconfig.py` | `def reset_dotenv_state() -> None` | Reset the dotenv loading state. |
| `section` | `aquilia/pyconfig.py` | `def section(cls: type) -> type` | Mark a nested class as a config *section*. |
| `has_crous` | `aquilia/response.py` | `def has_crous() -> bool` | Return ``True`` if the ``crous`` library is importable. |
| `Ok` | `aquilia/response.py` | `def Ok(content: Any = None, **kwargs) -> Response` | 200 OK response. |
| `Created` | `aquilia/response.py` | `def Created(content: Any = None, location: str &#124; None = None, **kwargs) -> Response` | 201 Created response. |
| `NoContent` | `aquilia/response.py` | `def NoContent() -> Response` | 204 No Content response. |
| `BadRequest` | `aquilia/response.py` | `def BadRequest(message: str = 'Bad Request', **kwargs) -> Response` | 400 Bad Request response. |
| `Unauthorized` | `aquilia/response.py` | `def Unauthorized(message: str = 'Unauthorized', **kwargs) -> Response` | 401 Unauthorized response. |
| `Forbidden` | `aquilia/response.py` | `def Forbidden(message: str = 'Forbidden', **kwargs) -> Response` | 403 Forbidden response. |
| `NotFound` | `aquilia/response.py` | `def NotFound(message: str = 'Not Found', **kwargs) -> Response` | 404 Not Found response. |
| `InternalError` | `aquilia/response.py` | `def InternalError(message: str = 'Internal Server Error', **kwargs) -> Response` | 500 Internal Server Error response. |
| `generate_etag` | `aquilia/response.py` | `def generate_etag(content: bytes, weak: bool = False) -> str` | Generate ETag from content. |
| `generate_etag_from_file` | `aquilia/response.py` | `def generate_etag_from_file(path: PathLike, weak: bool = True) -> str` | Generate ETag from file metadata. |
| `check_not_modified` | `aquilia/response.py` | `def check_not_modified(request: Any, etag: str &#124; None = None, last_modified: datetime &#124; None = None) -> bool` | Check if response should be 304 Not Modified. |
| `not_modified_response` | `aquilia/response.py` | `def not_modified_response(etag: str &#124; None = None) -> Response` | Create 304 Not Modified response. |
| `requires_crous` | `aquilia/response.py` | `def requires_crous(func: Callable) -> Callable` | Mark a handler as preferring CROUS binary responses. |
| `b64_encode` | `aquilia/signing.py` | `def b64_encode(data: bytes) -> str` | URL-safe, no-padding Base64 encode. |
| `b64_decode` | `aquilia/signing.py` | `def b64_decode(data: str &#124; bytes) -> bytes` | URL-safe, no-padding Base64 decode. |
| `constant_time_compare` | `aquilia/signing.py` | `def constant_time_compare(a: bytes &#124; str, b: bytes &#124; str) -> bool` | Compare two values in constant time to prevent timing attacks. |
| `derive_key` | `aquilia/signing.py` | `def derive_key(secret: str &#124; bytes, salt: str, algorithm: str = 'HS256') -> bytes` | Derive a signing sub-key from *secret* and *salt* using HKDF-lite. |
| `dumps` | `aquilia/signing.py` | `def dumps(obj: Any, *, secret: str &#124; bytes &#124; None = None, salt: str = 'aquilia.signing.dumps', algorithm: str = 'HS256', compress: bool = False, max_age: float &#124; int &#124; timedelta &#124; None = None, timestamp: bool = True) -> str` | Serialise *obj* to a signed URL-safe string. |
| `loads` | `aquilia/signing.py` | `def loads(token: str, *, secret: str &#124; bytes &#124; None = None, salt: str = 'aquilia.signing.dumps', algorithm: str = 'HS256', max_age: float &#124; int &#124; timedelta &#124; None = None) -> Any` | Verify and deserialise a token produced by :func:`dumps`. |
| `configure` | `aquilia/signing.py` | `def configure(secret: str &#124; bytes, *, fallback_secrets: Sequence[str &#124; bytes] &#124; None = None, algorithm: str = 'HS256', salt: str = 'aquilia.signing') -> None` | Configure the global signing secret used by module-level helpers. |
| `make_signer` | `aquilia/signing.py` | `def make_signer(secret: str &#124; bytes &#124; None = None, *, salt: str = 'aquilia.signing', algorithm: str &#124; None = None) -> Signer` | Create a :class:`Signer` with the given (or global) settings. |
| `make_timestamp_signer` | `aquilia/signing.py` | `def make_timestamp_signer(secret: str &#124; bytes &#124; None = None, *, salt: str = 'aquilia.signing.ts', algorithm: str &#124; None = None) -> TimestampSigner` | Create a :class:`TimestampSigner` with the given (or global) settings. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `VERSION` | `aquilia/_version.py` | `tuple[int, int, int]` |
| `WORKSPACE_VERSION` | `aquilia/_version.py` | `str` |
| `_VAR_NAME_PATTERN` | `aquilia/dotenv.py` | `Final` |
| `_INTERPOLATE_BRACES` | `aquilia/dotenv.py` | `Final` |
| `_INTERPOLATE_SIMPLE` | `aquilia/dotenv.py` | `Final` |
| `T` | `aquilia/effects.py` | `TypeVar('T')` |
| `T` | `aquilia/flow.py` | `TypeVar('T')` |
| `R` | `aquilia/flow.py` | `TypeVar('R')` |
| `E` | `aquilia/flow.py` | `TypeVar('E')` |
| `PRIORITY_CRITICAL` | `aquilia/flow.py` | `10` |
| `PRIORITY_AUTH` | `aquilia/flow.py` | `20` |
| `PRIORITY_VALIDATE` | `aquilia/flow.py` | `30` |
| `PRIORITY_TRANSFORM` | `aquilia/flow.py` | `40` |
| `PRIORITY_DEFAULT` | `aquilia/flow.py` | `50` |
| `PRIORITY_ENRICH` | `aquilia/flow.py` | `60` |
| `PRIORITY_LOG` | `aquilia/flow.py` | `70` |
| `PRIORITY_CLEANUP` | `aquilia/flow.py` | `80` |
| `_FD_SECURITY` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.SECURITY)` |
| `_FD_IO` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.IO)` |
| `_FD_ROUTING` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.ROUTING)` |
| `_FD_EFFECT` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.EFFECT)` |
| `_FD_MODEL` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.MODEL)` |
| `_FD_CACHE` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.CACHE)` |
| `_FD_CONFIG` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.CONFIG)` |
| `_FD_REGISTRY` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.REGISTRY)` |
| `_FD_DI` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.DI)` |
| `_FD_FLOW` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.FLOW)` |
| `_FD_SYSTEM` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.SYSTEM)` |
| `_FD_STORAGE` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.STORAGE)` |
| `_FD_TASKS` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.TASKS)` |
| `_FD_TEMPLATE` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.TEMPLATE)` |
| `_FD_HTTP` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.HTTP)` |
| `_FAST_SKIP_NAMES` | `aquilia/middleware.py` | `frozenset({'LoggingMiddleware', 'TimeoutMiddleware'})` |
| `_FALLBACK_500_HTML` | `aquilia/middleware.py` | `'<!DOCTYPE html><html><head><meta charset="utf-8"><title>500 Internal Server Error</title><style>body{font-family:system-ui,sans-serif;background:#000;color:#ed` |
| `T` | `aquilia/pyconfig.py` | `TypeVar('T')` |
| `CROUS_MEDIA_TYPE` | `aquilia/request.py` | `'application/x-crous'` |
| `CROUS_MEDIA_TYPES` | `aquilia/request.py` | `frozenset({'application/x-crous', 'application/crous', 'application/vnd.crous'})` |
| `CROUS_MAGIC` | `aquilia/request.py` | `b'CROUSv1'` |
| `T` | `aquilia/request.py` | `TypeVar('T')` |
| `_FD_IO` | `aquilia/request.py` | `cast(FaultDomain, FaultDomain.IO)` |
| `_FD_SECURITY` | `aquilia/request.py` | `cast(FaultDomain, FaultDomain.SECURITY)` |
| `CROUS_MEDIA_TYPE` | `aquilia/response.py` | `'application/x-crous'` |
| `CROUS_MAGIC` | `aquilia/response.py` | `b'CROUSv1'` |
| `_PHASE_ORDER` | `aquilia/runtime.py` | `dict[RuntimePhase, int]` |
| `_HMAC_ALGORITHMS` | `aquilia/signing.py` | `frozenset[str]` |
| `_ASYMMETRIC_ALGORITHMS` | `aquilia/signing.py` | `frozenset[str]` |
| `_ALL_ALGORITHMS` | `aquilia/signing.py` | `frozenset[str]` |
| `_HMAC_DIGEST_MAP` | `aquilia/signing.py` | `dict[str, str]` |
| `_SEP` | `aquilia/signing.py` | `':'` |
| `_MIN_KEY_BYTES` | `aquilia/signing.py` | `32` |
| `_EPOCH` | `aquilia/signing.py` | `int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp() * 1000000)` |
| `_TS_FORMAT_V1` | `aquilia/signing.py` | `1` |
| `_GLOBAL_SECRETS` | `aquilia/signing.py` | `list[str &#124; bytes]` |
| `_GLOBAL_ALGORITHM` | `aquilia/signing.py` | `str` |
| `_GLOBAL_SALT` | `aquilia/signing.py` | `str` |

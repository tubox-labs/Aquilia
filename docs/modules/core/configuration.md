# Core Runtime Configuration

## Configuration Entry Points

The implementation exposes the following configuration-like classes, policies, integrations, or dataclasses.

| Type | Source | Fields | Purpose |
| --- | --- | --- | --- |
| `Headers` | `aquilia/_datastructures.py` | raw: list[tuple[bytes, bytes]] | Case-insensitive header access with raw preservation. |
| `URL` | `aquilia/_datastructures.py` | scheme: str, host: str, port: int &#124; None, path: str, query: str, fragment: str, username: str &#124; None, password: str &#124; None | Parsed URL representation. |
| `ParsedContentType` | `aquilia/_datastructures.py` | media_type: str, params: dict[str, str] | Parsed Content-Type header. |
| `Range` | `aquilia/_datastructures.py` | unit: str, ranges: list[tuple[int &#124; None, int &#124; None]] | Parsed HTTP Range header. |
| `UploadFile` | `aquilia/_uploads.py` | filename: str, content_type: str, size: int &#124; None | Uploaded file representation. |
| `FormData` | `aquilia/_uploads.py` | fields: MultiDict, files: dict[str, list[UploadFile]] | Parsed form data containing both fields and files. |
| `Config` | `aquilia/config.py` | See class attributes and constructor methods. | Base class for typed configuration classes. |
| `RuntimeConfig` | `aquilia/config_builders.py` | mode: str, host: str, port: int, reload: bool, workers: int | Runtime configuration. |
| `ModuleConfig` | `aquilia/config_builders.py` | name: str, version: str, description: str, fault_domain: str &#124; None, route_prefix: str &#124; None, depends_on: list[str], tags: list[str], imports: list[str], exports: list[str], on_startup: str &#124; None, on_shutdown: str &#124; None, database: dict[str, Any] &#124; None, ... | Module configuration -- workspace-level orchestration metadata. |
| `AuthConfig` | `aquilia/config_builders.py` | enabled: bool, store_type: str, secret_key: str &#124; None, algorithm: str, issuer: str, audience: str, access_token_ttl_minutes: int, refresh_token_ttl_days: int, require_auth_by_default: bool | Authentication configuration. |
| `Integration` | `aquilia/config_builders.py` | See class attributes and constructor methods. | Integration configuration builders. |
| `FlowNode` | `aquilia/flow.py` | type: FlowNodeType, callable: Callable[..., Any], name: str, priority: int, effects: list[str], condition: Callable[[FlowContext], bool] &#124; None, timeout: float &#124; None | A typed unit in a flow pipeline. |
| `FlowResult` | `aquilia/flow.py` | status: FlowStatus, value: Any, context: FlowContext &#124; None, error: Exception &#124; None, guard: FlowNode &#124; None, timings: dict[str, float] | Result of a flow pipeline execution. |
| `Layer` | `aquilia/flow.py` | name: str, factory: Callable[..., Any], deps: list[str], scope: str | Composable effect layer -- separates effect construction from usage. |
| `LayerComposition` | `aquilia/flow.py` | layers: list[Layer] | A composition of multiple layers, resolved in dependency order. |
| `HealthStatus` | `aquilia/health.py` | name: str, status: SubsystemStatus, latency_ms: float, message: str, details: dict[str, Any], checked_at: datetime | Health status for a single subsystem. |
| `LifecycleEvent` | `aquilia/lifecycle.py` | phase: LifecyclePhase, app_name: str &#124; None, message: str &#124; None, error: Exception &#124; None | Event emitted during lifecycle transitions. |
| `ComponentRef` | `aquilia/manifest.py` | class_path: str, kind: ComponentKind, metadata: ManifestMetadata | Universal typed reference to any framework component. |
| `LifecycleConfig` | `aquilia/manifest.py` | on_startup: str &#124; None, on_shutdown: str &#124; None, depends_on: list[str], startup_timeout: float, shutdown_timeout: float, error_strategy: str | Lifecycle hook configuration. |
| `ServiceConfig` | `aquilia/manifest.py` | class_path: str, scope: ServiceScope, auto_discover: bool, lifecycle: LifecycleConfig &#124; None, feature_flags: list[str], aliases: list[str], factory: str &#124; None, factory_args: dict[str, Any] &#124; None, config: dict[str, Any] &#124; None, observable: bool, required: bool | Service registration configuration with complete DI support. |
| `MiddlewareConfig` | `aquilia/manifest.py` | class_path: str, scope: str, scope_target: str &#124; None, priority: int, condition: Callable &#124; None, config: dict[str, Any] &#124; None, on_error: str, fallback: str &#124; None, observable: bool, log_requests: bool, log_responses: bool | Middleware registration configuration. |
| `SessionConfig` | `aquilia/manifest.py` | name: str, enabled: bool, ttl: timedelta, idle_timeout: timedelta &#124; None, renewal: timedelta &#124; None, transport: str, transport_config: dict[str, Any] &#124; None, cookie_name: str, cookie_domain: str &#124; None, cookie_path: str, cookie_secure: bool, cookie_httponly: bool, ... | Session management configuration. |
| `FaultHandlerConfig` | `aquilia/manifest.py` | domain: str, handler_path: str, recovery_strategy: str, fallback_response: dict[str, Any] &#124; None | Fault handler configuration. |
| `FaultHandlingConfig` | `aquilia/manifest.py` | default_domain: str, strategy: str, handlers: list[FaultHandlerConfig], middlewares: list[MiddlewareConfig], metrics_enabled: bool | Fault/error handling configuration. |
| `FeatureConfig` | `aquilia/manifest.py` | name: str, enabled: bool, conditions: dict[str, Any] &#124; None, services: list[str], controllers: list[str], middleware: list[MiddlewareConfig], routes: list[str], log_usage: bool, metrics_enabled: bool | Feature flag configuration. |
| `BackgroundTaskConfig` | `aquilia/manifest.py` | tasks: list[str], default_queue: str, auto_discover: bool, enabled: bool | Per-module background task configuration. |
| `TemplateConfig` | `aquilia/manifest.py` | enabled: bool, search_paths: list[str], precompile: bool, cache: str, sandbox: bool, context_processors: list[str] | Template engine configuration. |
| `DatabaseConfig` | `aquilia/manifest.py` | url: str, auto_connect: bool, auto_create: bool, auto_migrate: bool, migrations_dir: str, pool_size: int, echo: bool, model_paths: list[str], scan_dirs: list[str] | DEPRECATED: Manifest-level database configuration. |
| `AppManifest` | `aquilia/manifest.py` | name: str, version: str, description: str, author: str, services: list[str &#124; ServiceConfig &#124; ComponentRef], controllers: list[str &#124; ComponentRef], socket_controllers: list[str &#124; ComponentRef], models: list[str &#124; ComponentRef], serializers: list[str &#124; ComponentRef], guards: list[str &#124; ComponentRef], pipes: list[str &#124; ComponentRef], interceptors: list[str &#124; ComponentRef], ... | Production-grade application manifest for complete app configuration. |
| `MiddlewareDescriptor` | `aquilia/middleware.py` | middleware: Middleware, scope: str, priority: int, name: str | Descriptor for middleware registration. |
| `AquilaConfig` | `aquilia/pyconfig.py` | env: str | Base class for Aquilia Python-native configuration. |
| `CallableBackgroundTask` | `aquilia/response.py` | func: Callable[[], Awaitable[None]], run_on_disconnect: bool | Simple callable-based background task. |
| `ServerSentEvent` | `aquilia/response.py` | data: str, id: str &#124; None, event: str &#124; None, retry: int &#124; None | Server-Sent Event data structure. |
| `MediaChunk` | `aquilia/response.py` | data: bytes &#124; str, content_type: str &#124; None, is_final: bool | Type-safe media chunk container for streaming payloads. |
| `HLSSegment` | `aquilia/response.py` | uri: str, duration: float, title: str &#124; None, byte_range: str &#124; None, discontinuity: bool | Single media segment entry in an HLS media playlist. |
| `HLSVariant` | `aquilia/response.py` | uri: str, bandwidth: int, resolution: str &#124; None, codecs: str &#124; None, frame_rate: float &#124; None, audio: str &#124; None | Variant stream descriptor for an HLS master playlist. |
| `RuntimeConfig` | `aquilia/runtime.py` | workspace_root: Path, mode: Literal['dev', 'test', 'prod'], debug: bool &#124; None, config_overrides: dict[str, Any] | Immutable configuration for an :class:`AquiliaRuntime` instance. |
| `SigningConfig` | `aquilia/signing.py` | secret: str, fallback_secrets: list[str], algorithm: str, salt: str, session_salt: str, csrf_salt: str, activation_salt: str, cache_salt: str | Runtime signing configuration. |

## Common Entry Points

- `Workspace.runtime()`
- `Workspace.security()`
- `Workspace.telemetry()`
- `RuntimeConfig`
- `ConfigLoader`

## Precedence Model

Aquilia generally resolves configuration in this order:

1. Explicit constructor arguments or typed integration dataclass values.
2. `Workspace` builder methods and `Workspace.integrate(...)` output.
3. `ConfigLoader` defaults and environment overlays.
4. Runtime defaults inside the subsystem service or provider constructor.

When this module is registered through an `AppManifest`, keep component declarations inside `modules/<name>/manifest.py` and keep cross-cutting integration settings in `workspace.py`.

## Datatype Guidance

- Prefer typed dataclasses, policy objects, and config objects listed above when they exist.
- Keep secret values in environment-backed config, not literal strings in committed workspace files.
- Keep runtime-only state in services, stores, providers, or request state rather than static configuration.
- Use `to_dict()` on integration dataclasses when you need to inspect exactly what enters `ConfigLoader`.

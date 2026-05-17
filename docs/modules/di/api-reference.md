# Dependency Injection API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
| --- | --- | --- | --- |
| `RequestCtx` | `aquilia/di/compat.py` | object | Legacy RequestCtx compatibility wrapper. |
| `ProviderMeta` | `aquilia/di/core.py` | object | Compact, serializable provider metadata. |
| `ResolveCtx` | `aquilia/di/core.py` | object | Context for resolution operations. |
| `Provider` | `aquilia/di/core.py` | Protocol | Provider protocol - how to instantiate a dependency. |
| `Container` | `aquilia/di/core.py` | object | DI Container - manages provider instances and scopes. |
| `Registry` | `aquilia/di/core.py` | object | Registry - builds and validates provider graph from manifests. |
| `Inject` | `aquilia/di/decorators.py` | object | Injection metadata marker. |
| `Dep` | `aquilia/di/dep.py` | object | Dependency descriptor for Annotated[]-based injection. |
| `Header` | `aquilia/di/dep.py` | object | Extract a header value from the current request. |
| `Query` | `aquilia/di/dep.py` | object | Extract a query parameter from the current request. |
| `Body` | `aquilia/di/dep.py` | object | Mark a parameter as coming from the request body. |
| `DIEventType` | `aquilia/di/diagnostics.py` | Enum | Types of DI events. |
| `DIEvent` | `aquilia/di/diagnostics.py` | object | A diagnostic event in the DI system. |
| `DiagnosticListener` | `aquilia/di/diagnostics.py` | Protocol | Interface for DI diagnostic listeners. |
| `ConsoleDiagnosticListener` | `aquilia/di/diagnostics.py` | object | Simple diagnostic listener that logs to console/logging. |
| `DIDiagnostics` | `aquilia/di/diagnostics.py` | object | Coordinator for DI diagnostic listeners. |
| `DIError` | `aquilia/di/errors.py` | Exception | Base exception for DI errors. |
| `ProviderNotFoundError` | `aquilia/di/errors.py` | DIError | Provider not found for requested token. |
| `DependencyCycleError` | `aquilia/di/errors.py` | DIError | Circular dependency detected. |
| `ScopeViolationError` | `aquilia/di/errors.py` | DIError | Scope violation detected (e.g., request-scoped injected into app-scoped). |
| `AmbiguousProviderError` | `aquilia/di/errors.py` | DIError | Multiple providers found for token without tag. |
| `ManifestValidationError` | `aquilia/di/errors.py` | DIError | Manifest validation failed. |
| `CrossAppDependencyError` | `aquilia/di/errors.py` | DIError | Cross-app dependency not declared in depends_on. |
| `CircularDependencyError` | `aquilia/di/errors.py` | DIError | Circular dependency detected in service graph. |
| `MissingDependencyError` | `aquilia/di/errors.py` | DIError | Required dependency not found in container. |
| `DependencyGraph` | `aquilia/di/graph.py` | object | Build and analyze dependency graph. |
| `DisposalStrategy` | `aquilia/di/lifecycle.py` | str, Enum | Strategy for disposing instances. |
| `LifecycleHook` | `aquilia/di/lifecycle.py` | object | Lifecycle hook registration. |
| `Lifecycle` | `aquilia/di/lifecycle.py` | object | Manages lifecycle hooks and deterministic disposal. |
| `LifecycleContext` | `aquilia/di/lifecycle.py` | object | Context manager for automatic lifecycle management. |
| `ClassProvider` | `aquilia/di/providers.py` | object | Provider that instantiates a class by resolving constructor dependencies. |
| `FactoryProvider` | `aquilia/di/providers.py` | object | Provider that calls a factory function to produce instances. |
| `ValueProvider` | `aquilia/di/providers.py` | object | Provider that returns a pre-bound constant value. |
| `PoolProvider` | `aquilia/di/providers.py` | object | Provider that manages a pool of instances. |
| `AliasProvider` | `aquilia/di/providers.py` | object | Provider that aliases one token to another. |
| `LazyProxyProvider` | `aquilia/di/providers.py` | object | Provider that creates a lazy proxy for cycle resolution. |
| `ScopedProvider` | `aquilia/di/providers.py` | object | Wrapper provider that enforces scope semantics. |
| `BlueprintProvider` | `aquilia/di/providers.py` | object | DI Provider that creates Blueprint instances with request context. |
| `RequestDAG` | `aquilia/di/request_dag.py` | object | Per-request dependency resolution graph. |
| `ServiceScope` | `aquilia/di/scopes.py` | str, Enum | Service lifetime scopes. |
| `Scope` | `aquilia/di/scopes.py` | object | Scope metadata and rules. |
| `ScopeValidator` | `aquilia/di/scopes.py` | object | Validates scope rules and relationships. |
| `MockProvider` | `aquilia/di/testing.py` | ValueProvider | Mock provider for testing. |
| `TestRegistry` | `aquilia/di/testing.py` | Registry | Registry with testing support. |

## Public Function Summary

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `load_manifests_from_settings` | `aquilia/di/cli.py` | `def load_manifests_from_settings(settings_path: str) -> tuple[list[Any], Any]` | Load manifests and config from settings file. |
| `cmd_di_check` | `aquilia/di/cli.py` | `def cmd_di_check(args)` | Validate DI configuration (static analysis). |
| `cmd_di_tree` | `aquilia/di/cli.py` | `def cmd_di_tree(args)` | Show dependency tree. |
| `cmd_di_graph` | `aquilia/di/cli.py` | `def cmd_di_graph(args)` | Export dependency graph as Graphviz DOT. |
| `cmd_di_profile` | `aquilia/di/cli.py` | `def cmd_di_profile(args)` | Benchmark DI performance. |
| `cmd_di_manifest` | `aquilia/di/cli.py` | `def cmd_di_manifest(args)` | Generate di_manifest.json for LSP integration. |
| `setup_di_commands` | `aquilia/di/cli.py` | `def setup_di_commands(subparsers)` | Setup DI subcommands. |
| `get_request_container` | `aquilia/di/compat.py` | `def get_request_container() -> Container &#124; None` | Get current request container from context. |
| `set_request_container` | `aquilia/di/compat.py` | `def set_request_container(container: Container) -> None` | Set request container in context. |
| `clear_request_container` | `aquilia/di/compat.py` | `def clear_request_container() -> None` | Clear request container from context. |
| `inject` | `aquilia/di/decorators.py` | `def inject(token: type &#124; str &#124; None = None, *, tag: str &#124; None = None, optional: bool = False) -> Inject` | Create injection metadata. |
| `service` | `aquilia/di/decorators.py` | `def service(*, scope: str = 'app', tag: str &#124; None = None, name: str &#124; None = None) -> Callable[[type[T]], type[T]]` | Decorator to mark a class as a DI service. |
| `factory` | `aquilia/di/decorators.py` | `def factory(*, scope: str = 'app', tag: str &#124; None = None, name: str &#124; None = None) -> Callable[[Callable[..., T]], Callable[..., T]]` | Decorator to mark a function as a DI factory. |
| `provides` | `aquilia/di/decorators.py` | `def provides(token: type &#124; str, *, scope: str = 'app', tag: str &#124; None = None) -> Callable[[Callable[..., T]], Callable[..., T]]` | Decorator to explicitly declare what a factory provides. |
| `auto_inject` | `aquilia/di/decorators.py` | `def auto_inject(func: Callable[..., T]) -> Callable[..., T]` | Decorator to auto-inject dependencies into a function. |
| `override_container` | `aquilia/di/testing.py` | `async def override_container(container: Container, token: type &#124; str, mock_value: Any, *, tag: str &#124; None = None)` | Context manager to temporarily override a provider. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `_CACHE_SENTINEL` | `aquilia/di/core.py` | `object()` |
| `_CACHEABLE_SCOPES` | `aquilia/di/core.py` | `frozenset(('singleton', 'app', 'request'))` |
| `T` | `aquilia/di/core.py` | `TypeVar('T')` |
| `T` | `aquilia/di/decorators.py` | `TypeVar('T')` |
| `T` | `aquilia/di/providers.py` | `TypeVar('T')` |
| `_RESOLVING` | `aquilia/di/request_dag.py` | `object()` |
| `SCOPES` | `aquilia/di/scopes.py` | `{'singleton': Scope(name='singleton', cacheable=True), 'app': Scope(name='app', cacheable=True), 'request': Scope(name='request', cacheable=True, parent='app'),` |

## Detailed Classes And Methods

### Class: `RequestCtx`

- Source: `aquilia/di/compat.py`
- Bases: `object`
- Summary: Legacy RequestCtx compatibility wrapper.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `container` | `def container(self) -> Container` | property | Get underlying container. |
| `container` | `def container(self, value: Container)` | container.setter | Set underlying container. |
| `get` | `def get(self, token, *, tag: str &#124; None = None, default = None)` |  | Get service from container (legacy API). |
| `get_async` | `async def get_async(self, token, *, tag: str &#124; None = None, default = None)` |  | Async version of get. |
| `from_container` | `def from_container(cls, container: Container) -> 'RequestCtx'` | classmethod | Create RequestCtx from container. |
| `set_current` | `def set_current(cls, ctx: 'RequestCtx') -> None` | classmethod | Set current request context. |
| `get_current` | `def get_current(cls) -> Optional['RequestCtx']` | classmethod | Get current request context. |

### Class: `ProviderMeta`

- Source: `aquilia/di/core.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Compact, serializable provider metadata.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `token` | `str` |  |
| `scope` | `str` |  |
| `tags` | `tuple[str, ...]` | `field(default_factory=tuple)` |
| `module` | `str` | `''` |
| `qualname` | `str` | `''` |
| `line` | `int &#124; None` | `None` |
| `version` | `str &#124; None` | `None` |
| `allow_lazy` | `bool` | `False` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize for manifest JSON. |

### Class: `ResolveCtx`

- Source: `aquilia/di/core.py`
- Bases: `object`
- Summary: Context for resolution operations.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `push` | `def push(self, token: str) -> None` |  | Push token onto resolution stack. |
| `pop` | `def pop(self) -> None` |  | Pop token from resolution stack. |
| `in_cycle` | `def in_cycle(self, token: str) -> bool` |  | Check if token is currently being resolved (cycle). |
| `get_trace` | `def get_trace(self) -> list[str]` |  | Get current resolution trace for error messages. |

### Class: `Provider`

- Source: `aquilia/di/core.py`
- Bases: `Protocol`
- Decorators: `runtime_checkable`
- Summary: Provider protocol - how to instantiate a dependency.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `meta` | `def meta(self) -> ProviderMeta` | property | Provider metadata. |
| `instantiate` | `async def instantiate(self, ctx: ResolveCtx) -> Any` |  | Instantiate the provider. |
| `shutdown` | `async def shutdown(self) -> None` |  | Shutdown hook for cleanup. |

### Class: `Container`

- Source: `aquilia/di/core.py`
- Bases: `object`
- Summary: DI Container - manages provider instances and scopes.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `register` | `def register(self, provider: Provider, tag: str &#124; None = None)` |  | Register a provider. |
| `bind` | `def bind(self, interface: type, implementation: type, scope: str = 'app', tag: str &#124; None = None)` |  | Bind an interface to an implementation class. |
| `register_instance` | `async def register_instance(self, token: type[T] &#124; str, instance: T, scope: str = 'request', tag: str &#124; None = None)` |  | Register a pre-instantiated object as a provider. |
| `resolve` | `def resolve(self, token: type[T] &#124; str, *, tag: str &#124; None = None, optional: bool = False) -> T` |  | Resolve a dependency (hot path - optimized). |
| `resolve_async` | `async def resolve_async(self, token: type[T] &#124; str, *, tag: str &#124; None = None, optional: bool = False) -> T` |  | Async resolve (primary resolution path). |
| `startup` | `async def startup(self) -> None` |  | Run startup hooks for all registered providers. |
| `is_registered` | `def is_registered(self, token: type[T] &#124; str, tag: str &#124; None = None) -> bool` |  | Check if a provider is registered for the token. |
| `create_request_scope` | `def create_request_scope(self) -> 'Container'` |  | Create a request-scoped child container (very cheap). |
| `shutdown` | `async def shutdown(self) -> None` |  | Shutdown container - run lifecycle hooks and finalizers in LIFO order. |

### Class: `Registry`

- Source: `aquilia/di/core.py`
- Bases: `object`
- Summary: Registry - builds and validates provider graph from manifests.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `from_manifests` | `def from_manifests(cls, manifests: list[Any], config: Any &#124; None = None, *, enforce_cross_app: bool = True) -> 'Registry'` | classmethod | Build registry from manifests. |
| `build_container` | `def build_container(self) -> Container` |  | Build container from registry. |

### Class: `Inject`

- Source: `aquilia/di/decorators.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Injection metadata marker.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `token` | `type &#124; str &#124; None` | `None` |
| `tag` | `str &#124; None` | `None` |
| `optional` | `bool` | `False` |

### Class: `Dep`

- Source: `aquilia/di/dep.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Dependency descriptor for Annotated[]-based injection.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `call` | `Callable[..., Any] &#124; None` | `None` |
| `cached` | `bool` | `True` |
| `scope` | `str &#124; None` | `None` |
| `tag` | `str &#124; None` | `None` |
| `use_cache` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_container_lookup` | `def is_container_lookup(self) -> bool` | property | True when Dep() has no callable -- just resolve by type from container. |
| `is_generator` | `def is_generator(self) -> bool` | property | True when the callable is an (async) generator -> needs teardown. |
| `is_async` | `def is_async(self) -> bool` | property | True when the callable is async (coroutine or async generator). |
| `cache_key` | `def cache_key(self) -> str` | property | Stable key for DAG deduplication. |
| `get_sub_dependencies` | `def get_sub_dependencies(self) -> dict[str, tuple[type, Any]]` |  | Inspect the callable's signature and extract sub-Dep annotations. |

### Class: `Header`

- Source: `aquilia/di/dep.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Extract a header value from the current request.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `alias` | `str &#124; None` | `None` |
| `required` | `bool` | `True` |
| `default` | `Any` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `header_key` | `def header_key(self) -> str` | property | Method. |
| `resolve` | `def resolve(self, context: dict[str, Any]) -> Any` |  | Resolve header from request context (allows use as Serializer default). |

### Class: `Query`

- Source: `aquilia/di/dep.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Extract a query parameter from the current request.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `default` | `Any` | `None` |
| `required` | `bool` | `False` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `resolve` | `def resolve(self, context: dict[str, Any]) -> Any` |  | Resolve query from request context (allows use as Serializer default). |

### Class: `Body`

- Source: `aquilia/di/dep.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Mark a parameter as coming from the request body.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `media_type` | `str` | `'application/json'` |
| `embed` | `bool` | `False` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `resolve` | `def resolve(self, context: dict[str, Any]) -> Any` |  | Resolve body from request context (async behavior not supported inside sync Serializer). |

### Class: `DIEventType`

- Source: `aquilia/di/diagnostics.py`
- Bases: `Enum`
- Summary: Types of DI events.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `REGISTRATION` |  | `'registration'` |
| `RESOLUTION_START` |  | `'resolution_start'` |
| `RESOLUTION_SUCCESS` |  | `'resolution_success'` |
| `RESOLUTION_FAILURE` |  | `'resolution_failure'` |
| `LIFECYCLE_STARTUP` |  | `'lifecycle_startup'` |
| `LIFECYCLE_SHUTDOWN` |  | `'lifecycle_shutdown'` |
| `PROVIDER_INSTANTATION` |  | `'provider_instantiation'` |

### Class: `DIEvent`

- Source: `aquilia/di/diagnostics.py`
- Bases: `object`
- Decorators: `dataclasses.dataclass`
- Summary: A diagnostic event in the DI system.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `type` | `DIEventType` |  |
| `timestamp` | `float` | `dataclasses.field(default_factory=time.monotonic)` |
| `token` | `Any &#124; None` | `None` |
| `tag` | `str &#124; None` | `None` |
| `provider_name` | `str &#124; None` | `None` |
| `duration` | `float &#124; None` | `None` |
| `error` | `Exception &#124; None` | `None` |
| `metadata` | `dict[str, Any]` | `dataclasses.field(default_factory=dict)` |

### Class: `DiagnosticListener`

- Source: `aquilia/di/diagnostics.py`
- Bases: `Protocol`
- Summary: Interface for DI diagnostic listeners.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `on_event` | `def on_event(self, event: DIEvent) -> None` |  | Called when a DI event occurs. |

### Class: `ConsoleDiagnosticListener`

- Source: `aquilia/di/diagnostics.py`
- Bases: `object`
- Summary: Simple diagnostic listener that logs to console/logging.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `on_event` | `def on_event(self, event: DIEvent) -> None` |  | Method. |

### Class: `DIDiagnostics`

- Source: `aquilia/di/diagnostics.py`
- Bases: `object`
- Summary: Coordinator for DI diagnostic listeners.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `add_listener` | `def add_listener(self, listener: DiagnosticListener) -> None` |  | Add a diagnostic listener. |
| `emit` | `def emit(self, event_type: DIEventType, **kwargs) -> None` |  | Emit a diagnostic event to all listeners. |
| `measure` | `def measure(self, event_type: DIEventType, **kwargs)` |  | Context manager to measure duration of an event. |

### Class: `DIError`

- Source: `aquilia/di/errors.py`
- Bases: `Exception`
- Summary: Base exception for DI errors.

### Class: `ProviderNotFoundError`

- Source: `aquilia/di/errors.py`
- Bases: `DIError`
- Summary: Provider not found for requested token.

### Class: `DependencyCycleError`

- Source: `aquilia/di/errors.py`
- Bases: `DIError`
- Summary: Circular dependency detected.

### Class: `ScopeViolationError`

- Source: `aquilia/di/errors.py`
- Bases: `DIError`
- Summary: Scope violation detected (e.g., request-scoped injected into app-scoped).

### Class: `AmbiguousProviderError`

- Source: `aquilia/di/errors.py`
- Bases: `DIError`
- Summary: Multiple providers found for token without tag.

### Class: `ManifestValidationError`

- Source: `aquilia/di/errors.py`
- Bases: `DIError`
- Summary: Manifest validation failed.

### Class: `CrossAppDependencyError`

- Source: `aquilia/di/errors.py`
- Bases: `DIError`
- Summary: Cross-app dependency not declared in depends_on.

### Class: `CircularDependencyError`

- Source: `aquilia/di/errors.py`
- Bases: `DIError`
- Summary: Circular dependency detected in service graph.

### Class: `MissingDependencyError`

- Source: `aquilia/di/errors.py`
- Bases: `DIError`
- Summary: Required dependency not found in container.

### Class: `DependencyGraph`

- Source: `aquilia/di/graph.py`
- Bases: `object`
- Summary: Build and analyze dependency graph.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `add_provider` | `def add_provider(self, provider: Provider, dependencies: list[str]) -> None` |  | Add provider to graph. |
| `detect_cycles` | `def detect_cycles(self) -> list[list[str]]` |  | Detect cycles using Tarjan's algorithm. |
| `get_resolution_order` | `def get_resolution_order(self) -> list[str]` |  | Get topological sort of providers (resolution order). |
| `export_dot` | `def export_dot(self) -> str` |  | Export graph as Graphviz DOT format. |
| `get_tree_view` | `def get_tree_view(self, root: str &#124; None = None) -> str` |  | Get tree view of dependencies. |

### Class: `DisposalStrategy`

- Source: `aquilia/di/lifecycle.py`
- Bases: `str, Enum`
- Summary: Strategy for disposing instances.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `LIFO` |  | `'lifo'` |
| `FIFO` |  | `'fifo'` |
| `PARALLEL` |  | `'parallel'` |

### Class: `LifecycleHook`

- Source: `aquilia/di/lifecycle.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Lifecycle hook registration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `callback` | `Callable[[], Coroutine[Any, Any, None]]` |  |
| `priority` | `int` | `0` |
| `phase` | `str` | `'shutdown'` |

### Class: `Lifecycle`

- Source: `aquilia/di/lifecycle.py`
- Bases: `object`
- Summary: Manages lifecycle hooks and deterministic disposal.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `on_startup` | `def on_startup(self, callback: Callable[[], Coroutine], *, name: str = 'startup_hook', priority: int = 0) -> None` |  | Register startup hook. |
| `on_shutdown` | `def on_shutdown(self, callback: Callable[[], Coroutine], *, name: str = 'shutdown_hook', priority: int = 0) -> None` |  | Register shutdown hook. |
| `register_finalizer` | `def register_finalizer(self, finalizer: Callable[[], Coroutine]) -> None` |  | Register finalizer for cleanup. |
| `run_startup_hooks` | `async def run_startup_hooks(self) -> None` |  | Run all startup hooks in priority order with per-hook timeout (SEC-DI-10). |
| `run_shutdown_hooks` | `async def run_shutdown_hooks(self) -> None` |  | Run all shutdown hooks in priority order with per-hook timeout (SEC-DI-10). |
| `run_finalizers` | `async def run_finalizers(self) -> None` |  | Run all finalizers according to disposal strategy. |
| `clear` | `def clear(self) -> None` |  | Clear all hooks and finalizers. |

### Class: `LifecycleContext`

- Source: `aquilia/di/lifecycle.py`
- Bases: `object`
- Summary: Context manager for automatic lifecycle management.

### Class: `ClassProvider`

- Source: `aquilia/di/providers.py`
- Bases: `object`
- Summary: Provider that instantiates a class by resolving constructor dependencies.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `meta` | `def meta(self) -> ProviderMeta` | property | Method. |
| `instantiate` | `async def instantiate(self, ctx: ResolveCtx) -> Any` |  | Instantiate class by resolving dependencies. |
| `shutdown` | `async def shutdown(self) -> None` |  | No-op for class provider (instances handle their own shutdown). |

### Class: `FactoryProvider`

- Source: `aquilia/di/providers.py`
- Bases: `object`
- Summary: Provider that calls a factory function to produce instances.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `meta` | `def meta(self) -> ProviderMeta` | property | Method. |
| `instantiate` | `async def instantiate(self, ctx: ResolveCtx) -> Any` |  | Call factory with resolved dependencies. |
| `shutdown` | `async def shutdown(self) -> None` |  | No-op for factory provider. |

### Class: `ValueProvider`

- Source: `aquilia/di/providers.py`
- Bases: `object`
- Summary: Provider that returns a pre-bound constant value.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `meta` | `def meta(self) -> ProviderMeta` | property | Method. |
| `instantiate` | `async def instantiate(self, ctx: ResolveCtx) -> Any` |  | Return pre-bound value. |
| `shutdown` | `async def shutdown(self) -> None` |  | No-op for value provider. |

### Class: `PoolProvider`

- Source: `aquilia/di/providers.py`
- Bases: `object`
- Summary: Provider that manages a pool of instances.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `meta` | `def meta(self) -> ProviderMeta` | property | Method. |
| `instantiate` | `async def instantiate(self, ctx: ResolveCtx) -> Any` |  | Acquire instance from pool (creates pool on first call). |
| `release` | `async def release(self, instance: Any) -> None` |  | Release instance back to pool. |
| `acquire` | `async def acquire(self, ctx: ResolveCtx = None)` | asynccontextmanager | Acquire an instance from the pool with auto-release. |
| `shutdown` | `async def shutdown(self) -> None` |  | Shutdown pool and clean up instances. |

### Class: `AliasProvider`

- Source: `aquilia/di/providers.py`
- Bases: `object`
- Summary: Provider that aliases one token to another.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `meta` | `def meta(self) -> ProviderMeta` | property | Method. |
| `instantiate` | `async def instantiate(self, ctx: ResolveCtx) -> Any` |  | Resolve target token. |
| `shutdown` | `async def shutdown(self) -> None` |  | No-op for alias provider. |

### Class: `LazyProxyProvider`

- Source: `aquilia/di/providers.py`
- Bases: `object`
- Summary: Provider that creates a lazy proxy for cycle resolution.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `meta` | `def meta(self) -> ProviderMeta` | property | Method. |
| `instantiate` | `async def instantiate(self, ctx: ResolveCtx) -> Any` |  | Create lazy proxy. |
| `shutdown` | `async def shutdown(self) -> None` |  | No-op for lazy proxy. |

### Class: `ScopedProvider`

- Source: `aquilia/di/providers.py`
- Bases: `object`
- Summary: Wrapper provider that enforces scope semantics.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `meta` | `def meta(self) -> ProviderMeta` | property | Method. |
| `instantiate` | `async def instantiate(self, ctx: ResolveCtx) -> Any` |  | Delegate to inner provider. |
| `shutdown` | `async def shutdown(self) -> None` |  | Delegate to inner provider. |

### Class: `BlueprintProvider`

- Source: `aquilia/di/providers.py`
- Bases: `object`
- Summary: DI Provider that creates Blueprint instances with request context.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `meta` | `def meta(self) -> ProviderMeta` | property | Method. |
| `instantiate` | `async def instantiate(self, ctx: ResolveCtx) -> Any` |  | Create Blueprint instance with request data from DI context. |
| `shutdown` | `async def shutdown(self) -> None` |  | No-op for blueprint provider. |

### Class: `RequestDAG`

- Source: `aquilia/di/request_dag.py`
- Bases: `object`
- Summary: Per-request dependency resolution graph.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `resolve` | `async def resolve(self, dep: Dep, param_type: type) -> Any` |  | Resolve a single Dep descriptor. |
| `teardown` | `async def teardown(self) -> None` |  | Run generator teardowns in LIFO order. |

### Class: `ServiceScope`

- Source: `aquilia/di/scopes.py`
- Bases: `str, Enum`
- Summary: Service lifetime scopes.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `SINGLETON` |  | `'singleton'` |
| `APP` |  | `'app'` |
| `REQUEST` |  | `'request'` |
| `TRANSIENT` |  | `'transient'` |
| `POOLED` |  | `'pooled'` |
| `EPHEMERAL` |  | `'ephemeral'` |

### Class: `Scope`

- Source: `aquilia/di/scopes.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Scope metadata and rules.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `cacheable` | `bool` |  |
| `parent` | `str &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `can_inject_into` | `def can_inject_into(self, other: 'Scope') -> bool` |  | Check if this scope can be injected into another scope. |

### Class: `ScopeValidator`

- Source: `aquilia/di/scopes.py`
- Bases: `object`
- Summary: Validates scope rules and relationships.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate_injection` | `def validate_injection(provider_scope: str, consumer_scope: str) -> bool` | staticmethod | Validate that provider scope can be injected into consumer scope. |
| `get_scope_hierarchy` | `def get_scope_hierarchy() -> dict[str, list[str]]` | staticmethod | Get scope hierarchy for diagnostics. |

### Class: `MockProvider`

- Source: `aquilia/di/testing.py`
- Bases: `ValueProvider`
- Summary: Mock provider for testing.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `instantiate` | `async def instantiate(self, ctx)` |  | Track instantiation calls. |
| `reset` | `def reset(self) -> None` |  | Reset tracking. |

### Class: `TestRegistry`

- Source: `aquilia/di/testing.py`
- Bases: `Registry`
- Summary: Registry with testing support.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `from_manifests` | `def from_manifests(cls, manifests: list[Any], config: Any &#124; None = None, *, overrides: dict[str, Provider] &#124; None = None, enforce_cross_app: bool = False) -> 'TestRegistry'` | classmethod | Build test registry with overrides. |
| `build_container` | `def build_container(self) -> Container` |  | Build container with overrides applied. |

## Functions

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `load_manifests_from_settings` | `aquilia/di/cli.py` | `def load_manifests_from_settings(settings_path: str) -> tuple[list[Any], Any]` | Load manifests and config from settings file. |
| `cmd_di_check` | `aquilia/di/cli.py` | `def cmd_di_check(args)` | Validate DI configuration (static analysis). |
| `cmd_di_tree` | `aquilia/di/cli.py` | `def cmd_di_tree(args)` | Show dependency tree. |
| `cmd_di_graph` | `aquilia/di/cli.py` | `def cmd_di_graph(args)` | Export dependency graph as Graphviz DOT. |
| `cmd_di_profile` | `aquilia/di/cli.py` | `def cmd_di_profile(args)` | Benchmark DI performance. |
| `cmd_di_manifest` | `aquilia/di/cli.py` | `def cmd_di_manifest(args)` | Generate di_manifest.json for LSP integration. |
| `setup_di_commands` | `aquilia/di/cli.py` | `def setup_di_commands(subparsers)` | Setup DI subcommands. |
| `get_request_container` | `aquilia/di/compat.py` | `def get_request_container() -> Container &#124; None` | Get current request container from context. |
| `set_request_container` | `aquilia/di/compat.py` | `def set_request_container(container: Container) -> None` | Set request container in context. |
| `clear_request_container` | `aquilia/di/compat.py` | `def clear_request_container() -> None` | Clear request container from context. |
| `inject` | `aquilia/di/decorators.py` | `def inject(token: type &#124; str &#124; None = None, *, tag: str &#124; None = None, optional: bool = False) -> Inject` | Create injection metadata. |
| `service` | `aquilia/di/decorators.py` | `def service(*, scope: str = 'app', tag: str &#124; None = None, name: str &#124; None = None) -> Callable[[type[T]], type[T]]` | Decorator to mark a class as a DI service. |
| `factory` | `aquilia/di/decorators.py` | `def factory(*, scope: str = 'app', tag: str &#124; None = None, name: str &#124; None = None) -> Callable[[Callable[..., T]], Callable[..., T]]` | Decorator to mark a function as a DI factory. |
| `provides` | `aquilia/di/decorators.py` | `def provides(token: type &#124; str, *, scope: str = 'app', tag: str &#124; None = None) -> Callable[[Callable[..., T]], Callable[..., T]]` | Decorator to explicitly declare what a factory provides. |
| `auto_inject` | `aquilia/di/decorators.py` | `def auto_inject(func: Callable[..., T]) -> Callable[..., T]` | Decorator to auto-inject dependencies into a function. |
| `override_container` | `aquilia/di/testing.py` | `async def override_container(container: Container, token: type &#124; str, mock_value: Any, *, tag: str &#124; None = None)` | Context manager to temporarily override a provider. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `_CACHE_SENTINEL` | `aquilia/di/core.py` | `object()` |
| `_CACHEABLE_SCOPES` | `aquilia/di/core.py` | `frozenset(('singleton', 'app', 'request'))` |
| `T` | `aquilia/di/core.py` | `TypeVar('T')` |
| `T` | `aquilia/di/decorators.py` | `TypeVar('T')` |
| `T` | `aquilia/di/providers.py` | `TypeVar('T')` |
| `_RESOLVING` | `aquilia/di/request_dag.py` | `object()` |
| `SCOPES` | `aquilia/di/scopes.py` | `{'singleton': Scope(name='singleton', cacheable=True), 'app': Scope(name='app', cacheable=True), 'request': Scope(name='request', cacheable=True, parent='app'),` |

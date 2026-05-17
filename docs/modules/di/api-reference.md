# Di API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/di/__init__.py` | 132 | 0 | 0 | Aquilia Dependency Injection System |
| `aquilia/di/cli.py` | 479 | 0 | 7 | CLI commands for DI system. |
| `aquilia/di/compat.py` | 105 | 1 | 3 | Compatibility layer with legacy Aquilia DI system. |
| `aquilia/di/core.py` | 1034 | 5 | 0 | Core DI types and protocols. |
| `aquilia/di/decorators.py` | 242 | 1 | 5 | Decorators and injection helpers for ergonomic DI usage. |
| `aquilia/di/dep.py` | 398 | 4 | 0 | Dep -- Composable dependency descriptor for annotation-driven DI. |
| `aquilia/di/diagnostics.py` | 122 | 5 | 0 | DI Diagnostics - Observability and event tracking for DI containers. |
| `aquilia/di/errors.py` | 239 | 9 | 0 | DI-specific error types with rich diagnostics. |
| `aquilia/di/graph.py` | 261 | 1 | 0 | Graph analysis and cycle detection for DI system. |
| `aquilia/di/lifecycle.py` | 241 | 4 | 0 | Lifecycle management for providers and containers. |
| `aquilia/di/providers.py` | 822 | 8 | 0 | Provider implementations for different instantiation strategies. |
| `aquilia/di/request_dag.py` | 431 | 1 | 0 | RequestDAG -- Per-request dependency graph resolver. |
| `aquilia/di/scopes.py` | 99 | 3 | 0 | Scope definitions and validation. |
| `aquilia/di/testing.py` | 195 | 2 | 1 | Testing utilities for DI system. |

## Public Exports

`AliasProvider`, `AmbiguousProviderError`, `BlueprintProvider`, `Body`, `ClassProvider`, `Container`, `DIError`, `Dep`, `DependencyCycleError`, `DependencyGraph`, `DisposalStrategy`, `FactoryProvider`, `Header`, `Inject`, `LazyProxyProvider`, `Lifecycle`, `LifecycleContext`, `LifecycleHook`, `MockProvider`, `PoolProvider`, `Provider`, `ProviderMeta`, `ProviderNotFoundError`, `Query`, `Registry`, `RequestCtx`, `RequestDAG`, `ResolveCtx`, `Scope`, `ScopeValidator`, `ScopeViolationError`, `ScopedProvider`, `ServiceScope`, `TestRegistry`, `ValueProvider`, `auto_inject`, `factory`, `inject`, `provides`, `service`

## Public Class Summary

| Class | Source | Bases | Summary |
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

| Function | Source | Signature | Summary |
| --- | --- | --- | --- |
| `load_manifests_from_settings` | `aquilia/di/cli.py` | `def load_manifests_from_settings(settings_path: str)` | Load manifests and config from settings file. |
| `cmd_di_check` | `aquilia/di/cli.py` | `def cmd_di_check(args)` | Validate DI configuration (static analysis). |
| `cmd_di_tree` | `aquilia/di/cli.py` | `def cmd_di_tree(args)` | Show dependency tree. |
| `cmd_di_graph` | `aquilia/di/cli.py` | `def cmd_di_graph(args)` | Export dependency graph as Graphviz DOT. |
| `cmd_di_profile` | `aquilia/di/cli.py` | `def cmd_di_profile(args)` | Benchmark DI performance. |
| `cmd_di_manifest` | `aquilia/di/cli.py` | `def cmd_di_manifest(args)` | Generate di_manifest.json for LSP integration. |
| `setup_di_commands` | `aquilia/di/cli.py` | `def setup_di_commands(subparsers)` | Setup DI subcommands. |
| `get_request_container` | `aquilia/di/compat.py` | `def get_request_container()` | Get current request container from context. |
| `set_request_container` | `aquilia/di/compat.py` | `def set_request_container(container: Container)` | Set request container in context. |
| `clear_request_container` | `aquilia/di/compat.py` | `def clear_request_container()` | Clear request container from context. |
| `inject` | `aquilia/di/decorators.py` | `def inject(token: type \| str \| None=None, *, tag: str \| None=None, optional: bool=False)` | Create injection metadata. |
| `service` | `aquilia/di/decorators.py` | `def service(*, scope: str='app', tag: str \| None=None, name: str \| None=None)` | Decorator to mark a class as a DI service. |
| `factory` | `aquilia/di/decorators.py` | `def factory(*, scope: str='app', tag: str \| None=None, name: str \| None=None)` | Decorator to mark a function as a DI factory. |
| `provides` | `aquilia/di/decorators.py` | `def provides(token: type \| str, *, scope: str='app', tag: str \| None=None)` | Decorator to explicitly declare what a factory provides. |
| `auto_inject` | `aquilia/di/decorators.py` | `def auto_inject(func: Callable[..., T])` | Decorator to auto-inject dependencies into a function. |
| `override_container` | `aquilia/di/testing.py` | `async def override_container(container: Container, token: type \| str, mock_value: Any, *, tag: str \| None=None)` | Context manager to temporarily override a provider. |

## Constants And Module Flags

| Name | Source | Value or Type |
| --- | --- | --- |
| `_CACHE_SENTINEL` | `aquilia/di/core.py` | `object()` |
| `_CACHEABLE_SCOPES` | `aquilia/di/core.py` | `frozenset(('singleton', 'app', 'request'))` |
| `T` | `aquilia/di/core.py` | `TypeVar('T')` |
| `T` | `aquilia/di/decorators.py` | `TypeVar('T')` |
| `T` | `aquilia/di/providers.py` | `TypeVar('T')` |
| `_RESOLVING` | `aquilia/di/request_dag.py` | `object()` |
| `SCOPES` | `aquilia/di/scopes.py` | `{'singleton': Scope(name='singleton', cacheable=True), 'app': Scope(name='app', cacheable=True), 'request': Scope(name='request', cacheable=True, parent='app'), 'transient': Scope(name='transient', cacheable=False), 'pooled': Scope(name='pooled', cacheable=False), 'ephemeral': Scope(name='ephemeral', cacheable=True, parent='request')}` |

## Detailed Classes And Methods

### `RequestCtx`

- Source: `aquilia/di/compat.py`
- Bases: `object`
- Summary: Legacy RequestCtx compatibility wrapper.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `container` | `def container(self)` | Get underlying container. |
| `container` | `def container(self, value: Container)` | Set underlying container. |
| `get` | `def get(self, token, *, tag: str \| None=None, default=None)` | Get service from container (legacy API). |
| `get_async` | `async def get_async(self, token, *, tag: str \| None=None, default=None)` | Async version of get. |
| `from_container` | `def from_container(cls, container: Container)` | Create RequestCtx from container. |
| `set_current` | `def set_current(cls, ctx: 'RequestCtx')` | Set current request context. |
| `get_current` | `def get_current(cls)` | Get current request context. |

### `ProviderMeta`

- Source: `aquilia/di/core.py`
- Bases: `object`
- Summary: Compact, serializable provider metadata.
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `token` | `str` | `` |
| `scope` | `str` | `` |
| `tags` | `tuple[str, ...]` | `field(default_factory=tuple)` |
| `module` | `str` | `''` |
| `qualname` | `str` | `''` |
| `line` | `int \| None` | `None` |
| `version` | `str \| None` | `None` |
| `allow_lazy` | `bool` | `False` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` | Serialize for manifest JSON. |

### `ResolveCtx`

- Source: `aquilia/di/core.py`
- Bases: `object`
- Summary: Context for resolution operations.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `push` | `def push(self, token: str)` | Push token onto resolution stack. |
| `pop` | `def pop(self)` | Pop token from resolution stack. |
| `in_cycle` | `def in_cycle(self, token: str)` | Check if token is currently being resolved (cycle). |
| `get_trace` | `def get_trace(self)` | Get current resolution trace for error messages. |

### `Provider`

- Source: `aquilia/di/core.py`
- Bases: `Protocol`
- Summary: Provider protocol - how to instantiate a dependency.
- Decorators: `runtime_checkable`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `meta` | `def meta(self)` | Provider metadata. |
| `instantiate` | `async def instantiate(self, ctx: ResolveCtx)` | Instantiate the provider. |
| `shutdown` | `async def shutdown(self)` | Shutdown hook for cleanup. |

### `Container`

- Source: `aquilia/di/core.py`
- Bases: `object`
- Summary: DI Container - manages provider instances and scopes.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `register` | `def register(self, provider: Provider, tag: str \| None=None)` | Register a provider. |
| `bind` | `def bind(self, interface: type, implementation: type, scope: str='app', tag: str \| None=None)` | Bind an interface to an implementation class. |
| `register_instance` | `async def register_instance(self, token: type[T] \| str, instance: T, scope: str='request', tag: str \| None=None)` | Register a pre-instantiated object as a provider. |
| `resolve` | `def resolve(self, token: type[T] \| str, *, tag: str \| None=None, optional: bool=False)` | Resolve a dependency (hot path - optimized). |
| `resolve_async` | `async def resolve_async(self, token: type[T] \| str, *, tag: str \| None=None, optional: bool=False)` | Async resolve (primary resolution path). |
| `startup` | `async def startup(self)` | Run startup hooks for all registered providers. |
| `is_registered` | `def is_registered(self, token: type[T] \| str, tag: str \| None=None)` | Check if a provider is registered for the token. |
| `create_request_scope` | `def create_request_scope(self)` | Create a request-scoped child container (very cheap). |
| `shutdown` | `async def shutdown(self)` | Shutdown container - run lifecycle hooks and finalizers in LIFO order. |

### `Registry`

- Source: `aquilia/di/core.py`
- Bases: `object`
- Summary: Registry - builds and validates provider graph from manifests.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `from_manifests` | `def from_manifests(cls, manifests: list[Any], config: Any \| None=None, *, enforce_cross_app: bool=True)` | Build registry from manifests. |
| `build_container` | `def build_container(self)` | Build container from registry. |

### `Inject`

- Source: `aquilia/di/decorators.py`
- Bases: `object`
- Summary: Injection metadata marker.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `token` | `type \| str \| None` | `None` |
| `tag` | `str \| None` | `None` |
| `optional` | `bool` | `False` |

### `Dep`

- Source: `aquilia/di/dep.py`
- Bases: `object`
- Summary: Dependency descriptor for Annotated[]-based injection.
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `call` | `Callable[..., Any] \| None` | `None` |
| `cached` | `bool` | `True` |
| `scope` | `str \| None` | `None` |
| `tag` | `str \| None` | `None` |
| `use_cache` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_container_lookup` | `def is_container_lookup(self)` | True when Dep() has no callable -- just resolve by type from container. |
| `is_generator` | `def is_generator(self)` | True when the callable is an (async) generator → needs teardown. |
| `is_async` | `def is_async(self)` | True when the callable is async (coroutine or async generator). |
| `cache_key` | `def cache_key(self)` | Stable key for DAG deduplication. |
| `get_sub_dependencies` | `def get_sub_dependencies(self)` | Inspect the callable's signature and extract sub-Dep annotations. |

### `Header`

- Source: `aquilia/di/dep.py`
- Bases: `object`
- Summary: Extract a header value from the current request.
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `alias` | `str \| None` | `None` |
| `required` | `bool` | `True` |
| `default` | `Any` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `header_key` | `def header_key(self)` |  |
| `resolve` | `def resolve(self, context: dict[str, Any])` | Resolve header from request context (allows use as Serializer default). |

### `Query`

- Source: `aquilia/di/dep.py`
- Bases: `object`
- Summary: Extract a query parameter from the current request.
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `default` | `Any` | `None` |
| `required` | `bool` | `False` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `resolve` | `def resolve(self, context: dict[str, Any])` | Resolve query from request context (allows use as Serializer default). |

### `Body`

- Source: `aquilia/di/dep.py`
- Bases: `object`
- Summary: Mark a parameter as coming from the request body.
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `media_type` | `str` | `'application/json'` |
| `embed` | `bool` | `False` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `resolve` | `def resolve(self, context: dict[str, Any])` | Resolve body from request context (async behavior not supported inside sync Serializer). |

### `DIEventType`

- Source: `aquilia/di/diagnostics.py`
- Bases: `Enum`
- Summary: Types of DI events.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `REGISTRATION` | `` | `'registration'` |
| `RESOLUTION_START` | `` | `'resolution_start'` |
| `RESOLUTION_SUCCESS` | `` | `'resolution_success'` |
| `RESOLUTION_FAILURE` | `` | `'resolution_failure'` |
| `LIFECYCLE_STARTUP` | `` | `'lifecycle_startup'` |
| `LIFECYCLE_SHUTDOWN` | `` | `'lifecycle_shutdown'` |
| `PROVIDER_INSTANTATION` | `` | `'provider_instantiation'` |

### `DIEvent`

- Source: `aquilia/di/diagnostics.py`
- Bases: `object`
- Summary: A diagnostic event in the DI system.
- Decorators: `dataclasses.dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `type` | `DIEventType` | `` |
| `timestamp` | `float` | `dataclasses.field(default_factory=time.monotonic)` |
| `token` | `Any \| None` | `None` |
| `tag` | `str \| None` | `None` |
| `provider_name` | `str \| None` | `None` |
| `duration` | `float \| None` | `None` |
| `error` | `Exception \| None` | `None` |
| `metadata` | `dict[str, Any]` | `dataclasses.field(default_factory=dict)` |

### `DiagnosticListener`

- Source: `aquilia/di/diagnostics.py`
- Bases: `Protocol`
- Summary: Interface for DI diagnostic listeners.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `on_event` | `def on_event(self, event: DIEvent)` | Called when a DI event occurs. |

### `ConsoleDiagnosticListener`

- Source: `aquilia/di/diagnostics.py`
- Bases: `object`
- Summary: Simple diagnostic listener that logs to console/logging.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `on_event` | `def on_event(self, event: DIEvent)` |  |

### `DIDiagnostics`

- Source: `aquilia/di/diagnostics.py`
- Bases: `object`
- Summary: Coordinator for DI diagnostic listeners.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `add_listener` | `def add_listener(self, listener: DiagnosticListener)` | Add a diagnostic listener. |
| `emit` | `def emit(self, event_type: DIEventType, **kwargs)` | Emit a diagnostic event to all listeners. |
| `measure` | `def measure(self, event_type: DIEventType, **kwargs)` | Context manager to measure duration of an event. |

### `DIError`

- Source: `aquilia/di/errors.py`
- Bases: `Exception`
- Summary: Base exception for DI errors.

### `ProviderNotFoundError`

- Source: `aquilia/di/errors.py`
- Bases: `DIError`
- Summary: Provider not found for requested token.

### `DependencyCycleError`

- Source: `aquilia/di/errors.py`
- Bases: `DIError`
- Summary: Circular dependency detected.

### `ScopeViolationError`

- Source: `aquilia/di/errors.py`
- Bases: `DIError`
- Summary: Scope violation detected (e.g., request-scoped injected into app-scoped).

### `AmbiguousProviderError`

- Source: `aquilia/di/errors.py`
- Bases: `DIError`
- Summary: Multiple providers found for token without tag.

### `ManifestValidationError`

- Source: `aquilia/di/errors.py`
- Bases: `DIError`
- Summary: Manifest validation failed.

### `CrossAppDependencyError`

- Source: `aquilia/di/errors.py`
- Bases: `DIError`
- Summary: Cross-app dependency not declared in depends_on.

### `CircularDependencyError`

- Source: `aquilia/di/errors.py`
- Bases: `DIError`
- Summary: Circular dependency detected in service graph.

### `MissingDependencyError`

- Source: `aquilia/di/errors.py`
- Bases: `DIError`
- Summary: Required dependency not found in container.

### `DependencyGraph`

- Source: `aquilia/di/graph.py`
- Bases: `object`
- Summary: Build and analyze dependency graph.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `add_provider` | `def add_provider(self, provider: Provider, dependencies: list[str])` | Add provider to graph. |
| `detect_cycles` | `def detect_cycles(self)` | Detect cycles using Tarjan's algorithm. |
| `get_resolution_order` | `def get_resolution_order(self)` | Get topological sort of providers (resolution order). |
| `export_dot` | `def export_dot(self)` | Export graph as Graphviz DOT format. |
| `get_tree_view` | `def get_tree_view(self, root: str \| None=None)` | Get tree view of dependencies. |

### `DisposalStrategy`

- Source: `aquilia/di/lifecycle.py`
- Bases: `str, Enum`
- Summary: Strategy for disposing instances.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `LIFO` | `` | `'lifo'` |
| `FIFO` | `` | `'fifo'` |
| `PARALLEL` | `` | `'parallel'` |

### `LifecycleHook`

- Source: `aquilia/di/lifecycle.py`
- Bases: `object`
- Summary: Lifecycle hook registration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `callback` | `Callable[[], Coroutine[Any, Any, None]]` | `` |
| `priority` | `int` | `0` |
| `phase` | `str` | `'shutdown'` |

### `Lifecycle`

- Source: `aquilia/di/lifecycle.py`
- Bases: `object`
- Summary: Manages lifecycle hooks and deterministic disposal.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `on_startup` | `def on_startup(self, callback: Callable[[], Coroutine], *, name: str='startup_hook', priority: int=0)` | Register startup hook. |
| `on_shutdown` | `def on_shutdown(self, callback: Callable[[], Coroutine], *, name: str='shutdown_hook', priority: int=0)` | Register shutdown hook. |
| `register_finalizer` | `def register_finalizer(self, finalizer: Callable[[], Coroutine])` | Register finalizer for cleanup. |
| `run_startup_hooks` | `async def run_startup_hooks(self)` | Run all startup hooks in priority order with per-hook timeout (SEC-DI-10). |
| `run_shutdown_hooks` | `async def run_shutdown_hooks(self)` | Run all shutdown hooks in priority order with per-hook timeout (SEC-DI-10). |
| `run_finalizers` | `async def run_finalizers(self)` | Run all finalizers according to disposal strategy. |
| `clear` | `def clear(self)` | Clear all hooks and finalizers. |

### `LifecycleContext`

- Source: `aquilia/di/lifecycle.py`
- Bases: `object`
- Summary: Context manager for automatic lifecycle management.

### `ClassProvider`

- Source: `aquilia/di/providers.py`
- Bases: `object`
- Summary: Provider that instantiates a class by resolving constructor dependencies.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `meta` | `def meta(self)` |  |
| `instantiate` | `async def instantiate(self, ctx: ResolveCtx)` | Instantiate class by resolving dependencies. |
| `shutdown` | `async def shutdown(self)` | No-op for class provider (instances handle their own shutdown). |

### `FactoryProvider`

- Source: `aquilia/di/providers.py`
- Bases: `object`
- Summary: Provider that calls a factory function to produce instances.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `meta` | `def meta(self)` |  |
| `instantiate` | `async def instantiate(self, ctx: ResolveCtx)` | Call factory with resolved dependencies. |
| `shutdown` | `async def shutdown(self)` | No-op for factory provider. |

### `ValueProvider`

- Source: `aquilia/di/providers.py`
- Bases: `object`
- Summary: Provider that returns a pre-bound constant value.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `meta` | `def meta(self)` |  |
| `instantiate` | `async def instantiate(self, ctx: ResolveCtx)` | Return pre-bound value. |
| `shutdown` | `async def shutdown(self)` | No-op for value provider. |

### `PoolProvider`

- Source: `aquilia/di/providers.py`
- Bases: `object`
- Summary: Provider that manages a pool of instances.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `meta` | `def meta(self)` |  |
| `instantiate` | `async def instantiate(self, ctx: ResolveCtx)` | Acquire instance from pool (creates pool on first call). |
| `release` | `async def release(self, instance: Any)` | Release instance back to pool. |
| `acquire` | `async def acquire(self, ctx: ResolveCtx=None)` | Acquire an instance from the pool with auto-release. |
| `shutdown` | `async def shutdown(self)` | Shutdown pool and clean up instances. |

### `AliasProvider`

- Source: `aquilia/di/providers.py`
- Bases: `object`
- Summary: Provider that aliases one token to another.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `meta` | `def meta(self)` |  |
| `instantiate` | `async def instantiate(self, ctx: ResolveCtx)` | Resolve target token. |
| `shutdown` | `async def shutdown(self)` | No-op for alias provider. |

### `LazyProxyProvider`

- Source: `aquilia/di/providers.py`
- Bases: `object`
- Summary: Provider that creates a lazy proxy for cycle resolution.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `meta` | `def meta(self)` |  |
| `instantiate` | `async def instantiate(self, ctx: ResolveCtx)` | Create lazy proxy. |
| `shutdown` | `async def shutdown(self)` | No-op for lazy proxy. |

### `ScopedProvider`

- Source: `aquilia/di/providers.py`
- Bases: `object`
- Summary: Wrapper provider that enforces scope semantics.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `meta` | `def meta(self)` |  |
| `instantiate` | `async def instantiate(self, ctx: ResolveCtx)` | Delegate to inner provider. |
| `shutdown` | `async def shutdown(self)` | Delegate to inner provider. |

### `BlueprintProvider`

- Source: `aquilia/di/providers.py`
- Bases: `object`
- Summary: DI Provider that creates Blueprint instances with request context.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `meta` | `def meta(self)` |  |
| `instantiate` | `async def instantiate(self, ctx: ResolveCtx)` | Create Blueprint instance with request data from DI context. |
| `shutdown` | `async def shutdown(self)` | No-op for blueprint provider. |

### `RequestDAG`

- Source: `aquilia/di/request_dag.py`
- Bases: `object`
- Summary: Per-request dependency resolution graph.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `resolve` | `async def resolve(self, dep: Dep, param_type: type)` | Resolve a single Dep descriptor. |
| `teardown` | `async def teardown(self)` | Run generator teardowns in LIFO order. |

### `ServiceScope`

- Source: `aquilia/di/scopes.py`
- Bases: `str, Enum`
- Summary: Service lifetime scopes.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `SINGLETON` | `` | `'singleton'` |
| `APP` | `` | `'app'` |
| `REQUEST` | `` | `'request'` |
| `TRANSIENT` | `` | `'transient'` |
| `POOLED` | `` | `'pooled'` |
| `EPHEMERAL` | `` | `'ephemeral'` |

### `Scope`

- Source: `aquilia/di/scopes.py`
- Bases: `object`
- Summary: Scope metadata and rules.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `cacheable` | `bool` | `` |
| `parent` | `str \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `can_inject_into` | `def can_inject_into(self, other: 'Scope')` | Check if this scope can be injected into another scope. |

### `ScopeValidator`

- Source: `aquilia/di/scopes.py`
- Bases: `object`
- Summary: Validates scope rules and relationships.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate_injection` | `def validate_injection(provider_scope: str, consumer_scope: str)` | Validate that provider scope can be injected into consumer scope. |
| `get_scope_hierarchy` | `def get_scope_hierarchy()` | Get scope hierarchy for diagnostics. |

### `MockProvider`

- Source: `aquilia/di/testing.py`
- Bases: `ValueProvider`
- Summary: Mock provider for testing.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `instantiate` | `async def instantiate(self, ctx)` | Track instantiation calls. |
| `reset` | `def reset(self)` | Reset tracking. |

### `TestRegistry`

- Source: `aquilia/di/testing.py`
- Bases: `Registry`
- Summary: Registry with testing support.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `from_manifests` | `def from_manifests(cls, manifests: list[Any], config: Any \| None=None, *, overrides: dict[str, Provider] \| None=None, enforce_cross_app: bool=False)` | Build test registry with overrides. |
| `build_container` | `def build_container(self)` | Build container with overrides applied. |

# Aquilary API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/aquilary/__init__.py` | 78 | 0 | 0 | Aquilary - Manifest-driven App Registry for Aquilia |
| `aquilia/aquilary/cli.py` | 501 | 0 | 7 | Aquilary CLI commands for manifest validation, inspection, and deployment. |
| `aquilia/aquilary/core.py` | 1498 | 6 | 0 | Core Aquilary types and main registry class. |
| `aquilia/aquilary/errors.py` | 448 | 11 | 0 | Aquilary registry error types with rich diagnostics. |
| `aquilia/aquilary/fingerprint.py` | 424 | 1 | 0 | Fingerprint generator for reproducible deployments. |
| `aquilia/aquilary/graph.py` | 334 | 2 | 0 | Dependency graph analysis with Tarjan's algorithm for cycle detection. |
| `aquilia/aquilary/handler_wrapper.py` | 204 | 2 | 2 | Handler wrapper for dependency injection into controller methods. |
| `aquilia/aquilary/loader.py` | 487 | 2 | 0 | Safe manifest loader with no import-time side effects. |
| `aquilia/aquilary/route_compiler.py` | 249 | 4 | 0 | Route Compiler - Extracts routes from controllers and compiles route table. |
| `aquilia/aquilary/validator.py` | 453 | 1 | 0 | Registry validator for manifests and configuration. |

## Public Exports

`AppContext`, `Aquilary`, `AquilaryRegistry`, `ConfigValidationError`, `CrossAppUsageError`, `DependencyCycleError`, `DependencyGraph`, `DuplicateAppError`, `ErrorSpan`, `FingerprintGenerator`, `FrozenManifestMismatchError`, `GraphNode`, `HotReloadError`, `ManifestLoader`, `ManifestSource`, `ManifestValidationError`, `RegistryError`, `RegistryFingerprint`, `RegistryMode`, `RegistryValidator`, `RouteConflictError`, `RuntimeRegistry`, `ValidationReport`

## Public Class Summary

| Class | Source | Bases | Summary |
| --- | --- | --- | --- |
| `RegistryMode` | `aquilia/aquilary/core.py` | str, Enum | Registry operational modes. |
| `AppContext` | `aquilia/aquilary/core.py` | object | Runtime context for a loaded app. |
| `RegistryFingerprint` | `aquilia/aquilary/core.py` | object | Immutable registry fingerprint for deployment gating. |
| `AquilaryRegistry` | `aquilia/aquilary/core.py` | object | Validated registry metadata (static phase output). |
| `Aquilary` | `aquilia/aquilary/core.py` | object | Main entry point for building registry from manifests. |
| `RuntimeRegistry` | `aquilia/aquilary/core.py` | object | Runtime registry instance (lazy compilation phase). |
| `ErrorSpan` | `aquilia/aquilary/errors.py` | object | File location for error context. |
| `RegistryError` | `aquilia/aquilary/errors.py` | Exception | Base error for all Aquilary registry errors. |
| `DependencyCycleError` | `aquilia/aquilary/errors.py` | RegistryError | Circular dependency detected in app dependency graph. |
| `RouteConflictError` | `aquilia/aquilary/errors.py` | RegistryError | Multiple controllers claim the same route path. |
| `ConfigValidationError` | `aquilia/aquilary/errors.py` | RegistryError | Configuration validation failed. |
| `CrossAppUsageError` | `aquilia/aquilary/errors.py` | RegistryError | App uses service/controller from another app without declaring dependency. |
| `ManifestValidationError` | `aquilia/aquilary/errors.py` | RegistryError | Manifest structure is invalid. |
| `DuplicateAppError` | `aquilia/aquilary/errors.py` | RegistryError | Multiple manifests declare the same app name. |
| `FrozenManifestMismatchError` | `aquilia/aquilary/errors.py` | RegistryError | Current manifests don't match frozen fingerprint. |
| `HotReloadError` | `aquilia/aquilary/errors.py` | RegistryError | Hot-reload operation failed. |
| `ValidationReport` | `aquilia/aquilary/errors.py` | object | Aggregated validation report. |
| `FingerprintGenerator` | `aquilia/aquilary/fingerprint.py` | object | Generates deterministic fingerprints for registry state. |
| `GraphNode` | `aquilia/aquilary/graph.py` | object | Dependency graph node. |
| `DependencyGraph` | `aquilia/aquilary/graph.py` | object | Dependency graph with cycle detection and topological sorting. |
| `DIInjectionError` | `aquilia/aquilary/handler_wrapper.py` | Exception | Raised when dependency injection fails. |
| `HandlerWrapper` | `aquilia/aquilary/handler_wrapper.py` | object | Wraps controller handlers to inject dependencies from DI container. |
| `ManifestSource` | `aquilia/aquilary/loader.py` | object | Manifest source descriptor. |
| `ManifestLoader` | `aquilia/aquilary/loader.py` | object | Safe manifest loader that NEVER triggers import-time side effects. |
| `RouteInfo` | `aquilia/aquilary/route_compiler.py` | object | Information about a single route. |
| `RouteTable` | `aquilia/aquilary/route_compiler.py` | object | Compiled routing table. |
| `RouteConflictError` | `aquilia/aquilary/route_compiler.py` | Exception | Raised when route patterns conflict. |
| `RouteCompiler` | `aquilia/aquilary/route_compiler.py` | object | Compiles routes from controller classes. Extracts @flow decorators and builds routing table. |
| `RegistryValidator` | `aquilia/aquilary/validator.py` | object | Validates registry manifests and configuration. |

## Public Function Summary

| Function | Source | Signature | Summary |
| --- | --- | --- | --- |
| `load_config` | `aquilia/aquilary/cli.py` | `def load_config(config_path: str \| None)` | Load config from Python file. |
| `cmd_validate` | `aquilia/aquilary/cli.py` | `def cmd_validate(args: argparse.Namespace)` | Validate manifests. |
| `cmd_inspect` | `aquilia/aquilary/cli.py` | `def cmd_inspect(args: argparse.Namespace)` | Inspect registry and show diagnostics. |
| `cmd_freeze` | `aquilia/aquilary/cli.py` | `def cmd_freeze(args: argparse.Namespace)` | Freeze manifest for reproducible deploys. |
| `cmd_graph` | `aquilia/aquilary/cli.py` | `def cmd_graph(args: argparse.Namespace)` | Visualize dependency graph. |
| `cmd_run` | `aquilia/aquilary/cli.py` | `def cmd_run(args: argparse.Namespace)` | Run application with registry. |
| `main` | `aquilia/aquilary/cli.py` | `def main()` | Main CLI entry point. |
| `wrap_handler` | `aquilia/aquilary/handler_wrapper.py` | `def wrap_handler(handler: Callable, controller_class: type)` | Wrap a controller handler for dependency injection. |
| `inject_dependencies` | `aquilia/aquilary/handler_wrapper.py` | `def inject_dependencies(handler: Callable)` | Decorator to enable dependency injection for a handler. |

## Detailed Classes And Methods

### `RegistryMode`

- Source: `aquilia/aquilary/core.py`
- Bases: `str, Enum`
- Summary: Registry operational modes.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `DEV` | `` | `'dev'` |
| `PROD` | `` | `'prod'` |
| `TEST` | `` | `'test'` |

### `AppContext`

- Source: `aquilia/aquilary/core.py`
- Bases: `object`
- Summary: Runtime context for a loaded app.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `version` | `str` | `` |
| `manifest` | `Any` | `` |
| `config_namespace` | `dict[str, Any]` | `` |
| `route_prefix` | `str` | `'/'` |
| `controllers` | `list[str]` | `field(default_factory=list)` |
| `services` | `list[str]` | `field(default_factory=list)` |
| `models` | `list[str]` | `field(default_factory=list)` |
| `middlewares` | `list[tuple[str, dict]]` | `field(default_factory=list)` |
| `depends_on` | `list[str]` | `field(default_factory=list)` |
| `on_startup` | `Callable \| None` | `None` |
| `on_shutdown` | `Callable \| None` | `None` |
| `di_container` | `Any \| None` | `None` |
| `route_metadata` | `list[dict[str, Any]]` | `field(default_factory=list)` |
| `load_order` | `int` | `0` |

### `RegistryFingerprint`

- Source: `aquilia/aquilary/core.py`
- Bases: `object`
- Summary: Immutable registry fingerprint for deployment gating.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `hash` | `str` | `` |
| `timestamp` | `str` | `` |
| `mode` | `str` | `` |
| `app_count` | `int` | `` |
| `route_count` | `int` | `` |
| `manifest_sources` | `list[str]` | `` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` | Serialize for JSON export. |

### `AquilaryRegistry`

- Source: `aquilia/aquilary/core.py`
- Bases: `object`
- Summary: Validated registry metadata (static phase output).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `build_runtime` | `def build_runtime(self)` | Build runtime registry. |
| `inspect` | `def inspect(self)` | Get diagnostics, routes, dependency graph, conflicts, fingerprint. |
| `export_manifest` | `def export_manifest(self, path: str)` | Write frozen manifest for reproducible deploys. |

### `Aquilary`

- Source: `aquilia/aquilary/core.py`
- Bases: `object`
- Summary: Main entry point for building registry from manifests.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `from_manifests` | `def from_manifests(cls, manifests: list[type \| str], config: Any, mode: Literal['dev', 'prod', 'test']='prod', *, allow_fs_autodiscovery: bool=False, freeze_manifest_path: str \| None=None, workspace_modules: dict[str, dict[str, Any]] \| None=None)` | Build and validate registry metadata (static phase). |

### `RuntimeRegistry`

- Source: `aquilia/aquilary/core.py`
- Bases: `object`
- Summary: Runtime registry instance (lazy compilation phase).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `from_metadata` | `def from_metadata(cls, registry_meta: AquilaryRegistry, config: Any)` | Create runtime registry from metadata. |
| `perform_autodiscovery` | `def perform_autodiscovery(self)` | Perform runtime auto-discovery of controllers and services. |
| `compile_routes` | `def compile_routes(self)` | Lazily import controllers and compile route trees. |
| `validate_dependencies` | `def validate_dependencies(self)` | Validate cross-app dependencies and service availability. |
| `validate_routes` | `def validate_routes(self)` | Validate route configuration for conflicts and errors. |
| `validate_effects` | `def validate_effects(self)` | Validate effect registration. |
| `validate_all` | `def validate_all(self)` | Run all validation checks. |
| `compile` | `def compile(self)` | Compile runtime registry with full validation. |
| `build_runtime_instance` | `def build_runtime_instance(self)` | Build complete runtime instance. |

### `ErrorSpan`

- Source: `aquilia/aquilary/errors.py`
- Bases: `object`
- Summary: File location for error context.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `file` | `str` | `` |
| `line` | `int \| None` | `None` |
| `column` | `int \| None` | `None` |
| `snippet` | `str \| None` | `None` |

### `RegistryError`

- Source: `aquilia/aquilary/errors.py`
- Bases: `Exception`
- Summary: Base error for all Aquilary registry errors.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `format_error` | `def format_error(self)` | Format error with rich diagnostics. |

### `DependencyCycleError`

- Source: `aquilia/aquilary/errors.py`
- Bases: `RegistryError`
- Summary: Circular dependency detected in app dependency graph.

### `RouteConflictError`

- Source: `aquilia/aquilary/errors.py`
- Bases: `RegistryError`
- Summary: Multiple controllers claim the same route path.

### `ConfigValidationError`

- Source: `aquilia/aquilary/errors.py`
- Bases: `RegistryError`
- Summary: Configuration validation failed.

### `CrossAppUsageError`

- Source: `aquilia/aquilary/errors.py`
- Bases: `RegistryError`
- Summary: App uses service/controller from another app without declaring dependency.

### `ManifestValidationError`

- Source: `aquilia/aquilary/errors.py`
- Bases: `RegistryError`
- Summary: Manifest structure is invalid.

### `DuplicateAppError`

- Source: `aquilia/aquilary/errors.py`
- Bases: `RegistryError`
- Summary: Multiple manifests declare the same app name.

### `FrozenManifestMismatchError`

- Source: `aquilia/aquilary/errors.py`
- Bases: `RegistryError`
- Summary: Current manifests don't match frozen fingerprint.

### `HotReloadError`

- Source: `aquilia/aquilary/errors.py`
- Bases: `RegistryError`
- Summary: Hot-reload operation failed.

### `ValidationReport`

- Source: `aquilia/aquilary/errors.py`
- Bases: `object`
- Summary: Aggregated validation report.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `errors` | `list[RegistryError]` | `field(default_factory=list)` |
| `warnings` | `list[str]` | `field(default_factory=list)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `add_error` | `def add_error(self, error: RegistryError)` | Add error to report. |
| `add_warning` | `def add_warning(self, warning: str)` | Add warning to report. |
| `has_errors` | `def has_errors(self)` | Check if report has errors. |
| `to_dict` | `def to_dict(self)` | Serialize report. |
| `to_exception` | `def to_exception(self)` | Convert report to exception. |
| `format_report` | `def format_report(self)` | Format report for display. |

### `FingerprintGenerator`

- Source: `aquilia/aquilary/fingerprint.py`
- Bases: `object`
- Summary: Generates deterministic fingerprints for registry state.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `generate` | `def generate(self, app_contexts: list[Any], config: Any, mode: Any)` | Generate fingerprint from registry state. |
| `generate_with_metadata` | `def generate_with_metadata(self, app_contexts: list[Any], config: Any, mode: Any)` | Generate fingerprint with metadata. |
| `verify_fingerprint` | `def verify_fingerprint(self, expected: str, app_contexts: list[Any], config: Any, mode: Any)` | Verify current state matches expected fingerprint. |
| `diff_fingerprints` | `def diff_fingerprints(self, expected_contexts: list[Any], actual_contexts: list[Any], config: Any, mode: Any)` | Compute diff between expected and actual registry state. |

### `GraphNode`

- Source: `aquilia/aquilary/graph.py`
- Bases: `object`
- Summary: Dependency graph node.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `dependencies` | `list[str]` | `field(default_factory=list)` |
| `index` | `int \| None` | `None` |
| `lowlink` | `int \| None` | `None` |
| `on_stack` | `bool` | `False` |

### `DependencyGraph`

- Source: `aquilia/aquilary/graph.py`
- Bases: `object`
- Summary: Dependency graph with cycle detection and topological sorting.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `add_node` | `def add_node(self, name: str, dependencies: list[str])` | Add node to graph. |
| `topological_sort` | `def topological_sort(self)` | Compute topological sort of graph (dependency order). |
| `find_cycle` | `def find_cycle(self)` | Find cycle in graph using Tarjan's algorithm. |
| `get_dependencies` | `def get_dependencies(self, node_name: str)` | Get direct dependencies of node. |
| `get_transitive_dependencies` | `def get_transitive_dependencies(self, node_name: str)` | Get transitive closure of dependencies. |
| `get_dependents` | `def get_dependents(self, node_name: str)` | Get nodes that depend on given node (reverse dependencies). |
| `to_dict` | `def to_dict(self)` | Export graph as adjacency dict. |
| `to_dot` | `def to_dot(self)` | Export graph as DOT format for visualization. |
| `get_load_order` | `def get_load_order(self)` | Get load order (topological sort). |
| `validate` | `def validate(self)` | Validate graph for cycles. |
| `get_roots` | `def get_roots(self)` | Get root nodes (no dependencies). |
| `get_leaves` | `def get_leaves(self)` | Get leaf nodes (no dependents). |
| `get_layers` | `def get_layers(self)` | Get dependency layers (parallel execution groups). |

### `DIInjectionError`

- Source: `aquilia/aquilary/handler_wrapper.py`
- Bases: `Exception`
- Summary: Raised when dependency injection fails.

### `HandlerWrapper`

- Source: `aquilia/aquilary/handler_wrapper.py`
- Bases: `object`
- Summary: Wraps controller handlers to inject dependencies from DI container.

### `ManifestSource`

- Source: `aquilia/aquilary/loader.py`
- Bases: `object`
- Summary: Manifest source descriptor.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `type` | `str` | `` |
| `value` | `Any` | `` |
| `origin` | `str` | `` |

### `ManifestLoader`

- Source: `aquilia/aquilary/loader.py`
- Bases: `object`
- Summary: Safe manifest loader that NEVER triggers import-time side effects.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `load_manifests` | `def load_manifests(self, sources: list[type \| str], *, allow_fs_autodiscovery: bool=False)` | Load manifests from sources. |

### `RouteInfo`

- Source: `aquilia/aquilary/route_compiler.py`
- Bases: `object`
- Summary: Information about a single route.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `pattern` | `str` | `` |
| `method` | `str` | `` |
| `handler` | `Any` | `` |
| `controller_class` | `type` | `` |
| `flow` | `Any` | `` |
| `metadata` | `dict[str, Any]` | `` |

### `RouteTable`

- Source: `aquilia/aquilary/route_compiler.py`
- Bases: `object`
- Summary: Compiled routing table.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `routes` | `list[RouteInfo]` | `` |
| `patterns` | `dict[str, RouteInfo]` | `` |
| `conflicts` | `list[tuple[RouteInfo, RouteInfo]]` | `` |

### `RouteConflictError`

- Source: `aquilia/aquilary/route_compiler.py`
- Bases: `Exception`
- Summary: Raised when route patterns conflict.

### `RouteCompiler`

- Source: `aquilia/aquilary/route_compiler.py`
- Bases: `object`
- Summary: Compiles routes from controller classes. Extracts @flow decorators and builds routing table.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `compile_controller` | `def compile_controller(self, controller_path: str, config: Any=None)` | Compile routes from a controller module or class. |
| `compile_from_manifests` | `def compile_from_manifests(self, manifests: list[dict[str, Any]], config: Any=None)` | Compile routes from app manifests. |
| `validate_routes` | `def validate_routes(self)` | Validate compiled routes. |
| `get_route_count` | `def get_route_count(self)` | Get total number of routes. |
| `get_routes_by_method` | `def get_routes_by_method(self, method: str)` | Get all routes for a specific HTTP method. |
| `get_routes_by_pattern` | `def get_routes_by_pattern(self, pattern: str)` | Get all routes matching a pattern. |
| `to_dict` | `def to_dict(self)` | Export route table as dictionary. |

### `RegistryValidator`

- Source: `aquilia/aquilary/validator.py`
- Bases: `object`
- Summary: Validates registry manifests and configuration.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate_manifests` | `def validate_manifests(self, manifests: list[Any], config: Any)` | Validate all manifests. |
| `validate_hot_reload` | `def validate_hot_reload(self, old_manifests: list[Any], new_manifests: list[Any])` | Validate hot-reload is safe. |

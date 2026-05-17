# Aquilary Registry API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
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
| `RouteCompiler` | `aquilia/aquilary/route_compiler.py` | object | Compiles routes from controller classes. |
| `RegistryValidator` | `aquilia/aquilary/validator.py` | object | Validates registry manifests and configuration. |

## Public Function Summary

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `load_config` | `aquilia/aquilary/cli.py` | `def load_config(config_path: str &#124; None) -> Any` | Load config from Python file. |
| `cmd_validate` | `aquilia/aquilary/cli.py` | `def cmd_validate(args: argparse.Namespace) -> None` | Validate manifests. |
| `cmd_inspect` | `aquilia/aquilary/cli.py` | `def cmd_inspect(args: argparse.Namespace) -> None` | Inspect registry and show diagnostics. |
| `cmd_freeze` | `aquilia/aquilary/cli.py` | `def cmd_freeze(args: argparse.Namespace) -> None` | Freeze manifest for reproducible deploys. |
| `cmd_graph` | `aquilia/aquilary/cli.py` | `def cmd_graph(args: argparse.Namespace) -> None` | Visualize dependency graph. |
| `cmd_run` | `aquilia/aquilary/cli.py` | `def cmd_run(args: argparse.Namespace) -> None` | Run application with registry. |
| `main` | `aquilia/aquilary/cli.py` | `def main()` | Main CLI entry point. |
| `wrap_handler` | `aquilia/aquilary/handler_wrapper.py` | `def wrap_handler(handler: Callable, controller_class: type) -> HandlerWrapper` | Wrap a controller handler for dependency injection. |
| `inject_dependencies` | `aquilia/aquilary/handler_wrapper.py` | `def inject_dependencies(handler: Callable) -> Callable` | Decorator to enable dependency injection for a handler. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| None detected |  |  |

## Detailed Classes And Methods

### Class: `RegistryMode`

- Source: `aquilia/aquilary/core.py`
- Bases: `str, Enum`
- Summary: Registry operational modes.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `DEV` |  | `'dev'` |
| `PROD` |  | `'prod'` |
| `TEST` |  | `'test'` |

### Class: `AppContext`

- Source: `aquilia/aquilary/core.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Runtime context for a loaded app.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `version` | `str` |  |
| `manifest` | `Any` |  |
| `config_namespace` | `dict[str, Any]` |  |
| `route_prefix` | `str` | `'/'` |
| `controllers` | `list[str]` | `field(default_factory=list)` |
| `services` | `list[str]` | `field(default_factory=list)` |
| `models` | `list[str]` | `field(default_factory=list)` |
| `middlewares` | `list[tuple[str, dict]]` | `field(default_factory=list)` |
| `depends_on` | `list[str]` | `field(default_factory=list)` |
| `on_startup` | `Callable &#124; None` | `None` |
| `on_shutdown` | `Callable &#124; None` | `None` |
| `di_container` | `Any &#124; None` | `None` |
| `route_metadata` | `list[dict[str, Any]]` | `field(default_factory=list)` |
| `load_order` | `int` | `0` |

### Class: `RegistryFingerprint`

- Source: `aquilia/aquilary/core.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Immutable registry fingerprint for deployment gating.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `hash` | `str` |  |
| `timestamp` | `str` |  |
| `mode` | `str` |  |
| `app_count` | `int` |  |
| `route_count` | `int` |  |
| `manifest_sources` | `list[str]` |  |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize for JSON export. |

### Class: `AquilaryRegistry`

- Source: `aquilia/aquilary/core.py`
- Bases: `object`
- Summary: Validated registry metadata (static phase output).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `build_runtime` | `def build_runtime(self) -> 'RuntimeRegistry'` |  | Build runtime registry. |
| `inspect` | `def inspect(self) -> dict[str, Any]` |  | Get diagnostics, routes, dependency graph, conflicts, fingerprint. |
| `export_manifest` | `def export_manifest(self, path: str) -> None` |  | Write frozen manifest for reproducible deploys. |

### Class: `Aquilary`

- Source: `aquilia/aquilary/core.py`
- Bases: `object`
- Summary: Main entry point for building registry from manifests.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `from_manifests` | `def from_manifests(cls, manifests: list[type &#124; str], config: Any, mode: Literal['dev', 'prod', 'test'] = 'prod', *, allow_fs_autodiscovery: bool = False, freeze_manifest_path: str &#124; None = None, workspace_modules: dict[str, dict[str, Any]] &#124; None = None) -> AquilaryRegistry` | classmethod | Build and validate registry metadata (static phase). |

### Class: `RuntimeRegistry`

- Source: `aquilia/aquilary/core.py`
- Bases: `object`
- Summary: Runtime registry instance (lazy compilation phase).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `from_metadata` | `def from_metadata(cls, registry_meta: AquilaryRegistry, config: Any) -> 'RuntimeRegistry'` | classmethod | Create runtime registry from metadata. |
| `perform_autodiscovery` | `def perform_autodiscovery(self) -> None` |  | Perform runtime auto-discovery of controllers and services. |
| `compile_routes` | `def compile_routes(self) -> None` |  | Lazily import controllers and compile route trees. |
| `validate_dependencies` | `def validate_dependencies(self) -> list[str]` |  | Validate cross-app dependencies and service availability. |
| `validate_routes` | `def validate_routes(self) -> list[str]` |  | Validate route configuration for conflicts and errors. |
| `validate_effects` | `def validate_effects(self) -> list[str]` |  | Validate effect registration. |
| `validate_all` | `def validate_all(self) -> dict[str, list[str]]` |  | Run all validation checks. |
| `compile` | `def compile(self)` |  | Compile runtime registry with full validation. |
| `build_runtime_instance` | `def build_runtime_instance(self) -> Any` |  | Build complete runtime instance. |

### Class: `ErrorSpan`

- Source: `aquilia/aquilary/errors.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: File location for error context.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `file` | `str` |  |
| `line` | `int &#124; None` | `None` |
| `column` | `int &#124; None` | `None` |
| `snippet` | `str &#124; None` | `None` |

### Class: `RegistryError`

- Source: `aquilia/aquilary/errors.py`
- Bases: `Exception`
- Summary: Base error for all Aquilary registry errors.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `format_error` | `def format_error(self) -> str` |  | Format error with rich diagnostics. |

### Class: `DependencyCycleError`

- Source: `aquilia/aquilary/errors.py`
- Bases: `RegistryError`
- Summary: Circular dependency detected in app dependency graph.

### Class: `RouteConflictError`

- Source: `aquilia/aquilary/errors.py`
- Bases: `RegistryError`
- Summary: Multiple controllers claim the same route path.

### Class: `ConfigValidationError`

- Source: `aquilia/aquilary/errors.py`
- Bases: `RegistryError`
- Summary: Configuration validation failed.

### Class: `CrossAppUsageError`

- Source: `aquilia/aquilary/errors.py`
- Bases: `RegistryError`
- Summary: App uses service/controller from another app without declaring dependency.

### Class: `ManifestValidationError`

- Source: `aquilia/aquilary/errors.py`
- Bases: `RegistryError`
- Summary: Manifest structure is invalid.

### Class: `DuplicateAppError`

- Source: `aquilia/aquilary/errors.py`
- Bases: `RegistryError`
- Summary: Multiple manifests declare the same app name.

### Class: `FrozenManifestMismatchError`

- Source: `aquilia/aquilary/errors.py`
- Bases: `RegistryError`
- Summary: Current manifests don't match frozen fingerprint.

### Class: `HotReloadError`

- Source: `aquilia/aquilary/errors.py`
- Bases: `RegistryError`
- Summary: Hot-reload operation failed.

### Class: `ValidationReport`

- Source: `aquilia/aquilary/errors.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Aggregated validation report.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `errors` | `list[RegistryError]` | `field(default_factory=list)` |
| `warnings` | `list[str]` | `field(default_factory=list)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `add_error` | `def add_error(self, error: RegistryError) -> None` |  | Add error to report. |
| `add_warning` | `def add_warning(self, warning: str) -> None` |  | Add warning to report. |
| `has_errors` | `def has_errors(self) -> bool` |  | Check if report has errors. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize report. |
| `to_exception` | `def to_exception(self) -> RegistryError` |  | Convert report to exception. |
| `format_report` | `def format_report(self) -> str` |  | Format report for display. |

### Class: `FingerprintGenerator`

- Source: `aquilia/aquilary/fingerprint.py`
- Bases: `object`
- Summary: Generates deterministic fingerprints for registry state.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `generate` | `def generate(self, app_contexts: list[Any], config: Any, mode: Any) -> str` |  | Generate fingerprint from registry state. |
| `generate_with_metadata` | `def generate_with_metadata(self, app_contexts: list[Any], config: Any, mode: Any) -> dict[str, Any]` |  | Generate fingerprint with metadata. |
| `verify_fingerprint` | `def verify_fingerprint(self, expected: str, app_contexts: list[Any], config: Any, mode: Any) -> bool` |  | Verify current state matches expected fingerprint. |
| `diff_fingerprints` | `def diff_fingerprints(self, expected_contexts: list[Any], actual_contexts: list[Any], config: Any, mode: Any) -> dict[str, Any]` |  | Compute diff between expected and actual registry state. |

### Class: `GraphNode`

- Source: `aquilia/aquilary/graph.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Dependency graph node.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `dependencies` | `list[str]` | `field(default_factory=list)` |
| `index` | `int &#124; None` | `None` |
| `lowlink` | `int &#124; None` | `None` |
| `on_stack` | `bool` | `False` |

### Class: `DependencyGraph`

- Source: `aquilia/aquilary/graph.py`
- Bases: `object`
- Summary: Dependency graph with cycle detection and topological sorting.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `add_node` | `def add_node(self, name: str, dependencies: list[str]) -> None` |  | Add node to graph. |
| `topological_sort` | `def topological_sort(self) -> list[str]` |  | Compute topological sort of graph (dependency order). |
| `find_cycle` | `def find_cycle(self) -> list[str] &#124; None` |  | Find cycle in graph using Tarjan's algorithm. |
| `get_dependencies` | `def get_dependencies(self, node_name: str) -> list[str]` |  | Get direct dependencies of node. |
| `get_transitive_dependencies` | `def get_transitive_dependencies(self, node_name: str) -> set[str]` |  | Get transitive closure of dependencies. |
| `get_dependents` | `def get_dependents(self, node_name: str) -> list[str]` |  | Get nodes that depend on given node (reverse dependencies). |
| `to_dict` | `def to_dict(self) -> dict[str, list[str]]` |  | Export graph as adjacency dict. |
| `to_dot` | `def to_dot(self) -> str` |  | Export graph as DOT format for visualization. |
| `get_load_order` | `def get_load_order(self) -> list[str]` |  | Get load order (topological sort). |
| `validate` | `def validate(self) -> tuple[bool, list[str] &#124; None]` |  | Validate graph for cycles. |
| `get_roots` | `def get_roots(self) -> list[str]` |  | Get root nodes (no dependencies). |
| `get_leaves` | `def get_leaves(self) -> list[str]` |  | Get leaf nodes (no dependents). |
| `get_layers` | `def get_layers(self) -> list[list[str]]` |  | Get dependency layers (parallel execution groups). |

### Class: `DIInjectionError`

- Source: `aquilia/aquilary/handler_wrapper.py`
- Bases: `Exception`
- Summary: Raised when dependency injection fails.

### Class: `HandlerWrapper`

- Source: `aquilia/aquilary/handler_wrapper.py`
- Bases: `object`
- Summary: Wraps controller handlers to inject dependencies from DI container.

### Class: `ManifestSource`

- Source: `aquilia/aquilary/loader.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Manifest source descriptor.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `type` | `str` |  |
| `value` | `Any` |  |
| `origin` | `str` |  |

### Class: `ManifestLoader`

- Source: `aquilia/aquilary/loader.py`
- Bases: `object`
- Summary: Safe manifest loader that NEVER triggers import-time side effects.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `load_manifests` | `def load_manifests(self, sources: list[type &#124; str], *, allow_fs_autodiscovery: bool = False) -> list[Any]` |  | Load manifests from sources. |

### Class: `RouteInfo`

- Source: `aquilia/aquilary/route_compiler.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Information about a single route.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `pattern` | `str` |  |
| `method` | `str` |  |
| `handler` | `Any` |  |
| `controller_class` | `type` |  |
| `flow` | `Any` |  |
| `metadata` | `dict[str, Any]` |  |

### Class: `RouteTable`

- Source: `aquilia/aquilary/route_compiler.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Compiled routing table.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `routes` | `list[RouteInfo]` |  |
| `patterns` | `dict[str, RouteInfo]` |  |
| `conflicts` | `list[tuple[RouteInfo, RouteInfo]]` |  |

### Class: `RouteConflictError`

- Source: `aquilia/aquilary/route_compiler.py`
- Bases: `Exception`
- Summary: Raised when route patterns conflict.

### Class: `RouteCompiler`

- Source: `aquilia/aquilary/route_compiler.py`
- Bases: `object`
- Summary: Compiles routes from controller classes.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `compile_controller` | `def compile_controller(self, controller_path: str, config: Any = None) -> list[RouteInfo]` |  | Compile routes from a controller module or class. |
| `compile_from_manifests` | `def compile_from_manifests(self, manifests: list[dict[str, Any]], config: Any = None) -> RouteTable` |  | Compile routes from app manifests. |
| `validate_routes` | `def validate_routes(self) -> list[str]` |  | Validate compiled routes. |
| `get_route_count` | `def get_route_count(self) -> int` |  | Get total number of routes. |
| `get_routes_by_method` | `def get_routes_by_method(self, method: str) -> list[RouteInfo]` |  | Get all routes for a specific HTTP method. |
| `get_routes_by_pattern` | `def get_routes_by_pattern(self, pattern: str) -> list[RouteInfo]` |  | Get all routes matching a pattern. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Export route table as dictionary. |

### Class: `RegistryValidator`

- Source: `aquilia/aquilary/validator.py`
- Bases: `object`
- Summary: Validates registry manifests and configuration.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate_manifests` | `def validate_manifests(self, manifests: list[Any], config: Any) -> ValidationReport` |  | Validate all manifests. |
| `validate_hot_reload` | `def validate_hot_reload(self, old_manifests: list[Any], new_manifests: list[Any]) -> ValidationReport` |  | Validate hot-reload is safe. |

## Functions

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `load_config` | `aquilia/aquilary/cli.py` | `def load_config(config_path: str &#124; None) -> Any` | Load config from Python file. |
| `cmd_validate` | `aquilia/aquilary/cli.py` | `def cmd_validate(args: argparse.Namespace) -> None` | Validate manifests. |
| `cmd_inspect` | `aquilia/aquilary/cli.py` | `def cmd_inspect(args: argparse.Namespace) -> None` | Inspect registry and show diagnostics. |
| `cmd_freeze` | `aquilia/aquilary/cli.py` | `def cmd_freeze(args: argparse.Namespace) -> None` | Freeze manifest for reproducible deploys. |
| `cmd_graph` | `aquilia/aquilary/cli.py` | `def cmd_graph(args: argparse.Namespace) -> None` | Visualize dependency graph. |
| `cmd_run` | `aquilia/aquilary/cli.py` | `def cmd_run(args: argparse.Namespace) -> None` | Run application with registry. |
| `main` | `aquilia/aquilary/cli.py` | `def main()` | Main CLI entry point. |
| `wrap_handler` | `aquilia/aquilary/handler_wrapper.py` | `def wrap_handler(handler: Callable, controller_class: type) -> HandlerWrapper` | Wrap a controller handler for dependency injection. |
| `inject_dependencies` | `aquilia/aquilary/handler_wrapper.py` | `def inject_dependencies(handler: Callable) -> Callable` | Decorator to enable dependency injection for a handler. |

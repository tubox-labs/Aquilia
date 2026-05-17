# Discovery API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/discovery/__init__.py` | 51 | 0 | 0 | Aquilia Discovery - Component auto-discovery subsystem. |
| `aquilia/discovery/engine.py` | 696 | 9 | 0 | Auto-Discovery Engine -- AST-based component classification and manifest sync. |

## Public Exports

`ASTClassifier`, `AutoDiscoveryEngine`, `ClassifiedComponent`, `DiscoveryResult`, `FileScanner`, `ManifestDiffer`, `ManifestWriter`, `PackageScanner`, `SyncAction`, `SyncReport`

## Public Class Summary

| Class | Source | Bases | Summary |
| --- | --- | --- | --- |
| `ClassifiedComponent` | `aquilia/discovery/engine.py` | object | A component discovered by the AST classifier. |
| `DiscoveryResult` | `aquilia/discovery/engine.py` | object | Result of scanning a single module. |
| `SyncAction` | `aquilia/discovery/engine.py` | object | Describes a change to make to a manifest file. |
| `SyncReport` | `aquilia/discovery/engine.py` | object | Report from a manifest sync operation. |
| `ASTClassifier` | `aquilia/discovery/engine.py` | object | Classifies Python classes using AST analysis -- no imports needed. |
| `FileScanner` | `aquilia/discovery/engine.py` | object | Scans module directories for Python files matching discovery patterns. |
| `ManifestDiffer` | `aquilia/discovery/engine.py` | object | Compares discovered components against declared manifest components. |
| `ManifestWriter` | `aquilia/discovery/engine.py` | object | Safely updates manifest.py files using text manipulation. |
| `AutoDiscoveryEngine` | `aquilia/discovery/engine.py` | object | Scans module directories for components and syncs manifest.py files. |

## Detailed Classes And Methods

### `ClassifiedComponent`

- Source: `aquilia/discovery/engine.py`
- Bases: `object`
- Summary: A component discovered by the AST classifier.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `kind` | `ComponentKind` | `` |
| `file_path` | `Path` | `` |
| `line` | `int` | `` |
| `import_path` | `str` | `''` |
| `bases` | `list[str]` | `field(default_factory=list)` |
| `decorators` | `list[str]` | `field(default_factory=list)` |

### `DiscoveryResult`

- Source: `aquilia/discovery/engine.py`
- Bases: `object`
- Summary: Result of scanning a single module.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `module_name` | `str` | `` |
| `components` | `list[ClassifiedComponent]` | `field(default_factory=list)` |
| `errors` | `list[str]` | `field(default_factory=list)` |
| `files_scanned` | `int` | `0` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `controllers` | `def controllers(self)` |  |
| `services` | `def services(self)` |  |
| `middleware` | `def middleware(self)` |  |
| `guards` | `def guards(self)` |  |
| `models` | `def models(self)` |  |
| `pipes` | `def pipes(self)` |  |
| `interceptors` | `def interceptors(self)` |  |

### `SyncAction`

- Source: `aquilia/discovery/engine.py`
- Bases: `object`
- Summary: Describes a change to make to a manifest file.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `action` | `str` | `` |
| `component` | `ClassifiedComponent` | `` |
| `field_name` | `str` | `` |

### `SyncReport`

- Source: `aquilia/discovery/engine.py`
- Bases: `object`
- Summary: Report from a manifest sync operation.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `module_name` | `str` | `` |
| `manifest_path` | `Path` | `` |
| `actions` | `list[SyncAction]` | `field(default_factory=list)` |
| `dry_run` | `bool` | `False` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `added` | `def added(self)` |  |
| `has_changes` | `def has_changes(self)` |  |

### `ASTClassifier`

- Source: `aquilia/discovery/engine.py`
- Bases: `object`
- Summary: Classifies Python classes using AST analysis -- no imports needed.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `CONTROLLER_BASES` | `set[str]` | `{'Controller', 'BaseController', 'RestController'}` |
| `SOCKET_CONTROLLER_BASES` | `set[str]` | `{'WebSocketController', 'SocketController'}` |
| `SERVICE_BASES` | `set[str]` | `{'Service', 'BaseService'}` |
| `MIDDLEWARE_BASES` | `set[str]` | `{'Middleware', 'BaseMiddleware'}` |
| `GUARD_BASES` | `set[str]` | `{'Guard', 'BaseGuard', 'AuthGuard'}` |
| `PIPE_BASES` | `set[str]` | `{'Pipe', 'BasePipe', 'ValidationPipe', 'TransformPipe'}` |
| `INTERCEPTOR_BASES` | `set[str]` | `{'Interceptor', 'BaseInterceptor', 'LoggingInterceptor', 'CacheInterceptor'}` |
| `MODEL_BASES` | `set[str]` | `{'Model', 'BaseModel', 'AquiliaModel'}` |
| `SERVICE_DECORATORS` | `set[str]` | `{'service', 'injectable', 'provides', 'provider'}` |
| `GUARD_DECORATORS` | `set[str]` | `{'guard', 'auth_guard'}` |
| `PIPE_DECORATORS` | `set[str]` | `{'pipe', 'transform', 'validate'}` |
| `INTERCEPTOR_DECORATORS` | `set[str]` | `{'interceptor', 'intercept'}` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `classify_file` | `def classify_file(self, file_path: Path)` | Parse a Python file with AST and classify its classes. |

### `FileScanner`

- Source: `aquilia/discovery/engine.py`
- Bases: `object`
- Summary: Scans module directories for Python files matching discovery patterns.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `SKIP_FILES` | `set[str]` | `{'__init__.py', '__pycache__', 'manifest.py', 'conftest.py', 'setup.py', 'workspace.py'}` |
| `SKIP_PREFIXES` | `tuple[str, ...]` | `('test_', '_', '.')` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `scan_module` | `def scan_module(self, module_name: str, patterns: list[str] \| None=None)` | Find all Python files in a module directory. |
| `discover_modules` | `def discover_modules(self)` | Discover all module directories (contain __init__.py or manifest.py). |

### `ManifestDiffer`

- Source: `aquilia/discovery/engine.py`
- Bases: `object`
- Summary: Compares discovered components against declared manifest components.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `KIND_TO_FIELD` | `` | `{ComponentKind.CONTROLLER: 'controllers', ComponentKind.SERVICE: 'services', ComponentKind.MIDDLEWARE: 'middleware', ComponentKind.GUARD: 'guards', ComponentKind.PIPE: 'pipes', ComponentKind.INTERCEPTOR: 'interceptors', ComponentKind.MODEL: 'models', ComponentKind.SOCKET_CONTROLLER: 'socket_controllers', ComponentKind.SERIALIZER: 'serializers'}` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `diff` | `def diff(self, discovered: list[ClassifiedComponent], manifest_refs: dict[str, list[str]])` | Calculate actions needed to sync manifest with discovered components. |

### `ManifestWriter`

- Source: `aquilia/discovery/engine.py`
- Bases: `object`
- Summary: Safely updates manifest.py files using text manipulation.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `write_sync_actions` | `def write_sync_actions(self, manifest_path: Path, actions: list[SyncAction], dry_run: bool=False)` | Apply sync actions to a manifest file. |

### `AutoDiscoveryEngine`

- Source: `aquilia/discovery/engine.py`
- Bases: `object`
- Summary: Scans module directories for components and syncs manifest.py files.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `discover` | `def discover(self, module_name: str, patterns: list[str] \| None=None)` | Discover all components in a module directory. |
| `discover_all` | `def discover_all(self)` | Discover components in all modules. |
| `sync_manifest` | `def sync_manifest(self, module_name: str, dry_run: bool=False)` | Sync discovered components into the module's manifest.py. |
| `sync_all` | `def sync_all(self, dry_run: bool=False)` | Sync manifests for all discovered modules. |

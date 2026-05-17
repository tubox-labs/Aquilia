# Discovery API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
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

## Public Function Summary

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| None detected |  |  |  |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| None detected |  |  |

## Detailed Classes And Methods

### Class: `ClassifiedComponent`

- Source: `aquilia/discovery/engine.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A component discovered by the AST classifier.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `kind` | `ComponentKind` |  |
| `file_path` | `Path` |  |
| `line` | `int` |  |
| `import_path` | `str` | `''` |
| `bases` | `list[str]` | `field(default_factory=list)` |
| `decorators` | `list[str]` | `field(default_factory=list)` |

### Class: `DiscoveryResult`

- Source: `aquilia/discovery/engine.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Result of scanning a single module.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `module_name` | `str` |  |
| `components` | `list[ClassifiedComponent]` | `field(default_factory=list)` |
| `errors` | `list[str]` | `field(default_factory=list)` |
| `files_scanned` | `int` | `0` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `controllers` | `def controllers(self) -> list[ClassifiedComponent]` | property | Method. |
| `services` | `def services(self) -> list[ClassifiedComponent]` | property | Method. |
| `middleware` | `def middleware(self) -> list[ClassifiedComponent]` | property | Method. |
| `guards` | `def guards(self) -> list[ClassifiedComponent]` | property | Method. |
| `models` | `def models(self) -> list[ClassifiedComponent]` | property | Method. |
| `pipes` | `def pipes(self) -> list[ClassifiedComponent]` | property | Method. |
| `interceptors` | `def interceptors(self) -> list[ClassifiedComponent]` | property | Method. |

### Class: `SyncAction`

- Source: `aquilia/discovery/engine.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Describes a change to make to a manifest file.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `action` | `str` |  |
| `component` | `ClassifiedComponent` |  |
| `field_name` | `str` |  |

### Class: `SyncReport`

- Source: `aquilia/discovery/engine.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Report from a manifest sync operation.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `module_name` | `str` |  |
| `manifest_path` | `Path` |  |
| `actions` | `list[SyncAction]` | `field(default_factory=list)` |
| `dry_run` | `bool` | `False` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `added` | `def added(self) -> list[SyncAction]` | property | Method. |
| `has_changes` | `def has_changes(self) -> bool` | property | Method. |

### Class: `ASTClassifier`

- Source: `aquilia/discovery/engine.py`
- Bases: `object`
- Summary: Classifies Python classes using AST analysis -- no imports needed.

Attributes and fields:

| Name | Type | Default |
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

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `classify_file` | `def classify_file(self, file_path: Path) -> list[ClassifiedComponent]` |  | Parse a Python file with AST and classify its classes. |

### Class: `FileScanner`

- Source: `aquilia/discovery/engine.py`
- Bases: `object`
- Summary: Scans module directories for Python files matching discovery patterns.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `SKIP_FILES` | `set[str]` | `{'__init__.py', '__pycache__', 'manifest.py', 'conftest.py', 'setup.py', 'workspace.py'}` |
| `SKIP_PREFIXES` | `tuple[str, ...]` | `('test_', '_', '.')` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `scan_module` | `def scan_module(self, module_name: str, patterns: list[str] &#124; None = None) -> list[Path]` |  | Find all Python files in a module directory. |
| `discover_modules` | `def discover_modules(self) -> list[str]` |  | Discover all module directories (contain __init__.py or manifest.py). |

### Class: `ManifestDiffer`

- Source: `aquilia/discovery/engine.py`
- Bases: `object`
- Summary: Compares discovered components against declared manifest components.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `KIND_TO_FIELD` |  | `{ComponentKind.CONTROLLER: 'controllers', ComponentKind.SERVICE: 'services', ComponentKind.MIDDLEWARE: 'middleware', Com` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `diff` | `def diff(self, discovered: list[ClassifiedComponent], manifest_refs: dict[str, list[str]]) -> list[SyncAction]` |  | Calculate actions needed to sync manifest with discovered components. |

### Class: `ManifestWriter`

- Source: `aquilia/discovery/engine.py`
- Bases: `object`
- Summary: Safely updates manifest.py files using text manipulation.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `write_sync_actions` | `def write_sync_actions(self, manifest_path: Path, actions: list[SyncAction], dry_run: bool = False) -> int` |  | Apply sync actions to a manifest file. |

### Class: `AutoDiscoveryEngine`

- Source: `aquilia/discovery/engine.py`
- Bases: `object`
- Summary: Scans module directories for components and syncs manifest.py files.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `discover` | `def discover(self, module_name: str, patterns: list[str] &#124; None = None) -> DiscoveryResult` |  | Discover all components in a module directory. |
| `discover_all` | `def discover_all(self) -> dict[str, DiscoveryResult]` |  | Discover components in all modules. |
| `sync_manifest` | `def sync_manifest(self, module_name: str, dry_run: bool = False) -> SyncReport` |  | Sync discovered components into the module's manifest.py. |
| `sync_all` | `def sync_all(self, dry_run: bool = False) -> list[SyncReport]` |  | Sync manifests for all discovered modules. |

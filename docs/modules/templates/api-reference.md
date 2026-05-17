# Templates API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
| --- | --- | --- | --- |
| `IdentityTemplateProxy` | `aquilia/templates/auth_integration.py` | object | Proxy object for safe identity access in templates. |
| `TemplateAuthGuard` | `aquilia/templates/auth_integration.py` | object | Guard to ensure templates have auth context. |
| `TemplateAuthMixin` | `aquilia/templates/auth_integration.py` | object | Mixin for controllers with auth-aware template rendering. |
| `BytecodeCache` | `aquilia/templates/bytecode_cache.py` | Jinja2BytecodeCache | Abstract base for bytecode caching. |
| `InMemoryBytecodeCache` | `aquilia/templates/bytecode_cache.py` | BytecodeCache | In-memory bytecode cache. |
| `CrousBytecodeCache` | `aquilia/templates/bytecode_cache.py` | BytecodeCache | Crous artifact-backed bytecode cache. |
| `RedisBytecodeCache` | `aquilia/templates/bytecode_cache.py` | BytecodeCache | Redis-backed bytecode cache for high-throughput deployments. |
| `TemplateContext` | `aquilia/templates/context.py` | object | Template rendering context. |
| `TemplateLoaderProvider` | `aquilia/templates/di_providers.py` | object | Provider for TemplateLoader with auto-discovered paths. |
| `BytecodeCacheProvider` | `aquilia/templates/di_providers.py` | object | Provider for bytecode cache with strategy selection. |
| `TemplateSandboxProvider` | `aquilia/templates/di_providers.py` | object | Provider for template sandbox with security policies. |
| `TemplateEngineProvider` | `aquilia/templates/di_providers.py` | object | Provider for TemplateEngine with full DI integration. |
| `TemplateManagerProvider` | `aquilia/templates/di_providers.py` | object | Provider for TemplateManager (compile/lint/inspect tools). |
| `TemplateEngine` | `aquilia/templates/engine.py` | object | Async-capable Jinja2 template engine. |
| `StaticTagExtension` | `aquilia/templates/extensions.py` | Extension | Provide first-class Aquilia asset tags for templates. |
| `TemplateFault` | `aquilia/templates/faults.py` | Fault | Base fault for the template subsystem. |
| `TemplateEngineUnavailableFault` | `aquilia/templates/faults.py` | TemplateFault | Template engine not available. |
| `TemplateCacheIntegrityFault` | `aquilia/templates/faults.py` | TemplateFault | Bytecode cache integrity check failed. |
| `TemplateSanitizationWarning` | `aquilia/templates/faults.py` | TemplateFault | HTML sanitization used regex-based implementation. |
| `TemplateLoader` | `aquilia/templates/loader.py` | BaseLoader | Namespace-aware template loader. |
| `PackageLoader` | `aquilia/templates/loader.py` | Jinja2PackageLoader | Package loader for library-embedded templates. |
| `TemplateLintIssue` | `aquilia/templates/manager.py` | object | Template lint issue. |
| `TemplateMetadata` | `aquilia/templates/manager.py` | object | Template metadata for compilation. |
| `TemplateManager` | `aquilia/templates/manager.py` | object | Template compilation and management. |
| `TemplateManifestConfig` | `aquilia/templates/manifest_integration.py` | object | Configuration for templates from manifest file. |
| `ModuleTemplateRegistry` | `aquilia/templates/manifest_integration.py` | object | Registry mapping module names to template directories. |
| `TemplateMiddleware` | `aquilia/templates/middleware.py` | object | Template context injection middleware. |
| `SandboxPolicy` | `aquilia/templates/security.py` | object | Template sandbox security policy. |
| `TemplateSandbox` | `aquilia/templates/security.py` | object | Template sandbox manager. |
| `SessionTemplateProxy` | `aquilia/templates/sessions_integration.py` | object | Proxy object for session access in templates. |
| `FlashMessages` | `aquilia/templates/sessions_integration.py` | object | Flash message manager for templates. |
| `TemplateFlashMixin` | `aquilia/templates/sessions_integration.py` | object | Mixin for controllers to add flash messages. |

## Public Function Summary

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `create_auth_helpers` | `aquilia/templates/auth_integration.py` | `def create_auth_helpers(identity: Optional['Identity'] = None, authz_engine: Optional['AuthzEngine'] = None)` | Create auth helper functions for templates. |
| `enhance_engine_with_auth` | `aquilia/templates/auth_integration.py` | `def enhance_engine_with_auth(engine: 'TemplateEngine', auth_manager: Optional['AuthManager'] = None, authz_engine: Optional['AuthzEngine'] = None) -> None` | Enhance template engine with auth integration. |
| `inject_auth_context` | `aquilia/templates/auth_integration.py` | `def inject_auth_context(context: dict[str, Any], request_ctx: Optional['RequestCtx'] = None, authz_engine: Optional['AuthzEngine'] = None) -> None` | Inject auth variables into template context. |
| `create_template_engine_from_config` | `aquilia/templates/cli.py` | `def create_template_engine_from_config(template_dirs: list[str], cache_dir: str = 'artifacts', sandbox: bool = True, mode: str = 'prod') -> TemplateEngine` | Create template engine from configuration. |
| `cmd_compile` | `aquilia/templates/cli.py` | `async def cmd_compile(template_dirs: list[str] &#124; None = None, output: str = 'artifacts/templates.crous', mode: str = 'prod', verbose: bool = False)` | Compile all templates to crous artifact. |
| `cmd_lint` | `aquilia/templates/cli.py` | `async def cmd_lint(template_dirs: list[str] &#124; None = None, strict: bool = True, json_output: bool = False, verbose: bool = False)` | Lint all templates. |
| `cmd_inspect` | `aquilia/templates/cli.py` | `async def cmd_inspect(template_name: str, template_dirs: list[str] &#124; None = None, verbose: bool = False)` | Inspect template metadata. |
| `cmd_clear_cache` | `aquilia/templates/cli.py` | `async def cmd_clear_cache(template_name: str &#124; None = None, cache_dir: str = 'artifacts', all_caches: bool = False, verbose: bool = False)` | Clear template cache. |
| `compile_command` | `aquilia/templates/cli.py` | `def compile_command(args)` | Entry point for `aq templates compile`. |
| `lint_command` | `aquilia/templates/cli.py` | `def lint_command(args)` | Entry point for `aq templates lint`. |
| `inspect_command` | `aquilia/templates/cli.py` | `def inspect_command(args)` | Entry point for `aq templates inspect`. |
| `clear_cache_command` | `aquilia/templates/cli.py` | `def clear_cache_command(args)` | Entry point for `aq templates clear-cache`. |
| `create_template_context` | `aquilia/templates/context.py` | `def create_template_context(user_context: dict[str, Any] &#124; None = None, request_ctx: Optional['RequestCtx'] = None, **extras) -> TemplateContext` | Create template context from request context and user variables. |
| `inject_url_helpers` | `aquilia/templates/context.py` | `def inject_url_helpers(context: dict[str, Any], url_for_func: Any) -> None` | Inject URL generation helpers into context. |
| `inject_static_helper` | `aquilia/templates/context.py` | `def inject_static_helper(context: dict[str, Any], static_func: Any) -> None` | Inject static asset URL helper into context. |
| `inject_csp_nonce` | `aquilia/templates/context.py` | `def inject_csp_nonce(context: dict[str, Any], nonce: str) -> None` | Inject CSP nonce into context. |
| `inject_csrf_token` | `aquilia/templates/context.py` | `def inject_csrf_token(context: dict[str, Any], token: str &#124; None = None) -> None` | Inject CSRF token into context. |
| `inject_config` | `aquilia/templates/context.py` | `def inject_config(context: dict[str, Any], config: Any) -> None` | Inject safe config subset into context. |
| `inject_i18n` | `aquilia/templates/context.py` | `def inject_i18n(context: dict[str, Any], gettext_func: Any = None) -> None` | Inject internationalization helpers into context. |
| `register_template_providers` | `aquilia/templates/di_providers.py` | `def register_template_providers(container, engine: TemplateEngine &#124; None = None) -> None` | Register all template providers with DI container. |
| `create_development_engine` | `aquilia/templates/di_providers.py` | `def create_development_engine(loader: TemplateLoader, config: Config &#124; None = None) -> TemplateEngine` | Factory for development template engine: |
| `create_production_engine` | `aquilia/templates/di_providers.py` | `def create_production_engine(loader: TemplateLoader, bytecode_cache: BytecodeCache, config: Config &#124; None = None) -> TemplateEngine` | Factory for production template engine: |
| `create_testing_engine` | `aquilia/templates/di_providers.py` | `def create_testing_engine(search_paths: list[Path] &#124; None = None) -> TemplateEngine` | Factory for testing template engine: |
| `discover_template_directories` | `aquilia/templates/manifest_integration.py` | `def discover_template_directories(root_path: Path &#124; None = None, scan_manifests: bool = True) -> list[Path]` | Discover template directories in project. |
| `discover_from_manifests` | `aquilia/templates/manifest_integration.py` | `def discover_from_manifests(root_path: Path) -> list[Path]` | Discover template directories from module.aq manifest files. |
| `should_precompile_module` | `aquilia/templates/manifest_integration.py` | `def should_precompile_module(manifest_path: Path) -> bool` | Check if module templates should be precompiled. |
| `get_cache_strategy` | `aquilia/templates/manifest_integration.py` | `def get_cache_strategy(manifest_path: Path) -> str` | Get cache strategy from manifest. |
| `generate_template_manifest` | `aquilia/templates/manifest_integration.py` | `def generate_template_manifest(template_dirs: list[Path], output_path: Path) -> None` | Generate template manifest for crous artifacts. |
| `create_manifest_aware_loader` | `aquilia/templates/manifest_integration.py` | `def create_manifest_aware_loader(root_path: Path &#124; None = None, scan_manifests: bool = True)` | Create TemplateLoader with manifest-based auto-discovery. |
| `create_module_registry` | `aquilia/templates/manifest_integration.py` | `def create_module_registry(root_path: Path &#124; None = None) -> ModuleTemplateRegistry` | Create and populate module template registry. |
| `create_safe_globals` | `aquilia/templates/security.py` | `def create_safe_globals() -> dict[str, Any]` | Create dictionary of safe global functions for templates. |
| `create_safe_filters` | `aquilia/templates/security.py` | `def create_safe_filters() -> dict[str, Callable]` | Create dictionary of safe custom filters. |
| `enhance_engine_with_sessions` | `aquilia/templates/sessions_integration.py` | `def enhance_engine_with_sessions(engine: 'TemplateEngine', session_engine: Optional['SessionEngine'] = None) -> None` | Enhance template engine with session integration. |
| `inject_session_context` | `aquilia/templates/sessions_integration.py` | `def inject_session_context(context: dict[str, Any], request_ctx: Optional['RequestCtx'] = None) -> None` | Inject session variables into template context. |
| `enhance_middleware_with_sessions` | `aquilia/templates/sessions_integration.py` | `def enhance_middleware_with_sessions()` | Enhance TemplateMiddleware with session context injection. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `TEMPLATE_COMMANDS` | `aquilia/templates/cli.py` | `{'compile': compile_command, 'lint': lint_command, 'inspect': inspect_command, 'clear-cache': clear_cache_command}` |
| `TEMPLATE_DOMAIN` | `aquilia/templates/faults.py` | `FaultDomain.custom('template', 'Template engine faults')` |

## Detailed Classes And Methods

### Class: `IdentityTemplateProxy`

- Source: `aquilia/templates/auth_integration.py`
- Bases: `object`
- Summary: Proxy object for safe identity access in templates.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `id` | `def id(self) -> str &#124; None` | property | Get identity ID. |
| `username` | `def username(self) -> str &#124; None` | property | Get username. |
| `email` | `def email(self) -> str &#124; None` | property | Get email. |
| `display_name` | `def display_name(self) -> str &#124; None` | property | Get display name. |
| `roles` | `def roles(self) -> set[str]` | property | Get roles set. |
| `has_role` | `def has_role(self, role: str) -> bool` |  | Check if identity has role. |
| `has_any_role` | `def has_any_role(self, *roles: str) -> bool` |  | Check if identity has any of the given roles. |
| `has_all_roles` | `def has_all_roles(self, *roles: str) -> bool` |  | Check if identity has all given roles. |
| `is_admin` | `def is_admin(self) -> bool` | property | Check if identity has admin role. |
| `is_verified` | `def is_verified(self) -> bool` | property | Check if identity is verified. |
| `get` | `def get(self, key: str, default: Any = None) -> Any` |  | Get identity attribute by key. |

### Class: `TemplateAuthGuard`

- Source: `aquilia/templates/auth_integration.py`
- Bases: `object`
- Summary: Guard to ensure templates have auth context.

### Class: `TemplateAuthMixin`

- Source: `aquilia/templates/auth_integration.py`
- Bases: `object`
- Summary: Mixin for controllers with auth-aware template rendering.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `render_with_auth` | `def render_with_auth(self, ctx: 'RequestCtx', template: str, user_context: dict[str, Any] &#124; None = None, **kwargs)` |  | Render template with auth context injected. |
| `require_role` | `def require_role(self, ctx: 'RequestCtx', role: str) -> None` |  | Ensure current user has role. |

### Class: `BytecodeCache`

- Source: `aquilia/templates/bytecode_cache.py`
- Bases: `Jinja2BytecodeCache`
- Summary: Abstract base for bytecode caching.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `load_bytecode_async` | `async def load_bytecode_async(self, key: str) -> bytes &#124; None` |  | Load bytecode asynchronously (optional optimization). |
| `store_bytecode_async` | `async def store_bytecode_async(self, key: str, data: bytes) -> None` |  | Store bytecode asynchronously (optional optimization). |
| `clear_async` | `async def clear_async(self) -> None` |  | Clear cache asynchronously. |

### Class: `InMemoryBytecodeCache`

- Source: `aquilia/templates/bytecode_cache.py`
- Bases: `BytecodeCache`
- Summary: In-memory bytecode cache.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `load_bytecode` | `def load_bytecode(self, bucket: Bucket) -> None` |  | Load bytecode from cache. |
| `dump_bytecode` | `def dump_bytecode(self, bucket: Bucket) -> None` |  | Store bytecode in cache. |
| `clear` | `def clear(self) -> None` |  | Clear all cached bytecode. |
| `invalidate` | `def invalidate(self, key: str) -> None` |  | Invalidate specific template cache. |

### Class: `CrousBytecodeCache`

- Source: `aquilia/templates/bytecode_cache.py`
- Bases: `BytecodeCache`
- Summary: Crous artifact-backed bytecode cache.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `load_bytecode` | `def load_bytecode(self, bucket: Bucket) -> None` |  | Load bytecode from cache. |
| `dump_bytecode` | `def dump_bytecode(self, bucket: Bucket) -> None` |  | Store bytecode in cache. |
| `clear` | `def clear(self) -> None` |  | Clear all cached bytecode. |
| `invalidate` | `def invalidate(self, key: str) -> None` |  | Invalidate specific template cache. |
| `save` | `def save(self) -> None` |  | Persist cache to disk. |

### Class: `RedisBytecodeCache`

- Source: `aquilia/templates/bytecode_cache.py`
- Bases: `BytecodeCache`
- Summary: Redis-backed bytecode cache for high-throughput deployments.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `load_bytecode` | `def load_bytecode(self, bucket: Bucket) -> None` |  | Load bytecode from Redis (sync wrapper). |
| `dump_bytecode` | `def dump_bytecode(self, bucket: Bucket) -> None` |  | Store bytecode in Redis (sync wrapper). |
| `load_bytecode_async` | `async def load_bytecode_async(self, key: str) -> bytes &#124; None` |  | Load bytecode from Redis asynchronously. |
| `store_bytecode_async` | `async def store_bytecode_async(self, key: str, data: bytes) -> None` |  | Store bytecode in Redis asynchronously. |
| `clear` | `def clear(self) -> None` |  | Clear all cached bytecode. |
| `clear_async` | `async def clear_async(self) -> None` |  | Clear all cached bytecode asynchronously. |

### Class: `TemplateContext`

- Source: `aquilia/templates/context.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Template rendering context.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `user_context` | `dict[str, Any]` | `field(default_factory=dict)` |
| `request` | `Optional['Request']` | `None` |
| `session` | `Optional['Session']` | `None` |
| `identity` | `Optional['Identity']` | `None` |
| `extras` | `dict[str, Any]` | `field(default_factory=dict)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Convert to flat dictionary for Jinja2 rendering. |

### Class: `TemplateLoaderProvider`

- Source: `aquilia/templates/di_providers.py`
- Bases: `object`
- Decorators: `service`
- Summary: Provider for TemplateLoader with auto-discovered paths.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `provide` | `def provide(self) -> TemplateLoader` |  | Provide TemplateLoader with configured search paths. |

### Class: `BytecodeCacheProvider`

- Source: `aquilia/templates/di_providers.py`
- Bases: `object`
- Decorators: `service`
- Summary: Provider for bytecode cache with strategy selection.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `provide` | `def provide(self) -> BytecodeCache` |  | Provide bytecode cache based on config: |

### Class: `TemplateSandboxProvider`

- Source: `aquilia/templates/di_providers.py`
- Bases: `object`
- Decorators: `service`
- Summary: Provider for template sandbox with security policies.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `provide` | `def provide(self) -> TemplateSandbox &#124; None` |  | Provide sandbox based on config: |

### Class: `TemplateEngineProvider`

- Source: `aquilia/templates/di_providers.py`
- Bases: `object`
- Decorators: `service`
- Summary: Provider for TemplateEngine with full DI integration.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `provide` | `def provide(self) -> TemplateEngine` |  | Provide fully configured TemplateEngine. |

### Class: `TemplateManagerProvider`

- Source: `aquilia/templates/di_providers.py`
- Bases: `object`
- Decorators: `service`
- Summary: Provider for TemplateManager (compile/lint/inspect tools).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `provide` | `def provide(self) -> TemplateManager` |  | Provide TemplateManager instance. |

### Class: `TemplateEngine`

- Source: `aquilia/templates/engine.py`
- Bases: `object`
- Summary: Async-capable Jinja2 template engine.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `render` | `async def render(self, template_name: str, context: Mapping[str, Any] &#124; None = None, request_ctx: Optional['RequestCtx'] = None) -> str` |  | Render template asynchronously. |
| `render_sync` | `def render_sync(self, template_name: str, context: Mapping[str, Any] &#124; None = None, request_ctx: Optional['RequestCtx'] = None) -> str` |  | Render template synchronously. |
| `stream` | `async def stream(self, template_name: str, context: Mapping[str, Any] &#124; None = None, request_ctx: Optional['RequestCtx'] = None) -> AsyncIterator[bytes]` |  | Stream template rendering. |
| `render_to_response` | `async def render_to_response(self, template_name: str, context: Mapping[str, Any] &#124; None = None, *, status: int = 200, headers: dict[str, str] &#124; None = None, content_type: str = 'text/html; charset=utf-8', request_ctx: Optional['RequestCtx'] = None) -> 'Response'` |  | Render template and return Response object. |
| `template_stream_response` | `def template_stream_response(self, template_name: str, context: Mapping[str, Any] &#124; None = None, *, status: int = 200, headers: dict[str, str] &#124; None = None, content_type: str = 'text/html; charset=utf-8', request_ctx: Optional['RequestCtx'] = None) -> 'Response'` |  | Render template as streaming response. |
| `get_template` | `def get_template(self, name: str) -> Template` |  | Get template by name. |
| `invalidate_cache` | `def invalidate_cache(self, template_name: str &#124; None = None) -> None` |  | Invalidate template cache. |
| `list_templates` | `def list_templates(self) -> list[str]` |  | List all available templates. |
| `register_filter` | `def register_filter(self, name: str, func: Callable) -> None` |  | Register custom filter. |
| `register_test` | `def register_test(self, name: str, func: Callable) -> None` |  | Register custom test. |
| `register_global` | `def register_global(self, name: str, value: Any) -> None` |  | Register global variable/function. |

### Class: `StaticTagExtension`

- Source: `aquilia/templates/extensions.py`
- Bases: `Extension`
- Summary: Provide first-class Aquilia asset tags for templates.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `tags` |  | `{'static', 'asset', 'media'}` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `parse` | `def parse(self, parser)` |  | Method. |

### Class: `TemplateFault`

- Source: `aquilia/templates/faults.py`
- Bases: `Fault`
- Summary: Base fault for the template subsystem.

### Class: `TemplateEngineUnavailableFault`

- Source: `aquilia/templates/faults.py`
- Bases: `TemplateFault`
- Summary: Template engine not available.

### Class: `TemplateCacheIntegrityFault`

- Source: `aquilia/templates/faults.py`
- Bases: `TemplateFault`
- Summary: Bytecode cache integrity check failed.

### Class: `TemplateSanitizationWarning`

- Source: `aquilia/templates/faults.py`
- Bases: `TemplateFault`
- Summary: HTML sanitization used regex-based implementation.

### Class: `TemplateLoader`

- Source: `aquilia/templates/loader.py`
- Bases: `BaseLoader`
- Summary: Namespace-aware template loader.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_source` | `def get_source(self, environment: Any, template: str) -> tuple[str, str &#124; None, Callable[[], bool] &#124; None]` |  | Load template source. |
| `list_templates` | `def list_templates(self) -> list[str]` |  | List all available templates. |

### Class: `PackageLoader`

- Source: `aquilia/templates/loader.py`
- Bases: `Jinja2PackageLoader`
- Summary: Package loader for library-embedded templates.

### Class: `TemplateLintIssue`

- Source: `aquilia/templates/manager.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Template lint issue.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `template_name` | `str` |  |
| `severity` | `str` |  |
| `message` | `str` |  |
| `code` | `str` |  |
| `line` | `int &#124; None` | `None` |
| `column` | `int &#124; None` | `None` |
| `context` | `str &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize to dictionary. |

### Class: `TemplateMetadata`

- Source: `aquilia/templates/manager.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Template metadata for compilation.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `path` | `str` |  |
| `module` | `str &#124; None` |  |
| `hash` | `str` |  |
| `size` | `int` |  |
| `mtime` | `float` |  |
| `compiled_at` | `str &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize to dictionary. |

### Class: `TemplateManager`

- Source: `aquilia/templates/manager.py`
- Bases: `object`
- Summary: Template compilation and management.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `compile_all` | `async def compile_all(self, output_path: str &#124; None = None) -> dict[str, Any]` |  | Compile all templates to crous artifact. |
| `lint_all` | `async def lint_all(self, strict_undefined: bool = True) -> list[TemplateLintIssue]` |  | Lint all templates. |
| `inspect` | `async def inspect(self, template_name: str) -> dict[str, Any]` |  | Inspect template metadata. |

### Class: `TemplateManifestConfig`

- Source: `aquilia/templates/manifest_integration.py`
- Bases: `object`
- Summary: Configuration for templates from manifest file.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `from_file` | `def from_file(cls, manifest_path: Path) -> 'TemplateManifestConfig'` | classmethod | Load from module.aq file. |

### Class: `ModuleTemplateRegistry`

- Source: `aquilia/templates/manifest_integration.py`
- Bases: `object`
- Summary: Registry mapping module names to template directories.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `register` | `def register(self, module_name: str, templates_dir: Path) -> None` |  | Register module's template directory. |
| `resolve` | `def resolve(self, module_name: str) -> Path &#124; None` |  | Resolve module name to templates directory. |
| `discover_and_register` | `def discover_and_register(self, root_path: Path &#124; None = None) -> None` |  | Auto-discover and register all module templates. |
| `to_dict` | `def to_dict(self) -> dict[str, str]` |  | Serialize registry to dictionary. |

### Class: `TemplateMiddleware`

- Source: `aquilia/templates/middleware.py`
- Bases: `object`
- Summary: Template context injection middleware.

### Class: `SandboxPolicy`

- Source: `aquilia/templates/security.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Template sandbox security policy.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `allow_unsafe_filters` | `bool` | `False` |
| `allow_unsafe_tests` | `bool` | `False` |
| `allow_unsafe_globals` | `bool` | `False` |
| `allowed_filters` | `set[str]` | `field(default_factory=lambda: {'abs', 'attr', 'batch', 'capitalize', 'center', 'default', 'dictsort', 'escape', 'filesizeformat', 'first', 'float', 'forceescape', 'format', 'groupby', 'indent', 'int', 'join', 'last', 'length', 'list', 'lower', 'map', 'max', 'min', 'pprint', 'random', 'reject', 'rejectattr', 'replace', 'reverse', 'round', 'safe', 'select', 'selectattr', 'slice', 'sort', 'string', 'striptags', 'sum', 'title', 'trim', 'truncate', 'unique', 'upper', 'urlencode', 'urlize', 'wordcount', 'wordwrap', 'xmlattr', 'format_date', 'format_currency', 'pluralize', 'sanitize_html'})` |
| `allowed_tests` | `set[str]` | `field(default_factory=lambda: {'boolean', 'callable', 'defined', 'divisibleby', 'eq', 'even', 'false', 'ge', 'gt', 'in', 'iterable', 'le', 'lower', 'lt', 'mapping', 'ne', 'none', 'number', 'odd', 'sameas', 'sequence', 'string', 'true', 'undefined', 'upper'})` |
| `allowed_globals` | `set[str]` | `field(default_factory=lambda: {'range', 'dict', 'lipsum', 'cycler', 'joiner', 'namespace', 'url_for', 'static', 'static_url', 'asset', 'asset_url', 'media', 'media_url', 'csrf_token', 'config'})` |
| `autoescape` | `bool` | `True` |
| `autoescape_extensions` | `list[str]` | `field(default_factory=lambda: ['html', 'htm', 'xml', 'xhtml'])` |
| `max_recursion_depth` | `int` | `50` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `strict` | `def strict(cls) -> 'SandboxPolicy'` | classmethod | Strict policy for production (minimal allowlist). |
| `permissive` | `def permissive(cls) -> 'SandboxPolicy'` | classmethod | Permissive policy for development (expanded allowlist). |
| `is_filter_allowed` | `def is_filter_allowed(self, name: str) -> bool` |  | Check if filter is allowed. |
| `is_test_allowed` | `def is_test_allowed(self, name: str) -> bool` |  | Check if test is allowed. |
| `is_global_allowed` | `def is_global_allowed(self, name: str) -> bool` |  | Check if global is allowed. |

### Class: `TemplateSandbox`

- Source: `aquilia/templates/security.py`
- Bases: `object`
- Summary: Template sandbox manager.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `create_environment` | `def create_environment(self, **kwargs) -> SandboxedEnvironment` |  | Create sandboxed Jinja2 environment. |
| `register_filter` | `def register_filter(self, name: str, func: Callable) -> None` |  | Register custom filter. |
| `register_test` | `def register_test(self, name: str, func: Callable) -> None` |  | Register custom test. |
| `register_global` | `def register_global(self, name: str, value: Any) -> None` |  | Register custom global. |

### Class: `SessionTemplateProxy`

- Source: `aquilia/templates/sessions_integration.py`
- Bases: `object`
- Summary: Proxy object for session access in templates.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get` | `def get(self, key: str, default: Any = None) -> Any` |  | Get session value by key. |
| `has` | `def has(self, key: str) -> bool` |  | Check if session has key. |
| `authenticated` | `def authenticated(self) -> bool` | property | Check if session is authenticated. |
| `id` | `def id(self) -> str &#124; None` | property | Get session ID. |
| `created_at` | `def created_at(self) -> str &#124; None` | property | Get session creation timestamp. |
| `expires_at` | `def expires_at(self) -> str &#124; None` | property | Get session expiration timestamp. |

### Class: `FlashMessages`

- Source: `aquilia/templates/sessions_integration.py`
- Bases: `object`
- Summary: Flash message manager for templates.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `FLASH_KEY` |  | `'_flash_messages'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_messages` | `def get_messages(self) -> list[dict[str, str]]` |  | Get and consume flash messages. |
| `peek_messages` | `def peek_messages(self) -> list[dict[str, str]]` |  | Get flash messages without consuming them. |
| `add_flash` | `def add_flash(session: 'Session', message: str, level: str = 'info') -> None` | staticmethod | Add flash message to session. |

### Class: `TemplateFlashMixin`

- Source: `aquilia/templates/sessions_integration.py`
- Bases: `object`
- Summary: Mixin for controllers to add flash messages.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `flash` | `def flash(self, ctx: 'RequestCtx', message: str, level: str = 'info') -> None` |  | Add flash message to session. |
| `flash_success` | `def flash_success(self, ctx: 'RequestCtx', message: str) -> None` |  | Flash success message. |
| `flash_error` | `def flash_error(self, ctx: 'RequestCtx', message: str) -> None` |  | Flash error message. |
| `flash_warning` | `def flash_warning(self, ctx: 'RequestCtx', message: str) -> None` |  | Flash warning message. |
| `flash_info` | `def flash_info(self, ctx: 'RequestCtx', message: str) -> None` |  | Flash info message. |

## Functions

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `create_auth_helpers` | `aquilia/templates/auth_integration.py` | `def create_auth_helpers(identity: Optional['Identity'] = None, authz_engine: Optional['AuthzEngine'] = None)` | Create auth helper functions for templates. |
| `enhance_engine_with_auth` | `aquilia/templates/auth_integration.py` | `def enhance_engine_with_auth(engine: 'TemplateEngine', auth_manager: Optional['AuthManager'] = None, authz_engine: Optional['AuthzEngine'] = None) -> None` | Enhance template engine with auth integration. |
| `inject_auth_context` | `aquilia/templates/auth_integration.py` | `def inject_auth_context(context: dict[str, Any], request_ctx: Optional['RequestCtx'] = None, authz_engine: Optional['AuthzEngine'] = None) -> None` | Inject auth variables into template context. |
| `create_template_engine_from_config` | `aquilia/templates/cli.py` | `def create_template_engine_from_config(template_dirs: list[str], cache_dir: str = 'artifacts', sandbox: bool = True, mode: str = 'prod') -> TemplateEngine` | Create template engine from configuration. |
| `cmd_compile` | `aquilia/templates/cli.py` | `async def cmd_compile(template_dirs: list[str] &#124; None = None, output: str = 'artifacts/templates.crous', mode: str = 'prod', verbose: bool = False)` | Compile all templates to crous artifact. |
| `cmd_lint` | `aquilia/templates/cli.py` | `async def cmd_lint(template_dirs: list[str] &#124; None = None, strict: bool = True, json_output: bool = False, verbose: bool = False)` | Lint all templates. |
| `cmd_inspect` | `aquilia/templates/cli.py` | `async def cmd_inspect(template_name: str, template_dirs: list[str] &#124; None = None, verbose: bool = False)` | Inspect template metadata. |
| `cmd_clear_cache` | `aquilia/templates/cli.py` | `async def cmd_clear_cache(template_name: str &#124; None = None, cache_dir: str = 'artifacts', all_caches: bool = False, verbose: bool = False)` | Clear template cache. |
| `compile_command` | `aquilia/templates/cli.py` | `def compile_command(args)` | Entry point for `aq templates compile`. |
| `lint_command` | `aquilia/templates/cli.py` | `def lint_command(args)` | Entry point for `aq templates lint`. |
| `inspect_command` | `aquilia/templates/cli.py` | `def inspect_command(args)` | Entry point for `aq templates inspect`. |
| `clear_cache_command` | `aquilia/templates/cli.py` | `def clear_cache_command(args)` | Entry point for `aq templates clear-cache`. |
| `create_template_context` | `aquilia/templates/context.py` | `def create_template_context(user_context: dict[str, Any] &#124; None = None, request_ctx: Optional['RequestCtx'] = None, **extras) -> TemplateContext` | Create template context from request context and user variables. |
| `inject_url_helpers` | `aquilia/templates/context.py` | `def inject_url_helpers(context: dict[str, Any], url_for_func: Any) -> None` | Inject URL generation helpers into context. |
| `inject_static_helper` | `aquilia/templates/context.py` | `def inject_static_helper(context: dict[str, Any], static_func: Any) -> None` | Inject static asset URL helper into context. |
| `inject_csp_nonce` | `aquilia/templates/context.py` | `def inject_csp_nonce(context: dict[str, Any], nonce: str) -> None` | Inject CSP nonce into context. |
| `inject_csrf_token` | `aquilia/templates/context.py` | `def inject_csrf_token(context: dict[str, Any], token: str &#124; None = None) -> None` | Inject CSRF token into context. |
| `inject_config` | `aquilia/templates/context.py` | `def inject_config(context: dict[str, Any], config: Any) -> None` | Inject safe config subset into context. |
| `inject_i18n` | `aquilia/templates/context.py` | `def inject_i18n(context: dict[str, Any], gettext_func: Any = None) -> None` | Inject internationalization helpers into context. |
| `register_template_providers` | `aquilia/templates/di_providers.py` | `def register_template_providers(container, engine: TemplateEngine &#124; None = None) -> None` | Register all template providers with DI container. |
| `create_development_engine` | `aquilia/templates/di_providers.py` | `def create_development_engine(loader: TemplateLoader, config: Config &#124; None = None) -> TemplateEngine` | Factory for development template engine: |
| `create_production_engine` | `aquilia/templates/di_providers.py` | `def create_production_engine(loader: TemplateLoader, bytecode_cache: BytecodeCache, config: Config &#124; None = None) -> TemplateEngine` | Factory for production template engine: |
| `create_testing_engine` | `aquilia/templates/di_providers.py` | `def create_testing_engine(search_paths: list[Path] &#124; None = None) -> TemplateEngine` | Factory for testing template engine: |
| `discover_template_directories` | `aquilia/templates/manifest_integration.py` | `def discover_template_directories(root_path: Path &#124; None = None, scan_manifests: bool = True) -> list[Path]` | Discover template directories in project. |
| `discover_from_manifests` | `aquilia/templates/manifest_integration.py` | `def discover_from_manifests(root_path: Path) -> list[Path]` | Discover template directories from module.aq manifest files. |
| `should_precompile_module` | `aquilia/templates/manifest_integration.py` | `def should_precompile_module(manifest_path: Path) -> bool` | Check if module templates should be precompiled. |
| `get_cache_strategy` | `aquilia/templates/manifest_integration.py` | `def get_cache_strategy(manifest_path: Path) -> str` | Get cache strategy from manifest. |
| `generate_template_manifest` | `aquilia/templates/manifest_integration.py` | `def generate_template_manifest(template_dirs: list[Path], output_path: Path) -> None` | Generate template manifest for crous artifacts. |
| `create_manifest_aware_loader` | `aquilia/templates/manifest_integration.py` | `def create_manifest_aware_loader(root_path: Path &#124; None = None, scan_manifests: bool = True)` | Create TemplateLoader with manifest-based auto-discovery. |
| `create_module_registry` | `aquilia/templates/manifest_integration.py` | `def create_module_registry(root_path: Path &#124; None = None) -> ModuleTemplateRegistry` | Create and populate module template registry. |
| `create_safe_globals` | `aquilia/templates/security.py` | `def create_safe_globals() -> dict[str, Any]` | Create dictionary of safe global functions for templates. |
| `create_safe_filters` | `aquilia/templates/security.py` | `def create_safe_filters() -> dict[str, Callable]` | Create dictionary of safe custom filters. |
| `enhance_engine_with_sessions` | `aquilia/templates/sessions_integration.py` | `def enhance_engine_with_sessions(engine: 'TemplateEngine', session_engine: Optional['SessionEngine'] = None) -> None` | Enhance template engine with session integration. |
| `inject_session_context` | `aquilia/templates/sessions_integration.py` | `def inject_session_context(context: dict[str, Any], request_ctx: Optional['RequestCtx'] = None) -> None` | Inject session variables into template context. |
| `enhance_middleware_with_sessions` | `aquilia/templates/sessions_integration.py` | `def enhance_middleware_with_sessions()` | Enhance TemplateMiddleware with session context injection. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `TEMPLATE_COMMANDS` | `aquilia/templates/cli.py` | `{'compile': compile_command, 'lint': lint_command, 'inspect': inspect_command, 'clear-cache': clear_cache_command}` |
| `TEMPLATE_DOMAIN` | `aquilia/templates/faults.py` | `FaultDomain.custom('template', 'Template engine faults')` |

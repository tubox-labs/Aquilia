# templates Module

## Purpose

Sandboxed Jinja2 rendering subsystem. Use this module for template engines, loaders, manifests, bytecode cache, sandbox policy, template middleware, auth and session context helpers, static tags, and CLI linting.

## Source Coverage

- Python files: 15
- Public classes: 32
- Dataclasses: 4
- Enums: 0
- Public functions: 35

## How It Fits In Aquilia

1. Import the package from `aquilia.templates` or its concrete submodules.
2. Configure it through workspace integrations, manifests, or direct service construction depending on the subsystem.
3. Keep business logic outside transport and framework glue so the subsystem stays testable.

## Practical Guidance

- Prefer typed configuration objects and framework helpers over ad hoc dictionaries when they exist.
- Use the tests in `tests/` as behavioral examples when changing this subsystem.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `IdentityTemplateProxy` | `aquilia/templates/auth_integration.py` | Proxy object for safe identity access in templates. |
| `TemplateAuthGuard` | `aquilia/templates/auth_integration.py` | Guard to ensure templates have auth context. |
| `TemplateAuthMixin` | `aquilia/templates/auth_integration.py` | Mixin for controllers with auth-aware template rendering. |
| `BytecodeCache` | `aquilia/templates/bytecode_cache.py` | Abstract base for bytecode caching. |
| `InMemoryBytecodeCache` | `aquilia/templates/bytecode_cache.py` | In-memory bytecode cache. |
| `CrousBytecodeCache` | `aquilia/templates/bytecode_cache.py` | Crous artifact-backed bytecode cache. |
| `RedisBytecodeCache` | `aquilia/templates/bytecode_cache.py` | Redis-backed bytecode cache for high-throughput deployments. |
| `TemplateContext` | `aquilia/templates/context.py` | Template rendering context. |
| `TemplateLoaderProvider` | `aquilia/templates/di_providers.py` | Provider for TemplateLoader with auto-discovered paths. |
| `BytecodeCacheProvider` | `aquilia/templates/di_providers.py` | Provider for bytecode cache with strategy selection. |
| `TemplateSandboxProvider` | `aquilia/templates/di_providers.py` | Provider for template sandbox with security policies. |
| `TemplateEngineProvider` | `aquilia/templates/di_providers.py` | Provider for TemplateEngine with full DI integration. |
| `TemplateManagerProvider` | `aquilia/templates/di_providers.py` | Provider for TemplateManager (compile/lint/inspect tools). |
| `TemplateEngine` | `aquilia/templates/engine.py` | Async-capable Jinja2 template engine. |
| `StaticTagExtension` | `aquilia/templates/extensions.py` | Provide first-class Aquilia asset tags for templates. |
| `TemplateFault` | `aquilia/templates/faults.py` | Base fault for the template subsystem. |
| `TemplateEngineUnavailableFault` | `aquilia/templates/faults.py` | Template engine not available. |
| `TemplateCacheIntegrityFault` | `aquilia/templates/faults.py` | Bytecode cache integrity check failed. |
| `TemplateSanitizationWarning` | `aquilia/templates/faults.py` | HTML sanitization used regex-based implementation. |
| `TemplateLoader` | `aquilia/templates/loader.py` | Namespace-aware template loader. |
| `PackageLoader` | `aquilia/templates/loader.py` | Package loader for library-embedded templates. |
| `TemplateLintIssue` | `aquilia/templates/manager.py` | Template lint issue. |
| `TemplateMetadata` | `aquilia/templates/manager.py` | Template metadata for compilation. |
| `TemplateManager` | `aquilia/templates/manager.py` | Template compilation and management. |
| `TemplateManifestConfig` | `aquilia/templates/manifest_integration.py` | Configuration for templates from manifest file. |
| `ModuleTemplateRegistry` | `aquilia/templates/manifest_integration.py` | Registry mapping module names to template directories. |
| `TemplateMiddleware` | `aquilia/templates/middleware.py` | Template context injection middleware. |
| `SandboxPolicy` | `aquilia/templates/security.py` | Template sandbox security policy. |
| `TemplateSandbox` | `aquilia/templates/security.py` | Template sandbox manager. |
| `SessionTemplateProxy` | `aquilia/templates/sessions_integration.py` | Proxy object for session access in templates. |
| `FlashMessages` | `aquilia/templates/sessions_integration.py` | Flash message manager for templates. |
| `TemplateFlashMixin` | `aquilia/templates/sessions_integration.py` | Mixin for controllers to add flash messages. |

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| `create_auth_helpers` | `aquilia/templates/auth_integration.py` | Create auth helper functions for templates. |
| `enhance_engine_with_auth` | `aquilia/templates/auth_integration.py` | Enhance template engine with auth integration. |
| `inject_auth_context` | `aquilia/templates/auth_integration.py` | Inject auth variables into template context. |
| `create_template_engine_from_config` | `aquilia/templates/cli.py` | Create template engine from configuration. |
| `cmd_compile` | `aquilia/templates/cli.py` | Compile all templates to crous artifact. |
| `cmd_lint` | `aquilia/templates/cli.py` | Lint all templates. |
| `cmd_inspect` | `aquilia/templates/cli.py` | Inspect template metadata. |
| `cmd_clear_cache` | `aquilia/templates/cli.py` | Clear template cache. |
| `compile_command` | `aquilia/templates/cli.py` | Entry point for `aq templates compile`. |
| `lint_command` | `aquilia/templates/cli.py` | Entry point for `aq templates lint`. |
| `inspect_command` | `aquilia/templates/cli.py` | Entry point for `aq templates inspect`. |
| `clear_cache_command` | `aquilia/templates/cli.py` | Entry point for `aq templates clear-cache`. |
| `create_template_context` | `aquilia/templates/context.py` | Create template context from request context and user variables. |
| `inject_url_helpers` | `aquilia/templates/context.py` | Inject URL generation helpers into context. |
| `inject_static_helper` | `aquilia/templates/context.py` | Inject static asset URL helper into context. |
| `inject_csp_nonce` | `aquilia/templates/context.py` | Inject CSP nonce into context. |
| `inject_csrf_token` | `aquilia/templates/context.py` | Inject CSRF token into context. |
| `inject_config` | `aquilia/templates/context.py` | Inject safe config subset into context. |
| `inject_i18n` | `aquilia/templates/context.py` | Inject internationalization helpers into context. |
| `register_template_providers` | `aquilia/templates/di_providers.py` | Register all template providers with DI container. |
| `create_development_engine` | `aquilia/templates/di_providers.py` | Factory for development template engine: |
| `create_production_engine` | `aquilia/templates/di_providers.py` | Factory for production template engine: |
| `create_testing_engine` | `aquilia/templates/di_providers.py` | Factory for testing template engine: |
| `discover_template_directories` | `aquilia/templates/manifest_integration.py` | Discover template directories in project. |
| `discover_from_manifests` | `aquilia/templates/manifest_integration.py` | Discover template directories from module.aq manifest files. |
| `should_precompile_module` | `aquilia/templates/manifest_integration.py` | Check if module templates should be precompiled. |
| `get_cache_strategy` | `aquilia/templates/manifest_integration.py` | Get cache strategy from manifest. |
| `generate_template_manifest` | `aquilia/templates/manifest_integration.py` | Generate template manifest for crous artifacts. |
| `create_manifest_aware_loader` | `aquilia/templates/manifest_integration.py` | Create TemplateLoader with manifest-based auto-discovery. |
| `create_module_registry` | `aquilia/templates/manifest_integration.py` | Create and populate module template registry. |
| `create_safe_globals` | `aquilia/templates/security.py` | Create dictionary of safe global functions for templates. |
| `create_safe_filters` | `aquilia/templates/security.py` | Create dictionary of safe custom filters. |
| `enhance_engine_with_sessions` | `aquilia/templates/sessions_integration.py` | Enhance template engine with session integration. |
| `inject_session_context` | `aquilia/templates/sessions_integration.py` | Inject session variables into template context. |
| `enhance_middleware_with_sessions` | `aquilia/templates/sessions_integration.py` | Enhance TemplateMiddleware with session context injection. |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/templates/__init__.py` | AquilaTemplates - First-class Jinja2-based template rendering for Aquilia. |
| `aquilia/templates/auth_integration.py` | AquilaTemplates - Auth Integration |
| `aquilia/templates/bytecode_cache.py` | Bytecode Cache - Template compilation caching system. |
| `aquilia/templates/cli.py` | Template CLI - Command-line interface for template management. |
| `aquilia/templates/context.py` | Template Context - Context building and injection helpers. |
| `aquilia/templates/di_providers.py` | AquilaTemplates - DI Providers |
| `aquilia/templates/engine.py` | Template Engine - Core async-capable Jinja2 template rendering engine. |
| `aquilia/templates/extensions.py` | Jinja2 template extensions used by Aquilia templates. |
| `aquilia/templates/faults.py` | AquilaTemplates - Fault Classes. |
| `aquilia/templates/loader.py` | Template Loader - Namespace-aware filesystem and package template loaders. |
| `aquilia/templates/manager.py` | Template Manager - Compilation, linting, and manifest integration. |
| `aquilia/templates/manifest_integration.py` | AquilaTemplates - Manifest Integration |
| `aquilia/templates/middleware.py` | Template Middleware - Automatic context injection for templates. |
| `aquilia/templates/security.py` | Template Security - Sandboxing and security policies. |
| `aquilia/templates/sessions_integration.py` | AquilaTemplates - Session Integration |

## Testing Pointers

Search `tests/` for `templates` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.

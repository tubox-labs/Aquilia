# Templates Architecture

Jinja2 template engine, loaders, manager, middleware, bytecode cache, sandbox, DI providers, manifest/session/auth/i18n integration, and template CLI helpers.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/templates/__init__.py` | 115 | 0 | 0 | AquilaTemplates - First-class Jinja2-based template rendering for Aquilia. |
| `aquilia/templates/auth_integration.py` | 433 | 3 | 3 | AquilaTemplates - Auth Integration |
| `aquilia/templates/bytecode_cache.py` | 401 | 4 | 0 | Bytecode Cache - Template compilation caching system. |
| `aquilia/templates/cli.py` | 355 | 0 | 9 | Template CLI - Command-line interface for template management. |
| `aquilia/templates/context.py` | 232 | 1 | 7 | Template Context - Context building and injection helpers. |
| `aquilia/templates/di_providers.py` | 363 | 5 | 4 | AquilaTemplates - DI Providers |
| `aquilia/templates/engine.py` | 407 | 1 | 0 | Template Engine - Core async-capable Jinja2 template rendering engine. |
| `aquilia/templates/extensions.py` | 112 | 1 | 0 | Jinja2 template extensions used by Aquilia templates. |
| `aquilia/templates/faults.py` | 112 | 4 | 0 | AquilaTemplates — Fault Classes. |
| `aquilia/templates/loader.py` | 212 | 2 | 0 | Template Loader - Namespace-aware filesystem and package template loaders. |
| `aquilia/templates/manager.py` | 409 | 3 | 0 | Template Manager - Compilation, linting, and manifest integration. |
| `aquilia/templates/manifest_integration.py` | 345 | 2 | 7 | AquilaTemplates - Manifest Integration |
| `aquilia/templates/middleware.py` | 132 | 1 | 0 | Template Middleware - Automatic context injection for templates. |
| `aquilia/templates/security.py` | 425 | 2 | 2 | Template Security - Sandboxing and security policies. |
| `aquilia/templates/sessions_integration.py` | 356 | 3 | 3 | AquilaTemplates - Session Integration |

## Internal Shape

`templates` has 15 Python files, 32 public classes, 35 public module-level functions, and 3 constants or module flags detected by AST.

## Runtime Responsibilities

- No mounted `aq` command group maps directly to this module; it is used through Python APIs, manifests, workspace integrations, or server startup wiring.

## Internal Imports

| Import | Count |
| --- | ---: |
| `.loader` | 5 |
| `.bytecode_cache` | 4 |
| `.engine` | 4 |
| `.security` | 4 |
| `.manager` | 3 |
| `.context` | 2 |
| `.extensions` | 2 |
| `.auth_integration` | 1 |
| `.di_providers` | 1 |
| `.faults` | 1 |
| `.manifest_integration` | 1 |
| `.middleware` | 1 |
| `.sessions_integration` | 1 |
| `aquilia._version` | 1 |
| `aquilia.config` | 1 |
| `aquilia.di.decorators` | 1 |
| `aquilia.faults.core` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `jinja2` | 12 |
| `typing` | 12 |
| `pathlib` | 6 |
| `logging` | 5 |
| `collections` | 4 |
| `json` | 4 |
| `__future__` | 3 |
| `dataclasses` | 3 |
| `os` | 3 |
| `datetime` | 2 |
| `hashlib` | 2 |
| `hmac` | 2 |
| `asyncio` | 1 |
| `base64` | 1 |
| `contextlib` | 1 |
| `sys` | 1 |
| `warnings` | 1 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `TemplateAuthGuard` | `aquilia/templates/auth_integration.py` | Guard to ensure templates have auth context. |
| `TemplateLoaderProvider` | `aquilia/templates/di_providers.py` | Provider for TemplateLoader with auto-discovered paths. |
| `BytecodeCacheProvider` | `aquilia/templates/di_providers.py` | Provider for bytecode cache with strategy selection. |
| `TemplateSandboxProvider` | `aquilia/templates/di_providers.py` | Provider for template sandbox with security policies. |
| `TemplateEngineProvider` | `aquilia/templates/di_providers.py` | Provider for TemplateEngine with full DI integration. |
| `TemplateManagerProvider` | `aquilia/templates/di_providers.py` | Provider for TemplateManager (compile/lint/inspect tools). |
| `TemplateEngine` | `aquilia/templates/engine.py` | Async-capable Jinja2 template engine. |
| `TemplateEngineUnavailableFault` | `aquilia/templates/faults.py` | Template engine not available. |
| `TemplateLoader` | `aquilia/templates/loader.py` | Namespace-aware template loader. |
| `PackageLoader` | `aquilia/templates/loader.py` | Package loader for library-embedded templates. |
| `TemplateManager` | `aquilia/templates/manager.py` | Template compilation and management. |
| `TemplateManifestConfig` | `aquilia/templates/manifest_integration.py` | Configuration for templates from manifest file. |
| `ModuleTemplateRegistry` | `aquilia/templates/manifest_integration.py` | Registry mapping module names to template directories. |
| `TemplateMiddleware` | `aquilia/templates/middleware.py` | Template context injection middleware. |
| `SandboxPolicy` | `aquilia/templates/security.py` | Template sandbox security policy. |

## Error Handling

Fault/error classes defined here:

`TemplateFault`, `TemplateEngineUnavailableFault`, `TemplateCacheIntegrityFault`

# Templates Configuration

Jinja2 template engine, loaders, manager, middleware, bytecode cache, sandbox, DI providers, manifest/session/auth/i18n integration, and template CLI helpers.

This page distinguishes direct configuration APIs from indirect runtime wiring. All class names and source files below are extracted from the current source tree.

## Configuration Model

This module exposes config-oriented public classes. Use the table below to locate exact constructors and `to_dict()` behavior in `api-reference.md`.

## Source Inventory

| File | Lines | Public classes | Public functions | Purpose |
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

## Detected Config-Oriented Classes

| Class | Source | Methods | Summary |
| --- | --- | --- | --- |
| `TemplateLoaderProvider` | `aquilia/templates/di_providers.py` | `provide` | Provider for TemplateLoader with auto-discovered paths. |
| `BytecodeCacheProvider` | `aquilia/templates/di_providers.py` | `provide` | Provider for bytecode cache with strategy selection. |
| `TemplateSandboxProvider` | `aquilia/templates/di_providers.py` | `provide` | Provider for template sandbox with security policies. |
| `TemplateEngineProvider` | `aquilia/templates/di_providers.py` | `provide` | Provider for TemplateEngine with full DI integration. |
| `TemplateManagerProvider` | `aquilia/templates/di_providers.py` | `provide` | Provider for TemplateManager (compile/lint/inspect tools). |
| `TemplateManifestConfig` | `aquilia/templates/manifest_integration.py` | `from_file` | Configuration for templates from manifest file. |
| `TemplateMiddleware` | `aquilia/templates/middleware.py` |  | Template context injection middleware. |
| `SandboxPolicy` | `aquilia/templates/security.py` | `strict`, `permissive`, `is_filter_allowed`, `is_test_allowed`, `is_global_allowed` | Template sandbox security policy. |

## Runtime Wiring Paths

- `workspace.py` defines workspace-level structure with `Workspace`, `Module`, and `Integration` builders.
- `modules/<name>/manifest.py` defines module internals with `AppManifest`.
- `ConfigLoader.get(...)` resolves dotted configuration paths at runtime.
- `AquiliaServer` consumes resolved config during middleware and subsystem setup.
- Subsystems with optional providers only require optional dependencies when their backend/provider is configured.

## Verification Checklist

1. Run `aq validate` to verify manifests.
2. Run `aq inspect config` to inspect resolved configuration.
3. Run `aq doctor` for workspace and integration diagnostics.
4. For server-only wiring, start via `aq run` and check startup logs plus `GET /_health`.

## Related Pages

- `api-reference.md` for exact class fields, methods, constants, and signatures.
- `integration-guide.md` for the workspace/manifest wiring pattern.
- `edge-cases-and-limitations.md` for fallback and compatibility behavior.

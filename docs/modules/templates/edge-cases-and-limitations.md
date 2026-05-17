# Templates Edge Cases And Limitations

## Fault And Error Types

The following error-oriented classes are present in the implementation and should guide defensive usage.

| Type | Source | Meaning |
| --- | --- | --- |
| `TemplateFault` | `aquilia/templates/faults.py` | Base fault for the template subsystem. |
| `TemplateEngineUnavailableFault` | `aquilia/templates/faults.py` | Template engine not available. |
| `TemplateCacheIntegrityFault` | `aquilia/templates/faults.py` | Bytecode cache integrity check failed. |

## Common Edge Cases

- Optional dependencies may change behavior. Check imports and constructor docs before enabling production features.
- In-memory stores, queues, caches, adapters, and registries are usually process-local. Use durable backends when state must survive restarts or scale across workers.
- Request-scoped data must not be cached globally. Use request state, DI request scopes, or explicit parameters.
- Decorators in Aquilia generally attach metadata at import time. Runtime behavior happens later during compilation, routing, middleware execution, or service startup.
- Many subsystems intentionally convert invalid states into typed faults. Catch the specific fault type when application code can recover.

## Source-Level Limits To Review

Review these files before changing behavior:

- `aquilia/templates/__init__.py`: AquilaTemplates - First-class Jinja2-based template rendering for Aquilia.
- `aquilia/templates/auth_integration.py`: AquilaTemplates - Auth Integration
- `aquilia/templates/bytecode_cache.py`: Bytecode Cache - Template compilation caching system.
- `aquilia/templates/cli.py`: Template CLI - Command-line interface for template management.
- `aquilia/templates/context.py`: Template Context - Context building and injection helpers.
- `aquilia/templates/di_providers.py`: AquilaTemplates - DI Providers
- `aquilia/templates/engine.py`: Template Engine - Core async-capable Jinja2 template rendering engine.
- `aquilia/templates/extensions.py`: Jinja2 template extensions used by Aquilia templates.
- `aquilia/templates/faults.py`: AquilaTemplates - Fault Classes.
- `aquilia/templates/loader.py`: Template Loader - Namespace-aware filesystem and package template loaders.
- `aquilia/templates/manager.py`: Template Manager - Compilation, linting, and manifest integration.
- `aquilia/templates/manifest_integration.py`: AquilaTemplates - Manifest Integration
- `aquilia/templates/middleware.py`: Template Middleware - Automatic context injection for templates.
- `aquilia/templates/security.py`: Template Security - Sandboxing and security policies.
- `aquilia/templates/sessions_integration.py`: AquilaTemplates - Session Integration

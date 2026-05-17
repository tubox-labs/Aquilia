# Templates Documentation

Jinja2 template engine, loaders, manager, middleware, bytecode cache, sandbox, DI providers, manifest/session/auth/i18n integration, and template CLI helpers.

## Coverage Snapshot

- Source files: 15
- Source lines: 4409
- Public classes: 32
- Public module functions: 35
- Constants/module flags: 3
- Public exports in `__all__`: 31

## Source Files Read

- `aquilia/templates/__init__.py`: AquilaTemplates - First-class Jinja2-based template rendering for Aquilia.
- `aquilia/templates/auth_integration.py`: AquilaTemplates - Auth Integration
- `aquilia/templates/bytecode_cache.py`: Bytecode Cache - Template compilation caching system.
- `aquilia/templates/cli.py`: Template CLI - Command-line interface for template management.
- `aquilia/templates/context.py`: Template Context - Context building and injection helpers.
- `aquilia/templates/di_providers.py`: AquilaTemplates - DI Providers
- `aquilia/templates/engine.py`: Template Engine - Core async-capable Jinja2 template rendering engine.
- `aquilia/templates/extensions.py`: Jinja2 template extensions used by Aquilia templates.
- `aquilia/templates/faults.py`: AquilaTemplates — Fault Classes.
- `aquilia/templates/loader.py`: Template Loader - Namespace-aware filesystem and package template loaders.
- `aquilia/templates/manager.py`: Template Manager - Compilation, linting, and manifest integration.
- `aquilia/templates/manifest_integration.py`: AquilaTemplates - Manifest Integration
- `aquilia/templates/middleware.py`: Template Middleware - Automatic context injection for templates.
- `aquilia/templates/security.py`: Template Security - Sandboxing and security policies.
- `aquilia/templates/sessions_integration.py`: AquilaTemplates - Session Integration

## Document Map

- `architecture.md`: module boundaries, dependencies, lifecycle, and extension points.
- `configuration.md`: configuration classes, builders, server wiring, and precedence.
- `api-reference.md`: source-extracted classes, methods, functions, constants, exports, and signatures.
- `integration-guide.md`: how to wire the module into an Aquilia app.
- `cli-reference.md`: mounted `aq` commands for this module, if any.
- `examples.md`: usage examples derived from source and checked example apps.
- `edge-cases-and-limitations.md`: implementation limits and compatibility behavior.
- `troubleshooting.md`: diagnostic commands and common failure patterns.

# Templates Documentation

This directory is the professional documentation set for `templates`. It is implementation-driven and aligned with the current source files under `aquilia/templates`.

## What This Covers

The sandboxed Jinja2 template subsystem with loaders, engines, managers, bytecode cache, manifest integration, static tags, security, DI, sessions, auth helpers, middleware, and CLI tooling.

## Source Files Read

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

## Document Map

- `architecture.md`: Runtime architecture and module boundaries
- `configuration.md`: Configuration entry points, datatypes, and precedence
- `api-reference.md`: Classes, methods, functions, constants, and data fields extracted from source
- `integration-guide.md`: How to wire the module into a real Aquilia application
- `cli-reference.md`: Command line surface and operational commands
- `edge-cases-and-limitations.md`: Known edge cases and implementation limits
- `troubleshooting.md`: Common failures and diagnosis steps
- `examples.md`: Code examples and usage patterns

## Public Surface Snapshot

- Python files: 15
- Public classes: 32
- Configuration or dataclass-like types: 5
- Public functions: 35
- Constants detected: 2

## Fast Start

```python
from aquilia.templates import TemplateEngine, create_development_engine

engine = create_development_engine(search_paths=["templates"])
html = await engine.render("orders/detail.html", {"order_id": "ord_001"})
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.

# Templates Architecture

## Runtime Role

The sandboxed Jinja2 template subsystem with loaders, engines, managers, bytecode cache, manifest integration, static tags, security, DI, sessions, auth helpers, middleware, and CLI tooling.

The implementation is split across 15 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

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

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `typing` | 12 |
| `jinja2` | 11 |
| `pathlib` | 6 |
| `loader` | 5 |
| `logging` | 5 |
| `aquilia` | 4 |
| `bytecode_cache` | 4 |
| `collections` | 4 |
| `engine` | 4 |
| `json` | 4 |
| `security` | 4 |
| `__future__` | 3 |
| `dataclasses` | 3 |
| `manager` | 3 |
| `os` | 3 |
| `context` | 2 |
| `datetime` | 2 |
| `extensions` | 2 |
| `hashlib` | 2 |
| `hmac` | 2 |
| `asyncio` | 1 |
| `auth_integration` | 1 |
| `base64` | 1 |
| `contextlib` | 1 |
| `di_providers` | 1 |
| `faults` | 1 |
| `manifest_integration` | 1 |
| `middleware` | 1 |
| `sessions_integration` | 1 |
| `sys` | 1 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.

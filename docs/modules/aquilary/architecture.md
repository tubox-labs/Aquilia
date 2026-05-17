# Aquilary Registry Architecture

## Runtime Role

The manifest-driven registry layer that validates app manifests, detects dependency cycles, fingerprints runtime graphs, and feeds metadata to the runtime registry.

The implementation is split across 10 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

- `aquilia/aquilary/__init__.py`: Aquilary - Manifest-driven App Registry for Aquilia
- `aquilia/aquilary/cli.py`: Aquilary CLI commands for manifest validation, inspection, and deployment.
- `aquilia/aquilary/core.py`: Core Aquilary types and main registry class.
- `aquilia/aquilary/errors.py`: Aquilary registry error types with rich diagnostics.
- `aquilia/aquilary/fingerprint.py`: Fingerprint generator for reproducible deployments.
- `aquilia/aquilary/graph.py`: Dependency graph analysis with Tarjan's algorithm for cycle detection.
- `aquilia/aquilary/handler_wrapper.py`: Handler wrapper for dependency injection into controller methods.
- `aquilia/aquilary/loader.py`: Safe manifest loader with no import-time side effects.
- `aquilia/aquilary/route_compiler.py`: Route Compiler - Extracts routes from controllers and compiles route table.
- `aquilia/aquilary/validator.py`: Registry validator for manifests and configuration.

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `typing` | 8 |
| `dataclasses` | 5 |
| `importlib` | 3 |
| `json` | 3 |
| `collections` | 2 |
| `errors` | 2 |
| `inspect` | 2 |
| `pathlib` | 2 |
| `sys` | 2 |
| `aquilia` | 1 |
| `argparse` | 1 |
| `contextlib` | 1 |
| `core` | 1 |
| `datetime` | 1 |
| `enum` | 1 |
| `fingerprint` | 1 |
| `functools` | 1 |
| `graph` | 1 |
| `handler_wrapper` | 1 |
| `hashlib` | 1 |
| `loader` | 1 |
| `logging` | 1 |
| `os` | 1 |
| `validator` | 1 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.

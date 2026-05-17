# Patterns Architecture

## Runtime Role

The route pattern grammar, parser, compiler, matcher, specificity model, diagnostics, type registry, transforms, constraints, OpenAPI parameter generation, and autofix suggestions.

The implementation is split across 21 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

- `aquilia/patterns/__init__.py`: AquilaPatterns - Professional URL pattern language and compiler for Aquilia.
- `aquilia/patterns/autofix.py`: Auto-fix suggestions and error recovery for pattern diagnostics.
- `aquilia/patterns/cache.py`: Production-ready caching layer for compiled patterns.
- `aquilia/patterns/compiler/__init__.py`: Compiler package for AquilaPatterns.
- `aquilia/patterns/compiler/ast_nodes.py`: AST node definitions for AquilaPatterns.
- `aquilia/patterns/compiler/compiler.py`: Compiler that transforms AST into executable compiled patterns.
- `aquilia/patterns/compiler/parser.py`: Tokenizer and parser for AquilaPatterns.
- `aquilia/patterns/compiler/specificity.py`: Specificity scoring for pattern ranking.
- `aquilia/patterns/diagnostics/__init__.py`: Diagnostics package.
- `aquilia/patterns/diagnostics/errors.py`: Diagnostic errors for AquilaPatterns.
- `aquilia/patterns/grammar.py`: Formal EBNF grammar for AquilaPatterns.
- `aquilia/patterns/lsp/__init__.py`: LSP support package.
- `aquilia/patterns/lsp/metadata.py`: LSP (Language Server Protocol) support for IDE integration.
- `aquilia/patterns/matcher.py`: Pattern matcher with optimized matching algorithm.
- `aquilia/patterns/openapi.py`: OpenAPI schema generation from compiled patterns.
- `aquilia/patterns/transforms/__init__.py`: Transforms package.
- `aquilia/patterns/transforms/registry.py`: Transform function registry.
- `aquilia/patterns/types/__init__.py`: Types package.
- `aquilia/patterns/types/registry.py`: Type registry and built-in type castors.
- `aquilia/patterns/validators/__init__.py`: Validators package.
- `aquilia/patterns/validators/registry.py`: Constraint validator registry.

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `compiler` | 13 |
| `typing` | 9 |
| `dataclasses` | 7 |
| `collections` | 5 |
| `ast_nodes` | 4 |
| `diagnostics` | 3 |
| `json` | 3 |
| `registry` | 3 |
| `types` | 3 |
| `validators` | 3 |
| `enum` | 2 |
| `specificity` | 2 |
| `transforms` | 2 |
| `aquilia` | 1 |
| `autofix` | 1 |
| `cache` | 1 |
| `contextlib` | 1 |
| `difflib` | 1 |
| `errors` | 1 |
| `hashlib` | 1 |
| `matcher` | 1 |
| `metadata` | 1 |
| `openapi` | 1 |
| `parser` | 1 |
| `pathlib` | 1 |
| `re` | 1 |
| `threading` | 1 |
| `time` | 1 |
| `uuid` | 1 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.

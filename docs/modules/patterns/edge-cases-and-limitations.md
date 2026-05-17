# Patterns Edge Cases And Limitations

## Fault And Error Types

The following error-oriented classes are present in the implementation and should guide defensive usage.

| Type | Source | Meaning |
| --- | --- | --- |
| `PatternSyntaxError` | `aquilia/patterns/diagnostics/errors.py` | Syntax error in pattern. |
| `PatternSemanticError` | `aquilia/patterns/diagnostics/errors.py` | Semantic error in pattern. |
| `RouteAmbiguityError` | `aquilia/patterns/diagnostics/errors.py` | Two routes have ambiguous patterns. |

## Common Edge Cases

- Optional dependencies may change behavior. Check imports and constructor docs before enabling production features.
- In-memory stores, queues, caches, adapters, and registries are usually process-local. Use durable backends when state must survive restarts or scale across workers.
- Request-scoped data must not be cached globally. Use request state, DI request scopes, or explicit parameters.
- Decorators in Aquilia generally attach metadata at import time. Runtime behavior happens later during compilation, routing, middleware execution, or service startup.
- Many subsystems intentionally convert invalid states into typed faults. Catch the specific fault type when application code can recover.

## Source-Level Limits To Review

Review these files before changing behavior:

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

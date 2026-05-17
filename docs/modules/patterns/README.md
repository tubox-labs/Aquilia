# Patterns Documentation

URL pattern grammar, parser, compiler, matcher, type/validator/transform registries, specificity scoring, OpenAPI conversion, diagnostics, autofix, and LSP metadata.

## Coverage Snapshot

- Source files: 21
- Source lines: 3246
- Public classes: 35
- Public module functions: 18
- Constants/module flags: 13
- Public exports in `__all__`: 39

## Source Files Read

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

## Document Map

- `architecture.md`: module boundaries, dependencies, lifecycle, and extension points.
- `configuration.md`: configuration classes, builders, server wiring, and precedence.
- `api-reference.md`: source-extracted classes, methods, functions, constants, exports, and signatures.
- `integration-guide.md`: how to wire the module into an Aquilia app.
- `cli-reference.md`: mounted `aq` commands for this module, if any.
- `examples.md`: usage examples derived from source and checked example apps.
- `edge-cases-and-limitations.md`: implementation limits and compatibility behavior.
- `troubleshooting.md`: diagnostic commands and common failure patterns.

# Patterns Documentation

This directory is the professional documentation set for `patterns`. It is implementation-driven and aligned with the current source files under `aquilia/patterns`.

## What This Covers

The route pattern grammar, parser, compiler, matcher, specificity model, diagnostics, type registry, transforms, constraints, OpenAPI parameter generation, and autofix suggestions.

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

- `architecture.md`: Runtime architecture and module boundaries
- `configuration.md`: Configuration entry points, datatypes, and precedence
- `api-reference.md`: Classes, methods, functions, constants, and data fields extracted from source
- `integration-guide.md`: How to wire the module into a real Aquilia application
- `cli-reference.md`: Command line surface and operational commands
- `edge-cases-and-limitations.md`: Known edge cases and implementation limits
- `troubleshooting.md`: Common failures and diagnosis steps
- `examples.md`: Code examples and usage patterns

## Public Surface Snapshot

- Python files: 21
- Public classes: 35
- Configuration or dataclass-like types: 19
- Public functions: 18
- Constants detected: 6

## Fast Start

```python
from aquilia.patterns import __version__, AutoFixEngine, DiagnosticFix, ErrorRecovery, FixSuggestion, generate_fix_suggestions

# The imported symbols above are public exports from this module.
# See api-reference.md for constructor signatures, methods, and data fields.
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.

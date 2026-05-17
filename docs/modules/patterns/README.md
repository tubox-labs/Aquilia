# patterns Module

## Purpose

URL pattern grammar, compiler, and matcher. Use this module for compiling route patterns, specificity, typed segments, transforms, constraints, diagnostics, OpenAPI params, and autofix suggestions.

## Source Coverage

- Python files: 21
- Public classes: 35
- Dataclasses: 19
- Enums: 3
- Public functions: 18

## How It Fits In Aquilia

1. Import the package from `aquilia.patterns` or its concrete submodules.
2. Configure it through workspace integrations, manifests, or direct service construction depending on the subsystem.
3. Keep business logic outside transport and framework glue so the subsystem stays testable.

## Practical Guidance

- Prefer typed configuration objects and framework helpers over ad hoc dictionaries when they exist.
- Use the tests in `tests/` as behavioral examples when changing this subsystem.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `FixSuggestion` | `aquilia/patterns/autofix.py` | Represents a single fix suggestion. |
| `DiagnosticFix` | `aquilia/patterns/autofix.py` | Container for diagnostic with fix suggestions. |
| `AutoFixEngine` | `aquilia/patterns/autofix.py` | Engine for generating automatic fix suggestions. |
| `ErrorRecovery` | `aquilia/patterns/autofix.py` | Error recovery strategies for parser. |
| `CacheStats` | `aquilia/patterns/cache.py` | Cache statistics for monitoring. |
| `CacheEntry` | `aquilia/patterns/cache.py` | Cache entry with metadata. |
| `PatternCache` | `aquilia/patterns/cache.py` | Thread-safe LRU cache for compiled patterns with TTL support. |
| `MatchResult` | `aquilia/patterns/matcher.py` | Result of pattern matching. |
| `PatternMatcher` | `aquilia/patterns/matcher.py` | Matches request paths against compiled patterns. |
| `TypeRegistry` | `aquilia/patterns/types/registry.py` | Registry of type castors for pattern parameters. |
| `TransformRegistry` | `aquilia/patterns/transforms/registry.py` | Registry of transform functions. |
| `PatternDiagnostic` | `aquilia/patterns/diagnostics/errors.py` | Base class for all pattern diagnostics. |
| `PatternSyntaxError` | `aquilia/patterns/diagnostics/errors.py` | Syntax error in pattern. |
| `PatternSemanticError` | `aquilia/patterns/diagnostics/errors.py` | Semantic error in pattern. |
| `RouteAmbiguityError` | `aquilia/patterns/diagnostics/errors.py` | Two routes have ambiguous patterns. |
| `ConstraintRegistry` | `aquilia/patterns/validators/registry.py` | Registry of constraint validators. |
| `SegmentKind` | `aquilia/patterns/compiler/ast_nodes.py` | Kind of path segment. |
| `ConstraintKind` | `aquilia/patterns/compiler/ast_nodes.py` | Kind of constraint. |
| `Span` | `aquilia/patterns/compiler/ast_nodes.py` | Source code span for diagnostics. |
| `Constraint` | `aquilia/patterns/compiler/ast_nodes.py` | Constraint on a parameter. |
| `Transform` | `aquilia/patterns/compiler/ast_nodes.py` | Transform function applied to parameter. |
| `BaseSegment` | `aquilia/patterns/compiler/ast_nodes.py` | Base class for all segments. |
| `StaticSegment` | `aquilia/patterns/compiler/ast_nodes.py` | Static text segment. |
| `TokenSegment` | `aquilia/patterns/compiler/ast_nodes.py` | Named parameter segment with type and constraints. |
| `SplatSegment` | `aquilia/patterns/compiler/ast_nodes.py` | Multi-segment capture (*path). |
| `OptionalGroup` | `aquilia/patterns/compiler/ast_nodes.py` | Optional segment group [...]. |
| `QueryParam` | `aquilia/patterns/compiler/ast_nodes.py` | Query parameter definition. |
| `PatternAST` | `aquilia/patterns/compiler/ast_nodes.py` | Complete AST for a URL pattern. |
| `CompiledParam` | `aquilia/patterns/compiler/compiler.py` | Compiled parameter metadata. |
| `CompiledPattern` | `aquilia/patterns/compiler/compiler.py` | Fully compiled pattern ready for matching. |
| `PatternCompiler` | `aquilia/patterns/compiler/compiler.py` | Compiles AST into optimized executable patterns. |
| `TokenType` | `aquilia/patterns/compiler/parser.py` | Token types for the lexer. |
| `PatternToken` | `aquilia/patterns/compiler/parser.py` | A lexical token with position information. |
| `Tokenizer` | `aquilia/patterns/compiler/parser.py` | Tokenizer for URL patterns. |
| `PatternParser` | `aquilia/patterns/compiler/parser.py` | Parser for URL patterns following the EBNF grammar. |

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| `generate_fix_suggestions` | `aquilia/patterns/autofix.py` | Generate fix suggestions for a diagnostic error. |
| `get_global_cache` | `aquilia/patterns/cache.py` | Get or create global cache instance. |
| `set_global_cache` | `aquilia/patterns/cache.py` | Set global cache instance. |
| `compile_pattern` | `aquilia/patterns/cache.py` | Convenience function to compile patterns with optional caching. |
| `generate_openapi_params` | `aquilia/patterns/openapi.py` | Generate OpenAPI parameter definitions from a compiled pattern. |
| `generate_openapi_path` | `aquilia/patterns/openapi.py` | Convert aquilia pattern to OpenAPI path template format. |
| `pattern_to_openapi_operation` | `aquilia/patterns/openapi.py` | Generate a complete OpenAPI operation object. |
| `patterns_to_openapi_spec` | `aquilia/patterns/openapi.py` | Generate complete OpenAPI 3.0 specification from patterns. |
| `register_type` | `aquilia/patterns/types/registry.py` | Decorator to register a custom type. |
| `generate_lsp_metadata` | `aquilia/patterns/lsp/metadata.py` | Generate patterns.json for LSP consumption. |
| `generate_hover_docs` | `aquilia/patterns/lsp/metadata.py` | Generate hover documentation for pattern syntax. |
| `generate_autocomplete_snippets` | `aquilia/patterns/lsp/metadata.py` | Generate autocomplete snippets for VS Code. |
| `generate_vscode_extension` | `aquilia/patterns/lsp/metadata.py` | Generate VS Code extension files for AquilaPatterns. |
| `generate_diagnostic_codes` | `aquilia/patterns/lsp/metadata.py` | Generate diagnostic code descriptions for LSP. |
| `register_transform` | `aquilia/patterns/transforms/registry.py` | Decorator to register a custom transform. |
| `register_constraint` | `aquilia/patterns/validators/registry.py` | Decorator to register a custom constraint. |
| `parse_pattern` | `aquilia/patterns/compiler/parser.py` | Parse a URL pattern into an AST. |
| `calculate_specificity` | `aquilia/patterns/compiler/specificity.py` | Calculate specificity score for pattern ranking. |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/patterns/__init__.py` | AquilaPatterns - Professional URL pattern language and compiler for Aquilia. |
| `aquilia/patterns/autofix.py` | Auto-fix suggestions and error recovery for pattern diagnostics. |
| `aquilia/patterns/cache.py` | Production-ready caching layer for compiled patterns. |
| `aquilia/patterns/compiler/__init__.py` | Compiler package for AquilaPatterns. |
| `aquilia/patterns/compiler/ast_nodes.py` | AST node definitions for AquilaPatterns. |
| `aquilia/patterns/compiler/compiler.py` | Compiler that transforms AST into executable compiled patterns. |
| `aquilia/patterns/compiler/parser.py` | Tokenizer and parser for AquilaPatterns. |
| `aquilia/patterns/compiler/specificity.py` | Specificity scoring for pattern ranking. |
| `aquilia/patterns/diagnostics/__init__.py` | Diagnostics package. |
| `aquilia/patterns/diagnostics/errors.py` | Diagnostic errors for AquilaPatterns. |
| `aquilia/patterns/grammar.py` | Formal EBNF grammar for AquilaPatterns. |
| `aquilia/patterns/lsp/__init__.py` | LSP support package. |
| `aquilia/patterns/lsp/metadata.py` | LSP (Language Server Protocol) support for IDE integration. |
| `aquilia/patterns/matcher.py` | Pattern matcher with optimized matching algorithm. |
| `aquilia/patterns/openapi.py` | OpenAPI schema generation from compiled patterns. |
| `aquilia/patterns/transforms/__init__.py` | Transforms package. |
| `aquilia/patterns/transforms/registry.py` | Transform function registry. |
| `aquilia/patterns/types/__init__.py` | Types package. |
| `aquilia/patterns/types/registry.py` | Type registry and built-in type castors. |
| `aquilia/patterns/validators/__init__.py` | Validators package. |
| `aquilia/patterns/validators/registry.py` | Constraint validator registry. |

## Testing Pointers

Search `tests/` for `patterns` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.

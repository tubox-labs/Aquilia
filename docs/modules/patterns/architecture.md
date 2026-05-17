# Patterns Architecture

URL pattern grammar, parser, compiler, matcher, type/validator/transform registries, specificity scoring, OpenAPI conversion, diagnostics, autofix, and LSP metadata.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/patterns/__init__.py` | 90 | 0 | 0 | AquilaPatterns - Professional URL pattern language and compiler for Aquilia. |
| `aquilia/patterns/autofix.py` | 478 | 4 | 1 | Auto-fix suggestions and error recovery for pattern diagnostics. |
| `aquilia/patterns/cache.py` | 322 | 3 | 3 | Production-ready caching layer for compiled patterns. |
| `aquilia/patterns/compiler/__init__.py` | 15 | 0 | 0 | Compiler package for AquilaPatterns. |
| `aquilia/patterns/compiler/ast_nodes.py` | 222 | 12 | 0 | AST node definitions for AquilaPatterns. |
| `aquilia/patterns/compiler/compiler.py` | 388 | 3 | 0 | Compiler that transforms AST into executable compiled patterns. |
| `aquilia/patterns/compiler/parser.py` | 622 | 4 | 1 | Tokenizer and parser for AquilaPatterns. |
| `aquilia/patterns/compiler/specificity.py` | 67 | 0 | 1 | Specificity scoring for pattern ranking. |
| `aquilia/patterns/diagnostics/__init__.py` | 15 | 0 | 0 | Diagnostics package. |
| `aquilia/patterns/diagnostics/errors.py` | 81 | 4 | 0 | Diagnostic errors for AquilaPatterns. |
| `aquilia/patterns/grammar.py` | 139 | 0 | 0 | Formal EBNF grammar for AquilaPatterns. |
| `aquilia/patterns/lsp/__init__.py` | 17 | 0 | 0 | LSP support package. |
| `aquilia/patterns/lsp/metadata.py` | 218 | 0 | 5 | LSP (Language Server Protocol) support for IDE integration. |
| `aquilia/patterns/matcher.py` | 235 | 2 | 0 | Pattern matcher with optimized matching algorithm. |
| `aquilia/patterns/openapi.py` | 128 | 0 | 4 | OpenAPI schema generation from compiled patterns. |
| `aquilia/patterns/transforms/__init__.py` | 5 | 0 | 0 | Transforms package. |
| `aquilia/patterns/transforms/registry.py` | 50 | 1 | 1 | Transform function registry. |
| `aquilia/patterns/types/__init__.py` | 5 | 0 | 0 | Types package. |
| `aquilia/patterns/types/registry.py` | 100 | 1 | 1 | Type registry and built-in type castors. |
| `aquilia/patterns/validators/__init__.py` | 5 | 0 | 0 | Validators package. |
| `aquilia/patterns/validators/registry.py` | 44 | 1 | 1 | Constraint validator registry. |

## Internal Shape

`patterns` has 21 Python files, 35 public classes, 18 public module-level functions, and 13 constants or module flags detected by AST.

## Runtime Responsibilities

- No mounted `aq` command group maps directly to this module; it is used through Python APIs, manifests, workspace integrations, or server startup wiring.

## Internal Imports

| Import | Count |
| --- | ---: |
| `.compiler.compiler` | 5 |
| `.ast_nodes` | 4 |
| `.registry` | 3 |
| `..diagnostics.errors` | 2 |
| `.compiler.ast_nodes` | 2 |
| `.compiler.parser` | 2 |
| `.specificity` | 2 |
| `.types.registry` | 2 |
| `.validators.registry` | 2 |
| `..compiler.ast_nodes` | 1 |
| `..compiler.compiler` | 1 |
| `..transforms.registry` | 1 |
| `..types.registry` | 1 |
| `..validators.registry` | 1 |
| `.autofix` | 1 |
| `.cache` | 1 |
| `.compiler` | 1 |
| `.compiler.specificity` | 1 |
| `.diagnostics.errors` | 1 |
| `.errors` | 1 |
| `.matcher` | 1 |
| `.metadata` | 1 |
| `.openapi` | 1 |
| `.parser` | 1 |
| `.transforms.registry` | 1 |
| `aquilia._version` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `typing` | 9 |
| `dataclasses` | 7 |
| `collections` | 5 |
| `json` | 3 |
| `enum` | 2 |
| `re` | 2 |
| `contextlib` | 1 |
| `difflib` | 1 |
| `hashlib` | 1 |
| `pathlib` | 1 |
| `threading` | 1 |
| `time` | 1 |
| `uuid` | 1 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `AutoFixEngine` | `aquilia/patterns/autofix.py` | Engine for generating automatic fix suggestions. |
| `PatternCompiler` | `aquilia/patterns/compiler/compiler.py` | Compiles AST into optimized executable patterns. |
| `TransformRegistry` | `aquilia/patterns/transforms/registry.py` | Registry of transform functions. |
| `TypeRegistry` | `aquilia/patterns/types/registry.py` | Registry of type castors for pattern parameters. |
| `ConstraintRegistry` | `aquilia/patterns/validators/registry.py` | Registry of constraint validators. |

## Error Handling

Fault/error classes defined here:

`ErrorRecovery`, `PatternSyntaxError`, `PatternSemanticError`, `RouteAmbiguityError`

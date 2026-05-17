# Patterns Configuration

URL pattern grammar, parser, compiler, matcher, type/validator/transform registries, specificity scoring, OpenAPI conversion, diagnostics, autofix, and LSP metadata.

This page distinguishes direct configuration APIs from indirect runtime wiring. All class names and source files below are extracted from the current source tree.

## Configuration Model

No public config-specific class was detected in this module. It is configured through workspace/module declarations, related integration objects, or direct Python APIs.

## Source Inventory

| File | Lines | Public classes | Public functions | Purpose |
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

## Runtime Wiring Paths

- `workspace.py` defines workspace-level structure with `Workspace`, `Module`, and `Integration` builders.
- `modules/<name>/manifest.py` defines module internals with `AppManifest`.
- `ConfigLoader.get(...)` resolves dotted configuration paths at runtime.
- `AquiliaServer` consumes resolved config during middleware and subsystem setup.
- Subsystems with optional providers only require optional dependencies when their backend/provider is configured.

## Verification Checklist

1. Run `aq validate` to verify manifests.
2. Run `aq inspect config` to inspect resolved configuration.
3. Run `aq doctor` for workspace and integration diagnostics.
4. For server-only wiring, start via `aq run` and check startup logs plus `GET /_health`.

## Related Pages

- `api-reference.md` for exact class fields, methods, constants, and signatures.
- `integration-guide.md` for the workspace/manifest wiring pattern.
- `edge-cases-and-limitations.md` for fallback and compatibility behavior.

# Patterns Troubleshooting

URL pattern grammar, parser, compiler, matcher, type/validator/transform registries, specificity scoring, OpenAPI conversion, diagnostics, autofix, and LSP metadata.

## Fast Diagnosis Flow

1. Confirm the command is run from a directory containing `workspace.py` unless it is help/version/init/doctor.
2. Run `aq doctor` for workspace, environment, registry, integration, and deployment checks.
3. Run `aq validate` to catch manifest errors.
4. Run `aq inspect config` to inspect resolved settings.
5. Run `aq inspect modules` and `aq inspect routes` when discovery or routing is suspect.
6. Check `api-reference.md` for exact public API signatures.

## Symptoms And Actions

| Symptom | Likely Source | Action |
| --- | --- | --- |
| Import error during startup | Bad manifest class path or optional provider dependency | Check `modules/<name>/manifest.py`, install the relevant extra, and rerun `aq validate`. |
| Route not found | Controller omitted from manifest, wrong route prefix, or startup conflict | Run `aq inspect routes`; inspect controller decorators and `Module.route_prefix()`. |
| Dependency not found | Service not registered or constructor annotation cannot be resolved | Check `AppManifest.services`, DI provider registrations, and `aq inspect di`. |
| Config value missing | Dotenv/env overlay not loaded or wrong nested key | Check `ConfigLoader` precedence and `AQ_` double-underscore key names. |
| Production security failure | Insecure secret or required key not configured | Set `AQ_SECRET_KEY`, `SECRET_KEY`, or Python-native secret config. |
| Optional subsystem unavailable | Provider/backend dependency or startup connection failed | Check startup logs; optional subsystems often log non-fatal failures. |

## Source Files To Inspect

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

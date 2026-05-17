# Patterns Configuration

## Configuration Entry Points

The implementation exposes the following configuration-like classes, policies, integrations, or dataclasses.

| Type | Source | Fields | Purpose |
| --- | --- | --- | --- |
| `FixSuggestion` | `aquilia/patterns/autofix.py` | title: str, description: str, old_code: str, new_code: str, confidence: float | Represents a single fix suggestion. |
| `DiagnosticFix` | `aquilia/patterns/autofix.py` | error_message: str, suggestions: list[FixSuggestion] | Container for diagnostic with fix suggestions. |
| `CacheStats` | `aquilia/patterns/cache.py` | hits: int, misses: int, evictions: int, errors: int, total_compile_time: float | Cache statistics for monitoring. |
| `CacheEntry` | `aquilia/patterns/cache.py` | pattern: CompiledPattern, created_at: float, last_accessed: float, access_count: int, compile_time: float | Cache entry with metadata. |
| `Span` | `aquilia/patterns/compiler/ast_nodes.py` | start: int, end: int, line: int, column: int | Source code span for diagnostics. |
| `Constraint` | `aquilia/patterns/compiler/ast_nodes.py` | kind: ConstraintKind, value: Any, span: Span &#124; None | Constraint on a parameter. |
| `Transform` | `aquilia/patterns/compiler/ast_nodes.py` | name: str, args: list[Any], span: Span &#124; None | Transform function applied to parameter. |
| `BaseSegment` | `aquilia/patterns/compiler/ast_nodes.py` | kind: SegmentKind, span: Span &#124; None | Base class for all segments. |
| `StaticSegment` | `aquilia/patterns/compiler/ast_nodes.py` | value: str | Static text segment. |
| `TokenSegment` | `aquilia/patterns/compiler/ast_nodes.py` | name: str, param_type: str, constraints: list[Constraint], default: Any &#124; None, transform: Transform &#124; None | Named parameter segment with type and constraints. |
| `SplatSegment` | `aquilia/patterns/compiler/ast_nodes.py` | name: str, param_type: str | Multi-segment capture (*path). |
| `OptionalGroup` | `aquilia/patterns/compiler/ast_nodes.py` | segments: list[BaseSegment] | Optional segment group [...]. |
| `QueryParam` | `aquilia/patterns/compiler/ast_nodes.py` | name: str, param_type: str, constraints: list[Constraint], default: Any &#124; None, span: Span &#124; None | Query parameter definition. |
| `PatternAST` | `aquilia/patterns/compiler/ast_nodes.py` | raw: str, segments: list[BaseSegment], query_params: list[QueryParam], file: str &#124; None, span: Span &#124; None | Complete AST for a URL pattern. |
| `CompiledParam` | `aquilia/patterns/compiler/compiler.py` | index: int, name: str, param_type: str, constraints: list[dict[str, Any]], default: Any &#124; None, transform: str &#124; None, castor: Callable[[str], Any], validators: list[Callable[[Any], bool]] | Compiled parameter metadata. |
| `CompiledPattern` | `aquilia/patterns/compiler/compiler.py` | raw: str, file: str &#124; None, span: dict[str, int] &#124; None, static_prefix: str, segments: list[dict[str, Any]], params: dict[str, CompiledParam], query: dict[str, CompiledParam], specificity: int, compiled_re: Pattern &#124; None, castors: list[Callable], openapi: dict[str, Any], ast: PatternAST | Fully compiled pattern ready for matching. |
| `PatternToken` | `aquilia/patterns/compiler/parser.py` | type: TokenType, value: Any, span: Span | A lexical token with position information. |
| `PatternDiagnostic` | `aquilia/patterns/diagnostics/errors.py` | message: str, span: Span &#124; None, file: str &#124; None, suggestions: list[str] | Base class for all pattern diagnostics. |
| `MatchResult` | `aquilia/patterns/matcher.py` | pattern: CompiledPattern, params: dict[str, Any], query: dict[str, Any] | Result of pattern matching. |

## Common Entry Points

- No dedicated workspace integration was detected from module naming. Configure this module through direct constructors, manifests, or the subsystem that owns it.

## Precedence Model

Aquilia generally resolves configuration in this order:

1. Explicit constructor arguments or typed integration dataclass values.
2. `Workspace` builder methods and `Workspace.integrate(...)` output.
3. `ConfigLoader` defaults and environment overlays.
4. Runtime defaults inside the subsystem service or provider constructor.

When this module is registered through an `AppManifest`, keep component declarations inside `modules/<name>/manifest.py` and keep cross-cutting integration settings in `workspace.py`.

## Datatype Guidance

- Prefer typed dataclasses, policy objects, and config objects listed above when they exist.
- Keep secret values in environment-backed config, not literal strings in committed workspace files.
- Keep runtime-only state in services, stores, providers, or request state rather than static configuration.
- Use `to_dict()` on integration dataclasses when you need to inspect exactly what enters `ConfigLoader`.

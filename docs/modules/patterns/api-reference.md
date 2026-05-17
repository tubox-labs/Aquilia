# Patterns API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

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

## Public Exports

`AutoFixEngine`, `CompiledPattern`, `ConstraintRegistry`, `DiagnosticFix`, `ErrorRecovery`, `FixSuggestion`, `MatchResult`, `OptionalGroup`, `PatternAST`, `PatternCache`, `PatternCompiler`, `PatternDiagnostic`, `PatternMatcher`, `PatternParser`, `PatternSemanticError`, `PatternSyntaxError`, `PatternToken`, `QueryParam`, `RouteAmbiguityError`, `SplatSegment`, `StaticSegment`, `TokenSegment`, `TransformRegistry`, `TypeRegistry`, `calculate_specificity`, `compile_pattern`, `generate_autocomplete_snippets`, `generate_diagnostic_codes`, `generate_fix_suggestions`, `generate_hover_docs`, `generate_lsp_metadata`, `generate_openapi_params`, `generate_vscode_extension`, `get_global_cache`, `parse_pattern`, `register_constraint`, `register_transform`, `register_type`, `set_global_cache`

## Public Class Summary

| Class | Source | Bases | Summary |
| --- | --- | --- | --- |
| `FixSuggestion` | `aquilia/patterns/autofix.py` | object | Represents a single fix suggestion. |
| `DiagnosticFix` | `aquilia/patterns/autofix.py` | object | Container for diagnostic with fix suggestions. |
| `AutoFixEngine` | `aquilia/patterns/autofix.py` | object | Engine for generating automatic fix suggestions. |
| `ErrorRecovery` | `aquilia/patterns/autofix.py` | object | Error recovery strategies for parser. |
| `CacheStats` | `aquilia/patterns/cache.py` | object | Cache statistics for monitoring. |
| `CacheEntry` | `aquilia/patterns/cache.py` | object | Cache entry with metadata. |
| `PatternCache` | `aquilia/patterns/cache.py` | object | Thread-safe LRU cache for compiled patterns with TTL support. |
| `SegmentKind` | `aquilia/patterns/compiler/ast_nodes.py` | str, Enum | Kind of path segment. |
| `ConstraintKind` | `aquilia/patterns/compiler/ast_nodes.py` | str, Enum | Kind of constraint. |
| `Span` | `aquilia/patterns/compiler/ast_nodes.py` | object | Source code span for diagnostics. |
| `Constraint` | `aquilia/patterns/compiler/ast_nodes.py` | object | Constraint on a parameter. |
| `Transform` | `aquilia/patterns/compiler/ast_nodes.py` | object | Transform function applied to parameter. |
| `BaseSegment` | `aquilia/patterns/compiler/ast_nodes.py` | object | Base class for all segments. |
| `StaticSegment` | `aquilia/patterns/compiler/ast_nodes.py` | BaseSegment | Static text segment. |
| `TokenSegment` | `aquilia/patterns/compiler/ast_nodes.py` | BaseSegment | Named parameter segment with type and constraints. |
| `SplatSegment` | `aquilia/patterns/compiler/ast_nodes.py` | BaseSegment | Multi-segment capture (*path). |
| `OptionalGroup` | `aquilia/patterns/compiler/ast_nodes.py` | BaseSegment | Optional segment group [...]. |
| `QueryParam` | `aquilia/patterns/compiler/ast_nodes.py` | object | Query parameter definition. |
| `PatternAST` | `aquilia/patterns/compiler/ast_nodes.py` | object | Complete AST for a URL pattern. |
| `CompiledParam` | `aquilia/patterns/compiler/compiler.py` | object | Compiled parameter metadata. |
| `CompiledPattern` | `aquilia/patterns/compiler/compiler.py` | object | Fully compiled pattern ready for matching. |
| `PatternCompiler` | `aquilia/patterns/compiler/compiler.py` | object | Compiles AST into optimized executable patterns. |
| `TokenType` | `aquilia/patterns/compiler/parser.py` | str, Enum | Token types for the lexer. |
| `PatternToken` | `aquilia/patterns/compiler/parser.py` | object | A lexical token with position information. |
| `Tokenizer` | `aquilia/patterns/compiler/parser.py` | object | Tokenizer for URL patterns. |
| `PatternParser` | `aquilia/patterns/compiler/parser.py` | object | Parser for URL patterns following the EBNF grammar. |
| `PatternDiagnostic` | `aquilia/patterns/diagnostics/errors.py` | object | Base class for all pattern diagnostics. |
| `PatternSyntaxError` | `aquilia/patterns/diagnostics/errors.py` | PatternDiagnostic, Exception | Syntax error in pattern. |
| `PatternSemanticError` | `aquilia/patterns/diagnostics/errors.py` | PatternDiagnostic, Exception | Semantic error in pattern. |
| `RouteAmbiguityError` | `aquilia/patterns/diagnostics/errors.py` | PatternDiagnostic, Exception | Two routes have ambiguous patterns. |
| `MatchResult` | `aquilia/patterns/matcher.py` | object | Result of pattern matching. |
| `PatternMatcher` | `aquilia/patterns/matcher.py` | object | Matches request paths against compiled patterns. |
| `TransformRegistry` | `aquilia/patterns/transforms/registry.py` | object | Registry of transform functions. |
| `TypeRegistry` | `aquilia/patterns/types/registry.py` | object | Registry of type castors for pattern parameters. |
| `ConstraintRegistry` | `aquilia/patterns/validators/registry.py` | object | Registry of constraint validators. |

## Public Function Summary

| Function | Source | Signature | Summary |
| --- | --- | --- | --- |
| `generate_fix_suggestions` | `aquilia/patterns/autofix.py` | `def generate_fix_suggestions(error_type: str, error_message: str, pattern: str, **context)` | Generate fix suggestions for a diagnostic error. |
| `get_global_cache` | `aquilia/patterns/cache.py` | `def get_global_cache()` | Get or create global cache instance. |
| `set_global_cache` | `aquilia/patterns/cache.py` | `def set_global_cache(cache: PatternCache \| None)` | Set global cache instance. |
| `compile_pattern` | `aquilia/patterns/cache.py` | `def compile_pattern(pattern: str, use_cache: bool=True, **kwargs)` | Convenience function to compile patterns with optional caching. |
| `parse_pattern` | `aquilia/patterns/compiler/parser.py` | `def parse_pattern(source: str, filename: str \| None=None)` | Parse a URL pattern into an AST. |
| `calculate_specificity` | `aquilia/patterns/compiler/specificity.py` | `def calculate_specificity(ast: PatternAST)` | Calculate specificity score for pattern ranking. |
| `generate_lsp_metadata` | `aquilia/patterns/lsp/metadata.py` | `def generate_lsp_metadata(patterns: list[CompiledPattern], output_path: Path)` | Generate patterns.json for LSP consumption. |
| `generate_hover_docs` | `aquilia/patterns/lsp/metadata.py` | `def generate_hover_docs()` | Generate hover documentation for pattern syntax. |
| `generate_autocomplete_snippets` | `aquilia/patterns/lsp/metadata.py` | `def generate_autocomplete_snippets()` | Generate autocomplete snippets for VS Code. |
| `generate_vscode_extension` | `aquilia/patterns/lsp/metadata.py` | `def generate_vscode_extension(output_dir: Path)` | Generate VS Code extension files for AquilaPatterns. |
| `generate_diagnostic_codes` | `aquilia/patterns/lsp/metadata.py` | `def generate_diagnostic_codes()` | Generate diagnostic code descriptions for LSP. |
| `generate_openapi_params` | `aquilia/patterns/openapi.py` | `def generate_openapi_params(pattern: CompiledPattern)` | Generate OpenAPI parameter definitions from a compiled pattern. |
| `generate_openapi_path` | `aquilia/patterns/openapi.py` | `def generate_openapi_path(pattern: CompiledPattern)` | Convert aquilia pattern to OpenAPI path template format. Example: /users/<id:int> -> /users/{id} |
| `pattern_to_openapi_operation` | `aquilia/patterns/openapi.py` | `def pattern_to_openapi_operation(pattern: CompiledPattern, method: str, handler_name: str, summary: str='', description: str='', tags: list[str]=None)` | Generate a complete OpenAPI operation object. |
| `patterns_to_openapi_spec` | `aquilia/patterns/openapi.py` | `def patterns_to_openapi_spec(patterns: list[tuple[CompiledPattern, str, str]], title: str='Aquilia API', version: str='1.0.0', description: str='')` | Generate complete OpenAPI 3.0 specification from patterns. |
| `register_transform` | `aquilia/patterns/transforms/registry.py` | `def register_transform(name: str)` | Decorator to register a custom transform. |
| `register_type` | `aquilia/patterns/types/registry.py` | `def register_type(name: str, castor: Callable[[str], Any])` | Decorator to register a custom type. |
| `register_constraint` | `aquilia/patterns/validators/registry.py` | `def register_constraint(name: str)` | Decorator to register a custom constraint. |

## Constants And Module Flags

| Name | Source | Value or Type |
| --- | --- | --- |
| `STRONG_TYPES` | `aquilia/patterns/compiler/specificity.py` | `{'int', 'float', 'uuid', 'bool', 'json'}` |
| `EBNF_GRAMMAR` | `aquilia/patterns/grammar.py` | `'\npattern        = "/" segment_list [ "/" ] [ "?" query_list ]\nsegment_list   = segment ( "/" segment )*\nsegment        = static \| token \| optional \| splat\nstatic         = char+\ntoken          = "<" ident [ ":" type ] [ "\|" constraint_list ] [ "=" default ] [ "@" transform ] ">"\noptional       = "[" segment_list "]"\nsplat          = "*" ident [ ":" type ]\nconstraint_list = constraint ( "\|" constraint )*\nconstraint     = cmp \| "re=" regex_literal \| "in=(" value_list ")" \| predicate\ncmp            = ("min="\|"max=") number\npredicate      = ident ":" value\nquery_list     = qparam ( "&" qparam )*\nqparam         = ident [ ":" type ] [ "\|" constraint_list ] [ "=" default ]\nident          = [A-Za-z_][A-Za-z0-9_]*\ntype           = ident\ntransform      = ident [ "(" arg_list ")" ]\ndefault        = string_literal \| number\n'` |
| `TOKEN_TYPES` | `aquilia/patterns/grammar.py` | `['SLASH', 'LANGLE', 'RANGLE', 'LBRACKET', 'RBRACKET', 'LPAREN', 'RPAREN', 'STAR', 'COLON', 'PIPE', 'EQUALS', 'AT', 'COMMA', 'AMP', 'QUESTION', 'IDENT', 'NUMBER', 'STRING', 'REGEX', 'STATIC', 'EOF']` |
| `KEYWORDS` | `aquilia/patterns/grammar.py` | `{'min', 'max', 're', 'in', 'str', 'int', 'float', 'uuid', 'slug', 'path', 'bool', 'json', 'any'}` |
| `CONSTRAINT_OPS` | `aquilia/patterns/grammar.py` | `{'min=': 'minimum value or length', 'max=': 'maximum value or length', 're=': 'regex pattern match', 'in=': 'value must be in enumerated set'}` |
| `DEFAULT_TYPES` | `aquilia/patterns/grammar.py` | `{'id': 'int', 'slug': 'slug', 'uuid': 'uuid', 'path': 'path', 'page': 'int', 'limit': 'int', 'offset': 'int'}` |

## Detailed Classes And Methods

### `FixSuggestion`

- Source: `aquilia/patterns/autofix.py`
- Bases: `object`
- Summary: Represents a single fix suggestion.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `title` | `str` | `` |
| `description` | `str` | `` |
| `old_code` | `str` | `` |
| `new_code` | `str` | `` |
| `confidence` | `float` | `` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `DiagnosticFix`

- Source: `aquilia/patterns/autofix.py`
- Bases: `object`
- Summary: Container for diagnostic with fix suggestions.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `error_message` | `str` | `` |
| `suggestions` | `list[FixSuggestion]` | `` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `AutoFixEngine`

- Source: `aquilia/patterns/autofix.py`
- Bases: `object`
- Summary: Engine for generating automatic fix suggestions.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `suggest_type_fix` | `def suggest_type_fix(self, invalid_type: str)` | Suggest fixes for invalid type names. |
| `suggest_delimiter_fix` | `def suggest_delimiter_fix(self, pattern: str, expected: str)` | Suggest fixes for missing or mismatched delimiters. |
| `suggest_duplicate_param_fix` | `def suggest_duplicate_param_fix(self, pattern: str, duplicate_name: str, occurrences: list[int])` | Suggest fixes for duplicate parameter names. |
| `suggest_conflict_resolution` | `def suggest_conflict_resolution(self, pattern1: CompiledPattern, pattern2: CompiledPattern)` | Suggest fixes for conflicting patterns with same specificity. |
| `suggest_empty_token_fix` | `def suggest_empty_token_fix(self, pattern: str)` | Suggest fixes for empty tokens <>. |
| `suggest_constraint_fix` | `def suggest_constraint_fix(self, invalid_constraint: str, param_type: str)` | Suggest fixes for invalid constraints. |
| `suggest_regex_fix` | `def suggest_regex_fix(self, pattern: str, regex_error: str)` | Suggest fixes for invalid regex patterns. |

### `ErrorRecovery`

- Source: `aquilia/patterns/autofix.py`
- Bases: `object`
- Summary: Error recovery strategies for parser.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `recover_from_unclosed_token` | `def recover_from_unclosed_token(source: str, pos: int)` | Attempt to recover from unclosed token by adding closing delimiter. |
| `recover_from_unclosed_bracket` | `def recover_from_unclosed_bracket(source: str, pos: int)` | Recover from unclosed optional group. |
| `recover_from_invalid_token` | `def recover_from_invalid_token(source: str, pos: int)` | Recover from invalid token by providing default. |

### `CacheStats`

- Source: `aquilia/patterns/cache.py`
- Bases: `object`
- Summary: Cache statistics for monitoring.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `hits` | `int` | `0` |
| `misses` | `int` | `0` |
| `evictions` | `int` | `0` |
| `errors` | `int` | `0` |
| `total_compile_time` | `float` | `0.0` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `hit_rate` | `def hit_rate(self)` | Calculate cache hit rate. |
| `to_dict` | `def to_dict(self)` | Export stats as dictionary. |

### `CacheEntry`

- Source: `aquilia/patterns/cache.py`
- Bases: `object`
- Summary: Cache entry with metadata.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `pattern` | `CompiledPattern` | `` |
| `created_at` | `float` | `` |
| `last_accessed` | `float` | `` |
| `access_count` | `int` | `` |
| `compile_time` | `float` | `` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_expired` | `def is_expired(self, ttl: float \| None)` | Check if entry has expired. |

### `PatternCache`

- Source: `aquilia/patterns/cache.py`
- Bases: `object`
- Summary: Thread-safe LRU cache for compiled patterns with TTL support.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get` | `def get(self, pattern: str, **kwargs)` | Get compiled pattern from cache. |
| `put` | `def put(self, pattern: str, compiled: CompiledPattern, compile_time: float=0.0, **kwargs)` | Store compiled pattern in cache. |
| `compile_with_cache` | `def compile_with_cache(self, pattern: str, **kwargs)` | Compile pattern with caching. |
| `invalidate` | `def invalidate(self, pattern: str \| None=None, **kwargs)` | Invalidate cache entries. |
| `get_stats` | `def get_stats(self)` | Get cache statistics. |
| `reset_stats` | `def reset_stats(self)` | Reset statistics counters. |
| `disabled` | `def disabled(self)` | Context manager to temporarily disable cache. |

### `SegmentKind`

- Source: `aquilia/patterns/compiler/ast_nodes.py`
- Bases: `str, Enum`
- Summary: Kind of path segment.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `STATIC` | `` | `'static'` |
| `TOKEN` | `` | `'token'` |
| `OPTIONAL` | `` | `'optional'` |
| `SPLAT` | `` | `'splat'` |

### `ConstraintKind`

- Source: `aquilia/patterns/compiler/ast_nodes.py`
- Bases: `str, Enum`
- Summary: Kind of constraint.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `MIN` | `` | `'min'` |
| `MAX` | `` | `'max'` |
| `REGEX` | `` | `'regex'` |
| `ENUM` | `` | `'enum'` |
| `PREDICATE` | `` | `'predicate'` |

### `Span`

- Source: `aquilia/patterns/compiler/ast_nodes.py`
- Bases: `object`
- Summary: Source code span for diagnostics.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `start` | `int` | `` |
| `end` | `int` | `` |
| `line` | `int` | `1` |
| `column` | `int` | `1` |

### `Constraint`

- Source: `aquilia/patterns/compiler/ast_nodes.py`
- Bases: `object`
- Summary: Constraint on a parameter.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `kind` | `ConstraintKind` | `` |
| `value` | `Any` | `` |
| `span` | `Span \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `Transform`

- Source: `aquilia/patterns/compiler/ast_nodes.py`
- Bases: `object`
- Summary: Transform function applied to parameter.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `args` | `list[Any]` | `field(default_factory=list)` |
| `span` | `Span \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `BaseSegment`

- Source: `aquilia/patterns/compiler/ast_nodes.py`
- Bases: `object`
- Summary: Base class for all segments.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `kind` | `SegmentKind` | `field(default=SegmentKind.STATIC, init=False)` |
| `span` | `Span \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `StaticSegment`

- Source: `aquilia/patterns/compiler/ast_nodes.py`
- Bases: `BaseSegment`
- Summary: Static text segment.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `value` | `str` | `''` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `TokenSegment`

- Source: `aquilia/patterns/compiler/ast_nodes.py`
- Bases: `BaseSegment`
- Summary: Named parameter segment with type and constraints.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `''` |
| `param_type` | `str` | `'str'` |
| `constraints` | `list[Constraint]` | `field(default_factory=list)` |
| `default` | `Any \| None` | `None` |
| `transform` | `Transform \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `SplatSegment`

- Source: `aquilia/patterns/compiler/ast_nodes.py`
- Bases: `BaseSegment`
- Summary: Multi-segment capture (*path).
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `''` |
| `param_type` | `str` | `'path'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `OptionalGroup`

- Source: `aquilia/patterns/compiler/ast_nodes.py`
- Bases: `BaseSegment`
- Summary: Optional segment group [...].
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `segments` | `list[BaseSegment]` | `field(default_factory=list)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `QueryParam`

- Source: `aquilia/patterns/compiler/ast_nodes.py`
- Bases: `object`
- Summary: Query parameter definition.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `param_type` | `str` | `'str'` |
| `constraints` | `list[Constraint]` | `field(default_factory=list)` |
| `default` | `Any \| None` | `None` |
| `span` | `Span \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `PatternAST`

- Source: `aquilia/patterns/compiler/ast_nodes.py`
- Bases: `object`
- Summary: Complete AST for a URL pattern.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `raw` | `str` | `` |
| `segments` | `list[BaseSegment]` | `field(default_factory=list)` |
| `query_params` | `list[QueryParam]` | `field(default_factory=list)` |
| `file` | `str \| None` | `None` |
| `span` | `Span \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` | Convert to JSON-serializable dict. |
| `get_static_prefix` | `def get_static_prefix(self)` | Extract maximal static prefix for radix trie. |
| `get_param_names` | `def get_param_names(self)` | Get all parameter names (including nested optionals). |

### `CompiledParam`

- Source: `aquilia/patterns/compiler/compiler.py`
- Bases: `object`
- Summary: Compiled parameter metadata.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `index` | `int` | `` |
| `name` | `str` | `` |
| `param_type` | `str` | `` |
| `constraints` | `list[dict[str, Any]]` | `` |
| `default` | `Any \| None` | `` |
| `transform` | `str \| None` | `` |
| `castor` | `Callable[[str], Any]` | `` |
| `validators` | `list[Callable[[Any], bool]]` | `` |

### `CompiledPattern`

- Source: `aquilia/patterns/compiler/compiler.py`
- Bases: `object`
- Summary: Fully compiled pattern ready for matching.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `raw` | `str` | `` |
| `file` | `str \| None` | `` |
| `span` | `dict[str, int] \| None` | `` |
| `static_prefix` | `str` | `` |
| `segments` | `list[dict[str, Any]]` | `` |
| `params` | `dict[str, CompiledParam]` | `` |
| `query` | `dict[str, CompiledParam]` | `` |
| `specificity` | `int` | `` |
| `compiled_re` | `Pattern \| None` | `` |
| `castors` | `list[Callable]` | `` |
| `openapi` | `dict[str, Any]` | `` |
| `ast` | `PatternAST` | `` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` | Convert to JSON-serializable dict. |
| `to_json` | `def to_json(self, indent: int \| None=2)` | Serialize to JSON string. |

### `PatternCompiler`

- Source: `aquilia/patterns/compiler/compiler.py`
- Bases: `object`
- Summary: Compiles AST into optimized executable patterns.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `compile` | `def compile(self, ast: PatternAST)` | Compile AST into executable pattern. |

### `TokenType`

- Source: `aquilia/patterns/compiler/parser.py`
- Bases: `str, Enum`
- Summary: Token types for the lexer.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `SLASH` | `` | `'SLASH'` |
| `LANGLE` | `` | `'LANGLE'` |
| `RANGLE` | `` | `'RANGLE'` |
| `LBRACKET` | `` | `'LBRACKET'` |
| `RBRACKET` | `` | `'RBRACKET'` |
| `LPAREN` | `` | `'LPAREN'` |
| `RPAREN` | `` | `'RPAREN'` |
| `STAR` | `` | `'STAR'` |
| `COLON` | `` | `'COLON'` |
| `PIPE` | `` | `'PIPE'` |
| `EQUALS` | `` | `'EQUALS'` |
| `AT` | `` | `'AT'` |
| `COMMA` | `` | `'COMMA'` |
| `AMP` | `` | `'AMP'` |
| `QUESTION` | `` | `'QUESTION'` |
| `IDENT` | `` | `'IDENT'` |
| `NUMBER` | `` | `'NUMBER'` |
| `STRING` | `` | `'STRING'` |
| `STATIC` | `` | `'STATIC'` |
| `EOF` | `` | `'EOF'` |

### `PatternToken`

- Source: `aquilia/patterns/compiler/parser.py`
- Bases: `object`
- Summary: A lexical token with position information.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `type` | `TokenType` | `` |
| `value` | `Any` | `` |
| `span` | `Span` | `` |

### `Tokenizer`

- Source: `aquilia/patterns/compiler/parser.py`
- Bases: `object`
- Summary: Tokenizer for URL patterns.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `error` | `def error(self, message: str)` | Create syntax error at current position. |
| `peek` | `def peek(self, offset: int=0)` | Peek at character without consuming. |
| `advance` | `def advance(self)` | Consume and return next character. |
| `skip_whitespace` | `def skip_whitespace(self)` | Skip whitespace characters. |
| `read_ident` | `def read_ident(self)` | Read identifier [A-Za-z_][A-Za-z0-9_]*. |
| `read_number` | `def read_number(self)` | Read numeric literal. |
| `read_string` | `def read_string(self, quote: str)` | Read quoted string. |
| `read_static` | `def read_static(self)` | Read static text until special character. |
| `tokenize` | `def tokenize(self)` | Tokenize the source into tokens. |

### `PatternParser`

- Source: `aquilia/patterns/compiler/parser.py`
- Bases: `object`
- Summary: Parser for URL patterns following the EBNF grammar.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `error` | `def error(self, message: str)` | Create syntax error at current token. |
| `current` | `def current(self)` | Get current token. |
| `peek` | `def peek(self, offset: int=0)` | Peek at token without consuming. |
| `advance` | `def advance(self)` | Consume and return current token. |
| `expect` | `def expect(self, token_type: TokenType)` | Consume token of expected type or error. |
| `match` | `def match(self, *token_types: TokenType)` | Check if current token matches any of the given types. |
| `parse` | `def parse(self, raw: str)` | Parse tokens into AST. |
| `parse_segment_list` | `def parse_segment_list(self)` | Parse segments within a single path component (until a slash or end). |
| `parse_segment` | `def parse_segment(self)` | Parse single segment. |
| `parse_static` | `def parse_static(self)` | Parse static text segment, combining IDENT and STATIC tokens. |
| `parse_token` | `def parse_token(self)` | Parse token segment <name:type\|constraints=default@transform>. |
| `parse_optional` | `def parse_optional(self)` | Parse optional group [...]. |
| `parse_splat` | `def parse_splat(self)` | Parse splat segment *name or *name:type. |
| `parse_constraint_list` | `def parse_constraint_list(self)` | Parse constraint list. |
| `parse_constraint` | `def parse_constraint(self)` | Parse single constraint. |
| `parse_value_list` | `def parse_value_list(self)` | Parse comma-separated value list. |
| `parse_default_value` | `def parse_default_value(self)` | Parse default value. |
| `parse_transform` | `def parse_transform(self)` | Parse transform function. |
| `parse_query_list` | `def parse_query_list(self)` | Parse query parameter list. |
| `parse_query_param` | `def parse_query_param(self)` | Parse single query parameter. |

### `PatternDiagnostic`

- Source: `aquilia/patterns/diagnostics/errors.py`
- Bases: `object`
- Summary: Base class for all pattern diagnostics.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `message` | `str` | `` |
| `span` | `Span \| None` | `None` |
| `file` | `str \| None` | `None` |
| `suggestions` | `list[str]` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `format` | `def format(self)` | Format diagnostic for display. |

### `PatternSyntaxError`

- Source: `aquilia/patterns/diagnostics/errors.py`
- Bases: `PatternDiagnostic, Exception`
- Summary: Syntax error in pattern.

### `PatternSemanticError`

- Source: `aquilia/patterns/diagnostics/errors.py`
- Bases: `PatternDiagnostic, Exception`
- Summary: Semantic error in pattern.

### `RouteAmbiguityError`

- Source: `aquilia/patterns/diagnostics/errors.py`
- Bases: `PatternDiagnostic, Exception`
- Summary: Two routes have ambiguous patterns.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `format` | `def format(self)` | Format ambiguity error. |

### `MatchResult`

- Source: `aquilia/patterns/matcher.py`
- Bases: `object`
- Summary: Result of pattern matching.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `pattern` | `CompiledPattern` | `` |
| `params` | `dict[str, Any]` | `` |
| `query` | `dict[str, Any]` | `` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `PatternMatcher`

- Source: `aquilia/patterns/matcher.py`
- Bases: `object`
- Summary: Matches request paths against compiled patterns.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `add_pattern` | `def add_pattern(self, pattern: CompiledPattern)` | Add a compiled pattern to the matcher. |
| `match` | `async def match(self, path: str, query_params: dict[str, str] \| None=None)` | Match a path against patterns. |

### `TransformRegistry`

- Source: `aquilia/patterns/transforms/registry.py`
- Bases: `object`
- Summary: Registry of transform functions.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `default` | `def default(cls)` | Create registry with built-in transforms. |
| `register` | `def register(self, name: str, transform: Callable)` | Register a custom transform. |
| `get_transform` | `def get_transform(self, name: str)` | Get transform by name. |

### `TypeRegistry`

- Source: `aquilia/patterns/types/registry.py`
- Bases: `object`
- Summary: Registry of type castors for pattern parameters.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `default` | `def default(cls)` | Create registry with built-in types. |
| `register` | `def register(self, type_name: str, castor: Callable[[str], Any])` | Register a custom type castor. |
| `get_castor` | `def get_castor(self, type_name: str)` | Get castor for type. |
| `has_type` | `def has_type(self, type_name: str)` | Check if type is registered. |

### `ConstraintRegistry`

- Source: `aquilia/patterns/validators/registry.py`
- Bases: `object`
- Summary: Registry of constraint validators.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `default` | `def default(cls)` | Create registry with built-in constraints. |
| `register` | `def register(self, name: str, validator: Callable)` | Register a custom constraint validator. |
| `get_validator` | `def get_validator(self, name: str)` | Get validator by name. |

# Patterns API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
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

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `generate_fix_suggestions` | `aquilia/patterns/autofix.py` | `def generate_fix_suggestions(error_type: str, error_message: str, pattern: str, **context) -> DiagnosticFix` | Generate fix suggestions for a diagnostic error. |
| `get_global_cache` | `aquilia/patterns/cache.py` | `def get_global_cache() -> PatternCache` | Get or create global cache instance. |
| `set_global_cache` | `aquilia/patterns/cache.py` | `def set_global_cache(cache: PatternCache &#124; None)` | Set global cache instance. |
| `compile_pattern` | `aquilia/patterns/cache.py` | `def compile_pattern(pattern: str, use_cache: bool = True, **kwargs) -> CompiledPattern` | Convenience function to compile patterns with optional caching. |
| `parse_pattern` | `aquilia/patterns/compiler/parser.py` | `def parse_pattern(source: str, filename: str &#124; None = None) -> PatternAST` | Parse a URL pattern into an AST. |
| `calculate_specificity` | `aquilia/patterns/compiler/specificity.py` | `def calculate_specificity(ast: PatternAST) -> int` | Calculate specificity score for pattern ranking. |
| `generate_lsp_metadata` | `aquilia/patterns/lsp/metadata.py` | `def generate_lsp_metadata(patterns: list[CompiledPattern], output_path: Path)` | Generate patterns.json for LSP consumption. |
| `generate_hover_docs` | `aquilia/patterns/lsp/metadata.py` | `def generate_hover_docs() -> dict[str, str]` | Generate hover documentation for pattern syntax. |
| `generate_autocomplete_snippets` | `aquilia/patterns/lsp/metadata.py` | `def generate_autocomplete_snippets() -> list[dict[str, Any]]` | Generate autocomplete snippets for VS Code. |
| `generate_vscode_extension` | `aquilia/patterns/lsp/metadata.py` | `def generate_vscode_extension(output_dir: Path)` | Generate VS Code extension files for AquilaPatterns. |
| `generate_diagnostic_codes` | `aquilia/patterns/lsp/metadata.py` | `def generate_diagnostic_codes() -> dict[str, str]` | Generate diagnostic code descriptions for LSP. |
| `generate_openapi_params` | `aquilia/patterns/openapi.py` | `def generate_openapi_params(pattern: CompiledPattern) -> list[dict[str, Any]]` | Generate OpenAPI parameter definitions from a compiled pattern. |
| `generate_openapi_path` | `aquilia/patterns/openapi.py` | `def generate_openapi_path(pattern: CompiledPattern) -> str` | Convert aquilia pattern to OpenAPI path template format. |
| `pattern_to_openapi_operation` | `aquilia/patterns/openapi.py` | `def pattern_to_openapi_operation(pattern: CompiledPattern, method: str, handler_name: str, summary: str = '', description: str = '', tags: list[str] = None) -> dict[str, Any]` | Generate a complete OpenAPI operation object. |
| `patterns_to_openapi_spec` | `aquilia/patterns/openapi.py` | `def patterns_to_openapi_spec(patterns: list[tuple[CompiledPattern, str, str]], title: str = 'Aquilia API', version: str = '1.0.0', description: str = '') -> dict[str, Any]` | Generate complete OpenAPI 3.0 specification from patterns. |
| `register_transform` | `aquilia/patterns/transforms/registry.py` | `def register_transform(name: str)` | Decorator to register a custom transform. |
| `register_type` | `aquilia/patterns/types/registry.py` | `def register_type(name: str, castor: Callable[[str], Any])` | Decorator to register a custom type. |
| `register_constraint` | `aquilia/patterns/validators/registry.py` | `def register_constraint(name: str)` | Decorator to register a custom constraint. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `STRONG_TYPES` | `aquilia/patterns/compiler/specificity.py` | `{'int', 'float', 'uuid', 'bool', 'json'}` |
| `EBNF_GRAMMAR` | `aquilia/patterns/grammar.py` | `'\npattern        = "/" segment_list [ "/" ] [ "?" query_list ]\nsegment_list   = segment ( "/" segment )*\nsegment        = static &#124; token &#124; optional &#124; splat\n` |
| `TOKEN_TYPES` | `aquilia/patterns/grammar.py` | `['SLASH', 'LANGLE', 'RANGLE', 'LBRACKET', 'RBRACKET', 'LPAREN', 'RPAREN', 'STAR', 'COLON', 'PIPE', 'EQUALS', 'AT', 'COMMA', 'AMP', 'QUESTION', 'IDENT', 'NUMBER'` |
| `KEYWORDS` | `aquilia/patterns/grammar.py` | `{'min', 'max', 're', 'in', 'str', 'int', 'float', 'uuid', 'slug', 'path', 'bool', 'json', 'any'}` |
| `CONSTRAINT_OPS` | `aquilia/patterns/grammar.py` | `{'min=': 'minimum value or length', 'max=': 'maximum value or length', 're=': 'regex pattern match', 'in=': 'value must be in enumerated set'}` |
| `DEFAULT_TYPES` | `aquilia/patterns/grammar.py` | `{'id': 'int', 'slug': 'slug', 'uuid': 'uuid', 'path': 'path', 'page': 'int', 'limit': 'int', 'offset': 'int'}` |

## Detailed Classes And Methods

### Class: `FixSuggestion`

- Source: `aquilia/patterns/autofix.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Represents a single fix suggestion.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `title` | `str` |  |
| `description` | `str` |  |
| `old_code` | `str` |  |
| `new_code` | `str` |  |
| `confidence` | `float` |  |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `DiagnosticFix`

- Source: `aquilia/patterns/autofix.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Container for diagnostic with fix suggestions.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `error_message` | `str` |  |
| `suggestions` | `list[FixSuggestion]` |  |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `AutoFixEngine`

- Source: `aquilia/patterns/autofix.py`
- Bases: `object`
- Summary: Engine for generating automatic fix suggestions.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `suggest_type_fix` | `def suggest_type_fix(self, invalid_type: str) -> list[FixSuggestion]` |  | Suggest fixes for invalid type names. |
| `suggest_delimiter_fix` | `def suggest_delimiter_fix(self, pattern: str, expected: str) -> list[FixSuggestion]` |  | Suggest fixes for missing or mismatched delimiters. |
| `suggest_duplicate_param_fix` | `def suggest_duplicate_param_fix(self, pattern: str, duplicate_name: str, occurrences: list[int]) -> list[FixSuggestion]` |  | Suggest fixes for duplicate parameter names. |
| `suggest_conflict_resolution` | `def suggest_conflict_resolution(self, pattern1: CompiledPattern, pattern2: CompiledPattern) -> list[FixSuggestion]` |  | Suggest fixes for conflicting patterns with same specificity. |
| `suggest_empty_token_fix` | `def suggest_empty_token_fix(self, pattern: str) -> list[FixSuggestion]` |  | Suggest fixes for empty tokens <>. |
| `suggest_constraint_fix` | `def suggest_constraint_fix(self, invalid_constraint: str, param_type: str) -> list[FixSuggestion]` |  | Suggest fixes for invalid constraints. |
| `suggest_regex_fix` | `def suggest_regex_fix(self, pattern: str, regex_error: str) -> list[FixSuggestion]` |  | Suggest fixes for invalid regex patterns. |

### Class: `ErrorRecovery`

- Source: `aquilia/patterns/autofix.py`
- Bases: `object`
- Summary: Error recovery strategies for parser.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `recover_from_unclosed_token` | `def recover_from_unclosed_token(source: str, pos: int) -> str &#124; None` | staticmethod | Attempt to recover from unclosed token by adding closing delimiter. |
| `recover_from_unclosed_bracket` | `def recover_from_unclosed_bracket(source: str, pos: int) -> str &#124; None` | staticmethod | Recover from unclosed optional group. |
| `recover_from_invalid_token` | `def recover_from_invalid_token(source: str, pos: int) -> str &#124; None` | staticmethod | Recover from invalid token by providing default. |

### Class: `CacheStats`

- Source: `aquilia/patterns/cache.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Cache statistics for monitoring.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `hits` | `int` | `0` |
| `misses` | `int` | `0` |
| `evictions` | `int` | `0` |
| `errors` | `int` | `0` |
| `total_compile_time` | `float` | `0.0` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `hit_rate` | `def hit_rate(self) -> float` | property | Calculate cache hit rate. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Export stats as dictionary. |

### Class: `CacheEntry`

- Source: `aquilia/patterns/cache.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Cache entry with metadata.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `pattern` | `CompiledPattern` |  |
| `created_at` | `float` |  |
| `last_accessed` | `float` |  |
| `access_count` | `int` |  |
| `compile_time` | `float` |  |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_expired` | `def is_expired(self, ttl: float &#124; None) -> bool` |  | Check if entry has expired. |

### Class: `PatternCache`

- Source: `aquilia/patterns/cache.py`
- Bases: `object`
- Summary: Thread-safe LRU cache for compiled patterns with TTL support.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get` | `def get(self, pattern: str, **kwargs) -> CompiledPattern &#124; None` |  | Get compiled pattern from cache. |
| `put` | `def put(self, pattern: str, compiled: CompiledPattern, compile_time: float = 0.0, **kwargs)` |  | Store compiled pattern in cache. |
| `compile_with_cache` | `def compile_with_cache(self, pattern: str, **kwargs) -> CompiledPattern` |  | Compile pattern with caching. |
| `invalidate` | `def invalidate(self, pattern: str &#124; None = None, **kwargs)` |  | Invalidate cache entries. |
| `get_stats` | `def get_stats(self) -> CacheStats` |  | Get cache statistics. |
| `reset_stats` | `def reset_stats(self)` |  | Reset statistics counters. |
| `disabled` | `def disabled(self)` | contextmanager | Context manager to temporarily disable cache. |

### Class: `SegmentKind`

- Source: `aquilia/patterns/compiler/ast_nodes.py`
- Bases: `str, Enum`
- Summary: Kind of path segment.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `STATIC` |  | `'static'` |
| `TOKEN` |  | `'token'` |
| `OPTIONAL` |  | `'optional'` |
| `SPLAT` |  | `'splat'` |

### Class: `ConstraintKind`

- Source: `aquilia/patterns/compiler/ast_nodes.py`
- Bases: `str, Enum`
- Summary: Kind of constraint.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `MIN` |  | `'min'` |
| `MAX` |  | `'max'` |
| `REGEX` |  | `'regex'` |
| `ENUM` |  | `'enum'` |
| `PREDICATE` |  | `'predicate'` |

### Class: `Span`

- Source: `aquilia/patterns/compiler/ast_nodes.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Source code span for diagnostics.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `start` | `int` |  |
| `end` | `int` |  |
| `line` | `int` | `1` |
| `column` | `int` | `1` |

### Class: `Constraint`

- Source: `aquilia/patterns/compiler/ast_nodes.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Constraint on a parameter.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `kind` | `ConstraintKind` |  |
| `value` | `Any` |  |
| `span` | `Span &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `Transform`

- Source: `aquilia/patterns/compiler/ast_nodes.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Transform function applied to parameter.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `args` | `list[Any]` | `field(default_factory=list)` |
| `span` | `Span &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `BaseSegment`

- Source: `aquilia/patterns/compiler/ast_nodes.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Base class for all segments.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `kind` | `SegmentKind` | `field(default=SegmentKind.STATIC, init=False)` |
| `span` | `Span &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `StaticSegment`

- Source: `aquilia/patterns/compiler/ast_nodes.py`
- Bases: `BaseSegment`
- Decorators: `dataclass`
- Summary: Static text segment.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `value` | `str` | `''` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `TokenSegment`

- Source: `aquilia/patterns/compiler/ast_nodes.py`
- Bases: `BaseSegment`
- Decorators: `dataclass`
- Summary: Named parameter segment with type and constraints.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` | `''` |
| `param_type` | `str` | `'str'` |
| `constraints` | `list[Constraint]` | `field(default_factory=list)` |
| `default` | `Any &#124; None` | `None` |
| `transform` | `Transform &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `SplatSegment`

- Source: `aquilia/patterns/compiler/ast_nodes.py`
- Bases: `BaseSegment`
- Decorators: `dataclass`
- Summary: Multi-segment capture (*path).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` | `''` |
| `param_type` | `str` | `'path'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `OptionalGroup`

- Source: `aquilia/patterns/compiler/ast_nodes.py`
- Bases: `BaseSegment`
- Decorators: `dataclass`
- Summary: Optional segment group [...].

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `segments` | `list[BaseSegment]` | `field(default_factory=list)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `QueryParam`

- Source: `aquilia/patterns/compiler/ast_nodes.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Query parameter definition.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `param_type` | `str` | `'str'` |
| `constraints` | `list[Constraint]` | `field(default_factory=list)` |
| `default` | `Any &#124; None` | `None` |
| `span` | `Span &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `PatternAST`

- Source: `aquilia/patterns/compiler/ast_nodes.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Complete AST for a URL pattern.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `raw` | `str` |  |
| `segments` | `list[BaseSegment]` | `field(default_factory=list)` |
| `query_params` | `list[QueryParam]` | `field(default_factory=list)` |
| `file` | `str &#124; None` | `None` |
| `span` | `Span &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Convert to JSON-serializable dict. |
| `get_static_prefix` | `def get_static_prefix(self) -> str` |  | Extract maximal static prefix for radix trie. |
| `get_param_names` | `def get_param_names(self) -> list[str]` |  | Get all parameter names (including nested optionals). |

### Class: `CompiledParam`

- Source: `aquilia/patterns/compiler/compiler.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Compiled parameter metadata.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `index` | `int` |  |
| `name` | `str` |  |
| `param_type` | `str` |  |
| `constraints` | `list[dict[str, Any]]` |  |
| `default` | `Any &#124; None` |  |
| `transform` | `str &#124; None` |  |
| `castor` | `Callable[[str], Any]` |  |
| `validators` | `list[Callable[[Any], bool]]` |  |

### Class: `CompiledPattern`

- Source: `aquilia/patterns/compiler/compiler.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Fully compiled pattern ready for matching.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `raw` | `str` |  |
| `file` | `str &#124; None` |  |
| `span` | `dict[str, int] &#124; None` |  |
| `static_prefix` | `str` |  |
| `segments` | `list[dict[str, Any]]` |  |
| `params` | `dict[str, CompiledParam]` |  |
| `query` | `dict[str, CompiledParam]` |  |
| `specificity` | `int` |  |
| `compiled_re` | `Pattern &#124; None` |  |
| `castors` | `list[Callable]` |  |
| `openapi` | `dict[str, Any]` |  |
| `ast` | `PatternAST` |  |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Convert to JSON-serializable dict. |
| `to_json` | `def to_json(self, indent: int &#124; None = 2) -> str` |  | Serialize to JSON string. |

### Class: `PatternCompiler`

- Source: `aquilia/patterns/compiler/compiler.py`
- Bases: `object`
- Summary: Compiles AST into optimized executable patterns.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `compile` | `def compile(self, ast: PatternAST) -> CompiledPattern` |  | Compile AST into executable pattern. |

### Class: `TokenType`

- Source: `aquilia/patterns/compiler/parser.py`
- Bases: `str, Enum`
- Summary: Token types for the lexer.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `SLASH` |  | `'SLASH'` |
| `LANGLE` |  | `'LANGLE'` |
| `RANGLE` |  | `'RANGLE'` |
| `LBRACKET` |  | `'LBRACKET'` |
| `RBRACKET` |  | `'RBRACKET'` |
| `LPAREN` |  | `'LPAREN'` |
| `RPAREN` |  | `'RPAREN'` |
| `STAR` |  | `'STAR'` |
| `COLON` |  | `'COLON'` |
| `PIPE` |  | `'PIPE'` |
| `EQUALS` |  | `'EQUALS'` |
| `AT` |  | `'AT'` |
| `COMMA` |  | `'COMMA'` |
| `AMP` |  | `'AMP'` |
| `QUESTION` |  | `'QUESTION'` |
| `IDENT` |  | `'IDENT'` |
| `NUMBER` |  | `'NUMBER'` |
| `STRING` |  | `'STRING'` |
| `STATIC` |  | `'STATIC'` |
| `EOF` |  | `'EOF'` |

### Class: `PatternToken`

- Source: `aquilia/patterns/compiler/parser.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A lexical token with position information.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `type` | `TokenType` |  |
| `value` | `Any` |  |
| `span` | `Span` |  |

### Class: `Tokenizer`

- Source: `aquilia/patterns/compiler/parser.py`
- Bases: `object`
- Summary: Tokenizer for URL patterns.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `error` | `def error(self, message: str) -> PatternSyntaxError` |  | Create syntax error at current position. |
| `peek` | `def peek(self, offset: int = 0) -> str &#124; None` |  | Peek at character without consuming. |
| `advance` | `def advance(self) -> str &#124; None` |  | Consume and return next character. |
| `skip_whitespace` | `def skip_whitespace(self)` |  | Skip whitespace characters. |
| `read_ident` | `def read_ident(self) -> str` |  | Read identifier [A-Za-z_][A-Za-z0-9_]*. |
| `read_number` | `def read_number(self) -> float` |  | Read numeric literal. |
| `read_string` | `def read_string(self, quote: str) -> str` |  | Read quoted string. |
| `read_static` | `def read_static(self) -> str` |  | Read static text until special character. |
| `tokenize` | `def tokenize(self) -> list[PatternToken]` |  | Tokenize the source into tokens. |

### Class: `PatternParser`

- Source: `aquilia/patterns/compiler/parser.py`
- Bases: `object`
- Summary: Parser for URL patterns following the EBNF grammar.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `error` | `def error(self, message: str) -> PatternSyntaxError` |  | Create syntax error at current token. |
| `current` | `def current(self) -> PatternToken` |  | Get current token. |
| `peek` | `def peek(self, offset: int = 0) -> PatternToken` |  | Peek at token without consuming. |
| `advance` | `def advance(self) -> PatternToken` |  | Consume and return current token. |
| `expect` | `def expect(self, token_type: TokenType) -> PatternToken` |  | Consume token of expected type or error. |
| `match` | `def match(self, *token_types: TokenType) -> bool` |  | Check if current token matches any of the given types. |
| `parse` | `def parse(self, raw: str) -> PatternAST` |  | Parse tokens into AST. |
| `parse_segment_list` | `def parse_segment_list(self) -> list[BaseSegment]` |  | Parse segments within a single path component (until a slash or end). |
| `parse_segment` | `def parse_segment(self) -> BaseSegment` |  | Parse single segment. |
| `parse_static` | `def parse_static(self) -> StaticSegment` |  | Parse static text segment, combining IDENT and STATIC tokens. |
| `parse_token` | `def parse_token(self) -> TokenSegment` &#124; | Parse token segment <name:type | constraints=default@transform>. |
| `parse_optional` | `def parse_optional(self) -> OptionalGroup` |  | Parse optional group [...]. |
| `parse_splat` | `def parse_splat(self) -> SplatSegment` |  | Parse splat segment *name or *name:type. |
| `parse_constraint_list` | `def parse_constraint_list(self) -> list[Constraint]` |  | Parse constraint list. |
| `parse_constraint` | `def parse_constraint(self) -> Constraint` |  | Parse single constraint. |
| `parse_value_list` | `def parse_value_list(self) -> list[Any]` |  | Parse comma-separated value list. |
| `parse_default_value` | `def parse_default_value(self) -> Any` |  | Parse default value. |
| `parse_transform` | `def parse_transform(self) -> Transform` |  | Parse transform function. |
| `parse_query_list` | `def parse_query_list(self) -> list[QueryParam]` |  | Parse query parameter list. |
| `parse_query_param` | `def parse_query_param(self) -> QueryParam` |  | Parse single query parameter. |

### Class: `PatternDiagnostic`

- Source: `aquilia/patterns/diagnostics/errors.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Base class for all pattern diagnostics.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `message` | `str` |  |
| `span` | `Span &#124; None` | `None` |
| `file` | `str &#124; None` | `None` |
| `suggestions` | `list[str]` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `format` | `def format(self) -> str` |  | Format diagnostic for display. |

### Class: `PatternSyntaxError`

- Source: `aquilia/patterns/diagnostics/errors.py`
- Bases: `PatternDiagnostic, Exception`
- Summary: Syntax error in pattern.

### Class: `PatternSemanticError`

- Source: `aquilia/patterns/diagnostics/errors.py`
- Bases: `PatternDiagnostic, Exception`
- Summary: Semantic error in pattern.

### Class: `RouteAmbiguityError`

- Source: `aquilia/patterns/diagnostics/errors.py`
- Bases: `PatternDiagnostic, Exception`
- Summary: Two routes have ambiguous patterns.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `format` | `def format(self) -> str` |  | Format ambiguity error. |

### Class: `MatchResult`

- Source: `aquilia/patterns/matcher.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Result of pattern matching.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `pattern` | `CompiledPattern` |  |
| `params` | `dict[str, Any]` |  |
| `query` | `dict[str, Any]` |  |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `PatternMatcher`

- Source: `aquilia/patterns/matcher.py`
- Bases: `object`
- Summary: Matches request paths against compiled patterns.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `add_pattern` | `def add_pattern(self, pattern: CompiledPattern)` |  | Add a compiled pattern to the matcher. |
| `match` | `async def match(self, path: str, query_params: dict[str, str] &#124; None = None) -> MatchResult &#124; None` |  | Match a path against patterns. |

### Class: `TransformRegistry`

- Source: `aquilia/patterns/transforms/registry.py`
- Bases: `object`
- Summary: Registry of transform functions.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `default` | `def default(cls) -> 'TransformRegistry'` | classmethod | Create registry with built-in transforms. |
| `register` | `def register(self, name: str, transform: Callable)` |  | Register a custom transform. |
| `get_transform` | `def get_transform(self, name: str) -> Callable` |  | Get transform by name. |

### Class: `TypeRegistry`

- Source: `aquilia/patterns/types/registry.py`
- Bases: `object`
- Summary: Registry of type castors for pattern parameters.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `default` | `def default(cls) -> 'TypeRegistry'` | classmethod | Create registry with built-in types. |
| `register` | `def register(self, type_name: str, castor: Callable[[str], Any])` |  | Register a custom type castor. |
| `get_castor` | `def get_castor(self, type_name: str) -> Callable[[str], Any]` |  | Get castor for type. |
| `has_type` | `def has_type(self, type_name: str) -> bool` |  | Check if type is registered. |

### Class: `ConstraintRegistry`

- Source: `aquilia/patterns/validators/registry.py`
- Bases: `object`
- Summary: Registry of constraint validators.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `default` | `def default(cls) -> 'ConstraintRegistry'` | classmethod | Create registry with built-in constraints. |
| `register` | `def register(self, name: str, validator: Callable)` |  | Register a custom constraint validator. |
| `get_validator` | `def get_validator(self, name: str) -> Callable` |  | Get validator by name. |

## Functions

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `generate_fix_suggestions` | `aquilia/patterns/autofix.py` | `def generate_fix_suggestions(error_type: str, error_message: str, pattern: str, **context) -> DiagnosticFix` | Generate fix suggestions for a diagnostic error. |
| `get_global_cache` | `aquilia/patterns/cache.py` | `def get_global_cache() -> PatternCache` | Get or create global cache instance. |
| `set_global_cache` | `aquilia/patterns/cache.py` | `def set_global_cache(cache: PatternCache &#124; None)` | Set global cache instance. |
| `compile_pattern` | `aquilia/patterns/cache.py` | `def compile_pattern(pattern: str, use_cache: bool = True, **kwargs) -> CompiledPattern` | Convenience function to compile patterns with optional caching. |
| `parse_pattern` | `aquilia/patterns/compiler/parser.py` | `def parse_pattern(source: str, filename: str &#124; None = None) -> PatternAST` | Parse a URL pattern into an AST. |
| `calculate_specificity` | `aquilia/patterns/compiler/specificity.py` | `def calculate_specificity(ast: PatternAST) -> int` | Calculate specificity score for pattern ranking. |
| `generate_lsp_metadata` | `aquilia/patterns/lsp/metadata.py` | `def generate_lsp_metadata(patterns: list[CompiledPattern], output_path: Path)` | Generate patterns.json for LSP consumption. |
| `generate_hover_docs` | `aquilia/patterns/lsp/metadata.py` | `def generate_hover_docs() -> dict[str, str]` | Generate hover documentation for pattern syntax. |
| `generate_autocomplete_snippets` | `aquilia/patterns/lsp/metadata.py` | `def generate_autocomplete_snippets() -> list[dict[str, Any]]` | Generate autocomplete snippets for VS Code. |
| `generate_vscode_extension` | `aquilia/patterns/lsp/metadata.py` | `def generate_vscode_extension(output_dir: Path)` | Generate VS Code extension files for AquilaPatterns. |
| `generate_diagnostic_codes` | `aquilia/patterns/lsp/metadata.py` | `def generate_diagnostic_codes() -> dict[str, str]` | Generate diagnostic code descriptions for LSP. |
| `generate_openapi_params` | `aquilia/patterns/openapi.py` | `def generate_openapi_params(pattern: CompiledPattern) -> list[dict[str, Any]]` | Generate OpenAPI parameter definitions from a compiled pattern. |
| `generate_openapi_path` | `aquilia/patterns/openapi.py` | `def generate_openapi_path(pattern: CompiledPattern) -> str` | Convert aquilia pattern to OpenAPI path template format. |
| `pattern_to_openapi_operation` | `aquilia/patterns/openapi.py` | `def pattern_to_openapi_operation(pattern: CompiledPattern, method: str, handler_name: str, summary: str = '', description: str = '', tags: list[str] = None) -> dict[str, Any]` | Generate a complete OpenAPI operation object. |
| `patterns_to_openapi_spec` | `aquilia/patterns/openapi.py` | `def patterns_to_openapi_spec(patterns: list[tuple[CompiledPattern, str, str]], title: str = 'Aquilia API', version: str = '1.0.0', description: str = '') -> dict[str, Any]` | Generate complete OpenAPI 3.0 specification from patterns. |
| `register_transform` | `aquilia/patterns/transforms/registry.py` | `def register_transform(name: str)` | Decorator to register a custom transform. |
| `register_type` | `aquilia/patterns/types/registry.py` | `def register_type(name: str, castor: Callable[[str], Any])` | Decorator to register a custom type. |
| `register_constraint` | `aquilia/patterns/validators/registry.py` | `def register_constraint(name: str)` | Decorator to register a custom constraint. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `STRONG_TYPES` | `aquilia/patterns/compiler/specificity.py` | `{'int', 'float', 'uuid', 'bool', 'json'}` |
| `EBNF_GRAMMAR` | `aquilia/patterns/grammar.py` | `'\npattern        = "/" segment_list [ "/" ] [ "?" query_list ]\nsegment_list   = segment ( "/" segment )*\nsegment        = static &#124; token &#124; optional &#124; splat\n` |
| `TOKEN_TYPES` | `aquilia/patterns/grammar.py` | `['SLASH', 'LANGLE', 'RANGLE', 'LBRACKET', 'RBRACKET', 'LPAREN', 'RPAREN', 'STAR', 'COLON', 'PIPE', 'EQUALS', 'AT', 'COMMA', 'AMP', 'QUESTION', 'IDENT', 'NUMBER'` |
| `KEYWORDS` | `aquilia/patterns/grammar.py` | `{'min', 'max', 're', 'in', 'str', 'int', 'float', 'uuid', 'slug', 'path', 'bool', 'json', 'any'}` |
| `CONSTRAINT_OPS` | `aquilia/patterns/grammar.py` | `{'min=': 'minimum value or length', 'max=': 'maximum value or length', 're=': 'regex pattern match', 'in=': 'value must be in enumerated set'}` |
| `DEFAULT_TYPES` | `aquilia/patterns/grammar.py` | `{'id': 'int', 'slug': 'slug', 'uuid': 'uuid', 'path': 'path', 'page': 'int', 'limit': 'int', 'offset': 'int'}` |

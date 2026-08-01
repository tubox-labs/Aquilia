"""
AquilaPatterns - Professional URL pattern language and compiler for Aquilia.

This module provides a unique, expressive, static-first URL pattern system with:
- Formal EBNF grammar with tokenizer/parser
- AST compilation with optimized matchers
- Radix trie integration for fast routing
- OpenAPI schema generation
- LSP support for IDE integration
- Comprehensive diagnostics and error reporting
"""

from aquilia._version import __version__  # noqa: F401 — re-exported
from aquilia.patterns.autofix import (
    AutoFixEngine,
    DiagnosticFix,
    ErrorRecovery,
    FixSuggestion,
    generate_fix_suggestions,
)
from aquilia.patterns.cache import PatternCache, compile_pattern, get_global_cache, set_global_cache
from aquilia.patterns.compiler.ast_nodes import (
    OptionalGroup,
    PatternAST,
    QueryParam,
    SplatSegment,
    StaticSegment,
    TokenSegment,
)
from aquilia.patterns.compiler.compiler import CompiledPattern, PatternCompiler
from aquilia.patterns.compiler.parser import PatternParser, PatternToken, parse_pattern
from aquilia.patterns.compiler.specificity import calculate_specificity
from aquilia.patterns.diagnostics.errors import (
    PatternDiagnostic,
    PatternSemanticError,
    PatternSyntaxError,
    RouteAmbiguityError,
)
from aquilia.patterns.matcher import MatchResult, PatternMatcher
from aquilia.patterns.openapi import generate_openapi_params
from aquilia.patterns.transforms.registry import TransformRegistry, register_transform
from aquilia.patterns.types.registry import TypeRegistry, register_type
from aquilia.patterns.validators.registry import ConstraintRegistry, register_constraint

__all__ = [
    # Parser
    "PatternParser",
    "PatternToken",
    "parse_pattern",
    # AST
    "PatternAST",
    "StaticSegment",
    "TokenSegment",
    "OptionalGroup",
    "SplatSegment",
    "QueryParam",
    # Compiler
    "PatternCompiler",
    "CompiledPattern",
    "calculate_specificity",
    # Registries
    "TypeRegistry",
    "register_type",
    "ConstraintRegistry",
    "register_constraint",
    "TransformRegistry",
    "register_transform",
    # Diagnostics
    "PatternSyntaxError",
    "PatternSemanticError",
    "RouteAmbiguityError",
    "PatternDiagnostic",
    # Matcher
    "PatternMatcher",
    "MatchResult",
    # OpenAPI
    "generate_openapi_params",
    # Caching (NEW in v1.0.0)
    "PatternCache",
    "compile_pattern",
    "get_global_cache",
    "set_global_cache",
    # Auto-fix (NEW in v1.0.0)
    "AutoFixEngine",
    "FixSuggestion",
    "DiagnosticFix",
    "generate_fix_suggestions",
    "ErrorRecovery",
]

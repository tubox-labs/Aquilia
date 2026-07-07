"""
Diagnostic errors for AquilaPatterns.
"""

from dataclasses import dataclass

from aquilia.faults.domains import RoutingFault

from ..compiler.ast_nodes import Span


@dataclass
class PatternDiagnostic:
    """Base class for all pattern diagnostics."""

    message: str
    span: Span | None = None
    file: str | None = None
    suggestions: list[str] = None

    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []

    def format(self) -> str:
        """Format diagnostic for display."""
        parts = []

        # Error type and location
        error_type = self.__class__.__name__
        if self.file and self.span:
            parts.append(f"{error_type}: {self.message}")
            parts.append(f"  --> {self.file}:{self.span.line}:{self.span.column}")
        elif self.span:
            parts.append(f"{error_type}: {self.message}")
            parts.append(f"  --> {self.span}")
        else:
            parts.append(f"{error_type}: {self.message}")

        # Suggestions
        if self.suggestions:
            parts.append("\nSuggestions:")
            for i, suggestion in enumerate(self.suggestions, 1):
                parts.append(f"  {i}) {suggestion}")

        return "\n".join(parts)


class PatternSyntaxError(PatternDiagnostic, RoutingFault):
    """Syntax error in pattern."""

    def __init__(self, message: str, **kwargs):
        PatternDiagnostic.__init__(self, message, **kwargs)
        RoutingFault.__init__(
            self,
            code="PATTERN_SYNTAX_ERROR",
            message=self.format(),
            metadata={
                "suggestions": self.suggestions,
                "span": str(self.span) if self.span else None,
                "file": self.file,
            },
        )


class PatternSemanticError(PatternDiagnostic, RoutingFault):
    """Semantic error in pattern."""

    def __init__(self, message: str, **kwargs):
        PatternDiagnostic.__init__(self, message, **kwargs)
        RoutingFault.__init__(
            self,
            code="PATTERN_SEMANTIC_ERROR",
            message=self.format(),
            metadata={
                "suggestions": self.suggestions,
                "span": str(self.span) if self.span else None,
                "file": self.file,
            },
        )


class RouteAmbiguityError(PatternDiagnostic, RoutingFault):
    """Two routes have ambiguous patterns."""

    def __init__(self, message: str, pattern1: str, pattern2: str, specificity: int, **kwargs):
        PatternDiagnostic.__init__(self, message, **kwargs)
        self.pattern1 = pattern1
        self.pattern2 = pattern2
        self.specificity = specificity
        RoutingFault.__init__(
            self,
            code="ROUTE_AMBIGUITY",
            message=self.format(),
            metadata={
                "pattern1": pattern1,
                "pattern2": pattern2,
                "specificity": specificity,
                "suggestions": self.suggestions,
            },
        )

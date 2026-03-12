"""
AST node definitions for AquilaPatterns.

These nodes represent the parsed structure of a URL pattern.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SegmentKind(str, Enum):
    """Kind of path segment."""

    STATIC = "static"
    TOKEN = "token"
    OPTIONAL = "optional"
    SPLAT = "splat"


class ConstraintKind(str, Enum):
    """Kind of constraint."""

    MIN = "min"
    MAX = "max"
    REGEX = "regex"
    ENUM = "enum"
    PREDICATE = "predicate"


@dataclass
class Span:
    """Source code span for diagnostics."""

    start: int
    end: int
    line: int = 1
    column: int = 1

    def __repr__(self) -> str:
        return f"Line {self.line}:{self.column} (pos {self.start}-{self.end})"


@dataclass
class Constraint:
    """Constraint on a parameter."""

    kind: ConstraintKind
    value: Any
    span: Span | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "value": self.value,
        }


@dataclass
class Transform:
    """Transform function applied to parameter."""

    name: str
    args: list[Any] = field(default_factory=list)
    span: Span | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "args": self.args,
        }


@dataclass
class BaseSegment:
    """Base class for all segments."""

    kind: SegmentKind = field(default=SegmentKind.STATIC, init=False)
    span: Span | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind.value}


@dataclass
class StaticSegment(BaseSegment):
    """Static text segment."""

    value: str = ""

    def __post_init__(self):
        self.kind = SegmentKind.STATIC

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "value": self.value,
        }


@dataclass
class TokenSegment(BaseSegment):
    """Named parameter segment with type and constraints."""

    name: str = ""
    param_type: str = "str"
    constraints: list[Constraint] = field(default_factory=list)
    default: Any | None = None
    transform: Transform | None = None

    def __post_init__(self):
        self.kind = SegmentKind.TOKEN

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "name": self.name,
            "type": self.param_type,
            "constraints": [c.to_dict() for c in self.constraints],
            "default": self.default,
            "transform": self.transform.to_dict() if self.transform else None,
        }


@dataclass
class SplatSegment(BaseSegment):
    """Multi-segment capture (*path)."""

    name: str = ""
    param_type: str = "path"

    def __post_init__(self):
        self.kind = SegmentKind.SPLAT

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "name": self.name,
            "type": self.param_type,
        }


@dataclass
class OptionalGroup(BaseSegment):
    """Optional segment group [...]."""

    segments: list[BaseSegment] = field(default_factory=list)

    def __post_init__(self):
        self.kind = SegmentKind.OPTIONAL

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "segments": [s.to_dict() for s in self.segments],
        }


@dataclass
class QueryParam:
    """Query parameter definition."""

    name: str
    param_type: str = "str"
    constraints: list[Constraint] = field(default_factory=list)
    default: Any | None = None
    span: Span | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.param_type,
            "constraints": [c.to_dict() for c in self.constraints],
            "default": self.default,
        }


@dataclass
class PatternAST:
    """Complete AST for a URL pattern."""

    raw: str
    segments: list[BaseSegment] = field(default_factory=list)
    query_params: list[QueryParam] = field(default_factory=list)
    file: str | None = None
    span: Span | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "raw": self.raw,
            "file": self.file,
            "span": {"start": self.span.start, "end": self.span.end} if self.span else None,
            "segments": [s.to_dict() for s in self.segments],
            "query_params": [q.to_dict() for q in self.query_params],
        }

    def get_static_prefix(self) -> str:
        """Extract maximal static prefix for radix trie."""
        prefix_parts = []
        for segment in self.segments:
            if isinstance(segment, StaticSegment):
                prefix_parts.append(segment.value)
            else:
                break
        prefix = "/" + "/".join(prefix_parts) if prefix_parts else ""
        # print(f"DEBUG: get_static_prefix for {self.raw} -> {prefix} (parts: {prefix_parts})")
        return prefix

    def get_param_names(self) -> list[str]:
        """Get all parameter names (including nested optionals)."""
        names = []

        def collect(segments: list[BaseSegment]):
            for seg in segments:
                if isinstance(seg, (TokenSegment, SplatSegment)):
                    names.append(seg.name)
                elif isinstance(seg, OptionalGroup):
                    collect(seg.segments)

        collect(self.segments)
        return names

"""Dataclasses shared across the Aquilia MCP server."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SourceAnchor:
    """A source-backed location that can be cited in tool output."""

    path: str
    line: int
    kind: str
    name: str
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SourceFile:
    """Indexed file metadata and compact searchable content."""

    path: str
    kind: str
    title: str
    summary: str
    symbols: list[str] = field(default_factory=list)
    anchors: list[SourceAnchor] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    sections: list[dict[str, Any]] = field(default_factory=list)
    content_hash: str = ""
    size: int = 0
    text: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["anchors"] = [anchor.to_dict() for anchor in self.anchors]
        return data


@dataclass(frozen=True)
class SearchResult:
    """Deterministic ranked search result."""

    path: str
    score: float
    summary: str
    anchors: list[SourceAnchor] = field(default_factory=list)
    symbols: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "score": self.score,
            "summary": self.summary,
            "anchors": [anchor.to_dict() for anchor in self.anchors],
            "symbols": self.symbols,
        }


@dataclass
class KnowledgeIndex:
    """Persistent local index of Aquilia source, docs, examples, and tests."""

    root: str
    aquilia_version: str
    fingerprint: str
    built_at: str
    sources: list[SourceFile] = field(default_factory=list)
    facts: list[dict[str, Any]] = field(default_factory=list)
    cli_commands: list[dict[str, Any]] = field(default_factory=list)
    deprecations: list[dict[str, Any]] = field(default_factory=list)
    examples: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "root": self.root,
            "aquilia_version": self.aquilia_version,
            "fingerprint": self.fingerprint,
            "built_at": self.built_at,
            "sources": [source.to_dict() for source in self.sources],
            "facts": self.facts,
            "cli_commands": self.cli_commands,
            "deprecations": self.deprecations,
            "examples": self.examples,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KnowledgeIndex:
        sources: list[SourceFile] = []
        for item in data.get("sources", []):
            anchors = [SourceAnchor(**anchor) for anchor in item.get("anchors", [])]
            source_data = dict(item)
            source_data["anchors"] = anchors
            source_data.setdefault("imports", [])
            source_data.setdefault("sections", [])
            sources.append(SourceFile(**source_data))
        return cls(
            root=data["root"],
            aquilia_version=data["aquilia_version"],
            fingerprint=data["fingerprint"],
            built_at=data["built_at"],
            sources=sources,
            facts=list(data.get("facts", [])),
            cli_commands=list(data.get("cli_commands", [])),
            deprecations=list(data.get("deprecations", [])),
            examples=list(data.get("examples", [])),
            metadata=dict(data.get("metadata", {})),
        )

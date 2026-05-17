"""Test corpus loader."""

from __future__ import annotations

from ..models import SourceFile


def test_mappings(sources: list[SourceFile]) -> list[dict[str, object]]:
    return [
        {"path": source.path, "symbols": source.symbols[:20], "summary": source.summary}
        for source in sources
        if source.path.startswith("tests/")
    ]

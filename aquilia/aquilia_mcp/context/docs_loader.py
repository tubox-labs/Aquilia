"""Documentation index loader."""

from __future__ import annotations

from ..models import SourceFile


def docs_summary(sources: list[SourceFile]) -> list[dict[str, object]]:
    return [
        {"path": source.path, "title": source.title, "summary": source.summary}
        for source in sources
        if source.path.startswith("docs/")
    ]

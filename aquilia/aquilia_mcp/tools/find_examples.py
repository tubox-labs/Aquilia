"""find_examples tool."""

from __future__ import annotations

from ..models import KnowledgeIndex


def find_examples(index: KnowledgeIndex, arguments: dict) -> dict:
    query = str(arguments.get("query") or "").lower()
    limit = min(int(arguments.get("limit", 10)), 50)
    examples = index.examples
    if query:
        examples = [
            example
            for example in examples
            if query in str(example["name"]).lower()
            or any(query in str(feature).lower() for feature in example.get("features", []))
            or any(query in str(path).lower() for path in example.get("paths", []))
        ]
    return {"examples": examples[:limit], "count": len(examples)}

"""find_api tool."""

from __future__ import annotations

from ..context.search import search_index
from ..models import KnowledgeIndex


def find_api(index: KnowledgeIndex, arguments: dict) -> dict:
    limit = min(int(arguments.get("limit", 8)), 25)
    results = search_index(index, arguments["query"], limit=limit, kind=arguments.get("kind") or None)
    return {
        "query": arguments["query"],
        "results": [result.to_dict() for result in results],
        "source": {"fingerprint": index.fingerprint, "aquilia_version": index.aquilia_version},
    }

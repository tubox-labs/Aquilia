"""Deterministic lightweight search over the local knowledge index."""

from __future__ import annotations

import re

from ..cache import LRUCache
from ..models import KnowledgeIndex, SearchResult

_CACHE: LRUCache[tuple[str, str, int], list[SearchResult]] = LRUCache(max_size=128)


def _tokens(value: str) -> list[str]:
    return [t.lower() for t in re.findall(r"[A-Za-z0-9_]{2,}", value)]


def search_index(index: KnowledgeIndex, query: str, *, limit: int = 10, kind: str | None = None) -> list[SearchResult]:
    normalized_query = " ".join(_tokens(query))
    q = normalized_query
    cache_key = (index.fingerprint, f"{kind or '*'}:{q}", limit)
    cached = _CACHE.get(cache_key)
    if cached is not None:
        return cached
    terms = _tokens(query)
    if not terms:
        return []
    results: list[SearchResult] = []
    for source in index.sources:
        if kind and source.kind != kind:
            continue
        haystacks = {
            "path": source.path.lower(),
            "title": source.title.lower(),
            "summary": source.summary.lower(),
            "symbols": " ".join(source.symbols).lower(),
            "text": source.text.lower(),
        }
        score = 0.0
        phrase = normalized_query
        if phrase and phrase in haystacks["path"]:
            score += 12
        if phrase and phrase in haystacks["symbols"]:
            score += 8
        if phrase and phrase in haystacks["text"]:
            score += 4
        for term in terms:
            if term in haystacks["path"]:
                score += 8
            if term in haystacks["title"]:
                score += 6
            if term in haystacks["symbols"]:
                score += 5
            if term in haystacks["summary"]:
                score += 3
            if term in haystacks["text"]:
                score += min(haystacks["text"].count(term), 5)
        if score:
            results.append(
                SearchResult(
                    path=source.path,
                    score=round(score, 3),
                    summary=source.summary,
                    anchors=source.anchors[:5],
                    symbols=source.symbols[:20],
                )
            )
    results.sort(key=lambda item: (-item.score, item.path))
    final = results[:limit]
    _CACHE.set(cache_key, final)
    return final

"""Persistent source-backed index builder for Aquilia MCP."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from aquilia import __version__ as aquilia_version

from ..faults import MCPIndexFault
from ..models import KnowledgeIndex
from .cli_loader import load_cli_commands
from .examples_loader import example_mappings
from .facts import derive_facts
from .parser import parse_source_file
from .scanner import iter_source_files


def _content_fingerprint(root: Path, file_hashes: list[tuple[str, str]]) -> str:
    digest = hashlib.sha256()
    digest.update(str(aquilia_version).encode())
    for rel, content_hash in file_hashes:
        digest.update(rel.encode())
        digest.update(content_hash.encode())
    return digest.hexdigest()[:24]


def build_index(root: Path) -> KnowledgeIndex:
    root = root.expanduser().resolve()
    sources = [parse_source_file(root, path) for path in iter_source_files(root)]
    file_hashes = [(source.path, source.content_hash) for source in sources]
    fingerprint = _content_fingerprint(root, file_hashes)
    facts, deprecations = derive_facts(sources)
    return KnowledgeIndex(
        root=str(root),
        aquilia_version=str(aquilia_version),
        fingerprint=fingerprint,
        built_at=datetime.now(timezone.utc).isoformat(),
        sources=sources,
        facts=facts,
        cli_commands=load_cli_commands(root),
        deprecations=deprecations,
        examples=example_mappings(sources),
    )


def save_index(index: KnowledgeIndex, path: Path) -> None:
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index.to_dict(), indent=2, sort_keys=True), encoding="utf-8")


def load_index(path: Path) -> KnowledgeIndex:
    try:
        data = json.loads(path.expanduser().read_text(encoding="utf-8"))
        return KnowledgeIndex.from_dict(data)
    except Exception as exc:
        raise MCPIndexFault(f"Could not load MCP index: {exc}") from exc


def load_or_build_index(root: Path, path: Path | None, *, force: bool = False) -> KnowledgeIndex:
    root = root.expanduser().resolve()
    if path is not None and path.exists() and not force:
        existing = load_index(path)
        current = build_index(root)
        if existing.fingerprint == current.fingerprint:
            return existing
        if path is not None:
            save_index(current, path)
        return current
    index = build_index(root)
    if path is not None:
        save_index(index, path)
    return index

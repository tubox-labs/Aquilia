"""Persistent source-backed index builder for Aquilia MCP."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from aquilia import __version__ as aquilia_version

from ..faults import MCPIndexFault
from ..models import KnowledgeIndex
from .cli_loader import load_cli_commands
from .examples_loader import example_mappings
from .facts import derive_facts
from .parser import parse_source_file
from .scanner import iter_source_files, resolve_repository_root


def _content_fingerprint(root: Path, file_hashes: list[tuple[str, str]]) -> str:
    digest = hashlib.sha256()
    digest.update(str(aquilia_version).encode())
    for rel, content_hash in file_hashes:
        digest.update(rel.encode())
        digest.update(content_hash.encode())
    return digest.hexdigest()[:24]


def tree_fingerprint(root: Path) -> str:
    """Fingerprint the indexed source tree without parsing every file."""
    root = resolve_repository_root(root)
    digest = hashlib.sha256()
    digest.update(str(aquilia_version).encode())
    for path in iter_source_files(root):
        rel = path.relative_to(root).as_posix()
        stat = path.stat()
        digest.update(rel.encode())
        digest.update(str(stat.st_size).encode())
        digest.update(str(stat.st_mtime_ns).encode())
    return digest.hexdigest()[:24]


def build_index(root: Path) -> KnowledgeIndex:
    root = resolve_repository_root(root)
    indexed_paths = iter_source_files(root)
    sources = [parse_source_file(root, path) for path in indexed_paths]
    file_hashes = [(source.path, source.content_hash) for source in sources]
    fingerprint = _content_fingerprint(root, file_hashes)
    facts, deprecations = derive_facts(sources)
    tree_fp = tree_fingerprint(root)
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
        metadata={
            "schema_version": 1,
            "tree_fingerprint": tree_fp,
            "source_count": len(sources),
            "indexed_globs": [
                "aquilia/**/*.py",
                "docs/**/*.md",
                "examples/**/*",
                "tests/**/test_*.py",
            ],
        },
    )


def save_index(index: KnowledgeIndex, path: Path) -> None:
    """Persist the knowledge index via ArtifactStore backend (atomic write)."""
    from aquilia.artifacts.backends.json_file import JSONFileBackend
    from aquilia.artifacts.canonical import bare_fingerprint
    from aquilia.artifacts.envelope import ArtifactEnvelope

    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = index.to_dict()
    fp = bare_fingerprint(payload, exclude_keys=frozenset())
    envelope = ArtifactEnvelope.build(
        artifact_type="mcp_knowledge_index",
        key="main",
        schema_version="1.0",
        payload=payload,
        fingerprint=fp,
    )
    JSONFileBackend().write_sync(path, envelope.to_dict())


def load_index(path: Path) -> KnowledgeIndex:
    """Load knowledge index via ArtifactStore backend."""
    from aquilia.artifacts.backends.json_file import JSONFileBackend
    from aquilia.artifacts.envelope import ArtifactEnvelope

    try:
        path = path.expanduser().resolve()
        raw = JSONFileBackend().read_sync(path)
        if raw is None:
            raise MCPIndexFault(f"MCP index not found at '{path}'.")

        # Support new ArtifactEnvelope format and legacy plain dict
        if raw.get("format") == "aquilia-artifact":
            envelope = ArtifactEnvelope.from_dict(raw)
            data = envelope.payload
        else:
            data = raw  # Legacy: plain KnowledgeIndex dict

        return KnowledgeIndex.from_dict(data)
    except MCPIndexFault:
        raise
    except Exception as exc:
        raise MCPIndexFault(f"Could not load MCP index: {exc}") from exc


def load_or_build_index(root: Path, path: Path | None, *, force: bool = False) -> KnowledgeIndex:
    root = resolve_repository_root(root)
    if path is not None and path.exists() and not force:
        existing = load_index(path)
        if existing.metadata.get("tree_fingerprint") == tree_fingerprint(root):
            return existing
        current = build_index(root)
        save_index(current, path)
        return current
    index = build_index(root)
    if path is not None:
        save_index(index, path)
    return index

"""Security helpers for the read-only MCP server."""

from __future__ import annotations

import os
from pathlib import Path

from .faults import MCPSecurityFault

_BINARY_SUFFIXES = {
    ".DS_Store",
    ".a",
    ".avif",
    ".bin",
    ".db",
    ".gif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".mp4",
    ".o",
    ".pdf",
    ".png",
    ".pyc",
    ".pyo",
    ".so",
    ".sqlite",
    ".sqlite3",
    ".surp",
    ".webp",
    ".zip",
}


def is_binary_path(path: Path) -> bool:
    return path.name in _BINARY_SUFFIXES or path.suffix.lower() in _BINARY_SUFFIXES


def resolve_under_root(root: Path, relative_or_uri: str | Path) -> Path:
    raw = str(relative_or_uri)
    if "\x00" in raw:
        raise MCPSecurityFault("Path contains a null byte")
    if raw.startswith("aquilia://"):
        raw = raw.removeprefix("aquilia://")
    candidate = Path(raw)
    if candidate.is_absolute():
        raise MCPSecurityFault("Absolute paths are not accepted by MCP resource readers", metadata={"path": raw})
    resolved_root = Path(os.path.realpath(root))
    resolved = Path(os.path.realpath(resolved_root / candidate))
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise MCPSecurityFault("Path traversal outside the workspace is not allowed", metadata={"path": raw}) from exc
    return resolved


def resolve_readable_file(root: Path, relative_or_uri: str | Path) -> Path:
    """Resolve a resource URI/path to a readable non-binary file under *root*."""
    path = resolve_under_root(root, relative_or_uri)
    if not path.exists():
        raise MCPSecurityFault("Resource does not exist", metadata={"path": str(relative_or_uri)})
    if not path.is_file():
        raise MCPSecurityFault("Resource is not a file", metadata={"path": str(relative_or_uri)})
    if is_binary_path(path):
        raise MCPSecurityFault("Binary resources are not exposed by the MCP server", metadata={"path": str(relative_or_uri)})
    return path


def redact_secrets(text: str) -> str:
    redacted = text
    secret_markers = ("api_key", "apikey", "password", "secret", "token", "credential")
    for line in text.splitlines():
        lower = line.lower()
        if any(marker in lower for marker in secret_markers) and ("=" in line or ":" in line):
            redacted = redacted.replace(line, "<redacted secret-like line>")
    return redacted

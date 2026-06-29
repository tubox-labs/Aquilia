"""Filesystem scanner for the MCP knowledge index."""

from __future__ import annotations

from pathlib import Path

from aquilia.faults.domains import ConfigInvalidFault

from ..security import is_binary_path

_EXCLUDED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "artifacts",
    "dist",
    "node_modules",
}


def _is_generated(path: Path) -> bool:
    parts = set(path.parts)
    return bool(parts & _EXCLUDED_DIRS) or path.name.endswith((".bak", ".bak2"))


def _include_file(root: Path, path: Path) -> bool:
    if _is_generated(path) or is_binary_path(path):
        return False
    rel = path.relative_to(root)
    rel_str = rel.as_posix()
    if rel_str.startswith("aquilia/") and path.suffix == ".py":
        return True
    if rel_str.startswith("docs/") and path.suffix == ".md":
        return True
    if rel_str.startswith("examples/") and path.is_file():
        return path.suffix in {"", ".py", ".md", ".json", ".toml", ".txt", ".sh", ".yml", ".yaml"}
    if rel_str.startswith("tests/") and path.name.startswith("test_") and path.suffix == ".py":
        return True
    return False


def resolve_repository_root(root: Path) -> Path:
    root = root.resolve()
    if not (root / "aquilia").is_dir():
        for parent in root.parents:
            if (parent / "aquilia").is_dir():
                return parent
        raise ConfigInvalidFault(key="mcp.root", reason="Expected repository root containing aquilia/")
    return root


def iter_source_files(root: Path) -> list[Path]:
    root = resolve_repository_root(root)
    files = [path for path in root.rglob("*") if path.is_file() and _include_file(root, path)]
    return sorted(files, key=lambda p: p.relative_to(root).as_posix())

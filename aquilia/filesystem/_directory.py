"""
Directory Operations — Async wrappers for directory manipulation.

Provides async equivalents of ``os.listdir``, ``os.walk``, ``os.scandir``,
``shutil.rmtree``, ``shutil.copytree``, and related functions.

All operations are delegated to the dedicated filesystem thread pool.
Recursive operations enforce a configurable depth limit (SEC-FS-10).
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import (
    AsyncIterator,
    List,
    Optional,
    Tuple,
    Union,
)

from ._config import FileSystemConfig
from ._errors import wrap_os_error, FileSystemIOFault
from ._pool import FileSystemPool


# ═══════════════════════════════════════════════════════════════════════════
# DirEntry — Async-friendly directory entry
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True, slots=True)
class DirEntry:
    """
    Async-friendly directory entry (mirrors ``os.DirEntry``).

    Fields are pre-populated from ``os.scandir()`` to avoid
    additional I/O for common queries.
    """

    name: str
    """Entry name (basename only)."""

    path: str
    """Full path."""

    is_file_cached: bool
    """Whether this entry is a regular file."""

    is_dir_cached: bool
    """Whether this entry is a directory."""

    is_symlink_cached: bool
    """Whether this entry is a symbolic link."""

    inode: int = 0
    """Inode number (platform-dependent)."""


# ═══════════════════════════════════════════════════════════════════════════
# Directory Operations
# ═══════════════════════════════════════════════════════════════════════════

async def list_dir(
    path: Union[str, Path],
    *,
    pool: Optional[FileSystemPool] = None,
) -> List[str]:
    """
    List directory contents (names only).

    Async equivalent of ``os.listdir()``.

    Args:
        path: Directory to list.
        pool: Thread pool to use.

    Returns:
        List of entry names (files and directories).
    """
    _pool = pool or _get_default_pool()
    path = Path(path)

    try:
        return await _pool.run(os.listdir, str(path))
    except Exception as exc:
        raise wrap_os_error(exc, "listdir", str(path)) from exc


async def scan_dir(
    path: Union[str, Path],
    *,
    pool: Optional[FileSystemPool] = None,
) -> List[DirEntry]:
    """
    Scan directory contents with metadata.

    Async equivalent of ``os.scandir()``.  Returns ``DirEntry`` objects
    with cached ``is_file``, ``is_dir``, ``is_symlink`` results.

    Args:
        path: Directory to scan.
        pool: Thread pool to use.

    Returns:
        List of ``DirEntry`` objects.
    """
    _pool = pool or _get_default_pool()
    path_str = str(path)

    def _scan() -> List[DirEntry]:
        entries: List[DirEntry] = []
        with os.scandir(path_str) as it:
            for entry in it:
                entries.append(DirEntry(
                    name=entry.name,
                    path=entry.path,
                    is_file_cached=entry.is_file(follow_symlinks=False),
                    is_dir_cached=entry.is_dir(follow_symlinks=False),
                    is_symlink_cached=entry.is_symlink(),
                    inode=entry.inode(),
                ))
        return entries

    try:
        return await _pool.run(_scan)
    except Exception as exc:
        raise wrap_os_error(exc, "scandir", path_str) from exc


async def make_dir(
    path: Union[str, Path],
    *,
    mode: int = 0o777,
    parents: bool = False,
    exist_ok: bool = False,
    pool: Optional[FileSystemPool] = None,
) -> None:
    """
    Create a directory.

    Async equivalent of ``os.makedirs()`` / ``Path.mkdir()``.

    Args:
        path: Directory to create.
        mode: Directory permissions.
        parents: Create parent directories as needed.
        exist_ok: Don't raise if directory already exists.
        pool: Thread pool to use.
    """
    _pool = pool or _get_default_pool()
    path = Path(path)

    def _mkdir() -> None:
        path.mkdir(mode=mode, parents=parents, exist_ok=exist_ok)

    try:
        await _pool.run(_mkdir)
    except Exception as exc:
        raise wrap_os_error(exc, "mkdir", str(path)) from exc


async def remove_dir(
    path: Union[str, Path],
    *,
    pool: Optional[FileSystemPool] = None,
) -> None:
    """
    Remove an empty directory.

    Async equivalent of ``os.rmdir()`` / ``Path.rmdir()``.

    Args:
        path: Directory to remove (must be empty).
        pool: Thread pool to use.
    """
    _pool = pool or _get_default_pool()
    path = Path(path)

    try:
        await _pool.run(path.rmdir)
    except Exception as exc:
        raise wrap_os_error(exc, "rmdir", str(path)) from exc


async def remove_tree(
    path: Union[str, Path],
    *,
    ignore_errors: bool = False,
    pool: Optional[FileSystemPool] = None,
    config: Optional[FileSystemConfig] = None,
) -> None:
    """
    Recursively remove a directory tree.

    Async equivalent of ``shutil.rmtree()``.

    SEC-FS-10: Enforces a maximum recursion depth to prevent
    path bomb attacks.

    Args:
        path: Root directory to remove.
        ignore_errors: If True, errors are silently ignored.
        pool: Thread pool to use.
        config: Filesystem config (for depth limit).
    """
    _pool = pool or _get_default_pool()
    cfg = config or FileSystemConfig()
    path_str = str(path)

    def _rmtree() -> None:
        # Verify depth limit before proceeding
        _check_depth(path_str, cfg.max_recursion_depth)
        shutil.rmtree(path_str, ignore_errors=ignore_errors)

    try:
        await _pool.run(_rmtree)
    except Exception as exc:
        if ignore_errors:
            return
        raise wrap_os_error(exc, "rmtree", path_str) from exc


async def copy_tree(
    src: Union[str, Path],
    dst: Union[str, Path],
    *,
    pool: Optional[FileSystemPool] = None,
    config: Optional[FileSystemConfig] = None,
    symlinks: bool = False,
    dirs_exist_ok: bool = False,
) -> str:
    """
    Recursively copy a directory tree.

    Async equivalent of ``shutil.copytree()``.

    SEC-FS-10: Enforces maximum recursion depth.

    Args:
        src: Source directory.
        dst: Destination directory.
        pool: Thread pool to use.
        config: Filesystem config.
        symlinks: Copy symlinks as symlinks (vs following them).
        dirs_exist_ok: Don't raise if destination dirs exist.

    Returns:
        Destination path as string.
    """
    _pool = pool or _get_default_pool()
    cfg = config or FileSystemConfig()
    src_str = str(src)
    dst_str = str(dst)

    def _copytree() -> str:
        _check_depth(src_str, cfg.max_recursion_depth)
        result = shutil.copytree(
            src_str, dst_str,
            symlinks=symlinks,
            dirs_exist_ok=dirs_exist_ok,
        )
        return str(result)

    try:
        return await _pool.run(_copytree)
    except Exception as exc:
        raise wrap_os_error(exc, "copytree", src_str) from exc


async def walk(
    top: Union[str, Path],
    *,
    topdown: bool = True,
    followlinks: bool = False,
    pool: Optional[FileSystemPool] = None,
    config: Optional[FileSystemConfig] = None,
) -> AsyncIterator[Tuple[str, List[str], List[str]]]:
    """
    Recursively walk a directory tree.

    Async equivalent of ``os.walk()``.

    SEC-FS-10: Enforces maximum recursion depth.

    Args:
        top: Root directory to walk.
        topdown: If True, yield directory before its subdirectories.
        followlinks: If True, follow symbolic links.
        pool: Thread pool to use.
        config: Filesystem config.

    Yields:
        ``(dirpath, dirnames, filenames)`` tuples.
    """
    _pool = pool or _get_default_pool()
    cfg = config or FileSystemConfig()
    top_str = str(top)

    def _walk() -> List[Tuple[str, List[str], List[str]]]:
        results: List[Tuple[str, List[str], List[str]]] = []
        depth = 0
        for dirpath, dirnames, filenames in os.walk(
            top_str, topdown=topdown, followlinks=followlinks,
        ):
            # Approximate depth check
            rel = os.path.relpath(dirpath, top_str)
            depth = 0 if rel == "." else rel.count(os.sep) + 1
            if depth > cfg.max_recursion_depth:
                dirnames.clear()  # Prune further descent
                continue
            results.append((dirpath, list(dirnames), list(filenames)))
        return results

    try:
        results = await _pool.run(_walk)
    except Exception as exc:
        raise wrap_os_error(exc, "walk", top_str) from exc

    for entry in results:
        yield entry


# ═══════════════════════════════════════════════════════════════════════════
# Internal Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _check_depth(path: str, max_depth: int) -> None:
    """
    Verify that a directory tree doesn't exceed the depth limit.

    Performs a quick breadth-first scan to check maximum depth.
    This is a best-effort check — the actual recursive operation
    may encounter deeper paths created concurrently.
    """
    depth = 0
    for dirpath, dirnames, _ in os.walk(path):
        rel = os.path.relpath(dirpath, path)
        current_depth = 0 if rel == "." else rel.count(os.sep) + 1
        if current_depth > max_depth:
            raise FileSystemIOFault(
                operation="depth_check",
                path=path,
                reason=f"Directory tree exceeds maximum depth ({max_depth})",
            )
        if current_depth >= max_depth:
            dirnames.clear()  # Don't descend further


def _get_default_pool() -> FileSystemPool:
    """Get the default filesystem pool (lazy singleton)."""
    from ._path import _get_default_pool as _get
    return _get()

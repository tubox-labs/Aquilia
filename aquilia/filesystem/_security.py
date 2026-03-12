"""
Filesystem Security — Path validation, sanitization, and sandbox enforcement.

This module is the security gateway for all filesystem operations.  Every
path-accepting function in the public API calls ``validate_path`` before
touching the OS.

Security annotations:
    SEC-FS-01  Null byte rejection
    SEC-FS-02  Canonical path resolution via ``os.path.realpath``
    SEC-FS-03  Sandbox containment check
    SEC-FS-04  Path length limit
    SEC-FS-05  Symlink resolution (configurable)
    SEC-FS-13  Filename sanitization
"""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath

from ._config import FileSystemConfig
from ._errors import (
    PathTooLongFault,
    PathTraversalFault,
    PermissionDeniedFault,
)

# ═══════════════════════════════════════════════════════════════════════════
# Path Validation
# ═══════════════════════════════════════════════════════════════════════════


def validate_path(
    path: str | Path,
    *,
    config: FileSystemConfig | None = None,
    sandbox: str | Path | None = None,
    operation: str = "",
) -> Path:
    """
    Validate and resolve a filesystem path through multiple security layers.

    Layers:
        1. Null byte rejection (SEC-FS-01)
        2. Path normalization & canonical resolution (SEC-FS-02)
        3. Sandbox containment check (SEC-FS-03)
        4. Path length validation (SEC-FS-04)

    Args:
        path: The raw path to validate.
        config: Optional ``FileSystemConfig`` for limits.  Uses defaults if None.
        sandbox: Override sandbox root.  If None, uses ``config.sandbox_root``.
        operation: Operation name for fault context.

    Returns:
        Resolved, validated ``Path`` object.

    Raises:
        PathTraversalFault: If the path escapes the sandbox.
        PathTooLongFault: If the path exceeds the configured limit.
        PermissionDeniedFault: If the path contains null bytes.
    """
    cfg = config or FileSystemConfig()
    path_str = str(path)

    # ── Layer 1: Null byte rejection (SEC-FS-01) ────────────────────────
    if "\x00" in path_str:
        raise PermissionDeniedFault(
            operation=operation,
            path="<contains null byte>",
        )

    # ── Layer 2: Canonical resolution (SEC-FS-02) ──────────────────────
    resolved = Path(os.path.realpath(path_str))

    # ── Layer 3: Path length check (SEC-FS-04) ─────────────────────────
    resolved_str = str(resolved)
    if len(resolved_str) > cfg.max_path_length:
        raise PathTooLongFault(
            operation=operation,
            path=path_str,
            length=len(resolved_str),
            max_length=cfg.max_path_length,
        )

    # ── Layer 4: Sandbox containment (SEC-FS-03) ───────────────────────
    sandbox_root = sandbox or cfg.sandbox_root
    if sandbox_root is not None:
        sandbox_resolved = Path(os.path.realpath(str(sandbox_root)))
        # Use os.path.commonpath to prevent prefix-matching pitfalls
        # e.g. /app/data-evil should not match sandbox /app/data
        try:
            resolved.relative_to(sandbox_resolved)
        except ValueError:
            raise PathTraversalFault(
                operation=operation,
                path=path_str,
            )

    return resolved


def validate_relative_path(
    name: str,
    *,
    config: FileSystemConfig | None = None,
    operation: str = "",
) -> str:
    """
    Validate a relative path/filename (no sandbox, just safety checks).

    Used for storage keys, upload filenames, etc.

    Checks:
        - No null bytes
        - No ``..`` segments after normalization
        - Path length within limits

    Args:
        name: The relative path to validate.
        config: Optional config for limits.
        operation: Operation name for fault context.

    Returns:
        Normalized relative path string.

    Raises:
        PermissionDeniedFault: On null bytes.
        PathTraversalFault: On ``..`` segments.
        PathTooLongFault: On excessive length.
    """
    cfg = config or FileSystemConfig()

    # Null byte check
    if "\x00" in name:
        raise PermissionDeniedFault(
            operation=operation,
            path="<contains null byte>",
        )

    # Normalize
    normalized = str(PurePosixPath(name)).lstrip("/")

    # Reject .. segments
    parts = normalized.split("/")
    if ".." in parts:
        raise PathTraversalFault(
            operation=operation,
            path=name,
        )

    # Length check
    if len(normalized) > cfg.max_path_length:
        raise PathTooLongFault(
            operation=operation,
            path=name,
            length=len(normalized),
            max_length=cfg.max_path_length,
        )

    return normalized


# ═══════════════════════════════════════════════════════════════════════════
# Filename Sanitization (SEC-FS-13)
# ═══════════════════════════════════════════════════════════════════════════

# Characters unsafe for filenames on any major OS
_UNSAFE_CHARS = frozenset('<>:"|?*\x00')

# Control characters (U+0000 – U+001F)
_CONTROL_CHARS = frozenset(chr(c) for c in range(0x20))

# Shell metacharacters
_SHELL_CHARS = frozenset(";|&$`(){}[]!~")

# Windows reserved names
_WINDOWS_RESERVED = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }
)

# All dangerous characters combined
_DANGEROUS = _UNSAFE_CHARS | _CONTROL_CHARS | _SHELL_CHARS | frozenset("/\\")


def sanitize_filename(
    filename: str,
    *,
    max_length: int = 255,
    replacement: str = "_",
) -> str:
    """
    Sanitize a filename for safe storage.

    SEC-FS-13: Removes path separators, null bytes, control characters,
    shell metacharacters, and reserved names.

    Args:
        filename: Raw filename (may contain dangerous characters).
        max_length: Maximum allowed length.
        replacement: Character to replace dangerous characters with.

    Returns:
        A safe filename string.  Never empty (falls back to ``"unnamed"``).
    """
    # Strip path components (take only the basename)
    filename = os.path.basename(filename)

    # Replace dangerous characters
    result: list[str] = []
    for ch in filename:
        if ch in _DANGEROUS:
            result.append(replacement)
        else:
            result.append(ch)
    filename = "".join(result)

    # Strip leading/trailing dots and whitespace
    filename = filename.strip(". \t\n\r")

    # Check for Windows reserved names
    name_upper = filename.split(".")[0].upper()
    if name_upper in _WINDOWS_RESERVED:
        filename = f"_{filename}"

    # Truncate to max length, preserving extension
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        available = max_length - len(ext)
        filename = name[:available] + ext if available > 0 else filename[:max_length]

    # Ensure non-empty
    if not filename or filename == replacement:
        filename = "unnamed"

    return filename

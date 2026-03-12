"""
Filesystem Errors — Typed fault hierarchy for file operations.

All filesystem errors extend ``aquilia.faults.domains.FilesystemFault``
(which extends ``IOFault`` → ``Fault``).  Each fault carries:

- A unique code (``FS_*``)
- The operation that failed (read, write, delete, …)
- The path involved
- A human-readable reason
- Severity and retryability metadata

Security annotation SEC-FS-11: All faults default to ``public=False``
to prevent leaking internal paths to HTTP clients.
"""

from __future__ import annotations

import builtins
import errno
from typing import Any

from aquilia.faults.core import Fault, FaultDomain, Severity

# ═══════════════════════════════════════════════════════════════════════════
# Filesystem Fault Domain
# ═══════════════════════════════════════════════════════════════════════════

FS_DOMAIN = FaultDomain.IO  # Reuse the standard I/O domain


# ═══════════════════════════════════════════════════════════════════════════
# Base Filesystem Fault
# ═══════════════════════════════════════════════════════════════════════════


class FileSystemFault(Fault):
    """Base class for all filesystem faults."""

    __slots__ = ("operation", "path", "reason")

    def __init__(
        self,
        *,
        code: str,
        message: str,
        operation: str = "",
        path: str = "",
        reason: str = "",
        severity: Severity = Severity.ERROR,
        retryable: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.operation = operation
        self.path = path
        self.reason = reason
        _meta = {
            "operation": operation,
            "path": path,
            "reason": reason,
        }
        if metadata:
            _meta.update(metadata)
        super().__init__(
            code=code,
            message=message,
            domain=FS_DOMAIN,
            severity=severity,
            retryable=retryable,
            public=False,  # SEC-FS-11: never leak paths to clients
            metadata=_meta,
        )


# ═══════════════════════════════════════════════════════════════════════════
# Concrete Fault Types
# ═══════════════════════════════════════════════════════════════════════════


class FileNotFoundFault(FileSystemFault):
    """Raised when a file or directory does not exist."""

    def __init__(self, operation: str = "", path: str = "", **kw: Any) -> None:
        super().__init__(
            code="FS_NOT_FOUND",
            message=f"File not found: '{path}'" if path else "File not found",
            operation=operation,
            path=path,
            severity=Severity.WARN,
            retryable=False,
            **kw,
        )


class PermissionDeniedFault(FileSystemFault):
    """Raised when the process lacks permission for the operation."""

    def __init__(self, operation: str = "", path: str = "", **kw: Any) -> None:
        super().__init__(
            code="FS_PERMISSION_DENIED",
            message=f"Permission denied: '{path}'" if path else "Permission denied",
            operation=operation,
            path=path,
            severity=Severity.ERROR,
            retryable=False,
            **kw,
        )


class FileExistsFault(FileSystemFault):
    """Raised when a file already exists and overwrite is not allowed."""

    def __init__(self, operation: str = "", path: str = "", **kw: Any) -> None:
        super().__init__(
            code="FS_ALREADY_EXISTS",
            message=f"File already exists: '{path}'" if path else "File already exists",
            operation=operation,
            path=path,
            severity=Severity.WARN,
            retryable=False,
            **kw,
        )


class IsDirectoryFault(FileSystemFault):
    """Raised when a file operation is attempted on a directory."""

    def __init__(self, operation: str = "", path: str = "", **kw: Any) -> None:
        super().__init__(
            code="FS_IS_DIRECTORY",
            message=f"Is a directory: '{path}'" if path else "Is a directory",
            operation=operation,
            path=path,
            severity=Severity.WARN,
            retryable=False,
            **kw,
        )


class NotDirectoryFault(FileSystemFault):
    """Raised when a directory operation is attempted on a file."""

    def __init__(self, operation: str = "", path: str = "", **kw: Any) -> None:
        super().__init__(
            code="FS_NOT_DIRECTORY",
            message=f"Not a directory: '{path}'" if path else "Not a directory",
            operation=operation,
            path=path,
            severity=Severity.WARN,
            retryable=False,
            **kw,
        )


class DiskFullFault(FileSystemFault):
    """Raised when no space is left on device."""

    def __init__(self, operation: str = "", path: str = "", **kw: Any) -> None:
        super().__init__(
            code="FS_DISK_FULL",
            message="No space left on device",
            operation=operation,
            path=path,
            severity=Severity.FATAL,
            retryable=True,  # Retryable after freeing space
            **kw,
        )


class PathTraversalFault(FileSystemFault):
    """
    Raised when a path traversal attack is detected.

    Security annotation: SEC-FS-01 through SEC-FS-03.
    """

    def __init__(self, operation: str = "", path: str = "", **kw: Any) -> None:
        super().__init__(
            code="FS_PATH_TRAVERSAL",
            message="Path traversal blocked",
            operation=operation,
            path=path,
            severity=Severity.FATAL,
            retryable=False,
            **kw,
        )


class PathTooLongFault(FileSystemFault):
    """Raised when a path exceeds the configured maximum length."""

    def __init__(self, operation: str = "", path: str = "", length: int = 0, max_length: int = 0, **kw: Any) -> None:
        super().__init__(
            code="FS_PATH_TOO_LONG",
            message=f"Path too long ({length} chars, max {max_length})",
            operation=operation,
            path=path,
            severity=Severity.ERROR,
            retryable=False,
            metadata={"length": length, "max_length": max_length},
            **kw,
        )


class FileSystemIOFault(FileSystemFault):
    """Generic I/O error for unclassified OS errors."""

    def __init__(self, operation: str = "", path: str = "", reason: str = "", **kw: Any) -> None:
        super().__init__(
            code="FS_IO_ERROR",
            message=f"I/O error during {operation}: {reason}" if reason else f"I/O error during {operation}",
            operation=operation,
            path=path,
            reason=reason,
            severity=Severity.ERROR,
            retryable=True,
            **kw,
        )


class FileClosedFault(FileSystemFault):
    """Raised when an operation is attempted on a closed file."""

    def __init__(self, operation: str = "", path: str = "", **kw: Any) -> None:
        super().__init__(
            code="FS_FILE_CLOSED",
            message="I/O operation on closed file",
            operation=operation,
            path=path,
            severity=Severity.ERROR,
            retryable=False,
            **kw,
        )


# ═══════════════════════════════════════════════════════════════════════════
# OS Error → Fault Mapper
# ═══════════════════════════════════════════════════════════════════════════


def wrap_os_error(exc: BaseException, operation: str = "", path: str = "") -> FileSystemFault:
    """
    Convert an OS-level exception to a typed ``FileSystemFault``.

    This is the single entry-point for error translation.  Called at
    the executor boundary in ``_pool.py``.

    Args:
        exc: The caught exception.
        operation: Human-readable operation name (e.g. "read", "write").
        path: The filesystem path involved.

    Returns:
        A concrete ``FileSystemFault`` subclass.
    """
    if isinstance(exc, builtins.FileNotFoundError):
        return FileNotFoundFault(operation=operation, path=path)

    if isinstance(exc, builtins.PermissionError):
        return PermissionDeniedFault(operation=operation, path=path)

    if isinstance(exc, builtins.FileExistsError):
        return FileExistsFault(operation=operation, path=path)

    if isinstance(exc, builtins.IsADirectoryError):
        return IsDirectoryFault(operation=operation, path=path)

    if isinstance(exc, builtins.NotADirectoryError):
        return NotDirectoryFault(operation=operation, path=path)

    if isinstance(exc, OSError):
        if exc.errno == errno.ENOSPC:
            return DiskFullFault(operation=operation, path=path)
        return FileSystemIOFault(operation=operation, path=path, reason=str(exc))

    # Fallback for unexpected exceptions
    return FileSystemIOFault(
        operation=operation,
        path=path,
        reason=f"{type(exc).__name__}: {exc}",
    )

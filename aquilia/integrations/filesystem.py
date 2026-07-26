"""
FileSystemIntegration — typed local filesystem configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FileSystemIntegration:
    """
    Typed configuration for the local filesystem subsystem.

    Declaring this integration makes ``FileSystem`` injectable from the DI
    container and hands its thread pool to the server lifecycle, replacing
    manual construction and registration in application code.

    Attributes:
        enabled: Register the subsystem.  Disabled by default, so existing
            applications that construct ``FileSystem`` by hand are unaffected.
        sandbox_root: Directory tree all file operations must stay within.
            Strongly recommended whenever paths derive from user input.
        allow_unsandboxed: When ``False``, an unset ``sandbox_root`` is a
            configuration error instead of silently disabling containment.
        max_pool_threads: Size of the dedicated blocking-I/O pool.
        max_path_length: Reject paths longer than this (SEC-FS-04).
        follow_symlinks: Whether ``stat`` and directory scans describe a link
            or its target.  Does not affect sandbox containment, which always
            resolves symlinks first.
        atomic_writes: Use write-to-temp plus ``os.replace`` for file writes.

    Example::

        from aquilia.integrations import Integration

        Integration.filesystem(
            enabled=True,
            sandbox_root="/srv/uploads",
            allow_unsandboxed=False,
        )
    """

    _integration_type: str = field(default="filesystem", init=False, repr=False)

    enabled: bool = False
    sandbox_root: str | None = None
    allow_unsandboxed: bool = True
    max_pool_threads: int = 8
    max_path_length: int = 1024
    follow_symlinks: bool = False
    atomic_writes: bool = True

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize to the configuration mapping consumed at boot.

        Returns:
            A dictionary keyed for ``ConfigLoader.get_filesystem_config()``.
        """
        return {
            "_integration_type": "filesystem",
            "enabled": self.enabled,
            "sandbox_root": self.sandbox_root,
            "allow_unsandboxed": self.allow_unsandboxed,
            "max_pool_threads": self.max_pool_threads,
            "max_path_length": self.max_path_length,
            "follow_symlinks": self.follow_symlinks,
            "atomic_writes": self.atomic_writes,
        }

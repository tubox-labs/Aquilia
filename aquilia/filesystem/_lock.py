"""
Async File Locking — Advisory file locks for concurrent access safety.

Provides a portable async file lock using ``fcntl.flock`` (POSIX) or
``msvcrt.locking`` (Windows) under the hood.

Usage::

    from aquilia.filesystem import AsyncFileLock

    lock = AsyncFileLock("/tmp/myapp.lock")
    async with lock:
        # Critical section — only one process/task at a time
        ...

Supports timeout, shared/exclusive modes, and reentrant acquisition
from the same task.
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Optional, Union

from ._config import FileSystemConfig
from ._errors import FileSystemFault, wrap_os_error
from ._pool import FileSystemPool

# Platform-specific imports
if sys.platform == "win32":
    import msvcrt  # type: ignore[import-not-found]
    _HAS_FCNTL = False
else:
    import fcntl
    _HAS_FCNTL = True


class LockAcquisitionError(FileSystemFault):
    """Raised when a file lock cannot be acquired."""

    __slots__ = ("_timeout",)

    def __init__(self, path: str, timeout: float) -> None:
        self._timeout = timeout
        super().__init__(
            code="FS_LOCK_TIMEOUT",
            message=f"Failed to acquire lock on '{path}' within {timeout:.1f}s",
            operation="lock",
            path=path,
        )

    @property
    def timeout(self) -> float:
        return self._timeout


class AsyncFileLock:
    """
    Async advisory file lock.

    Wraps the platform's file locking mechanism (``fcntl.flock`` on
    POSIX, ``msvcrt.locking`` on Windows) in an async-friendly API.

    Parameters
    ----------
    path
        Path to the lock file.  Created automatically if it doesn't exist.
    timeout
        Maximum seconds to wait for the lock.  ``-1`` means wait forever.
        ``0`` means non-blocking (fail immediately).
    poll_interval
        Seconds between lock acquisition attempts when waiting.
    shared
        If ``True``, acquire a shared (read) lock instead of exclusive.
    pool
        Filesystem pool for offloading blocking operations.
    config
        Filesystem configuration.

    Usage::

        lock = AsyncFileLock("/var/lock/app.lock", timeout=5.0)

        async with lock:
            # Exclusive access
            ...

        # Or explicit acquire/release
        await lock.acquire()
        try:
            ...
        finally:
            await lock.release()
    """

    __slots__ = (
        "_path",
        "_timeout",
        "_poll_interval",
        "_shared",
        "_pool",
        "_config",
        "_fd",
        "_lock_count",
        "_owner_task",
    )

    def __init__(
        self,
        path: Union[str, Path],
        *,
        timeout: float = -1,
        poll_interval: float = 0.05,
        shared: bool = False,
        pool: Optional[FileSystemPool] = None,
        config: Optional[FileSystemConfig] = None,
    ) -> None:
        self._path = str(path)
        self._timeout = timeout
        self._poll_interval = poll_interval
        self._shared = shared
        self._pool = pool or _get_default_pool()
        self._config = config or FileSystemConfig()
        self._fd: Optional[int] = None
        self._lock_count = 0
        self._owner_task: Optional[asyncio.Task] = None

    @property
    def path(self) -> str:
        """Lock file path."""
        return self._path

    @property
    def is_locked(self) -> bool:
        """Whether the lock is currently held."""
        return self._fd is not None

    async def acquire(self) -> None:
        """
        Acquire the file lock.

        Reentrant: if the current task already holds the lock, the
        internal counter is incremented.

        Raises
        ------
        LockAcquisitionError
            If the lock cannot be acquired within the timeout.
        """
        current = asyncio.current_task()
        if self._fd is not None and self._owner_task is current:
            self._lock_count += 1
            return

        deadline = (
            None if self._timeout < 0
            else time.monotonic() + self._timeout
        )

        while True:
            try:
                await self._try_acquire()
                self._lock_count = 1
                self._owner_task = current
                return
            except _WouldBlock:
                if deadline is not None and time.monotonic() >= deadline:
                    raise LockAcquisitionError(self._path, self._timeout)
                await asyncio.sleep(self._poll_interval)

    async def release(self) -> None:
        """
        Release the file lock.

        Decrements the reentrant counter; the lock is actually released
        only when the counter reaches zero.
        """
        if self._fd is None:
            return

        self._lock_count -= 1
        if self._lock_count > 0:
            return

        fd = self._fd
        self._fd = None
        self._owner_task = None
        self._lock_count = 0

        def _release():
            try:
                if _HAS_FCNTL:
                    fcntl.flock(fd, fcntl.LOCK_UN)
                else:
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            finally:
                os.close(fd)

        try:
            await self._pool.run(_release)
        except Exception:
            # Best effort — if we can't unlock, at least close the FD
            try:
                os.close(fd)
            except OSError:
                pass

    async def _try_acquire(self) -> None:
        """Attempt a non-blocking lock acquisition."""
        def _lock():
            fd = os.open(self._path, os.O_RDWR | os.O_CREAT, 0o644)
            try:
                if _HAS_FCNTL:
                    flag = fcntl.LOCK_SH if self._shared else fcntl.LOCK_EX
                    fcntl.flock(fd, flag | fcntl.LOCK_NB)
                else:
                    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            except (BlockingIOError, OSError) as exc:
                os.close(fd)
                if isinstance(exc, BlockingIOError) or (
                    hasattr(exc, "errno") and exc.errno in (11, 35, 36)
                ):
                    raise _WouldBlock() from None
                raise
            return fd

        try:
            self._fd = await self._pool.run(_lock)
        except _WouldBlock:
            raise
        except Exception as exc:
            raise wrap_os_error(exc, "lock", self._path) from exc

    async def __aenter__(self) -> "AsyncFileLock":
        await self.acquire()
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.release()


class _WouldBlock(Exception):
    """Internal signal: lock attempt would block."""
    __slots__ = ()


def _get_default_pool() -> FileSystemPool:
    """Get the default filesystem pool (lazy singleton)."""
    from ._path import _get_default_pool as _get
    return _get()

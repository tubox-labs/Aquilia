"""
Storage Executor -- Dedicated thread pool for blocking cloud SDK calls.

Cloud SDKs (``boto3``, ``google-cloud-storage``, ``azure-storage-blob``,
``paramiko``) are synchronous, so every call must be offloaded off the event
loop.  Using ``run_in_executor(None, ...)`` would put that traffic on the
interpreter's shared default executor, where it competes with unrelated
library code and cannot be sized or observed.

This module provides a single dedicated, bounded pool for all storage
backends, mirroring the discipline of ``aquilia.filesystem.FileSystemPool``.

Usage::

    from aquilia.storage.executor import run_blocking

    head = await run_blocking(client.head_object, Bucket=bucket, Key=key)
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")

#: Environment override for the pool size.
_ENV_MAX_WORKERS = "AQUILIA_STORAGE_MAX_WORKERS"

_executor: ThreadPoolExecutor | None = None


def _default_max_workers() -> int:
    """
    Return the default worker count for the storage pool.

    Returns:
        The value of ``AQUILIA_STORAGE_MAX_WORKERS`` when set and positive,
        otherwise ``min(32, cpu_count + 4)``.
    """
    raw = os.environ.get(_ENV_MAX_WORKERS, "")
    if raw.isdigit() and int(raw) > 0:
        return int(raw)
    return min(32, (os.cpu_count() or 4) + 4)


def get_executor() -> ThreadPoolExecutor:
    """
    Return the shared storage thread pool, creating it on first use.

    Returns:
        The process-wide :class:`ThreadPoolExecutor` used by all storage
        backends.

    Usage::

        loop.run_in_executor(get_executor(), fn)
    """
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(
            max_workers=_default_max_workers(),
            thread_name_prefix="aquilia-storage",
        )
    return _executor


async def run_blocking(fn: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    """
    Run a blocking callable on the dedicated storage pool.

    Args:
        fn: Synchronous callable to execute.
        *args: Positional arguments forwarded to *fn*.
        **kwargs: Keyword arguments forwarded to *fn*.

    Returns:
        Whatever *fn* returns.

    Raises:
        Exception: Any exception raised by *fn* propagates unchanged.

    Usage::

        data = await run_blocking(client.get_object, Bucket="b", Key="k")
    """
    loop = asyncio.get_running_loop()
    if kwargs:
        return await loop.run_in_executor(get_executor(), lambda: fn(*args, **kwargs))
    return await loop.run_in_executor(get_executor(), fn, *args)  # type: ignore[arg-type]


def shutdown_executor(wait: bool = False) -> None:
    """
    Shut down the shared storage pool.

    Args:
        wait: Block until queued work drains.

    Returns:
        ``None``.

    Note:
        Called during server shutdown.  A subsequent :func:`run_blocking` will
        transparently create a fresh pool.
    """
    global _executor
    if _executor is not None:
        _executor.shutdown(wait=wait)
        _executor = None


__all__: list[str] = ["get_executor", "run_blocking", "shutdown_executor"]

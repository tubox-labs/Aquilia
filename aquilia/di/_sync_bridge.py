"""
Sync→async bridge — run an awaitable from synchronous code, safely.

The DI container is async-first, but two paths must occasionally drive the
async resolution engine from *synchronous* code: :meth:`Container.resolve`
(the sync convenience API) and :class:`_LazyProxy._resolve` (first-touch of a
lazily-injected proxy).

Historically each such call did ``loop = asyncio.new_event_loop(); ...;
loop.close()`` — a full event-loop create+teardown *per call* (Bug 8). Under a
sync-resolve loop that is pure waste. This module keeps **one persistent event
loop per thread**, created lazily and reused, so repeated sync resolutions pay
loop setup exactly once per thread.

Rules enforced here:

* **Never** run inside a running loop — the caller is in async context and must
  ``await`` the async API instead. :func:`run_sync` raises
  :class:`~aquilia.faults.domains.DIResolutionFault` rather than deadlock.
* The persistent loop is **thread-local**: each thread gets its own, so there
  is no cross-thread loop sharing (which asyncio forbids).
* The loop is closed on interpreter shutdown via :mod:`atexit` and can be
  reset explicitly (tests) via :func:`reset_sync_loops`.
"""

from __future__ import annotations

import asyncio
import atexit
import threading
from collections.abc import Coroutine
from typing import Any, TypeVar

T = TypeVar("T")

# One persistent loop per thread (asyncio loops are not thread-safe to share).
_thread_local = threading.local()

# Track every loop we create so atexit can close them all.
_all_loops: list[asyncio.AbstractEventLoop] = []
_all_loops_lock = threading.Lock()


def _get_thread_loop() -> asyncio.AbstractEventLoop:
    """Return this thread's persistent DI bridge loop, creating it once."""
    loop = getattr(_thread_local, "loop", None)
    if loop is None or loop.is_closed():
        loop = asyncio.new_event_loop()
        _thread_local.loop = loop
        with _all_loops_lock:
            _all_loops.append(loop)
    return loop


def run_sync(coro: Coroutine[Any, Any, T], *, provider: str = "<unknown>") -> T:
    """Drive *coro* to completion from synchronous code.

    Reuses a persistent per-thread event loop instead of creating a throwaway
    one per call (Bug 8 fix).

    Args:
        coro: The coroutine to run.
        provider: Label for the fault message if called from async context.

    Returns:
        The coroutine's result.

    Raises:
        DIResolutionFault: If called from within a running event loop (the
            caller must ``await`` the async API instead of blocking).
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        pass  # No running loop — safe to drive synchronously.
    else:
        coro.close()  # avoid "coroutine was never awaited" warning
        from ..faults.domains import DIResolutionFault

        raise DIResolutionFault(
            provider=provider,
            reason=(
                "Synchronous resolution called from a running async context. "
                "Use 'await resolve_async(...)' instead of the sync API."
            ),
        )

    loop = _get_thread_loop()
    return loop.run_until_complete(coro)


def reset_sync_loops() -> None:
    """Close all bridge loops. Intended for test teardown."""
    with _all_loops_lock:
        loops = list(_all_loops)
        _all_loops.clear()
    for loop in loops:
        if not loop.is_closed():
            loop.close()
    if getattr(_thread_local, "loop", None) is not None:
        _thread_local.loop = None


@atexit.register
def _close_all_loops() -> None:
    """Close every bridge loop at interpreter shutdown."""
    with _all_loops_lock:
        loops = list(_all_loops)
        _all_loops.clear()
    for loop in loops:
        try:
            if not loop.is_closed():
                loop.close()
        except Exception:
            pass

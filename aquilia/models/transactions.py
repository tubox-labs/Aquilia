"""
Aquilia Transactions -- atomic() context manager with savepoint support.

Provides safe transaction handling with nested savepoint support,
automatic rollback on exception, and properly scoped commit/rollback hooks.

Usage:
    from aquilia.models.transactions import atomic

    async with atomic():
        user = await User.create(name="Alice")
        await Profile.create(user=user.id)
        # Both committed together

    async with atomic() as sp1:
        await User.create(name="Bob")
        async with atomic() as sp2:
            await Post.create(title="Hello")
            raise ValueError("oops")  # sp2 rolled back
        # sp1 still active -- Bob is saved, Post is not

    # With commit hooks:
    async with atomic() as txn:
        await Order.create(total=100)
        txn.on_commit(lambda: send_email("order confirmed"))
        txn.on_rollback(lambda: log_rollback("order failed"))

    # With isolation level (PostgreSQL/MySQL):
    async with atomic(isolation="SERIALIZABLE"):
        ...

    # As a decorator -- wraps the whole call in a transaction, matching
    # Tortoise ORM's `@atomic()`:
    @atomic()
    async def transfer(src, dst, amount):
        await src.save()
        await dst.save()

    # Read-only -- routes to a reader connection instead of contending for
    # the writer, when the block is known not to write:
    async with atomic(readonly=True):
        ...

    # With a timeout (seconds) -- rolled back and raised as a QueryFault if
    # the block hasn't finished in time, Prisma-style:
    async with atomic(timeout=5.0):
        ...
"""

from __future__ import annotations

import asyncio
import functools
import inspect
import logging
import re
import uuid
import weakref
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager, suppress
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..db.engine import AquiliaDatabase

logger = logging.getLogger("aquilia.models.transactions")

# Regex for validating savepoint identifiers (alphanumeric + underscores only)
_SP_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

__all__ = [
    "atomic",
    "TransactionManager",
    "Atomic",
]

# Track nested transaction depth per asyncio Task using a WeakValueDictionary
# keyed on task. This prevents memory leaks -- when a Task is GC'd, its
# entry is automatically removed.
_task_depths: weakref.WeakValueDictionary = weakref.WeakValueDictionary()


class _DepthHolder:
    """Weak-referenceable holder for an integer depth counter."""

    __slots__ = ("value", "__weakref__")

    def __init__(self, value: int = 0):
        self.value = value


def _get_depth_holder() -> _DepthHolder:
    """
    Get or create the depth counter for the current asyncio task.

    Uses WeakValueDictionary so entries are cleaned up when the Task
    is garbage collected -- no memory leak.
    """
    try:
        task = asyncio.current_task()
        if task is None:
            # Not inside an async task; use a thread-local fallback
            return _DepthHolder(0)
    except RuntimeError:
        return _DepthHolder(0)

    task_id = id(task)
    holder = _task_depths.get(task_id)
    if holder is None:
        holder = _DepthHolder(0)
        _task_depths[task_id] = holder
    return holder


class Atomic:
    """
    Async context manager for database transactions.

    Supports nested savepoints:
    - First atomic() opens a transaction (BEGIN)
    - Nested atomic() creates a SAVEPOINT
    - Exception causes rollback of the innermost savepoint/transaction
    - Successful exit commits or releases the savepoint

    Supports:
    - ``on_commit(fn)`` -- called after outermost commit only
    - ``on_rollback(fn)`` -- called on any rollback
    - ``isolation`` -- set transaction isolation level (PostgreSQL/MySQL)
    - ``durable`` -- disallows nesting
    """

    def __init__(
        self,
        db: AquiliaDatabase | None = None,
        *,
        savepoint: bool = True,
        durable: bool = False,
        isolation: str | None = None,
        readonly: bool = False,
        timeout: float | None = None,
    ):
        """
        Args:
            db: Database instance. If None, uses the default database.
            savepoint: Whether to use savepoints for nesting (default True)
            durable: If True, raises error when used inside another atomic block
            isolation: Transaction isolation level
                (e.g., "READ COMMITTED", "SERIALIZABLE")
            readonly: If True, hints the backend this transaction only reads --
                routes to a reader connection on SQLite instead of contending
                for the single writer. Ignored for nested (savepoint) blocks.
            timeout: Seconds before the block is cancelled, rolled back, and a
                ``QueryFault`` is raised instead of leaving the transaction open.
        """
        self._db = db
        self._use_savepoint = savepoint
        self._durable = durable
        self._isolation = isolation
        self._readonly = readonly
        self._timeout = timeout
        self._savepoint_id: str | None = None
        self._is_outermost = False
        self._depth_holder: _DepthHolder | None = None
        self._commit_hooks: list[Callable] = []
        self._rollback_hooks: list[Callable] = []
        self._timeout_task: asyncio.Task | None = None
        self._timed_out = False

    def _get_db(self) -> AquiliaDatabase:
        if self._db is not None:
            return self._db
        from ..db.engine import get_database

        return get_database()

    def on_commit(self, fn: Callable) -> None:
        """
        Register a function to call after successful outermost commit.

        The hook is NOT called if an inner savepoint rolls back -- only
        after the entire transaction successfully commits.

        Supports both sync and async callables.

        Usage:
            async with atomic() as txn:
                await Order.create(total=100)
                txn.on_commit(lambda: send_notification("created"))
        """
        self._commit_hooks.append(fn)

    def on_rollback(self, fn: Callable) -> None:
        """
        Register a function to call if this block rolls back.

        Usage:
            async with atomic() as txn:
                txn.on_rollback(lambda: log("transaction failed"))
        """
        self._rollback_hooks.append(fn)

    async def _fire_hooks(self, hooks: list[Callable]) -> None:
        """Execute a list of hooks, catching exceptions."""
        for hook in hooks:
            try:
                if inspect.iscoroutinefunction(hook):
                    await hook()
                else:
                    hook()
            except Exception as exc:
                logger.error(f"Transaction hook failed: {exc}")

    async def __aenter__(self) -> Atomic:
        db = self._get_db()
        if not db.is_connected:
            await db.connect()

        self._depth_holder = _get_depth_holder()
        depth = self._depth_holder.value

        if depth == 0:
            # Outermost: start transaction
            self._is_outermost = True

            normalized_isolation: str | None = None
            if self._isolation:
                _ALLOWED_ISOLATION_LEVELS = {
                    "READ UNCOMMITTED",
                    "READ COMMITTED",
                    "REPEATABLE READ",
                    "SERIALIZABLE",
                }
                normalized_isolation = self._isolation.upper().strip()
                if normalized_isolation not in _ALLOWED_ISOLATION_LEVELS:
                    from ..faults.domains import QueryFault

                    raise QueryFault(
                        model="(transaction)",
                        operation="atomic",
                        reason=f"Invalid isolation level: {self._isolation!r}. "
                        f"Allowed: {sorted(_ALLOWED_ISOLATION_LEVELS)}",
                    )

            # Real adapter-level BEGIN (pins a dedicated connection and
            # disables per-statement auto-commit) instead of sending "BEGIN"
            # as ordinary SQL text through execute() -- see module docstring
            # history / CHANGELOG for why the latter silently no-ops.
            await db.begin(isolation=normalized_isolation, readonly=self._readonly)
            self._depth_holder.value = 1
        else:
            if self._durable:
                from ..faults.domains import QueryFault

                raise QueryFault(
                    model="(transaction)",
                    operation="atomic",
                    reason="atomic(durable=True) cannot be nested inside another atomic block",
                )
            if self._use_savepoint:
                # Nested: create savepoint with safe alphanumeric name
                self._savepoint_id = f"sp_{uuid.uuid4().hex[:12]}"
                await db.savepoint(self._savepoint_id)
            self._depth_holder.value = depth + 1

        if self._timeout is not None:
            self._timeout_task = asyncio.ensure_future(self._watchdog(asyncio.current_task()))

        return self

    async def _watchdog(self, owner_task: asyncio.Task | None) -> None:
        """Cancel the owning task if the block outlives ``self._timeout`` seconds."""
        assert self._timeout is not None
        await asyncio.sleep(self._timeout)
        if owner_task is not None and not owner_task.done():
            self._timed_out = True
            owner_task.cancel()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        db = self._get_db()

        # Stop the timeout watchdog before it can fire a spurious late
        # cancellation once we're already past the guarded block.
        if self._timeout_task is not None and not self._timeout_task.done():
            self._timeout_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._timeout_task

        try:
            if exc_type is not None:
                # Exception occurred -- rollback
                if self._savepoint_id:
                    await db.rollback_to_savepoint(self._savepoint_id)
                elif self._is_outermost:
                    await db.rollback()

                # Fire rollback hooks
                await self._fire_hooks(self._rollback_hooks)
            else:
                # Success -- commit or release savepoint
                if self._savepoint_id:
                    await db.release_savepoint(self._savepoint_id)
                elif self._is_outermost:
                    await db.commit()

                    # Fire on_commit hooks only at outermost level
                    await self._fire_hooks(self._commit_hooks)
        finally:
            # Decrement depth
            if self._depth_holder is not None:
                new_depth = self._depth_holder.value - 1
                self._depth_holder.value = max(new_depth, 0)

        if self._timed_out and exc_type is not None and issubclass(exc_type, asyncio.CancelledError):
            from ..faults.domains import QueryFault

            raise QueryFault(
                model="(transaction)",
                operation="atomic",
                reason=f"Transaction exceeded timeout of {self._timeout}s and was rolled back",
            ) from exc_val

        return False  # Don't suppress exceptions

    async def savepoint(self) -> str:
        """Create an explicit savepoint within this atomic block."""
        db = self._get_db()
        sp_id = f"sp_{uuid.uuid4().hex[:12]}"
        await db.savepoint(sp_id)
        return sp_id

    async def rollback_to_savepoint(self, savepoint_id: str) -> None:
        """Roll back to a specific savepoint."""
        if not _SP_NAME_RE.match(savepoint_id):
            from aquilia.faults.domains import QueryFault

            raise QueryFault(
                message=f"Invalid savepoint name: {savepoint_id!r}. Must be alphanumeric/underscores only.",
            )
        db = self._get_db()
        await db.rollback_to_savepoint(savepoint_id)

    async def release_savepoint(self, savepoint_id: str) -> None:
        """Release (commit) a savepoint."""
        if not _SP_NAME_RE.match(savepoint_id):
            from aquilia.faults.domains import QueryFault

            raise QueryFault(
                message=f"Invalid savepoint name: {savepoint_id!r}. Must be alphanumeric/underscores only.",
            )
        db = self._get_db()
        await db.release_savepoint(savepoint_id)

    def __call__(self, func: Callable) -> Callable:
        """
        Use ``atomic()`` as a decorator on an async function (Tortoise-ORM
        style), wrapping the whole call in its own transaction:

            @atomic()
            async def transfer(src, dst, amount):
                ...

        A fresh ``Atomic`` (with the same config) is used per call so
        concurrent calls to the decorated function don't share mutable
        transaction state.
        """
        if not inspect.iscoroutinefunction(func):
            from ..faults.domains import QueryFault

            raise QueryFault(
                model="(transaction)",
                operation="atomic",
                reason=f"atomic() can only decorate an async function, got {func!r}",
            )

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            async with Atomic(
                self._db,
                savepoint=self._use_savepoint,
                durable=self._durable,
                isolation=self._isolation,
                readonly=self._readonly,
                timeout=self._timeout,
            ):
                return await func(*args, **kwargs)

        return wrapper


def atomic(
    db: AquiliaDatabase | None = None,
    *,
    savepoint: bool = True,
    durable: bool = False,
    isolation: str | None = None,
    readonly: bool = False,
    timeout: float | None = None,
) -> Atomic:
    """
    Create an atomic transaction context manager (and/or decorator).

    Can be used as a context manager:
        async with atomic():
            ...

    Or with a specific database:
        async with atomic(db=my_db):
            ...

    Or with isolation level (PostgreSQL/MySQL):
        async with atomic(isolation="SERIALIZABLE"):
            ...

    Or as a decorator on an async function:
        @atomic()
        async def transfer(src, dst, amount):
            ...

    Or read-only (routes to a reader connection on SQLite instead of the
    single writer):
        async with atomic(readonly=True):
            ...

    Or with a timeout in seconds (rolled back and raised as a QueryFault if
    exceeded):
        async with atomic(timeout=5.0):
            ...

    Args:
        db: Database instance. If None, uses the default.
        savepoint: Use savepoints for nesting (default True)
        durable: Disallow nesting inside another atomic block
        isolation: SQL transaction isolation level
        readonly: Hint that this transaction only reads
        timeout: Seconds before the block is cancelled and rolled back
    """
    return Atomic(
        db,
        savepoint=savepoint,
        durable=durable,
        isolation=isolation,
        readonly=readonly,
        timeout=timeout,
    )


class TransactionManager:
    """
    Higher-level transaction manager with properly scoped on_commit hooks.

    Unlike using bare on_commit hooks, TransactionManager ensures hooks
    are tied to the outermost transaction and only fire on full success.
    """

    def __init__(self, db: AquiliaDatabase | None = None):
        self._db = db
        self._on_commit_hooks: list[Callable] = []
        self._on_rollback_hooks: list[Callable] = []

    def on_commit(self, func: Callable) -> None:
        """Register a function to be called after successful commit."""
        self._on_commit_hooks.append(func)

    def on_rollback(self, func: Callable) -> None:
        """Register a function to be called on rollback."""
        self._on_rollback_hooks.append(func)

    @asynccontextmanager
    async def atomic(self, **kwargs) -> AsyncIterator[Atomic]:
        """
        Use as: async with manager.atomic() as txn: ...

        All on_commit/on_rollback hooks from the manager are attached
        to the outermost transaction.
        """
        txn = Atomic(self._db, **kwargs)

        # Transfer manager hooks to the transaction
        for hook in self._on_commit_hooks:
            txn.on_commit(hook)
        for hook in self._on_rollback_hooks:
            txn.on_rollback(hook)

        try:
            async with txn:
                yield txn
        finally:
            # Clear hooks after execution
            self._on_commit_hooks.clear()
            self._on_rollback_hooks.clear()

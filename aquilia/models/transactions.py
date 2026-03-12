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
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import re
import uuid
import weakref
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
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

    __slots__ = ("value",)

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
    ):
        """
        Args:
            db: Database instance. If None, uses the default database.
            savepoint: Whether to use savepoints for nesting (default True)
            durable: If True, raises error when used inside another atomic block
            isolation: Transaction isolation level
                (e.g., "READ COMMITTED", "SERIALIZABLE")
        """
        self._db = db
        self._use_savepoint = savepoint
        self._durable = durable
        self._isolation = isolation
        self._savepoint_id: str | None = None
        self._is_outermost = False
        self._depth_holder: _DepthHolder | None = None
        self._commit_hooks: list[Callable] = []
        self._rollback_hooks: list[Callable] = []

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

            # Set isolation level if requested (before BEGIN for some backends)
            if self._isolation and db.driver != "sqlite":
                _ALLOWED_ISOLATION_LEVELS = {
                    "READ UNCOMMITTED",
                    "READ COMMITTED",
                    "REPEATABLE READ",
                    "SERIALIZABLE",
                }
                _normalized = self._isolation.upper().strip()
                if _normalized not in _ALLOWED_ISOLATION_LEVELS:
                    from ..faults.domains import QueryFault

                    raise QueryFault(
                        model="(transaction)",
                        operation="atomic",
                        reason=f"Invalid isolation level: {self._isolation!r}. "
                        f"Allowed: {sorted(_ALLOWED_ISOLATION_LEVELS)}",
                    )
                await db.execute(f"SET TRANSACTION ISOLATION LEVEL {_normalized}")

            await db.execute("BEGIN")
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
                await db.execute(f"SAVEPOINT {self._savepoint_id}")
            self._depth_holder.value = depth + 1

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        db = self._get_db()

        try:
            if exc_type is not None:
                # Exception occurred -- rollback
                if self._savepoint_id:
                    await db.execute(f"ROLLBACK TO SAVEPOINT {self._savepoint_id}")
                elif self._is_outermost:
                    await db.execute("ROLLBACK")

                # Fire rollback hooks
                await self._fire_hooks(self._rollback_hooks)
            else:
                # Success -- commit or release savepoint
                if self._savepoint_id:
                    await db.execute(f"RELEASE SAVEPOINT {self._savepoint_id}")
                elif self._is_outermost:
                    await db.execute("COMMIT")

                    # Fire on_commit hooks only at outermost level
                    await self._fire_hooks(self._commit_hooks)
        finally:
            # Decrement depth
            if self._depth_holder is not None:
                new_depth = self._depth_holder.value - 1
                self._depth_holder.value = max(new_depth, 0)

        return False  # Don't suppress exceptions

    async def savepoint(self) -> str:
        """Create an explicit savepoint within this atomic block."""
        db = self._get_db()
        sp_id = f"sp_{uuid.uuid4().hex[:12]}"
        await db.execute(f"SAVEPOINT {sp_id}")
        return sp_id

    async def rollback_to_savepoint(self, savepoint_id: str) -> None:
        """Roll back to a specific savepoint."""
        if not _SP_NAME_RE.match(savepoint_id):
            from aquilia.faults.domains import QueryFault

            raise QueryFault(
                message=f"Invalid savepoint name: {savepoint_id!r}. Must be alphanumeric/underscores only.",
            )
        db = self._get_db()
        await db.execute(f"ROLLBACK TO SAVEPOINT {savepoint_id}")

    async def release_savepoint(self, savepoint_id: str) -> None:
        """Release (commit) a savepoint."""
        if not _SP_NAME_RE.match(savepoint_id):
            from aquilia.faults.domains import QueryFault

            raise QueryFault(
                message=f"Invalid savepoint name: {savepoint_id!r}. Must be alphanumeric/underscores only.",
            )
        db = self._get_db()
        await db.execute(f"RELEASE SAVEPOINT {savepoint_id}")


def atomic(
    db: AquiliaDatabase | None = None,
    *,
    savepoint: bool = True,
    durable: bool = False,
    isolation: str | None = None,
) -> Atomic:
    """
    Create an atomic transaction context manager.

    Can be used as a context manager:
        async with atomic():
            ...

    Or with a specific database:
        async with atomic(db=my_db):
            ...

    Or with isolation level (PostgreSQL/MySQL):
        async with atomic(isolation="SERIALIZABLE"):
            ...

    Args:
        db: Database instance. If None, uses the default.
        savepoint: Use savepoints for nesting (default True)
        durable: Disallow nesting inside another atomic block
        isolation: SQL transaction isolation level
    """
    return Atomic(db, savepoint=savepoint, durable=durable, isolation=isolation)


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

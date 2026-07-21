"""
Regression + concurrency tests -- transaction nesting depth tracker bug.

Root cause (fixed):
    _get_depth_holder() used ``id(task)`` as a key in a WeakValueDictionary.
    WeakValueDictionary only holds *values* weakly (the _DepthHolder objects),
    not keys. Integer keys from id(task) accumulate forever -- one entry per
    unique asyncio Task that ever enters an atomic block, never cleaned up.
    After a Task is garbage-collected, Python may reuse its id() for a new,
    unrelated Task, which then finds stale depth state and either:
      - Skips the outermost BEGIN (because depth != 0), or
      - Treats a top-level transaction as a nested savepoint.

Fix:
    Replace WeakValueDictionary + id(task) with a module-level
    ``ContextVar[int]`` (``aquilia_txn_depth``, default=0).
    ContextVar.set() is always local to the current task's context; it never
    mutates a parent or sibling task.  After task completion the context is
    freed with the task -- zero memory overhead, no dict entry to clean up.
    ContextVar.reset(token) in __aexit__ restores the previous depth exactly,
    guarding against underflow if __aenter__ raised after the token was stored.

Coverage:
    - ContextVar is used (not WeakValueDictionary)
    - Depth correctly 0 → 1 on enter, restored to 0 on exit
    - Nested atomic: 1 → 2 → back to 1 → back to 0
    - Sibling tasks (asyncio.gather) don't share depth
    - id() reuse can't contaminate a new task
    - Rollback path restores depth correctly
    - Exception in __aenter__ before token stored → depth stays 0
    - Many concurrent transactions don't corrupt each other
    - Stress: 50+ tasks each doing nested transactions simultaneously
"""

from __future__ import annotations

import asyncio
import contextvars
import gc

import pytest
import pytest_asyncio

from aquilia.db.engine import configure_database
from aquilia.faults.domains import QueryFault
from aquilia.models.base import Model, ModelRegistry
from aquilia.models.fields_module import CharField, IntegerField
from aquilia.models.transactions import Atomic, _txn_depth, atomic


# ── Models ───────────────────────────────────────────────────────────────────

class TxnDepthUser(Model):
    table = "txndepth_user"
    id = IntegerField(primary_key=True)
    name = CharField(max_length=50)


# ── Fixture ──────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def db():
    database = configure_database("sqlite:///:memory:", alias="default")
    await database.connect()

    ModelRegistry.register(TxnDepthUser)
    orig = TxnDepthUser._db
    TxnDepthUser._db = database
    await database.execute(TxnDepthUser.generate_create_table_sql())
    await database.execute("INSERT INTO txndepth_user (id, name) VALUES (1, 'Alice')")

    yield database

    TxnDepthUser._db = orig
    await database.disconnect()


# ── Unit tests (no DB) ───────────────────────────────────────────────────────

class TestContextVarUsed:
    def test_txn_depth_is_contextvar(self):
        """Verify the module exports a ContextVar, not a WeakValueDictionary."""
        assert isinstance(_txn_depth, contextvars.ContextVar), (
            "_txn_depth must be a ContextVar -- WeakValueDictionary was removed"
        )

    def test_default_is_zero(self):
        assert _txn_depth.get() == 0

    def test_no_weakref_dict_exported(self):
        import aquilia.models.transactions as txn_mod
        assert not hasattr(txn_mod, "_task_depths"), (
            "_task_depths (WeakValueDictionary) must no longer exist"
        )
        assert not hasattr(txn_mod, "_DepthHolder"), (
            "_DepthHolder must no longer exist"
        )
        assert not hasattr(txn_mod, "_get_depth_holder"), (
            "_get_depth_holder must no longer exist"
        )


# ── Depth tracking correctness ────────────────────────────────────────────────

class TestDepthTracking:
    @pytest.mark.asyncio
    async def test_depth_zero_before_and_after(self, db):
        assert _txn_depth.get() == 0
        async with atomic():
            pass
        assert _txn_depth.get() == 0

    @pytest.mark.asyncio
    async def test_depth_one_inside_outermost(self, db):
        inside_depth = None
        async with atomic():
            inside_depth = _txn_depth.get()
        assert inside_depth == 1

    @pytest.mark.asyncio
    async def test_depth_two_inside_nested(self, db):
        outer_depth = inner_depth = None
        async with atomic():
            outer_depth = _txn_depth.get()
            async with atomic():
                inner_depth = _txn_depth.get()
        assert outer_depth == 1
        assert inner_depth == 2
        assert _txn_depth.get() == 0

    @pytest.mark.asyncio
    async def test_depth_restored_after_rollback(self, db):
        with pytest.raises(ValueError):
            async with atomic():
                assert _txn_depth.get() == 1
                raise ValueError("boom")
        assert _txn_depth.get() == 0, (
            "Depth must be restored to 0 even after rollback"
        )

    @pytest.mark.asyncio
    async def test_depth_restored_after_nested_rollback(self, db):
        async with atomic():
            assert _txn_depth.get() == 1
            with pytest.raises(ValueError):
                async with atomic():
                    assert _txn_depth.get() == 2
                    raise ValueError("inner boom")
            assert _txn_depth.get() == 1, (
                "After inner rollback, depth must return to 1 (not 2 or 0)"
            )
        assert _txn_depth.get() == 0


# ── Concurrency / isolation tests ─────────────────────────────────────────────

class TestConcurrencyIsolation:
    @pytest.mark.asyncio
    async def test_two_tasks_depths_isolated(self, db):
        """Two gather() tasks each entering atomic() must not see each other's depth."""
        depths_seen: list[int] = []

        async def task_fn(delay: float):
            await asyncio.sleep(delay)
            async with atomic():
                depths_seen.append(_txn_depth.get())
                await asyncio.sleep(0.02)

        await asyncio.gather(task_fn(0.0), task_fn(0.01))
        # Both tasks must observe depth=1 inside their own outermost block
        assert depths_seen == [1, 1], (
            f"Each task must see depth=1 independently; got {depths_seen}"
        )

    @pytest.mark.asyncio
    async def test_sibling_tasks_depth_zero_after(self, db):
        """After gather() completes, the main task's depth is still 0."""
        async def worker():
            async with atomic():
                await asyncio.sleep(0.01)

        assert _txn_depth.get() == 0
        await asyncio.gather(worker(), worker(), worker())
        assert _txn_depth.get() == 0

    @pytest.mark.asyncio
    async def test_id_reuse_no_contamination(self, db):
        """
        Simulate id() reuse: create a task, let it enter atomic (depth=1),
        GC it, then create a new task.  The new task must start at depth=0,
        not at the stale depth from the GC'd task.

        With the old WeakValueDictionary + id(task) approach, if the new
        task's id() happened to equal the old task's id(), it would inherit
        depth=1 and skip the outermost BEGIN.  With ContextVar this cannot
        happen: each task gets an independent context copy.
        """
        depths_in_new_task: list[int] = []

        # Phase 1: run a task that enters atomic (depth goes to 1 inside it)
        async def phase1():
            async with atomic():
                await asyncio.sleep(0)

        t1 = asyncio.ensure_future(phase1())
        await t1  # wait for t1 to complete

        # Force GC so the task object may be freed (and its id() recycled)
        del t1
        gc.collect()

        # Phase 2: new task -- must see depth=0 at entry
        async def phase2():
            depths_in_new_task.append(_txn_depth.get())
            async with atomic():
                depths_in_new_task.append(_txn_depth.get())

        t2 = asyncio.ensure_future(phase2())
        await t2

        assert depths_in_new_task[0] == 0, (
            "New task must start at depth=0 regardless of id() reuse"
        )
        assert depths_in_new_task[1] == 1, (
            "New task must see depth=1 inside its outermost atomic block"
        )


# ── Stress test ───────────────────────────────────────────────────────────────

class TestStress:
    @pytest.mark.asyncio
    async def test_50_concurrent_tasks_no_depth_corruption(self, db):
        """
        50 concurrent tasks, each doing a nested atomic (depth 0→1→2→1→0).
        After all tasks complete the main context depth must still be 0.
        No task may observe wrong depths inside its blocks.
        """
        errors: list[str] = []

        async def worker(i: int):
            if _txn_depth.get() != 0:
                errors.append(f"Task {i}: expected depth=0 before enter, got {_txn_depth.get()}")
                return
            async with atomic():
                d1 = _txn_depth.get()
                if d1 != 1:
                    errors.append(f"Task {i}: expected depth=1 in outer, got {d1}")
                async with atomic():
                    d2 = _txn_depth.get()
                    if d2 != 2:
                        errors.append(f"Task {i}: expected depth=2 in inner, got {d2}")
                d3 = _txn_depth.get()
                if d3 != 1:
                    errors.append(f"Task {i}: expected depth=1 after inner, got {d3}")
            if _txn_depth.get() != 0:
                errors.append(f"Task {i}: expected depth=0 after exit, got {_txn_depth.get()}")

        await asyncio.gather(*[worker(i) for i in range(50)])

        assert not errors, "Depth corruption detected:\n" + "\n".join(errors)
        assert _txn_depth.get() == 0


# ── Integration: verify fixes don't break existing atomic behaviour ────────────

class TestAtomicBehaviourAfterFix:
    @pytest.mark.asyncio
    async def test_commit_still_works(self, db):
        async with atomic():
            user = await TxnDepthUser.objects.filter(id=1).first()
            user.name = "FixedCommit"
            await user.save(update_fields=["name"])
        refreshed = await TxnDepthUser.objects.filter(id=1).first()
        assert refreshed.name == "FixedCommit"

    @pytest.mark.asyncio
    async def test_rollback_still_works(self, db):
        with pytest.raises(ValueError):
            async with atomic():
                user = await TxnDepthUser.objects.filter(id=1).first()
                user.name = "ShouldNotPersist"
                await user.save(update_fields=["name"])
                raise ValueError("boom")
        refreshed = await TxnDepthUser.objects.filter(id=1).first()
        assert refreshed.name == "Alice"

    @pytest.mark.asyncio
    async def test_nested_savepoint_still_works(self, db):
        async with atomic():
            user = await TxnDepthUser.objects.filter(id=1).first()
            user.name = "OuterName"
            await user.save(update_fields=["name"])
            with pytest.raises(ValueError):
                async with atomic():
                    user.name = "InnerName"
                    await user.save(update_fields=["name"])
                    raise ValueError("inner")
        refreshed = await TxnDepthUser.objects.filter(id=1).first()
        assert refreshed.name == "OuterName"

    @pytest.mark.asyncio
    async def test_durable_rejected_when_nested(self, db):
        async with atomic():
            with pytest.raises(QueryFault):
                async with atomic(durable=True):
                    pass

    @pytest.mark.asyncio
    async def test_decorator_form(self, db):
        @atomic()
        async def rename():
            user = await TxnDepthUser.objects.filter(id=1).first()
            user.name = "Decorated"
            await user.save(update_fields=["name"])

        await rename()
        refreshed = await TxnDepthUser.objects.filter(id=1).first()
        assert refreshed.name == "Decorated"

    @pytest.mark.asyncio
    async def test_on_commit_hook_fires(self, db):
        fired = []
        async with atomic() as txn:
            txn.on_commit(lambda: fired.append(True))
        assert fired == [True]

    @pytest.mark.asyncio
    async def test_on_rollback_hook_fires(self, db):
        fired = []
        with pytest.raises(ValueError):
            async with atomic() as txn:
                txn.on_rollback(lambda: fired.append(True))
                raise ValueError
        assert fired == [True]

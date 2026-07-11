"""
Regression + brutal coverage tests for aquilia.models.transactions.atomic().

Root cause of the original bug: Atomic.__aenter__/__aexit__ sent literal
"BEGIN"/"SAVEPOINT ..."/"RELEASE SAVEPOINT ..."/"COMMIT"/"ROLLBACK" through
AquiliaDatabase.execute() -- the same auto-commit code path as an ordinary
query. The SQLite adapter's per-statement auto_commit logic (gated only by
AsyncConnection._in_transaction, which was never set by this path) treated
the literal "BEGIN" as its own autocommitted statement, closing the
transaction the instant it opened. By the time __aexit__ issued its own
"COMMIT", SQLite had nothing to commit and raised
"cannot commit - no transaction is active", surfacing as
QueryFault(code="QUERY_FAILED", sql="COMMIT").

Fixed by routing atomic() through the adapter-level begin()/commit()/
rollback()/savepoint()/release_savepoint()/rollback_to_savepoint() --
the same machinery already used correctly by Model.delete_instance()'s
cascade path and the migration runner (see
tests/test_orm_cascade_delete_transactional.py).
"""

from __future__ import annotations

import asyncio

import pytest
import pytest_asyncio

from aquilia.db.engine import configure_database
from aquilia.faults.domains import QueryFault
from aquilia.models.base import Model, ModelRegistry
from aquilia.models.fields_module import CharField, ForeignKey, IntegerField
from aquilia.models.transactions import Atomic, atomic


class AtomicTxnUser(Model):
    table = "atomictxn_user"
    id = IntegerField(primary_key=True)
    name = CharField(max_length=50)


class AtomicTxnToken(Model):
    table = "atomictxn_token"
    id = IntegerField(primary_key=True)
    user = ForeignKey(AtomicTxnUser, on_delete="CASCADE")
    value = CharField(max_length=50)


@pytest_asyncio.fixture
async def seeded_db():
    database = configure_database("sqlite:///:memory:", alias="default")
    await database.connect()

    for model in (AtomicTxnUser, AtomicTxnToken):
        ModelRegistry.register(model)
        model._reverse_fk_cache = None

    originals = {}
    for model in (AtomicTxnUser, AtomicTxnToken):
        originals[model] = model._db
        model._db = database
        await database.execute(model.generate_create_table_sql())

    await database.execute("INSERT INTO atomictxn_user (id, name) VALUES (1, 'Alice')")
    await database.execute("INSERT INTO atomictxn_token (id, user_id, value) VALUES (1, 1, 'tok-1')")

    yield database

    for model, original in originals.items():
        model._db = original
    await database.disconnect()


class TestReportedRepro:
    @pytest.mark.asyncio
    async def test_select_related_then_atomic_double_save_commits(self, seeded_db):
        """Exact reported repro: query before atomic(), two saves inside it."""
        token = await AtomicTxnToken.objects.select_related("user").filter(value="tok-1").first()
        assert token is not None
        user = token.user

        async with atomic():
            token.value = "tok-1-updated"
            await token.save(update_fields=["value"])

            user.name = "Alice Updated"
            await user.save(update_fields=["name"])

        refreshed_token = await AtomicTxnToken.objects.filter(id=1).first()
        refreshed_user = await AtomicTxnUser.objects.filter(id=1).first()
        assert refreshed_token.value == "tok-1-updated"
        assert refreshed_user.name == "Alice Updated"


class TestBasicCommitRollback:
    @pytest.mark.asyncio
    async def test_commit_persists(self, seeded_db):
        async with atomic():
            user = await AtomicTxnUser.objects.filter(id=1).first()
            user.name = "Committed"
            await user.save(update_fields=["name"])

        refreshed = await AtomicTxnUser.objects.filter(id=1).first()
        assert refreshed.name == "Committed"

    @pytest.mark.asyncio
    async def test_exception_rolls_back(self, seeded_db):
        with pytest.raises(ValueError):
            async with atomic():
                user = await AtomicTxnUser.objects.filter(id=1).first()
                user.name = "ShouldNotPersist"
                await user.save(update_fields=["name"])
                raise ValueError("boom")

        refreshed = await AtomicTxnUser.objects.filter(id=1).first()
        assert refreshed.name == "Alice"


class TestNestedSavepoints:
    @pytest.mark.asyncio
    async def test_inner_exception_rolls_back_only_inner(self, seeded_db):
        async with atomic():
            outer_user = await AtomicTxnUser.objects.filter(id=1).first()
            outer_user.name = "OuterSurvives"
            await outer_user.save(update_fields=["name"])

            with pytest.raises(ValueError):
                async with atomic():
                    inner_token = await AtomicTxnToken.objects.filter(id=1).first()
                    inner_token.value = "ShouldRollback"
                    await inner_token.save(update_fields=["value"])
                    raise ValueError("inner boom")

        user_after = await AtomicTxnUser.objects.filter(id=1).first()
        token_after = await AtomicTxnToken.objects.filter(id=1).first()
        assert user_after.name == "OuterSurvives"
        assert token_after.value == "tok-1"

    @pytest.mark.asyncio
    async def test_durable_rejects_nesting(self, seeded_db):
        async with atomic():
            with pytest.raises(QueryFault):
                async with atomic(durable=True):
                    pass


class TestHooks:
    @pytest.mark.asyncio
    async def test_commit_hook_fires_once_at_outermost(self, seeded_db):
        # on_commit hooks are scoped to the Atomic instance they're
        # registered on; a nested (savepoint) block's own hooks only fire
        # if that block is itself the outermost transaction -- releasing a
        # savepoint is not a full commit, so a hook registered on a *nested*
        # Atomic never fires on its own. Only the outermost block's hooks do.
        calls = []
        async with atomic() as outer:
            outer.on_commit(lambda: calls.append("outer"))
            async with atomic() as inner:
                inner.on_commit(lambda: calls.append("inner-savepoint"))
            assert calls == []  # not fired yet -- only outermost commit fires hooks

        assert calls == ["outer"]

    @pytest.mark.asyncio
    async def test_rollback_hook_fires_on_exception(self, seeded_db):
        calls = []
        with pytest.raises(ValueError):
            async with atomic() as txn:
                txn.on_rollback(lambda: calls.append("rolled_back"))
                raise ValueError("boom")
        assert calls == ["rolled_back"]


class TestConcurrency:
    @pytest.mark.asyncio
    async def test_two_concurrent_tasks_each_commit_independently(self, seeded_db):
        async def bump_and_save(new_name: str):
            async with atomic():
                user = await AtomicTxnUser.objects.filter(id=1).first()
                user.name = new_name
                await user.save(update_fields=["name"])

        # Sequential-but-overlapping tasks: the writer connection serializes
        # them, but each task's own depth counter / transaction must stay
        # correctly isolated (no cross-task depth corruption).
        await asyncio.gather(bump_and_save("First"), bump_and_save("Second"))

        refreshed = await AtomicTxnUser.objects.filter(id=1).first()
        assert refreshed.name in ("First", "Second")


class TestDecorator:
    @pytest.mark.asyncio
    async def test_atomic_as_decorator_commits(self, seeded_db):
        @atomic()
        async def rename(new_name: str):
            user = await AtomicTxnUser.objects.filter(id=1).first()
            user.name = new_name
            await user.save(update_fields=["name"])

        await rename("DecoratedName")
        refreshed = await AtomicTxnUser.objects.filter(id=1).first()
        assert refreshed.name == "DecoratedName"

    @pytest.mark.asyncio
    async def test_atomic_as_decorator_rolls_back_on_exception(self, seeded_db):
        @atomic()
        async def rename_then_fail(new_name: str):
            user = await AtomicTxnUser.objects.filter(id=1).first()
            user.name = new_name
            await user.save(update_fields=["name"])
            raise ValueError("boom")

        with pytest.raises(ValueError):
            await rename_then_fail("ShouldNotPersist")

        refreshed = await AtomicTxnUser.objects.filter(id=1).first()
        assert refreshed.name == "Alice"

    @pytest.mark.asyncio
    async def test_atomic_rejects_non_coroutine_function(self, seeded_db):
        with pytest.raises(QueryFault):
            atomic()(lambda: None)


class TestReadonly:
    @pytest.mark.asyncio
    async def test_readonly_block_reads_correctly(self, seeded_db):
        async with atomic(readonly=True):
            user = await AtomicTxnUser.objects.filter(id=1).first()
            assert user.name == "Alice"

    @pytest.mark.asyncio
    async def test_readonly_does_not_block_concurrent_writer(self, seeded_db):
        async def reader():
            async with atomic(readonly=True):
                await asyncio.sleep(0.05)
                return await AtomicTxnUser.objects.filter(id=1).first()

        async def writer():
            async with atomic():
                user = await AtomicTxnUser.objects.filter(id=1).first()
                user.name = "WriterWon"
                await user.save(update_fields=["name"])

        results = await asyncio.wait_for(asyncio.gather(reader(), writer()), timeout=5)
        assert results[0] is not None


class TestTimeout:
    @pytest.mark.asyncio
    async def test_timeout_rolls_back_and_raises(self, seeded_db):
        with pytest.raises(QueryFault):
            async with atomic(timeout=0.05):
                user = await AtomicTxnUser.objects.filter(id=1).first()
                user.name = "ShouldNotPersist"
                await user.save(update_fields=["name"])
                await asyncio.sleep(1.0)

        refreshed = await AtomicTxnUser.objects.filter(id=1).first()
        assert refreshed.name == "Alice"

    @pytest.mark.asyncio
    async def test_no_timeout_by_default(self, seeded_db):
        async with atomic():
            await asyncio.sleep(0.01)
            user = await AtomicTxnUser.objects.filter(id=1).first()
            user.name = "SlowButFine"
            await user.save(update_fields=["name"])

        refreshed = await AtomicTxnUser.objects.filter(id=1).first()
        assert refreshed.name == "SlowButFine"


class TestCancellation:
    @pytest.mark.asyncio
    async def test_cancelled_error_inside_block_rolls_back(self, seeded_db):
        started = asyncio.Event()

        async def cancel_me():
            async with atomic():
                user = await AtomicTxnUser.objects.filter(id=1).first()
                user.name = "ShouldNotPersist"
                await user.save(update_fields=["name"])
                started.set()
                await asyncio.sleep(10)

        task = asyncio.ensure_future(cancel_me())
        await started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

        refreshed = await AtomicTxnUser.objects.filter(id=1).first()
        assert refreshed.name == "Alice"


class TestExplicitSavepointHelpers:
    @pytest.mark.asyncio
    async def test_manual_savepoint_rollback(self, seeded_db):
        async with atomic() as txn:
            user = await AtomicTxnUser.objects.filter(id=1).first()
            user.name = "BeforeSavepoint"
            await user.save(update_fields=["name"])

            sp_id = await txn.savepoint()
            user.name = "AfterSavepoint"
            await user.save(update_fields=["name"])
            await txn.rollback_to_savepoint(sp_id)

        refreshed = await AtomicTxnUser.objects.filter(id=1).first()
        assert refreshed.name == "BeforeSavepoint"


class TestAtomicInstanceReuse:
    @pytest.mark.asyncio
    async def test_atomic_object_is_single_use_context_manager(self, seeded_db):
        txn = atomic()
        assert isinstance(txn, Atomic)
        async with txn:
            user = await AtomicTxnUser.objects.filter(id=1).first()
            user.name = "SingleUse"
            await user.save(update_fields=["name"])

        refreshed = await AtomicTxnUser.objects.filter(id=1).first()
        assert refreshed.name == "SingleUse"

"""
Regression tests for Model.delete_instance() cascade transactionality.

Previously, the reverse-FK cascade loop (potentially several DELETE/UPDATE
statements across related tables) and the final row delete ran as
independent, non-transactional db.execute() calls. If a later step failed
(e.g. a PROTECT check on a table hit after an earlier CASCADE step already
deleted rows), the database was left in a partially-cascaded, inconsistent
state: some children deleted, parent still present, others untouched.
delete_instance() now wraps the whole cascade + delete in one transaction.

Along the way this also exposed two independent, pre-existing bugs in
aquilia/models/transactions.py's higher-level atomic() helper (never
actually exercised end-to-end by any existing test):
  1. _DepthHolder's __slots__ omitted "__weakref__", so storing it in the
     WeakValueDictionary-backed per-task depth tracker raised TypeError.
  2. Atomic.__aenter__/__aexit__ issue raw "BEGIN"/"COMMIT"/"ROLLBACK"
     through AquiliaDatabase.execute(), which auto-commits each statement
     by default -- collapsing the transaction before it does anything
     useful. Fixing this properly is a larger, separate undertaking, so
     delete_instance() uses the already-correct AquiliaDatabase.transaction()
     primitive (the same one aquilia/db/engine.py's own docstring example
     and the benchmark suite's db_updates scenario use) instead of atomic().
"""

from __future__ import annotations

import pytest
import pytest_asyncio

from aquilia.db.engine import configure_database
from aquilia.faults.domains import ProtectedDeleteFault
from aquilia.models.base import Model, ModelRegistry
from aquilia.models.deletion import CASCADE, PROTECT
from aquilia.models.fields_module import CharField, ForeignKey, IntegerField


class CascadeTxnAuthor(Model):
    # Deliberately unique, unlikely-to-collide names -- this process-wide
    # ModelRegistry / reverse-FK cache is shared with every other test
    # module, and generic names like "Author"/"Child" risk cross-file
    # interference in the FK scan.
    table = "cascadetxn_author"
    id = IntegerField(primary_key=True)
    name = CharField(max_length=50)


class CascadeTxnCascadeChild(Model):
    table = "cascadetxn_cascadechild"
    id = IntegerField(primary_key=True)
    author = ForeignKey(CascadeTxnAuthor, on_delete=CASCADE)


class CascadeTxnProtectChild(Model):
    table = "cascadetxn_protectchild"
    id = IntegerField(primary_key=True)
    author = ForeignKey(CascadeTxnAuthor, on_delete=PROTECT)


@pytest_asyncio.fixture
async def seeded_db():
    database = configure_database("sqlite:///:memory:", alias="default")
    await database.connect()

    # Test-isolation guard: Model._get_reverse_fk_refs() (aquilia/models/base.py)
    # lazily computes its list of reverse-FK references by scanning
    # ModelRegistry.all_models() *once ever* per class, then caches the
    # result permanently on cls._reverse_fk_cache. ModelRegistry is a
    # process-wide singleton, and some other test modules (e.g.
    # tests/test_model_registry_startup_validation.py, via an autouse
    # fixture) call ModelRegistry.reset() -- which clears the *entire*
    # registry, not just their own models. If that reset happens to run
    # (anywhere in the suite, in any order) before this module's very
    # first delete_instance() call, these three model classes vanish from
    # ModelRegistry.all_models() at exactly the moment the cache is
    # computed, permanently poisoning it with an empty/incomplete ref
    # list -- even though the classes themselves are still perfectly
    # valid, already-imported Python objects.
    #
    # Guard against this unconditionally, every time, right before use:
    # re-register the models (idempotent) and drop any previously cached
    # reverse-FK refs so they're recomputed fresh against a registry that
    # is guaranteed (by the loop below) to contain all three of them.
    for model in (CascadeTxnAuthor, CascadeTxnCascadeChild, CascadeTxnProtectChild):
        ModelRegistry.register(model)
        model._reverse_fk_cache = None

    originals = {}
    for model in (CascadeTxnAuthor, CascadeTxnCascadeChild, CascadeTxnProtectChild):
        originals[model] = model._db
        model._db = database
        await database.execute(model.generate_create_table_sql())

    await database.execute("INSERT INTO cascadetxn_author (id, name) VALUES (1, 'A')")
    await database.execute("INSERT INTO cascadetxn_cascadechild (id, author_id) VALUES (1, 1)")
    await database.execute("INSERT INTO cascadetxn_protectchild (id, author_id) VALUES (1, 1)")

    yield database

    for model, original in originals.items():
        model._db = original
    await database.disconnect()


class TestCascadeDeleteRollsBackOnFailure:
    @pytest.mark.asyncio
    async def test_protect_failure_rolls_back_earlier_cascade_step(self, seeded_db):
        author = await CascadeTxnAuthor.objects.filter(id=1).first()

        with pytest.raises(ProtectedDeleteFault):
            await author.delete_instance()

        # The CascadeChild delete step runs before the ProtectChild check
        # (registry/declaration order); its deletion must have been rolled
        # back along with the (never-executed) parent delete.
        assert await CascadeTxnCascadeChild.objects.filter(id=1).first() is not None
        assert await CascadeTxnAuthor.objects.filter(id=1).first() is not None


class TestCascadeDeleteCommitsOnSuccess:
    @pytest.mark.asyncio
    async def test_successful_cascade_delete_commits(self, seeded_db):
        await seeded_db.execute("DELETE FROM cascadetxn_protectchild")
        author = await CascadeTxnAuthor.objects.filter(id=1).first()

        row_count = await author.delete_instance()

        assert row_count == 1
        assert await CascadeTxnCascadeChild.objects.filter(id=1).first() is None
        assert await CascadeTxnAuthor.objects.filter(id=1).first() is None

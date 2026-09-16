"""
Regression tests for the DB transaction / migration audit fixes (v1.4.1).

Covers:
    - N1: cross-task transaction bleed. The SQLite adapter used to store
      transaction state (``_in_transaction`` + pinned writer) on the shared
      adapter instance, so a rollback in request A's transaction silently
      rolled back request B's auto-commit writes. Routing is now per-task
      via a ContextVar.
    - N2: ``db.transaction()`` leaks on ``CancelledError`` -- it caught
      ``Exception`` only; it now rolls back and re-raises on
      ``BaseException``.
    - Migrations (a): a failing ``RunPython`` must roll the migration back
      *including its history row* so it is retried instead of being
      recorded as applied and skipped forever.
    - Migrations (b): concurrent boots serialize through the
      cross-process migration lock.
    - Migrations (c): the sqlite adapter passes ``pool_timeout`` through.

Every test uses its own file-backed scratch sqlite DB under tmp_path.
"""

from __future__ import annotations

import asyncio
import subprocess
import sys

import pytest
import pytest_asyncio

from aquilia.db.engine import AquiliaDatabase, configure_database
from aquilia.faults.domains import MigrationFault
from aquilia.models.base import Model, ModelRegistry
from aquilia.models.fields_module import AutoField, CharField
from aquilia.models.migration.engine import MigrationEngine
from aquilia.models.migration.executor import MIGRATION_TABLE, MigrationExecutor
from aquilia.models.migration.graph import MigrationNode
from aquilia.models.migration.operations import CreateModel, RunPython
from aquilia.models.migration.schema import ColumnState, ProjectState, TableState
from aquilia.models.transactions import atomic


def _probe_table(table: str) -> TableState:
    """A minimal auto-PK + name table state for CreateModel."""
    return TableState(
        model="Probe",
        db_table=table,
        columns={
            "id": ColumnState(
                name="id", column="id", field_class="AutoField", primary_key=True, auto_increment=True
            ),
            "name": ColumnState(name="name", column="name", field_class="CharField", null=True),
        },
    )


# ═══════════════════════════════════════════════════════════════════════════
# Models
# ═══════════════════════════════════════════════════════════════════════════


class TxnBleedCounter(Model):
    table = "txnbleed_counter"
    id = AutoField()
    name = CharField(max_length=50)


@pytest_asyncio.fixture
async def db(tmp_path):
    """A fresh file-backed database with one model table created."""
    database = configure_database(f"sqlite:///{tmp_path}/txnfix.db", alias="default")
    await database.connect()

    ModelRegistry.register(TxnBleedCounter)
    TxnBleedCounter._reverse_fk_cache = None
    original_db = TxnBleedCounter._db
    TxnBleedCounter._db = database
    await database.execute(TxnBleedCounter.generate_create_table_sql())

    yield database

    TxnBleedCounter._db = original_db
    await database.disconnect()


# ═══════════════════════════════════════════════════════════════════════════
# N1: cross-task transaction bleed
# ═══════════════════════════════════════════════════════════════════════════


class TestCrossTaskTransactionBleed:
    """SQLite serializes writes through one writer connection: while A's
    transaction pins the writer, B's auto-commit write WAITS for the writer
    (it used to be silently routed onto A's connection and joined A's
    transaction -- the bleed under test). These tests therefore synchronize
    on a ``b_pending`` event, set just before B issues its write, so A's
    transaction ends while B's write is in flight."""

    async def test_rollback_in_task_a_does_not_kill_task_b_writes(self, db):
        """The audit's exact scenario: task A holds a transaction and rolls
        it back while task B does a plain auto-commit create() concurrently.
        B's row must survive."""

        a_started = asyncio.Event()
        b_pending = asyncio.Event()

        async def task_a():
            async with atomic():  # BEGIN; pins the writer for A only
                await TxnBleedCounter.create(name="a-rolled-back")
                a_started.set()
                # B has issued (or is about to issue) its write; end the
                # transaction -- rolled back -- while B is in flight.
                await asyncio.wait_for(b_pending.wait(), timeout=5)
                await asyncio.sleep(0.05)  # let B queue on the writer
                raise RuntimeError("intentional rollback in A")

        async def task_b():
            await a_started.wait()
            b_pending.set()
            obj = await TxnBleedCounter.create(name="b-survivor")
            assert obj.pk is not None  # B got a normal pk, no error...

        results = await asyncio.gather(task_a(), task_b(), return_exceptions=True)
        # A raised its intentional error...
        assert any(isinstance(r, RuntimeError) for r in results)
        # ...and B's row survived A's rollback (previously B's write joined
        # A's transaction and vanished with it, with no error to B).
        names = [r.name for r in await TxnBleedCounter.objects.all()]
        assert "b-survivor" in names
        assert "a-rolled-back" not in names

    async def test_commit_in_task_a_leaves_task_b_autocommit_intact(self, db):
        a_started = asyncio.Event()
        b_pending = asyncio.Event()

        async def task_a():
            async with atomic():
                await TxnBleedCounter.create(name="a-committed")
                a_started.set()
                # Commit once B's write is in flight.
                await asyncio.wait_for(b_pending.wait(), timeout=5)
                await asyncio.sleep(0.05)

        async def task_b():
            await a_started.wait()
            b_pending.set()
            await TxnBleedCounter.create(name="b-autocommit")

        await asyncio.gather(task_a(), task_b())

        names = {r.name for r in await TxnBleedCounter.objects.all()}
        assert names == {"a-committed", "b-autocommit"}

    async def test_reads_outside_transaction_unaffected_by_open_one(self, db):
        """While A's transaction is open, B's reads take the pool path and
        see committed data (not A's uncommitted writes)."""

        await TxnBleedCounter.create(name="committed-before")

        a_started = asyncio.Event()
        b_read = asyncio.Event()

        async def task_a():
            async with atomic():
                await TxnBleedCounter.create(name="a-uncommitted")
                a_started.set()
                await asyncio.wait_for(b_read.wait(), timeout=5)

        seen_by_b: list[str] = []

        async def task_b():
            await a_started.wait()
            rows = await TxnBleedCounter.objects.all()
            seen_by_b.extend(r.name for r in rows)
            b_read.set()

        await asyncio.gather(task_a(), task_b())

        # B saw the committed row; whether it sees A's uncommitted row is
        # isolation-dependent, but the committed one must be there.
        assert "committed-before" in seen_by_b

    async def test_nested_savepoints_still_work(self, db):
        """Per-task routing must not break savepoint nesting: an inner
        rollback leaves the outer transaction usable."""

        async with atomic():
            await TxnBleedCounter.create(name="outer-kept")
            try:
                async with atomic():
                    await TxnBleedCounter.create(name="inner-rolled-back")
                    raise ValueError("inner boom")
            except ValueError:
                pass  # caught between the blocks -- outer stays alive
            await TxnBleedCounter.create(name="after-inner")

        names = {r.name for r in await TxnBleedCounter.objects.all()}
        assert names == {"outer-kept", "after-inner"}

    async def test_sequential_transactions_reuse_pool(self, db):
        """After commit/rollback the task's routing var is cleared, so
        subsequent writes take the normal auto-commit path."""
        async with atomic():
            await TxnBleedCounter.create(name="t1")
        try:
            async with atomic():
                await TxnBleedCounter.create(name="t2")
                raise RuntimeError("rollback t2")
        except RuntimeError:
            pass

        await TxnBleedCounter.create(name="t3")
        names = {r.name for r in await TxnBleedCounter.objects.all()}
        assert names == {"t1", "t3"}


# ═══════════════════════════════════════════════════════════════════════════
# N2: db.transaction() CancelledError leak
# ═══════════════════════════════════════════════════════════════════════════


class TestEngineTransactionCancellation:
    async def test_cancelled_error_rolls_back_and_releases(self, db):
        """Cancelling the task inside db.transaction() must roll the
        transaction back and leave the engine usable (no leaked pinned
        connection / in-transaction flag)."""
        task = asyncio.ensure_future(self._hold_transaction(db))
        await asyncio.sleep(0.1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

        assert db.in_transaction is False

        # The engine is fully usable afterwards: writes auto-commit again.
        await db.execute("INSERT INTO txnbleed_counter (name) VALUES (?)", ["after-cancel"])
        row = await db.fetch_one("SELECT name FROM txnbleed_counter WHERE name = 'after-cancel'")
        assert row is not None

        # ...and the cancelled transaction's writes are gone.
        leaked = await db.fetch_one("SELECT name FROM txnbleed_counter WHERE name = 'in-flight'")
        assert leaked is None

    async def _hold_transaction(self, db):
        async with db.transaction():
            await db.execute("INSERT INTO txnbleed_counter (name) VALUES (?)", ["in-flight"])
            await asyncio.sleep(10)

    async def test_plain_exception_still_rolls_back(self, db):
        with pytest.raises(ValueError):
            async with db.transaction():
                await db.execute("INSERT INTO txnbleed_counter (name) VALUES (?)", ["boom"])
                raise ValueError("boom")

        row = await db.fetch_one("SELECT name FROM txnbleed_counter WHERE name = 'boom'")
        assert row is None
        assert db.in_transaction is False

    async def test_transaction_commits_normally(self, db):
        async with db.transaction():
            await db.execute("INSERT INTO txnbleed_counter (name) VALUES (?)", ["ok"])
        row = await db.fetch_one("SELECT name FROM txnbleed_counter WHERE name = 'ok'")
        assert row is not None


# ═══════════════════════════════════════════════════════════════════════════
# Migrations (a): RunPython runs before history is committed
# ═══════════════════════════════════════════════════════════════════════════


class TestRunPythonHistoryOrdering:
    async def test_failing_runpython_is_not_recorded_as_applied(self, tmp_path):
        """A migration whose RunPython fails must NOT land in the tracking
        table -- previously history was committed before python_ops ran, so
        the migration was recorded as applied and skipped forever."""

        async def failing_code(db):
            await db.execute("INSERT INTO txnfix_probe (name) VALUES (?)", ["from-python"])
            raise RuntimeError("data migration failed")

        node = MigrationNode(
            revision="20260901_000001",
            slug="probe_with_python",
            operations=(
                CreateModel(model="Probe", table=_probe_table("txnfix_probe")),
                RunPython(code=failing_code),
            ),
            atomic=True,
        )

        db = AquiliaDatabase(f"sqlite:///{tmp_path}/runpython.db")
        await db.connect()
        try:
            executor = MigrationExecutor(db)
            await executor.ensure_tracking_table()

            with pytest.raises(MigrationFault):
                await executor.apply(node, ProjectState())

            # History must not contain the failed migration...
            applied = await db.fetch_all(f"SELECT revision FROM {MIGRATION_TABLE}")
            assert applied == []

            # ...and the DDL must have been rolled back with it.
            table = await db.fetch_one(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='txnfix_probe'"
            )
            assert table is None
        finally:
            await db.disconnect()

    async def test_successful_runpython_is_recorded(self, tmp_path):
        ran = {"count": 0}

        async def good_code(db):
            ran["count"] += 1
            await db.execute("INSERT INTO txnfix_probe (name) VALUES (?)", ["seeded"])

        node = MigrationNode(
            revision="20260901_000002",
            slug="probe_good_python",
            operations=(
                CreateModel(model="Probe", table=_probe_table("txnfix_probe")),
                RunPython(code=good_code),
            ),
            atomic=True,
        )

        db = AquiliaDatabase(f"sqlite:///{tmp_path}/runpython_ok.db")
        await db.connect()
        try:
            executor = MigrationExecutor(db)
            result = await executor.apply(node, ProjectState())

            assert result.python_operations == 1
            applied = await db.fetch_all(f"SELECT revision FROM {MIGRATION_TABLE}")
            assert [r["revision"] for r in applied] == ["20260901_000002"]
            row = await db.fetch_one("SELECT name FROM txnfix_probe")
            assert row["name"] == "seeded"
        finally:
            await db.disconnect()


# ═══════════════════════════════════════════════════════════════════════════
# Migrations (b): cross-process boot migration lock
# ═══════════════════════════════════════════════════════════════════════════


_CONCURRENT_BOOT_WORKER = r"""
import asyncio
import sys

from aquilia.models.migration.engine import MigrationEngine

async def main(migrations_dir: str, db_url: str) -> int:
    from aquilia.db.engine import AquiliaDatabase

    db = AquiliaDatabase(db_url)
    await db.connect()
    try:
        engine = MigrationEngine(migrations_dir)
        await engine.migrate(db)
        return 0
    except Exception as exc:
        print(f"BOOT FAILED: {exc}", file=sys.stderr)
        return 1
    finally:
        await db.disconnect()

sys.exit(asyncio.run(main(sys.argv[1], sys.argv[2])))
"""


class TestCrossProcessMigrationLock:
    def _write_migration(self, migrations_dir, slug: str, table: str) -> None:
        """Write a minimal valid migration module (the loader requires a
        ``Meta`` class and a module-level ``operations`` list)."""
        (migrations_dir / f"20260901_000001_{slug}.py").write_text(
            "from aquilia.models.migration.operations import CreateModel\n"
            "from aquilia.models.migration.schema import ColumnState, TableState\n"
            "\n"
            "\n"
            "class Meta:\n"
            '    """Migration metadata read by the migration runner."""\n'
            "\n"
            "    revision = '20260901_000001'\n"
            f"    slug = '{slug}'\n"
            "    dependencies = []\n"
            "    replaces = []\n"
            "    atomic = True\n"
            "\n"
            "\n"
            "operations: list = [\n"
            "    CreateModel(\n"
            "        model='Probe',\n"
            "        table=TableState(\n"
            "            model='Probe',\n"
            f"            db_table='{table}',\n"
            "            columns={'id': ColumnState(name='id', column='id', field_class='AutoField')},\n"
            "        ),\n"
            "    ),\n"
            "]\n",
            encoding="utf-8",
        )

    async def test_concurrent_boots_both_succeed(self, tmp_path):
        """Three processes booting against the same DB file used to race:
        two failed with 'table already exists'. Under the migration lock
        the first applies the migration and the others find it applied."""
        migrations_dir = tmp_path / "migrations"
        migrations_dir.mkdir()
        self._write_migration(migrations_dir, "concurrent_probe", "lockprobe")

        worker = tmp_path / "boot_worker.py"
        worker.write_text(_CONCURRENT_BOOT_WORKER, encoding="utf-8")

        db_path = tmp_path / "concurrent.db"
        db_url = f"sqlite:///{db_path}"
        # Pre-create the tracking table so the race window (between reading
        # applied revisions and applying) is what gets exercised.
        primed = AquiliaDatabase(db_url)
        await primed.connect()
        await MigrationExecutor(primed).ensure_tracking_table()
        await primed.disconnect()

        loop = asyncio.get_running_loop()

        def _boot():
            return subprocess.run(
                [sys.executable, str(worker), str(migrations_dir), db_url],
                capture_output=True,
                text=True,
                timeout=60,
            )

        procs = list(await asyncio.gather(*[loop.run_in_executor(None, _boot) for _ in range(3)]))

        failures = [p for p in procs if p.returncode != 0]
        assert not failures, "\n".join(p.stderr or p.stdout for p in failures)

        # The migration ran exactly once.
        db = AquiliaDatabase(db_url)
        await db.connect()
        try:
            applied = await db.fetch_all(f"SELECT revision FROM {MIGRATION_TABLE}")
            assert [r["revision"] for r in applied] == ["20260901_000001"]
            tables = await db.fetch_all(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='lockprobe'"
            )
            assert len(tables) == 1
        finally:
            await db.disconnect()

    async def test_lock_released_after_migrate(self, tmp_path):
        """The flock is released when migrate() exits, so a subsequent
        migrate() (second boot) is not blocked."""
        migrations_dir = tmp_path / "migrations"
        migrations_dir.mkdir()
        self._write_migration(migrations_dir, "lock_release", "lockrelease")

        db_url = f"sqlite:///{tmp_path}/lockrelease.db"
        engine = MigrationEngine(migrations_dir)
        db = AquiliaDatabase(db_url)
        await db.connect()
        try:
            await engine.migrate(db)
            # Second run must not block on a held lock (acquires instantly).
            await asyncio.wait_for(engine.migrate(db), timeout=10)
        finally:
            await db.disconnect()


# ═══════════════════════════════════════════════════════════════════════════
# Migrations (c): sqlite adapter passes pool_timeout through
# ═══════════════════════════════════════════════════════════════════════════


class TestSqlitePoolTimeoutPassthrough:
    async def test_pool_timeout_mapped_into_pool_config(self, tmp_path):
        """``configure_database(..., pool_timeout=1.5)`` must reach the
        native pool config instead of being silently dropped."""
        db = configure_database(
            f"sqlite:///{tmp_path}/pooltimeout.db",
            alias="pooltimeout-test",
            pool_timeout=1.5,
        )
        await db.connect()
        try:
            pool = db.adapter.pool
            assert pool is not None
            assert pool.config.pool_timeout == 1.5
        finally:
            await db.disconnect()


# ═══════════════════════════════════════════════════════════════════════════
# Shared-fault guard: a rollback in one transaction must not fault other
# tasks' queries afterwards.
# ═══════════════════════════════════════════════════════════════════════════


class TestPostRollbackHealth:
    async def test_other_task_writes_work_after_foreign_rollback(self, db):
        """After A's transaction rolls back, B's writes (issued while A was
        still open -- they queue on the single writer) complete normally
        and the engine stays healthy."""
        b_pending = asyncio.Event()

        async def task_a():
            try:
                async with atomic():
                    await TxnBleedCounter.create(name="a")
                    await asyncio.wait_for(b_pending.wait(), timeout=5)
                    await asyncio.sleep(0.05)
                    raise RuntimeError("rollback A")
            except RuntimeError:
                pass

        async def task_b():
            # Issue the first write while A's transaction is open; it waits
            # for the writer, then auto-commits once A's rollback releases it.
            b_pending.set()
            await TxnBleedCounter.create(name="b-after")
            await TxnBleedCounter.objects.count()

        await asyncio.gather(task_a(), task_b())

        names = {r.name for r in await TxnBleedCounter.objects.all()}
        assert "b-after" in names
        assert "a" not in names

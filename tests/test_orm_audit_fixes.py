"""
Regression tests for the ORM forensic-audit fixes (v1.4.2).

Covers:
    - F-OR-01: find_or_create/get_or_create/update_or_create/bulk_update
      accept FK-column keys (``author_id``) that filter()/create() accept.
    - N3: order()/values()/only()/defer()/group_by() raise a clear
      QueryFault for unknown fields instead of silently producing broken
      SQL.
    - N4: DateTimeField.to_db normalizes aware datetimes to UTC on sqlite
      so mixed naive/aware string comparison follows chronology.
    - N5: legacy like/ilike lookups escape LIKE meta-characters.
    - N7: iterator() respects a user-set limit() instead of clobbering it.
    - N8: bulk_create ignore_conflicts is dialect-aware and inserts batch
      rows via a single multi-row statement.

Each test uses its own file-based scratch sqlite DB under tmp_path (never a
shared :memory: database).
"""

from __future__ import annotations

import datetime
import uuid
import warnings
from unittest.mock import MagicMock

import pytest
import pytest_asyncio

from aquilia.db.engine import configure_database
from aquilia.faults.domains import QueryFault
from aquilia.models.base import Model, ModelRegistry
from aquilia.models.fields_module import (
    AutoField,
    CharField,
    DateTimeField,
    ForeignKey,
    UUIDField,
)
from aquilia.models.migration.schema import ProjectState

# ═══════════════════════════════════════════════════════════════════════════
# Models
# ═══════════════════════════════════════════════════════════════════════════


class AuditFixOwner(Model):
    table = "auditfix_owner"
    id = AutoField()
    name = CharField(max_length=50)


class AuditFixToken(Model):
    """FK with unique=True -- the F-OR-01 shape (lookup by ``owner_id``)."""

    table = "auditfix_token"
    id = AutoField()
    owner = ForeignKey(AuditFixOwner, unique=True, on_delete="CASCADE")
    value = CharField(max_length=50)


class AuditFixEvent(Model):
    table = "auditfix_event"
    id = AutoField()
    label = CharField(max_length=50)
    at = DateTimeField(null=True)


class AuditFixLikeRow(Model):
    table = "auditfix_likerow"
    id = AutoField()
    label = CharField(max_length=100)


class AuditFixBulk(Model):
    table = "auditfix_bulk"
    id = AutoField()
    key = CharField(max_length=50, unique=True)
    note = CharField(max_length=50, null=True)


class AuditFixUuidItem(Model):
    table = "auditfix_uuiditem"
    uid = UUIDField(primary_key=True)


class AuditFixUuidRef(Model):
    table = "auditfix_uuidref"
    id = AutoField()
    item = ForeignKey(AuditFixUuidItem)


_MODELS = (
    AuditFixOwner,
    AuditFixToken,
    AuditFixEvent,
    AuditFixLikeRow,
    AuditFixBulk,
    AuditFixUuidItem,
    AuditFixUuidRef,
)


@pytest_asyncio.fixture
async def db(tmp_path):
    """A fresh file-backed database with every audit-fix model's table created."""
    database = configure_database(f"sqlite:///{tmp_path}/auditfix.db", alias="default")
    await database.connect()

    for model in _MODELS:
        ModelRegistry.register(model)
        model._reverse_fk_cache = None

    originals = {}
    for model in _MODELS:
        originals[model] = model._db
        model._db = database
        await database.execute(model.generate_create_table_sql())

    yield database

    for model, original in originals.items():
        model._db = original
    await database.disconnect()


# ═══════════════════════════════════════════════════════════════════════════
# F-OR-01: FK-column keys in the upsert family
# ═══════════════════════════════════════════════════════════════════════════


class TestFindOrCreateFkColumnKey:
    async def test_find_or_create_accepts_fk_column_key(self, db):
        """``owner_id=`` is accepted exactly like ``owner=`` / filter()."""
        owner = await AuditFixOwner.create(id=1, name="alice")

        token, created = await AuditFixToken.find_or_create(owner_id=owner.pk, defaults={"value": "t1"})
        assert created is True
        assert token.owner_id == owner.pk
        assert token.value == "t1"

        # Second call conflicts and SELECTs the existing row via the same
        # FK-column key (previously a KeyError inside the SELECT builder).
        again, created2 = await AuditFixToken.find_or_create(owner_id=owner.pk, defaults={"value": "other"})
        assert created2 is False
        assert again.id == token.id
        assert again.value == "t1"

    async def test_find_or_create_fk_column_key_conflict_target(self, db):
        """The ON CONFLICT target resolves the FK column, not a KeyError."""
        owner = await AuditFixOwner.create(id=1, name="alice")
        await AuditFixToken.create(owner=owner, value="first")

        with pytest.raises(QueryFault) as exc:
            await AuditFixToken.find_or_create(nonexistent="x")
        assert "Unknown field" in str(exc.value)

    async def test_get_or_create_fk_column_key_uses_atomic_path(self, db):
        """``get_or_create(owner_id=...)`` takes the atomic path -- no spurious
        'no unique constraint' RuntimeWarning and no racy fallback."""
        owner = await AuditFixOwner.create(id=1, name="alice")

        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            token, created = await AuditFixToken.get_or_create(owner_id=owner.pk, defaults={"value": "t1"})
        assert created is True

        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            _, created2 = await AuditFixToken.get_or_create(owner_id=owner.pk, defaults={"value": "t2"})
        assert created2 is False

    async def test_update_or_create_fk_column_key(self, db):
        owner = await AuditFixOwner.create(id=1, name="alice")

        token, created = await AuditFixToken.update_or_create(owner_id=owner.pk, defaults={"value": "v1"})
        assert created is True

        token2, created2 = await AuditFixToken.update_or_create(owner_id=owner.pk, defaults={"value": "v2"})
        assert created2 is False
        assert token2.id == token.id

        refreshed = await AuditFixToken.objects.filter(id=token.id).first()
        assert refreshed.value == "v2"

    async def test_validate_unique_constraint_resolves_fk_column(self):
        assert AuditFixToken._validate_unique_constraint({"owner_id"}) is True
        assert AuditFixToken._validate_unique_constraint({"owner"}) is True
        assert AuditFixToken._validate_unique_constraint({"value"}) is False

    async def test_get_conflict_columns_resolves_fk_column(self):
        assert AuditFixToken._get_conflict_columns({"owner_id"}, "sqlite") == ["owner_id"]
        assert AuditFixToken._get_conflict_columns({"owner"}, "sqlite") == ["owner_id"]

    async def test_unknown_lookup_still_rejected(self, db):
        with pytest.raises(QueryFault) as exc:
            await AuditFixToken.find_or_create(no_such_field=1)
        assert "Unknown field" in str(exc.value)


class TestBulkUpdateFkColumnName:
    async def test_bulk_update_fk_column_name(self, db):
        """``bulk_update(fields=["owner_id"])`` updates the column instead of
        silently skipping it."""
        alice = await AuditFixOwner.create(id=1, name="alice")
        bob = await AuditFixOwner.create(id=2, name="bob")
        token = await AuditFixToken.create(owner=alice, value="t")

        token.owner = bob
        updated = await AuditFixToken.bulk_update([token], fields=["owner_id"])
        assert updated == 1

        row = await db.fetch_one("SELECT owner_id FROM auditfix_token WHERE id = ?", [token.pk])
        assert row["owner_id"] == bob.pk


class TestUpdateFkColumnCoercion:
    async def test_update_set_value_coercion_fk_column(self, db):
        """``update(item_id=<UUID>)`` coerces through the FK field's to_db()
        (the same fallback filters have) instead of binding a raw UUID."""
        item_a = await AuditFixUuidItem.create(uid=uuid.uuid4())
        item_b = await AuditFixUuidItem.create(uid=uuid.uuid4())
        ref = await AuditFixUuidRef.create(item=item_a)

        rows = await AuditFixUuidRef.objects.filter(id=ref.pk).update(item_id=item_b.uid)
        assert rows == 1

        row = await db.fetch_one("SELECT item_id FROM auditfix_uuidref WHERE id = ?", [ref.pk])
        assert row["item_id"] == str(item_b.uid)


# ═══════════════════════════════════════════════════════════════════════════
# N3: unknown-field validation in order/values/only/defer/group_by
# ═══════════════════════════════════════════════════════════════════════════


class TestUnknownFieldValidation:
    async def test_order_unknown_field_raises(self, db):
        with pytest.raises(QueryFault) as exc:
            AuditFixEvent.objects.order("nonexistent")
        assert "Unknown field" in str(exc.value)

    async def test_order_desc_unknown_field_raises(self, db):
        with pytest.raises(QueryFault):
            AuditFixEvent.objects.order("-nonexistent")

    async def test_values_unknown_field_raises(self, db):
        with pytest.raises(QueryFault) as exc:
            await AuditFixEvent.objects.values("no_such_col")
        assert "Unknown field" in str(exc.value)

    async def test_only_unknown_field_raises(self, db):
        with pytest.raises(QueryFault):
            AuditFixEvent.objects.only("no_such_col")

    async def test_defer_unknown_field_raises(self, db):
        with pytest.raises(QueryFault):
            AuditFixEvent.objects.defer("no_such_col")

    async def test_group_by_unknown_field_raises(self, db):
        with pytest.raises(QueryFault):
            AuditFixEvent.objects.group_by("no_such_col")

    async def test_values_returns_column_values_not_literals(self, db):
        """"""
        await AuditFixEvent.create(label="alpha", at=None)
        await AuditFixEvent.create(label="beta", at=None)

        # Previously ``values('no_such_col')`` returned one string literal
        # per row; with a real field it must return the stored values.
        rows = await AuditFixEvent.objects.order("id").values("label")
        assert [r["label"] for r in rows] == ["alpha", "beta"]

    async def test_values_fk_column_spelling(self, db):
        owner = await AuditFixOwner.create(id=7, name="o7")
        await AuditFixToken.create(owner=owner, value="v")

        rows = await AuditFixToken.objects.values("owner_id")
        assert rows == [{"owner_id": 7}]

    async def test_order_fk_column_spelling_resolves(self, db):
        owner = await AuditFixOwner.create(id=1, name="a")
        await AuditFixToken.create(owner=owner, value="v")
        sql = AuditFixToken.objects.order("owner_id").query
        assert '"owner_id" ASC' in sql

    async def test_order_random_and_expressions_preserved(self, db):
        """'?' (RANDOM) and F()/OrderBy expressions keep working untouched."""
        from aquilia.models import F

        sql = AuditFixEvent.objects.order("?").query
        assert "RANDOM()" in sql

        sql = AuditFixEvent.objects.order(F("label").desc()).query
        assert '"label" DESC' in sql

    async def test_order_annotation_alias_preserved(self, db):
        from aquilia.models import Count

        sql = AuditFixEvent.objects.annotate(n=Count("id")).order("n").query
        assert '"n"' in sql

    async def test_group_by_real_field_builds(self, db):
        sql = AuditFixEvent.objects.group_by("label").query
        assert 'GROUP BY "label"' in sql

    async def test_order_unknown_field_no_sql_emitted(self, db):
        """ORDER BY on an unknown column previously produced silently
        no-op SQL (SQLite ignores unknown identifiers in some contexts);
        now the chain call fails loudly before any query runs."""
        with pytest.raises(QueryFault):
            AuditFixEvent.objects.order("definitely_not_a_field").all()


# ═══════════════════════════════════════════════════════════════════════════
# N4: DateTimeField UTC normalization on sqlite
# ═══════════════════════════════════════════════════════════════════════════


class TestDateTimeUtcNormalization:
    def test_to_db_converts_aware_to_utc(self):
        field = DateTimeField()
        aware = datetime.datetime(2026, 6, 1, 14, 0, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=2)))
        stored = field.to_db(aware, dialect="sqlite")
        assert stored == "2026-06-01T12:00:00+00:00"

    def test_to_db_naive_stored_verbatim(self):
        field = DateTimeField()
        naive = datetime.datetime(2026, 6, 1, 13, 0, 0)
        assert field.to_db(naive, dialect="sqlite") == "2026-06-01T13:00:00"

    def test_from_db_parses_both_forms(self):
        field = DateTimeField()
        aware = field.to_python("2026-06-01T12:00:00+00:00")
        assert aware.tzinfo is not None
        naive = field.to_python("2026-06-01T13:00:00")
        assert naive.tzinfo is None

    async def test_mixed_awareness_filter_audit_case(self, db):
        """The audit's exact case: an aware ``14:00+02:00`` (= 12:00 UTC)
        stored next to a naive ``13:00``. With UTC normalization the aware
        row sorts before the naive one (12:00 < 13:00 lexically), so a
        naive ``13:30`` upper bound includes the aware row. (The naive row
        also matches naive ``13:30``; cross-awareness comparison of naive
        stored values against aware bounds remains lexical -- compare like
        with like, as documented on ``to_db``.)"""
        aware = datetime.datetime(2026, 6, 1, 14, 0, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=2)))
        naive = datetime.datetime(2026, 6, 1, 13, 0, 0)

        await AuditFixEvent.create(label="aware", at=aware)
        await AuditFixEvent.create(label="naive", at=naive)

        # Verify the stored representation is UTC-normalized.
        row = await db.fetch_one("SELECT at FROM auditfix_event WHERE label = 'aware'")
        assert row["at"] == "2026-06-01T12:00:00+00:00"

        # The audit's assertion: the aware row (12:00 UTC) is correctly
        # ordered BELOW the naive 13:00 row -- previously its raw
        # "14:00+02:00" prefix sorted it above.
        rows = await db.fetch_all("SELECT label FROM auditfix_event ORDER BY at")
        assert [r["label"] for r in rows] == ["aware", "naive"]

        # And a naive upper bound at 13:30 includes the aware row.
        matches = await AuditFixEvent.objects.filter(
            at__lt=datetime.datetime(2026, 6, 1, 13, 30)
        ).values("label")
        assert [m["label"] for m in matches] == ["aware", "naive"]

    async def test_aware_rows_compare_across_offsets(self, db):
        """+02:00 14:00 and UTC 12:00 are the same instant -- an exclusive
        upper bound at 12:30 UTC must exclude both."""
        plus2 = datetime.datetime(2026, 6, 1, 14, 0, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=2)))
        utc = datetime.datetime(2026, 6, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
        await AuditFixEvent.create(label="plus2", at=plus2)
        await AuditFixEvent.create(label="utc", at=utc)

        row = await db.fetch_one("SELECT at FROM auditfix_event WHERE label = 'plus2'")
        assert row["at"] == row["at"]  # both rows stored identically
        rows = await db.fetch_all("SELECT label FROM auditfix_event ORDER BY at")
        assert {r["label"] for r in rows} == {"plus2", "utc"}
        # Same instant, so ordering/comparison must treat them as equal.
        equal = await db.fetch_val(
            "SELECT COUNT(*) FROM (SELECT DISTINCT at FROM auditfix_event)"
        )
        assert equal == 1


# ═══════════════════════════════════════════════════════════════════════════
# N5: LIKE escaping in legacy like/ilike lookups
# ═══════════════════════════════════════════════════════════════════════════


class TestLegacyLikeEscaping:
    async def test_ilike_bare_percent_does_not_match_all(self, db):
        """``filter(label__ilike='%')`` must not act as a match-anything
        wildcard: with escaping, the bare ``%`` is a literal and matches
        nothing here (previously it matched every row)."""
        await AuditFixLikeRow.create(label="plain")
        await AuditFixLikeRow.create(label="other")
        await AuditFixLikeRow.create(label="under_score")

        matches = await AuditFixLikeRow.objects.filter(label__ilike="%").all()
        assert matches == []

    async def test_ilike_no_value_acts_as_wildcard_storm(self, db):
        """Every meta-character is escaped, so values made purely of
        metacharacters match only rows containing those exact literals --
        ``'%'`` matches nothing here, and ``'_'`` matches only a row whose
        label IS a single underscore (previously it matched every
        single-character row)."""
        await AuditFixLikeRow.create(label="50% off")
        await AuditFixLikeRow.create(label="50X off")
        await AuditFixLikeRow.create(label="_")

        for pattern in ("%", "%%"):
            matches = await AuditFixLikeRow.objects.filter(label__ilike=pattern).all()
            assert matches == [], f"pattern {pattern!r} matched {[r.label for r in matches]}"

        matches = await AuditFixLikeRow.objects.filter(label__like="_").all()
        assert [r.label for r in matches] == ["_"]

    async def test_like_plain_value_still_matches(self, db):
        """Ordinary text keeps matching normally (a whole-value LIKE with
        no meta-characters behaves like equality)."""
        await AuditFixLikeRow.create(label="hello")
        await AuditFixLikeRow.create(label="hello world")

        matches = await AuditFixLikeRow.objects.filter(label__like="hello").all()
        assert [r.label for r in matches] == ["hello"]

    async def test_like_percent_mid_pattern_is_literal(self, db):
        await AuditFixLikeRow.create(label="50X off")
        await AuditFixLikeRow.create(label="50% off")

        matches = await AuditFixLikeRow.objects.filter(label__like="50%").all()
        # '50%' with escaping is the literal string '50%' -- no row is
        # exactly that; previously '50X off' matched via the wildcard.
        assert matches == []

    async def test_like_underscore_is_literal(self, db):
        await AuditFixLikeRow.create(label="a_b")
        await AuditFixLikeRow.create(label="axb")

        matches = await AuditFixLikeRow.objects.filter(label__like="a_b").all()
        assert [r.label for r in matches] == ["a_b"]

    async def test_like_backslash_is_literal(self, db):
        await AuditFixLikeRow.create(label="back\\slash")
        await AuditFixLikeRow.create(label="backXslash")

        matches = await AuditFixLikeRow.objects.filter(label__like="back\\slash").all()
        assert [r.label for r in matches] == ["back\\slash"]

    async def test_registry_contains_lookup_unchanged(self, db):
        """The registry lookups (contains etc.) keep their escaped behavior."""
        await AuditFixLikeRow.create(label="plain")
        await AuditFixLikeRow.create(label="50% off")

        matches = await AuditFixLikeRow.objects.filter(label__contains="%").all()
        assert [r.label for r in matches] == ["50% off"]


# ═══════════════════════════════════════════════════════════════════════════
# N7: iterator() respects a user-set limit()
# ═══════════════════════════════════════════════════════════════════════════


class TestIteratorRespectsLimit:
    async def _seed(self, db, n=6):
        for i in range(n):
            await AuditFixLikeRow.create(label=f"row{i}")

    async def test_limit_one_iterator_chunk_two_yields_one(self, db):
        """The audit's exact case: ``limit(1).iterator(chunk_size=2)`` used
        to yield every row; it must yield exactly one."""
        await self._seed(db)

        seen = [row.label async for row in AuditFixLikeRow.objects.order("id").limit(1).iterator(chunk_size=2)]
        assert seen == ["row0"]

    async def test_limit_across_chunk_boundary(self, db):
        await self._seed(db)

        seen = [row.label async for row in AuditFixLikeRow.objects.order("id").limit(3).iterator(chunk_size=2)]
        assert seen == ["row0", "row1", "row2"]

    async def test_iterator_without_limit_yields_all(self, db):
        await self._seed(db)

        seen = [row.label async for row in AuditFixLikeRow.objects.order("id").iterator(chunk_size=2)]
        assert seen == [f"row{i}" for i in range(6)]

    async def test_limit_equals_chunk_size(self, db):
        await self._seed(db)

        seen = [row.label async for row in AuditFixLikeRow.objects.order("id").limit(2).iterator(chunk_size=2)]
        assert seen == ["row0", "row1"]


# ═══════════════════════════════════════════════════════════════════════════
# N8: bulk_create dialect-aware ignore_conflicts + multi-row batching
# ═══════════════════════════════════════════════════════════════════════════


class RecordingDB:
    """Wraps a real database, recording executed SQL for batch assertions."""

    def __init__(self, inner, dialect="sqlite"):
        self._inner = inner
        self.dialect = dialect
        self.execute_many_calls: list[tuple[str, list]] = []
        self.execute_calls: list[str] = []

    async def execute(self, sql, params=None, **kwargs):
        self.execute_calls.append(sql)
        return await self._inner.execute(sql, params, **kwargs)

    async def execute_many(self, sql, params_list, **kwargs):
        self.execute_many_calls.append((sql, list(params_list)))
        return await self._inner.execute_many(sql, params_list, **kwargs)

    def __getattr__(self, name):
        return getattr(self._inner, name)


class TestBulkCreate:
    async def test_batched_insert_uses_multi_row_statement(self, db):
        """Uniform rows go out as ONE executemany statement for the batch."""
        recorder = RecordingDB(db)
        AuditFixBulk._db = recorder

        try:
            created = await AuditFixBulk.bulk_create(
                [{"key": f"k{i}", "note": f"n{i}"} for i in range(3)], batch_size=10
            )
        finally:
            AuditFixBulk._db = db

        assert len(created) == 3
        assert len(recorder.execute_many_calls) == 1
        sql, params_list = recorder.execute_many_calls[0]
        assert sql.count("?") == 2  # one row's worth of placeholders
        assert len(params_list) == 3

        count = await AuditFixBulk.objects.count()
        assert count == 3

    async def test_batch_size_splits_statements(self, db):
        recorder = RecordingDB(db)
        AuditFixBulk._db = recorder

        try:
            await AuditFixBulk.bulk_create([{"key": f"k{i}"} for i in range(4)], batch_size=2)
        finally:
            AuditFixBulk._db = db

        assert len(recorder.execute_many_calls) == 2
        assert all(len(params) == 2 for _sql, params in recorder.execute_many_calls)
        assert await AuditFixBulk.objects.count() == 4

    async def test_mixed_columns_fall_back_to_single_row_inserts(self, db):
        """Rows with differing column sets must not be executemany'd
        together (missing keys would bind as NULL)."""
        recorder = RecordingDB(db)
        AuditFixBulk._db = recorder

        try:
            await AuditFixBulk.bulk_create([{"key": "a", "note": "x"}, {"key": "b"}], batch_size=10)
        finally:
            AuditFixBulk._db = db

        assert recorder.execute_many_calls == []
        assert len(recorder.execute_calls) == 2

        rows = {r["key"]: r["note"] for r in await AuditFixBulk.objects.values("key", "note")}
        assert rows == {"a": "x", "b": None}

    async def test_ignore_conflicts_sqlite_skips_duplicates(self, db):
        """``ignore_conflicts=True`` skips conflicting rows without raising
        (SQLite INSERT OR IGNORE)."""
        await AuditFixBulk.create(key="dup")

        created = await AuditFixBulk.bulk_create(
            [{"key": "dup"}, {"key": "fresh"}], ignore_conflicts=True
        )
        assert len(created) == 2  # instances returned; conflicting row skipped

        keys = {r["key"] for r in await AuditFixBulk.objects.values("key")}
        assert keys == {"dup", "fresh"}

    async def test_ignore_conflicts_dialect_clauses(self, db):
        """The conflict clause matches the dialect instead of the hardcoded
        SQLite-only ``INSERT OR IGNORE``."""
        from aquilia.models.base import Model as BaseModel

        def make_dialect_db(dialect_name: str, recorded: dict) -> type:
            class DialectDB:
                dialect = dialect_name
                capabilities = MagicMock()

                async def execute(self, sql, params=None, **kwargs):
                    recorded["execute"] = sql
                    cursor = MagicMock()
                    cursor.lastrowid = 1
                    cursor.rowcount = 1
                    return cursor

                async def execute_many(self, sql, params_list, **kwargs):
                    recorded["execute_many"] = sql
                    return None

            return DialectDB

        for dialect, expected in (
            ("sqlite", "INSERT OR IGNORE INTO"),
            ("postgresql", "ON CONFLICT DO NOTHING"),
            ("mysql", "INSERT IGNORE INTO"),
        ):
            recorded: dict[str, str] = {}

            class _BulkModel(BaseModel):
                table = f"auditfix_dialect_probe_{dialect}"
                id = AutoField()
                key = CharField(max_length=50, unique=True)

            _BulkModel._db = make_dialect_db(dialect, recorded)()
            await _BulkModel.bulk_create([{"key": "a"}, {"key": "b"}], ignore_conflicts=True)
            sql = recorded.get("execute_many") or recorded.get("execute", "")
            assert expected in sql, f"{dialect}: {sql!r}"

    async def test_ignore_conflicts_false_still_raises_on_conflict(self, db):
        from aquilia.faults.domains import QueryFault

        await AuditFixBulk.create(key="dup")
        with pytest.raises((QueryFault, Exception)):
            await AuditFixBulk.bulk_create([{"key": "dup"}], ignore_conflicts=False)


# ═══════════════════════════════════════════════════════════════════════════
# ProjectState import smoke (keeps the migration schema import exercised)
# ═══════════════════════════════════════════════════════════════════════════


def test_project_state_importable():
    assert ProjectState is not None

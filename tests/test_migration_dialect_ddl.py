"""
Dialect-specific DDL rendering.

Each dialect resolves the same :class:`ColumnState` differently, and most of
these differences are ones a database will reject rather than tolerate:

* An auto key is ``AUTOINCREMENT`` (SQLite), ``SERIAL`` (PostgreSQL),
  ``AUTO_INCREMENT`` (MySQL), or ``GENERATED ALWAYS AS IDENTITY`` (Oracle).
  Oracle without the identity clause raises ORA-01400 on the first insert.
* ``DEFAULT TRUE`` is valid only on an actual BOOLEAN column. PostgreSQL is the
  only dialect that *has* one, and rejects ``DEFAULT 1`` on it.
* Oracle requires ``DEFAULT`` before ``NOT NULL`` (ORA-00907 otherwise).
* MySQL rejects a ``DEFAULT`` on TEXT/BLOB/JSON entirely.
* A naive ``TIMESTAMP`` silently drops the offset on PostgreSQL and Oracle,
  which both offer ``TIMESTAMP WITH TIME ZONE``.

These were previously pinned against the v1 DSL's ``ColumnDef.to_sql()``; they
are asserted here against the backend that replaced it.
"""

from __future__ import annotations

import pytest

from aquilia.models import fields
from aquilia.models.migration import ColumnState, Reference, get_backend

DIALECTS = ("sqlite", "postgresql", "mysql", "oracle")


def _definition(column: ColumnState, dialect: str) -> str:
    return get_backend(dialect).column_definition(column)


# ── Auto-increment primary keys ─────────────────────────────────────────────


@pytest.mark.parametrize(
    ("dialect", "expected"),
    [
        ("sqlite", '"id" INTEGER PRIMARY KEY AUTOINCREMENT'),
        ("postgresql", '"id" SERIAL PRIMARY KEY'),
        ("mysql", "`id` INTEGER PRIMARY KEY AUTO_INCREMENT"),
        ("oracle", '"id" NUMBER(10) GENERATED ALWAYS AS IDENTITY PRIMARY KEY'),
    ],
)
def test_auto_primary_key_per_dialect(dialect, expected):
    assert _definition(ColumnState.of("id", fields.AutoField(primary_key=True)), dialect) == expected


@pytest.mark.parametrize(
    ("dialect", "expected"),
    [
        # Only SQLite keeps INTEGER -- there, only that exact type aliases the
        # 64-bit rowid, so BIGINT would lose auto-increment entirely.
        ("sqlite", '"id" INTEGER PRIMARY KEY AUTOINCREMENT'),
        ("postgresql", '"id" BIGSERIAL PRIMARY KEY'),
        ("mysql", "`id` BIGINT PRIMARY KEY AUTO_INCREMENT"),
        ("oracle", '"id" NUMBER(19) GENERATED ALWAYS AS IDENTITY PRIMARY KEY'),
    ],
)
def test_big_auto_primary_key_per_dialect(dialect, expected):
    assert _definition(ColumnState.of("id", fields.BigAutoField(primary_key=True)), dialect) == expected


def test_oracle_auto_key_never_uses_other_dialects_keywords():
    sql = _definition(ColumnState.of("id", fields.AutoField(primary_key=True)), "oracle")
    assert "GENERATED ALWAYS AS IDENTITY" in sql
    assert "AUTOINCREMENT" not in sql
    assert "AUTO_INCREMENT" not in sql
    assert "SERIAL" not in sql


def test_foreign_key_to_auto_key_does_not_generate_its_own_identity():
    """A referencing column stores the key; it must not generate one.

    On PostgreSQL and Oracle the target's type is identity-generating
    (``SERIAL``, ``... AS IDENTITY``); the FK column has to be demoted to the
    plain storage type or the table cannot be created.
    """
    fk = ColumnState.of(
        "author",
        fields.ForeignKey("User", on_delete="CASCADE"),
        column="author_id",
        reference=Reference(model="User", table="users", column="id"),
    )

    postgres = _definition(fk, "postgresql")
    assert "SERIAL" not in postgres
    assert "INTEGER" in postgres

    oracle = _definition(fk, "oracle")
    assert "IDENTITY" not in oracle
    assert "NUMBER(10)" in oracle


# ── Boolean columns ─────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("dialect", "expected_true", "expected_false"),
    [
        ("sqlite", '"flag" INTEGER NOT NULL DEFAULT 1', '"flag" INTEGER NOT NULL DEFAULT 0'),
        ("postgresql", '"flag" BOOLEAN NOT NULL DEFAULT TRUE', '"flag" BOOLEAN NOT NULL DEFAULT FALSE'),
        ("mysql", "`flag` INTEGER NOT NULL DEFAULT 1", "`flag` INTEGER NOT NULL DEFAULT 0"),
        # Oracle: DEFAULT must precede NOT NULL.
        ("oracle", '"flag" NUMBER(1) DEFAULT 1 NOT NULL', '"flag" NUMBER(1) DEFAULT 0 NOT NULL'),
    ],
)
def test_boolean_column_per_dialect(dialect, expected_true, expected_false):
    assert _definition(ColumnState.of("flag", fields.BooleanField(default=True)), dialect) == expected_true
    assert _definition(ColumnState.of("flag", fields.BooleanField(default=False)), dialect) == expected_false


def test_nullable_boolean_omits_not_null():
    assert "NOT NULL" not in _definition(ColumnState.of("flag", fields.BooleanField(null=True)), "sqlite")


@pytest.mark.parametrize("dialect", DIALECTS)
def test_integer_column_with_bool_default_never_renders_true(dialect):
    """``IntegerField(default=True)`` must emit ``1``, not ``TRUE``.

    PostgreSQL rejects ``DEFAULT TRUE`` on an INTEGER column, so the literal has
    to follow the resolved column type rather than the Python value's type.
    """
    sql = _definition(ColumnState.of("flag", fields.IntegerField(default=True)), dialect)
    assert "DEFAULT 1" in sql
    assert "TRUE" not in sql.upper().replace("DEFAULT 1", "")


# ── Timestamps ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("dialect", "expect_timezone"),
    [("postgresql", True), ("oracle", True), ("sqlite", False), ("mysql", False)],
)
def test_datetime_resolves_to_timezone_aware_type_where_available(dialect, expect_timezone):
    sql = _definition(ColumnState.of("created", fields.DateTimeField()), dialect)
    assert "TIMESTAMP" in sql.upper()
    assert ("WITH TIME ZONE" in sql.upper()) is expect_timezone


# ── Defaults MySQL cannot accept ────────────────────────────────────────────


def test_mysql_suppresses_default_on_text():
    """MySQL rejects a DEFAULT on TEXT/BLOB/JSON; other dialects accept it."""
    column = ColumnState.of("bio", fields.TextField(default="", null=True))

    assert "DEFAULT" not in _definition(column, "mysql")
    assert "DEFAULT ''" in _definition(column, "sqlite")
    assert "DEFAULT ''" in _definition(column, "postgresql")


def test_mysql_keeps_default_on_varchar():
    """The suppression is type-specific -- VARCHAR defaults are fine on MySQL."""
    column = ColumnState.of("name", fields.CharField(max_length=255, default="", null=True))
    assert "DEFAULT ''" in _definition(column, "mysql")


# ── String literals ─────────────────────────────────────────────────────────


@pytest.mark.parametrize("dialect", DIALECTS)
def test_string_default_is_quoted_and_escaped(dialect):
    sql = _definition(ColumnState.of("note", fields.CharField(max_length=20, default="it's")), dialect)
    assert "DEFAULT 'it''s'" in sql


@pytest.mark.parametrize("dialect", DIALECTS)
def test_nullable_column_with_null_default(dialect):
    sql = _definition(ColumnState.of("note", fields.CharField(max_length=20, null=True, default=None)), dialect)
    assert "NOT NULL" not in sql

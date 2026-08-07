"""Tests for :mod:`aquilia.sqlite._inline` -- inline-execution eligibility.

This is the highest-risk optimisation in the data path: an admitted statement
runs on the event loop, so a wrong verdict stalls the server rather than merely
being slow. The tests are therefore weighted towards proving that *unsafe*
statements are rejected, not that safe ones are admitted.
"""

from __future__ import annotations

import sqlite3

import pytest

import aquilia.db  # noqa: F401  -- resolves the sqlite<->db import cycle
from aquilia.sqlite._inline import InlinePolicy


@pytest.fixture
def conn() -> sqlite3.Connection:
    """An in-memory database with an indexed table and an unindexed column."""
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE world (id INTEGER PRIMARY KEY, randomNumber INTEGER)")
    c.execute("CREATE TABLE fortune (id INTEGER PRIMARY KEY, message TEXT)")
    c.executemany("INSERT INTO world VALUES (?, ?)", [(i, i * 7 % 10000) for i in range(1, 501)])
    c.executemany("INSERT INTO fortune VALUES (?, ?)", [(i, f"m{i}") for i in range(1, 13)])
    return c


class TestAdmitted:
    """Statements the planner proves are bounded."""

    def test_primary_key_lookup(self, conn):
        p = InlinePolicy(conn)
        assert p.may_run_inline("SELECT id, randomNumber FROM world WHERE id = ?") is True

    def test_constant_select(self, conn):
        p = InlinePolicy(conn)
        assert p.may_run_inline("SELECT 1") is True

    def test_multiple_parameters(self, conn):
        p = InlinePolicy(conn)
        assert p.may_run_inline("SELECT id FROM world WHERE id = ? OR id = ?") is True


class TestRejected:
    """Anything that could do unbounded work on the event loop."""

    def test_full_table_scan(self, conn):
        p = InlinePolicy(conn)
        assert p.may_run_inline("SELECT * FROM world") is False

    def test_unindexed_predicate(self, conn):
        """The whole reason for probing the planner instead of the SQL text: this
        looks identical to a primary-key lookup but scans the table."""
        p = InlinePolicy(conn)
        assert p.may_run_inline("SELECT id FROM world WHERE randomNumber = ?") is False

    def test_small_table_scan_still_rejected(self, conn):
        """`fortune` has 12 rows, but "small today" is not a guarantee."""
        p = InlinePolicy(conn)
        assert p.may_run_inline("SELECT id, message FROM fortune") is False

    @pytest.mark.parametrize(
        "sql",
        [
            "UPDATE world SET randomNumber = ? WHERE id = ?",
            "DELETE FROM world WHERE id = ?",
            "INSERT INTO world (id, randomNumber) VALUES (?, ?)",
            "CREATE TABLE t (a INTEGER)",
            "BEGIN",
            "PRAGMA journal_mode",
        ],
    )
    def test_non_select_rejected(self, conn, sql):
        """Writes must serialise through the writer and may block on the WAL."""
        p = InlinePolicy(conn)
        assert p.may_run_inline(sql) is False

    def test_multi_statement_rejected(self, conn):
        """EXPLAIN QUERY PLAN describes only the first statement, so a batch
        could otherwise smuggle unplanned work past the probe."""
        p = InlinePolicy(conn)
        assert p.may_run_inline("SELECT id FROM world WHERE id = ?; DROP TABLE world") is False

    def test_trailing_semicolon_is_fine(self, conn):
        p = InlinePolicy(conn)
        assert p.may_run_inline("SELECT id FROM world WHERE id = ?;") is True

    def test_subquery_rejected(self, conn):
        p = InlinePolicy(conn)
        assert p.may_run_inline("SELECT id FROM world WHERE id IN (SELECT id FROM fortune)") is False

    def test_sort_rejected(self, conn):
        """An ORDER BY on an unindexed column builds a temp b-tree."""
        p = InlinePolicy(conn)
        assert p.may_run_inline("SELECT id FROM world ORDER BY randomNumber") is False

    def test_join_scan_rejected(self, conn):
        p = InlinePolicy(conn)
        assert p.may_run_inline("SELECT w.id FROM world w, fortune f WHERE w.id = f.id") is False

    def test_unparseable_rejected(self, conn):
        p = InlinePolicy(conn)
        assert p.may_run_inline("SELECT nope FROM missing_table") is False

    def test_syntax_error_rejected(self, conn):
        p = InlinePolicy(conn)
        assert p.may_run_inline("SELECT FROM WHERE") is False


class TestDisabled:
    def test_nothing_admitted_when_disabled(self, conn):
        p = InlinePolicy(conn, enabled=False)
        assert p.may_run_inline("SELECT id FROM world WHERE id = ?") is False
        assert p.enabled is False

    def test_no_probe_runs_when_disabled(self, conn):
        p = InlinePolicy(conn, enabled=False)
        p.may_run_inline("SELECT 1")
        assert p.cache_size() == 0


class TestRuntimeDemotion:
    """The backstop for a plan that was right when probed and wrong later."""

    def test_slow_statement_is_demoted(self, conn):
        sql = "SELECT id FROM world WHERE id = ?"
        p = InlinePolicy(conn, max_duration_ms=1.0)
        assert p.may_run_inline(sql) is True
        p.record_duration(sql, 5.0)
        assert p.may_run_inline(sql) is False

    def test_demotion_is_permanent(self, conn):
        sql = "SELECT id FROM world WHERE id = ?"
        p = InlinePolicy(conn, max_duration_ms=1.0)
        p.may_run_inline(sql)
        p.record_duration(sql, 5.0)
        for _ in range(10):
            assert p.may_run_inline(sql) is False

    def test_fast_statement_stays_admitted(self, conn):
        sql = "SELECT id FROM world WHERE id = ?"
        p = InlinePolicy(conn, max_duration_ms=1.0)
        assert p.may_run_inline(sql) is True
        p.record_duration(sql, 0.05)
        assert p.may_run_inline(sql) is True

    def test_recording_an_unknown_statement_is_harmless(self, conn):
        p = InlinePolicy(conn)
        p.record_duration("SELECT never_probed", 99.0)  # must not raise


class TestCaching:
    def test_probe_runs_once_per_statement(self, conn):
        sql = "SELECT id FROM world WHERE id = ?"
        p = InlinePolicy(conn)
        for _ in range(50):
            p.may_run_inline(sql)
        assert p.cache_size() == 1

    def test_cache_is_bounded_by_distinct_statements(self, conn):
        p = InlinePolicy(conn)
        for i in range(20):
            p.may_run_inline(f"SELECT id FROM world WHERE id = ? -- {i}")
        assert p.cache_size() == 20


class TestPlanChangeSafety:
    def test_dropping_an_index_is_caught_by_the_duration_backstop(self, conn):
        """A plan can stop being true under a live process.

        The probe cache is not invalidated (that would mean re-probing on every
        query, which is the cost we removed), so the duration backstop is what
        catches it. This test documents that division of responsibility.
        """
        conn.execute("CREATE TABLE t (a INTEGER, b INTEGER)")
        conn.execute("CREATE INDEX idx_t_a ON t (a)")
        conn.executemany("INSERT INTO t VALUES (?, ?)", [(i, i) for i in range(1000)])
        sql = "SELECT b FROM t WHERE a = ?"

        p = InlinePolicy(conn, max_duration_ms=1.0)
        assert p.may_run_inline(sql) is True

        conn.execute("DROP INDEX idx_t_a")
        # Still cached as eligible -- by design.
        assert p.may_run_inline(sql) is True
        # A slow measurement demotes it.
        p.record_duration(sql, 12.0)
        assert p.may_run_inline(sql) is False

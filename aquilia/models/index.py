"""
Aquilia Model Indexes -- standalone index rendering.

Re-exports Index and UniqueConstraint from fields_module and adds
additional index types: GinIndex, GistIndex, BrinIndex, HashIndex,
and FunctionalIndex.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

# Re-export originals from fields_module
from ..models.fields_module import Index, UniqueConstraint

__all__ = [
    # Re-exported
    "Index",
    "UniqueConstraint",
    # New
    "GinIndex",
    "GistIndex",
    "BrinIndex",
    "HashIndex",
    "FunctionalIndex",
]


class _PostgresOnlyIndex:
    """Base class for PostgreSQL-specific index types."""

    _index_type: str = ""

    def __init__(
        self,
        *,
        fields: Sequence[str] = (),
        name: str | None = None,
        condition: str | None = None,
        opclasses: Sequence[str] = (),
    ):
        """
        Args:
            fields: Column names to index, in order.
            name: Index name. Auto-generated as ``idx_{table}_{fields}`` if omitted.
            condition: Raw SQL boolean expression for a partial index (``WHERE (...)``).

                .. warning::
                    Not parameterized -- interpolated directly into DDL.
                    Never build it from untrusted input.
            opclasses: Per-column operator class overrides (e.g.
                ``"gin_trgm_ops"`` for trigram search on a GIN index),
                aligned positionally with *fields*.
        """
        self.fields = list(fields)
        self.name = name
        self.condition = condition
        self.opclasses = list(opclasses)

    def sql(self, table_name: str, dialect: str = "sqlite") -> str:
        """Generate CREATE INDEX statement."""
        if dialect in ("sqlite", "mysql"):
            # Fall back to B-tree on non-PostgreSQL databases
            return self._btree_fallback(table_name, dialect=dialect)

        idx_name = self.name or f"idx_{table_name}_{'_'.join(self.fields)}"
        cols_with_opclass = []
        for i, field in enumerate(self.fields):
            col_str = f'"{field}"'
            if i < len(self.opclasses) and self.opclasses[i]:
                col_str += f" {self.opclasses[i]}"
            cols_with_opclass.append(col_str)

        col_list = ", ".join(cols_with_opclass)
        sql = f'CREATE INDEX IF NOT EXISTS "{idx_name}" ON "{table_name}" USING {self._index_type} ({col_list})'
        if self.condition:
            sql += f" WHERE ({self.condition})"
        sql += ";"
        return sql

    def _btree_fallback(self, table_name: str, dialect: str = "sqlite") -> str:
        """Fallback to B-tree index on non-PostgreSQL databases."""
        idx_name = self.name or f"idx_{table_name}_{'_'.join(self.fields)}"
        col_list = ", ".join(f'"{f}"' for f in self.fields)
        ine = "" if dialect == "mysql" else " IF NOT EXISTS"
        return f'CREATE INDEX{ine} "{idx_name}" ON "{table_name}" ({col_list});'

    def deconstruct(self) -> dict[str, Any]:
        """Return a plain-dict representation used by migration diffing/serialization."""
        return {
            "type": self.__class__.__name__,
            "fields": self.fields,
            "name": self.name,
            "condition": self.condition,
            "opclasses": self.opclasses if self.opclasses else None,
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(fields={self.fields!r}, name={self.name!r})"


class GinIndex(_PostgresOnlyIndex):
    """
    PostgreSQL GIN index -- useful for full-text search, JSONB, arrays.

    Usage:
        GinIndex(fields=["tags"], name="idx_posts_tags_gin")
    """

    _index_type = "GIN"


class GistIndex(_PostgresOnlyIndex):
    """
    PostgreSQL GiST index -- useful for geometric, range types, exclusion constraints.

    Usage:
        GistIndex(fields=["location"], name="idx_places_location_gist")
    """

    _index_type = "GIST"


class BrinIndex(_PostgresOnlyIndex):
    """
    PostgreSQL BRIN index -- useful for very large tables with natural ordering.

    Usage:
        BrinIndex(fields=["created_at"], name="idx_events_created_at_brin")
    """

    _index_type = "BRIN"


class HashIndex(_PostgresOnlyIndex):
    """
    PostgreSQL Hash index -- useful for equality lookups only.

    Usage:
        HashIndex(fields=["session_token"], name="idx_sessions_token_hash")
    """

    _index_type = "HASH"


class FunctionalIndex:
    """
    Index on an expression or function call.

    Usage:
        FunctionalIndex(
            expression='LOWER("email")',
            name="idx_users_email_lower",
        )
    """

    def __init__(
        self,
        *,
        expression: str,
        name: str,
        index_type: str | None = None,
        condition: str | None = None,
    ):
        """
        Args:
            expression: Raw SQL expression forming the index key (e.g.
                ``'LOWER("email")'``).

                .. warning::
                    Not parameterized or validated -- interpolated directly
                    into DDL. Never build it from untrusted input.
            name: Index name.
            index_type: Access method, e.g. ``"GIN"``, ``"GIST"``; ``None``
                (default) uses the database default (B-tree). Only applied
                on dialects that support ``USING`` for expression indexes
                (see ``sql()``).
            condition: Raw SQL boolean expression for a partial index (``WHERE (...)``).
        """
        self.expression = expression
        self.name = name
        self.index_type = index_type  # e.g., "GIN", "GIST", None for B-tree
        self.condition = condition

    def sql(self, table_name: str, dialect: str = "sqlite") -> str:
        """
        Generate ``CREATE INDEX ... ON table (<expression>)``.

        The ``USING <index_type>`` clause is only emitted outside of
        SQLite/MySQL (both lack the same expression-index access-method
        selection). ``IF NOT EXISTS`` is omitted on MySQL, which doesn't
        support it for ``CREATE INDEX``.
        """
        using = f" USING {self.index_type}" if self.index_type and dialect not in ("sqlite", "mysql") else ""
        ine = "" if dialect == "mysql" else " IF NOT EXISTS"
        sql = f'CREATE INDEX{ine} "{self.name}" ON "{table_name}"{using} ({self.expression})'
        if self.condition:
            sql += f" WHERE ({self.condition})"
        sql += ";"
        return sql

    def deconstruct(self) -> dict[str, Any]:
        """Return a plain-dict representation used by migration diffing/serialization."""
        return {
            "type": "FunctionalIndex",
            "expression": self.expression,
            "name": self.name,
            "index_type": self.index_type,
            "condition": self.condition,
        }

    def __repr__(self) -> str:
        return f"FunctionalIndex(name={self.name!r}, expression={self.expression!r})"

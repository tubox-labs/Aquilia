"""MySQL / MariaDB schema backend.

Two MySQL characteristics drive everything in this module, and generating
PostgreSQL-shaped SQL gets both wrong:

* **Identifier quoting is backticks**, not double quotes, unless the server
  happens to run with ``ANSI_QUOTES`` enabled. Hardcoding ``"`` makes every
  generated statement a syntax error on a default MySQL install.
* **``CREATE INDEX`` has no ``IF NOT EXISTS``**, and neither does
  ``DROP INDEX``; emitting either is a syntax error. Re-running such a
  statement raises error 1061/1091 instead, which the adapter reports as
  ignorable.

MySQL also lacks transactional DDL: a failed migration leaves earlier
statements applied. The capability flag records that so the runner can warn
rather than promise an atomicity it cannot deliver.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from aquilia.models.migration.backends import BackendCapabilities, SchemaBackend, Statement, register_backend
from aquilia.models.migration.schema import NOT_PROVIDED

if TYPE_CHECKING:
    from aquilia.models.migration.schema import ColumnState, TableState

__all__ = ["MySQLBackend"]


class MySQLBackend(SchemaBackend):
    """DDL generation for MySQL 8.0 and MariaDB 10.5 and later.

    Notes:
        MySQL expresses column alteration through ``MODIFY COLUMN``, which
        restates the *entire* column definition rather than patching individual
        clauses. Anything omitted from a ``MODIFY`` is reset to its default, so
        the full target definition is always emitted.
    """

    dialect = "mysql"
    quote_char = "`"
    capabilities = BackendCapabilities(
        alter_column_type=True,
        alter_column_null=True,
        alter_column_default=True,
        drop_column=True,
        rename_column=True,
        add_constraint=True,
        drop_constraint=True,
        check_constraints=True,
        exclusion_constraints=False,
        deferrable_constraints=False,
        partial_indexes=False,
        expression_indexes=True,
        index_methods=frozenset({"BTREE", "HASH"}),
        covering_indexes=False,
        index_if_not_exists=False,
        table_if_not_exists=True,
        generated_columns=True,
        stored_generated_columns=True,
        column_comments=True,
        table_comments=True,
        collations=True,
        tablespaces=False,
        transactional_ddl=False,
        table_rebuild_required=False,
        supports_returning=False,
        max_identifier_length=64,
    )

    _NO_DEFAULT_TYPES = frozenset(
        {
            "TEXT",
            "TINYTEXT",
            "MEDIUMTEXT",
            "LONGTEXT",
            "BLOB",
            "TINYBLOB",
            "MEDIUMBLOB",
            "LONGBLOB",
            "JSON",
            "GEOMETRY",
        }
    )

    def _boolean_literal(self, value: bool, column: ColumnState | None) -> str:
        """Render a boolean as ``1``/``0`` -- MySQL's ``BOOLEAN`` is an alias for ``TINYINT(1)``."""
        return "1" if value else "0"

    def _bytes_literal(self, value: bytes) -> str:
        """Render bytes as a ``0x``-prefixed hex literal."""
        return f"0x{value.hex()}"

    def _default_clause(self, column: ColumnState) -> str:
        """Render ``DEFAULT ...``, omitting it for types MySQL forbids defaults on.

        MySQL raises error 1101 for a ``DEFAULT`` on ``TEXT``, ``BLOB``,
        ``JSON``, or ``GEOMETRY``. The Python-level default still applies at
        insert time, so dropping the DDL clause changes nothing observable.

        Args:
            column: The column being rendered.

        Returns:
            The clause, or ``""``.
        """

        if column.default is NOT_PROVIDED:
            return ""
        base_type = self.column_type(column).upper().split("(")[0].strip()
        if base_type in self._NO_DEFAULT_TYPES:
            return ""
        return f"DEFAULT {self.literal(column.default, column)}"

    def _primary_key_clause(self, column: ColumnState) -> list[str]:
        """Render ``PRIMARY KEY``, adding ``AUTO_INCREMENT`` for auto-fields."""
        if column.auto_increment:
            return ["PRIMARY KEY", "AUTO_INCREMENT"]
        return ["PRIMARY KEY"]

    def _inline_column_comment(self, column: ColumnState) -> str:
        """Render MySQL's inline ``COMMENT '...'`` clause for a column."""
        if not column.comment:
            return ""
        return f"COMMENT {self._string_literal(column.comment)}"

    def _create_table_suffix(self, table: TableState) -> str:
        """Append the table comment, which MySQL takes inline on ``CREATE TABLE``."""
        comment = table.options.get("comment")
        if comment:
            return f" COMMENT={self._string_literal(comment)}"
        return ""

    def alter_column(self, table: TableState, old: ColumnState, new: ColumnState) -> list[Statement]:
        """Alter a column via ``MODIFY COLUMN`` with its complete new definition.

        MySQL has no per-clause ``ALTER COLUMN``: a ``MODIFY`` replaces the
        whole definition, and any clause left out is reset. Emitting the full
        definition is therefore mandatory, not merely convenient.

        Args:
            table: The table being altered.
            old: The column's current state.
            new: Its desired state.

        Returns:
            A single ``MODIFY COLUMN`` statement, or none if nothing differs.
        """
        if old == new:
            return []
        definition = self.column_definition(new, inline_reference=False)
        return [
            Statement(
                sql=f"ALTER TABLE {self.quote(table.db_table)} MODIFY COLUMN {definition};",
                description=f"Alter column {table.db_table}.{new.column}",
            )
        ]

    def drop_index(self, db_table: str, name: str) -> list[Statement]:
        """Drop an index, qualified with its table.

        MySQL index names are scoped to a table, so ``DROP INDEX`` requires
        ``ON <table>``. It also has no ``IF EXISTS`` for this statement.

        Args:
            db_table: Table the index belongs to.
            name: Index name.

        Returns:
            A single ``DROP INDEX ... ON ...`` statement.
        """
        return [
            Statement(
                sql=f"DROP INDEX {self.quote(self.truncate_identifier(name))} ON {self.quote(db_table)};",
                description=f"Drop index {name} on {db_table}",
            )
        ]

    def drop_constraint(self, db_table: str, name: str) -> list[Statement]:
        """Drop a named constraint.

        Note:
            MySQL accepts ``DROP CONSTRAINT`` for ``CHECK`` and ``FOREIGN KEY``
            constraints from 8.0.19 onward. A unique constraint is physically an
            index and must be dropped with ``DROP INDEX`` instead; the operation
            layer routes those correctly based on the constraint's own type.
        """
        return [
            Statement(
                sql=(
                    f"ALTER TABLE {self.quote(db_table)} DROP CONSTRAINT {self.quote(self.truncate_identifier(name))};"
                ),
                description=f"Drop constraint {name} on {db_table}",
                destructive=True,
            )
        ]


register_backend(MySQLBackend(), aliases=("mariadb",))

"""PostgreSQL schema backend.

PostgreSQL is the most capable target Aquilia supports: it has full
``ALTER COLUMN``, transactional DDL, exclusion constraints, partial and
expression indexes, multiple index access methods, and generated columns. The
base :class:`~aquilia.models.migration.backends.SchemaBackend` is modelled on
it, so this subclass is mostly capability declarations plus the handful of
places PostgreSQL differs from generic SQL -- identity columns and
out-of-line comments.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import BackendCapabilities, SchemaBackend, Statement, register_backend

if TYPE_CHECKING:
    from ..schema import ColumnState, TableState

__all__ = ["PostgreSQLBackend"]


class PostgreSQLBackend(SchemaBackend):
    """DDL generation for PostgreSQL 12 and later.

    Notes:
        Auto-incrementing keys rely on the ``SERIAL``/``BIGSERIAL`` types
        returned by the field's own ``sql_type()``, which already imply an
        identity sequence -- so unlike MySQL or SQLite, no extra keyword is
        appended after ``PRIMARY KEY``.
    """

    dialect = "postgresql"
    quote_char = '"'
    capabilities = BackendCapabilities(
        alter_column_type=True,
        alter_column_null=True,
        alter_column_default=True,
        drop_column=True,
        rename_column=True,
        add_constraint=True,
        drop_constraint=True,
        check_constraints=True,
        exclusion_constraints=True,
        deferrable_constraints=True,
        partial_indexes=True,
        expression_indexes=True,
        index_methods=frozenset({"BTREE", "HASH", "GIN", "GIST", "BRIN", "SPGIST"}),
        index_opclasses=True,
        covering_indexes=True,
        index_if_not_exists=True,
        table_if_not_exists=True,
        generated_columns=True,
        stored_generated_columns=True,
        column_comments=True,
        table_comments=True,
        collations=True,
        tablespaces=True,
        transactional_ddl=True,
        table_rebuild_required=False,
        supports_returning=True,
        max_identifier_length=63,
    )

    def _boolean_literal(self, value: bool, column: ColumnState | None) -> str:
        """Render a boolean as ``TRUE``/``FALSE``, or ``1``/``0`` on a numeric column.

        A ``BooleanField`` maps to a real ``BOOLEAN`` column here, but an
        ``IntegerField`` given ``default=True`` maps to ``INTEGER`` -- and
        PostgreSQL, unlike SQLite, refuses to coerce ``TRUE`` into an integer
        column. Consulting the column's actual type avoids that type mismatch.

        Args:
            value: The boolean default.
            column: The target column, or ``None`` when unknown.

        Returns:
            ``"TRUE"``/``"FALSE"`` for boolean columns, ``"1"``/``"0"`` otherwise.
        """
        if column is not None:
            try:
                sql_type = self.column_type(column).upper()
            except Exception:  # pragma: no cover -- unresolvable custom field
                sql_type = "BOOLEAN"
            if not sql_type.startswith("BOOL"):
                return "1" if value else "0"
        return "TRUE" if value else "FALSE"

    def _bytes_literal(self, value: bytes) -> str:
        """Render bytes in PostgreSQL's ``bytea`` hex-escape form."""
        return f"'\\x{value.hex()}'"

    _SERIAL_STORAGE = {
        "SMALLSERIAL": "SMALLINT",
        "SERIAL": "INTEGER",
        "BIGSERIAL": "BIGINT",
    }

    def _storage_type(self, sql_type: str) -> str:
        """Demote a ``SERIAL`` family type to the integer type that stores its values.

        A ``SERIAL`` column creates and owns a sequence. A foreign key pointing
        at a ``SERIAL`` primary key must be a plain ``INTEGER`` -- declaring it
        ``SERIAL`` would give the referencing table its own sequence and
        default, so inserts that omit the key would silently invent a value
        instead of failing.

        Args:
            sql_type: A resolved SQL type.

        Returns:
            ``INTEGER`` for ``SERIAL``, ``BIGINT`` for ``BIGSERIAL``, and so on;
            otherwise *sql_type* unchanged.
        """
        return self._SERIAL_STORAGE.get(sql_type.upper(), sql_type)

    def _table_comment_statements(self, table: TableState) -> list[Statement]:
        """Render ``COMMENT ON`` statements for the table and its columns.

        PostgreSQL has no inline comment syntax, so comments must follow the
        ``CREATE TABLE`` as separate statements.

        Args:
            table: The table just created.

        Returns:
            One statement per non-empty comment, ordered deterministically.
        """
        statements: list[Statement] = []
        table_comment = table.options.get("comment")
        if table_comment:
            statements.append(
                Statement(
                    sql=f"COMMENT ON TABLE {self.quote(table.db_table)} IS {self._string_literal(table_comment)};",
                    description=f"Comment on table {table.db_table}",
                )
            )
        for column in table.columns.values():
            if not column.comment:
                continue
            statements.append(
                Statement(
                    sql=(
                        f"COMMENT ON COLUMN {self.quote(table.db_table)}.{self.quote(column.column)} "
                        f"IS {self._string_literal(column.comment)};"
                    ),
                    description=f"Comment on column {table.db_table}.{column.column}",
                )
            )
        return statements

    def alter_column(self, table: TableState, old: ColumnState, new: ColumnState) -> list[Statement]:
        """Alter a column, adding a ``USING`` cast when the type change needs one.

        PostgreSQL refuses an ``ALTER COLUMN ... TYPE`` that is not an implicit
        cast (text to integer, for instance) unless an explicit ``USING`` clause
        is supplied. Emitting it unconditionally for cross-family changes turns
        a hard failure into a working migration.

        Args:
            table: The table being altered.
            old: The column's current state.
            new: Its desired state.

        Returns:
            The statements, in execution order.
        """
        statements = super().alter_column(table, old, new)
        old_type = self.column_type(old).upper()
        new_type = self.column_type(new).upper()
        if old_type == new_type:
            return statements

        if not self._implicitly_castable(old_type, new_type):
            quoted_column = self.quote(new.column)
            patched: list[Statement] = []
            for statement in statements:
                if " TYPE " in statement.sql:
                    patched.append(
                        Statement(
                            sql=statement.sql.rstrip(";") + f" USING {quoted_column}::{self.column_type(new)};",
                            description=statement.description,
                        )
                    )
                else:
                    patched.append(statement)
            return patched
        return statements

    @staticmethod
    def _implicitly_castable(old_type: str, new_type: str) -> bool:
        """Return whether PostgreSQL will cast *old_type* to *new_type* implicitly.

        Only same-family widening is implicit -- integer to bigint, varchar to
        text. Anything crossing families needs ``USING``.

        Args:
            old_type: Current SQL type, upper-cased.
            new_type: Target SQL type, upper-cased.

        Returns:
            ``True`` when no ``USING`` clause is required.
        """
        families = (
            ("SMALLINT", "INTEGER", "BIGINT", "SERIAL", "BIGSERIAL", "NUMERIC", "DECIMAL"),
            ("VARCHAR", "CHARACTER VARYING", "TEXT", "CHAR"),
            ("TIMESTAMP", "TIMESTAMPTZ", "DATE", "TIME"),
        )
        for family in families:
            if any(old_type.startswith(t) for t in family) and any(new_type.startswith(t) for t in family):
                return True
        return False


register_backend(PostgreSQLBackend(), aliases=("postgres", "psql", "pg"))

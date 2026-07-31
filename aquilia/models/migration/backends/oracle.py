"""Oracle schema backend.

Oracle diverges from every other target in ways that make generic SQL unusable
against it. Each of these needs an explicit code path; returning an empty
statement list instead would be a silent no-op:

* No ``IF NOT EXISTS`` on ``CREATE TABLE``, ``CREATE INDEX``, or ``DROP``.
* Column alteration is ``MODIFY``, not ``ALTER COLUMN``.
* Setting a column ``NOT NULL`` when it already is raises ORA-01442, so
  nullability changes must be emitted only when they actually change.
* Identifiers were limited to 30 characters before 12.2 and 128 after.
* An empty string is indistinguishable from ``NULL``.

Oracle's DDL is auto-committing: each statement commits implicitly and cannot
be rolled back, which the capability flag records so the runner can warn.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import BackendCapabilities, SchemaBackend, Statement, register_backend

if TYPE_CHECKING:
    from ..schema import ColumnState, IndexState, TableState

__all__ = ["OracleBackend"]


class OracleBackend(SchemaBackend):
    """DDL generation for Oracle Database 12c Release 2 and later.

    Notes:
        Auto-incrementing keys use ``GENERATED ALWAYS AS IDENTITY``, which the
        field's own ``sql_type()`` already includes for auto-fields, so no extra
        keyword is appended here.
    """

    dialect = "oracle"
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
        exclusion_constraints=False,
        deferrable_constraints=True,
        partial_indexes=False,
        expression_indexes=True,
        index_methods=frozenset({"BTREE"}),
        covering_indexes=False,
        index_if_not_exists=False,
        table_if_not_exists=False,
        generated_columns=True,
        stored_generated_columns=False,
        column_comments=True,
        table_comments=True,
        collations=True,
        tablespaces=True,
        transactional_ddl=False,
        table_rebuild_required=False,
        supports_returning=True,
        max_identifier_length=128,
    )

    def _boolean_literal(self, value: ColumnState | bool, column: ColumnState | None = None) -> str:
        """Render a boolean as ``1``/``0`` -- Oracle has no boolean column type before 23c."""
        return "1" if value else "0"

    def _bytes_literal(self, value: bytes) -> str:
        """Render bytes via ``HEXTORAW``, Oracle's raw-literal constructor."""
        return f"HEXTORAW('{value.hex()}')"

    def _primary_key_clause(self, column: ColumnState) -> list[str]:
        """Render ``PRIMARY KEY``, adding the identity clause for auto-fields.

        Oracle has no ``AUTOINCREMENT`` keyword and no ``SERIAL`` type. An
        auto-incrementing key is declared with ``GENERATED ALWAYS AS IDENTITY``,
        which must precede ``PRIMARY KEY``. Without it the column is an ordinary
        ``NUMBER`` and every insert that omits the key fails with ORA-01400.

        Args:
            column: The primary-key column.

        Returns:
            The keyword parts to append after the column type.
        """
        if column.auto_increment:
            return ["GENERATED ALWAYS AS IDENTITY", "PRIMARY KEY"]
        return ["PRIMARY KEY"]

    def _storage_type(self, sql_type: str) -> str:
        """Strip the identity clause from a type used by a referencing column.

        Oracle auto-fields resolve to ``NUMBER(n) GENERATED ALWAYS AS IDENTITY``.
        A foreign key must store the same ``NUMBER(n)`` without generating its
        own identity values, so the clause is removed.

        Args:
            sql_type: A resolved SQL type.

        Returns:
            The type with any ``GENERATED ... IDENTITY`` clause removed.
        """
        upper = sql_type.upper()
        marker = " GENERATED "
        if marker in upper and "IDENTITY" in upper:
            return sql_type[: upper.index(marker)]
        return sql_type

    def _generated_clause(self, column: ColumnState) -> str:
        """Render a virtual generated column.

        Oracle supports only virtual (computed-on-read) generated columns; it
        has no ``STORED`` equivalent. The mode keyword is omitted entirely,
        since Oracle's syntax is ``GENERATED ALWAYS AS (expr) VIRTUAL``.

        Args:
            column: The generated column.

        Returns:
            The generated-column clause.
        """
        return f"GENERATED ALWAYS AS ({column.generated}) VIRTUAL"

    def column_definition(self, column: ColumnState, *, inline_reference: bool = True) -> str:
        """Render a column definition with Oracle's mandatory clause ordering.

        Oracle requires ``DEFAULT`` to precede ``NOT NULL``; the reverse order
        that every other dialect accepts is an ORA-00907 syntax error here. The
        base implementation emits ``NOT NULL DEFAULT ...``, so the two clauses
        are reordered after the fact.

        Args:
            column: The column to render.
            inline_reference: Whether to emit the foreign key inline.

        Returns:
            A SQL column-definition fragment valid for Oracle.
        """
        rendered = super().column_definition(column, inline_reference=inline_reference)
        marker = " NOT NULL DEFAULT "
        if marker in rendered:
            head, _, tail = rendered.partition(marker)
            # `tail` may carry trailing clauses (REFERENCES ...) after the
            # literal; only the literal itself moves ahead of NOT NULL.
            literal, separator, trailing = tail.partition(" REFERENCES ")
            reordered = f"{head} DEFAULT {literal} NOT NULL"
            return reordered + (separator + trailing if separator else "")
        return rendered

    def _references_clause(self, reference: object) -> str:
        """Render an inline ``REFERENCES`` clause without ``ON UPDATE``.

        Oracle implements no ``ON UPDATE`` referential action at all, and
        rejects the clause outright. It also supports only ``CASCADE`` and
        ``SET NULL`` for ``ON DELETE`` -- ``RESTRICT`` and ``NO ACTION`` are the
        default behavior and must be written as no clause rather than named
        explicitly.

        Args:
            reference: The column's foreign-key target.

        Returns:
            An Oracle-valid ``REFERENCES`` clause.
        """
        clause = f"REFERENCES {self.quote(reference.table)} ({self.quote(reference.column)})"
        if reference.on_delete in ("CASCADE", "SET NULL"):
            clause += f" ON DELETE {reference.on_delete}"
        if reference.deferrable and self.capabilities.deferrable_constraints:
            clause += " DEFERRABLE INITIALLY DEFERRED"
        return clause

    def constraint_definition(self, constraint: object) -> str:
        """Render a constraint, stripping the ``ON UPDATE`` clause Oracle rejects.

        Args:
            constraint: The constraint to render.

        Returns:
            An Oracle-valid constraint fragment.
        """
        rendered = super().constraint_definition(constraint)
        if " ON UPDATE " in rendered:
            head, _, tail = rendered.partition(" ON UPDATE ")
            # Drop the action word that follows, keeping anything after it.
            remainder = tail.split(" ", 1)
            rendered = head + (f" {remainder[1]}" if len(remainder) > 1 else "")
        if " ON DELETE RESTRICT" in rendered:
            rendered = rendered.replace(" ON DELETE RESTRICT", "")
        if " ON DELETE NO ACTION" in rendered:
            rendered = rendered.replace(" ON DELETE NO ACTION", "")
        return rendered

    def drop_table(self, db_table: str, *, cascade: bool = False) -> list[Statement]:
        """Drop a table, always cascading constraints.

        Oracle has no ``DROP TABLE IF EXISTS``. ``CASCADE CONSTRAINTS`` is
        emitted unconditionally because Oracle otherwise refuses to drop a table
        that any foreign key still references, which would break the
        reverse-topological drop order the planner relies on.

        Args:
            db_table: Table to drop.
            cascade: Accepted for interface compatibility; Oracle always
                cascades constraints.

        Returns:
            A single destructive ``DROP TABLE`` statement.
        """
        return [
            Statement(
                sql=f"DROP TABLE {self.quote(db_table)} CASCADE CONSTRAINTS;",
                description=f"Drop table {db_table}",
                destructive=True,
            )
        ]

    def drop_index(self, db_table: str, name: str) -> list[Statement]:
        """Drop an index. Oracle has no ``IF EXISTS`` for this statement."""
        return [
            Statement(
                sql=f"DROP INDEX {self.quote(self.truncate_identifier(name))};",
                description=f"Drop index {name}",
            )
        ]

    def create_index(self, db_table: str, index: IndexState) -> list[Statement]:
        """Create an index, rejecting partial indexes Oracle cannot express.

        Args:
            db_table: Table to index.
            index: The index definition.

        Returns:
            A single ``CREATE INDEX`` statement.

        Raises:
            MigrationFault: If the index is partial. Oracle has no ``WHERE``
                clause on ``CREATE INDEX``; the conventional workaround is a
                function-based index over a ``CASE`` expression, which changes
                the index semantics enough that it must be an explicit
                developer decision rather than a silent substitution.
        """
        return super().create_index(db_table, index)

    def alter_column(self, table: TableState, old: ColumnState, new: ColumnState) -> list[Statement]:
        """Alter a column via ``MODIFY``, emitting only genuine changes.

        Oracle raises ORA-01442 ("column to be modified to NOT NULL is already
        NOT NULL") when a nullability change is a no-op, so each clause is
        emitted only when it actually differs.

        Args:
            table: The table being altered.
            old: The column's current state.
            new: Its desired state.

        Returns:
            The statements, in execution order.
        """
        from ..schema import NOT_PROVIDED

        quoted_table = self.quote(table.db_table)
        quoted_column = self.quote(new.column)
        clauses: list[str] = []

        if self.column_type(old) != self.column_type(new):
            clauses.append(self.column_type(new))
        if old.default != new.default:
            if new.default is NOT_PROVIDED:
                clauses.append("DEFAULT NULL")
            else:
                clauses.append(f"DEFAULT {self.literal(new.default, new)}")
        if old.null != new.null:
            clauses.append("NULL" if new.null else "NOT NULL")

        if not clauses:
            return []
        return [
            Statement(
                sql=f"ALTER TABLE {quoted_table} MODIFY ({quoted_column} {' '.join(clauses)});",
                description=f"Alter column {table.db_table}.{new.column}",
            )
        ]

    def _table_comment_statements(self, table: TableState) -> list[Statement]:
        """Render ``COMMENT ON`` statements for the table and its columns."""
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


register_backend(OracleBackend())

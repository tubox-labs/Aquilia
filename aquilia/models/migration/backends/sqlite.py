"""SQLite schema backend.

SQLite is the most constrained target Aquilia supports: no ``ALTER COLUMN``, no
``DROP CONSTRAINT``, no ``ADD CONSTRAINT``. Emitting a ``-- not supported``
comment for those is worse than failing -- such a statement reports success
while changing nothing, so a migration appears to apply cleanly, leaves the
schema untouched, and the next migration builds on a schema that never came to
exist.

This backend implements the standard twelve-step table rebuild instead, which
is how SQLite's own documentation prescribes making these changes:

1. Create a new table with the desired schema under a temporary name.
2. Copy data across for the columns common to both.
3. Drop the original table.
4. Rename the new table into its place.

Indexes are recreated afterwards by the operation layer, since dropping the
original table drops them too.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from aquilia.models.migration.backends import BackendCapabilities, SchemaBackend, Statement, register_backend

if TYPE_CHECKING:
    from aquilia.models.migration.schema import ColumnState, TableState

__all__ = ["SQLiteBackend"]


class SQLiteBackend(SchemaBackend):
    """DDL generation for SQLite 3.35 and later.

    Notes:
        ``DROP COLUMN`` requires SQLite 3.35 (March 2021). ``RENAME COLUMN``
        requires 3.25 (2018). Both are declared supported; a runtime failure on
        an older library surfaces as a database error naming the exact
        statement, which is more useful than pre-emptively rebuilding tables
        for a version almost nobody runs.
    """

    dialect = "sqlite"
    quote_char = '"'
    capabilities = BackendCapabilities(
        # SQLite has no ALTER COLUMN in any form; these are emulated by
        # rebuild_table() rather than declared supported, so that operations
        # know to take the rebuild path instead of emitting invalid SQL.
        alter_column_type=False,
        alter_column_null=False,
        alter_column_default=False,
        drop_column=True,
        rename_column=True,
        add_constraint=False,
        drop_constraint=False,
        check_constraints=True,
        exclusion_constraints=False,
        deferrable_constraints=True,
        partial_indexes=True,
        expression_indexes=True,
        index_methods=frozenset({"BTREE"}),
        covering_indexes=False,
        index_if_not_exists=True,
        table_if_not_exists=True,
        generated_columns=True,
        stored_generated_columns=True,
        column_comments=False,
        table_comments=False,
        collations=True,
        tablespaces=False,
        transactional_ddl=True,
        table_rebuild_required=True,
        supports_returning=True,
        max_identifier_length=1_000_000,
    )

    def _boolean_literal(self, value: bool, column: ColumnState | None) -> str:
        """Render a boolean as ``1``/``0`` -- SQLite has no native boolean type."""
        return "1" if value else "0"

    def _primary_key_clause(self, column: ColumnState) -> list[str]:
        """Render ``PRIMARY KEY``, adding ``AUTOINCREMENT`` for auto-fields.

        SQLite requires the ``AUTOINCREMENT`` keyword to guarantee monotonically
        increasing rowids that are never reused after a delete. It is emitted
        only for genuine auto-fields -- never inferred from "primary key with an
        integer type", which would turn every natural integer key into an
        auto-incrementing one and made it impossible to insert explicit keys.

        Args:
            column: The primary-key column.

        Returns:
            The keyword parts to append after the column type.
        """
        if column.auto_increment:
            return ["PRIMARY KEY", "AUTOINCREMENT"]
        return ["PRIMARY KEY"]

    def alter_column(self, table: TableState, old: ColumnState, new: ColumnState) -> list[Statement]:
        """Alter a column by rebuilding the table.

        SQLite cannot change a column in place, so the whole table is recreated
        with the new definition and its data copied across. The caller is
        responsible for recreating indexes afterwards -- see
        :meth:`rebuild_table`.

        Args:
            table: The table state *after* the alteration, used as the target
                schema for the rebuild.
            old: The column's previous state.
            new: Its desired state.

        Returns:
            The rebuild statements, in execution order. Empty when nothing
            actually differs.
        """
        if old == new:
            return []
        target = table.with_column(new)
        return self.rebuild_table(target, copy_from=table, description=f"Alter column {table.db_table}.{new.column}")

    def add_constraint(self, db_table: str, constraint: object) -> list[Statement]:
        """Add a constraint, using a unique index where SQLite permits one.

        SQLite has no ``ALTER TABLE ... ADD CONSTRAINT``. A ``UNIQUE``
        constraint has an exact equivalent as a unique index, so that path
        works. Anything else -- ``CHECK``, ``FOREIGN KEY``, ``PRIMARY KEY`` --
        requires a full table rebuild, which needs the table state this method
        does not receive; the operation layer detects that via
        :attr:`BackendCapabilities.add_constraint` and rebuilds instead.

        Args:
            db_table: Table to constrain.
            constraint: The constraint to add.

        Returns:
            The statements, in execution order.

        Raises:
            MigrationFault: If the constraint kind needs a rebuild. The message
                names the rebuild as the remedy rather than silently skipping,
                which would be wrong.
        """
        return super().add_constraint(db_table, constraint)

    def drop_index(self, db_table: str, name: str) -> list[Statement]:
        """Drop an index. SQLite index names are database-wide, so no table qualifier."""
        return [
            Statement(
                sql=f"DROP INDEX IF EXISTS {self.quote(name)};",
                description=f"Drop index {name}",
            )
        ]

    # ── Table rebuild ───────────────────────────────────────────────────

    def rebuild_table(
        self,
        target: TableState,
        *,
        copy_from: TableState,
        description: str = "",
    ) -> list[Statement]:
        """Rebuild a table to match *target*, preserving data.

        Implements SQLite's documented procedure for schema changes it cannot
        express as ``ALTER TABLE``. Only columns present in *both* states are
        copied; a column being added arrives with its default, and one being
        dropped is simply not carried over.

        Foreign-key enforcement must be suspended around the rebuild, since
        dropping the original table would otherwise trip referential checks
        from other tables. ``PRAGMA foreign_keys`` is a no-op inside a
        transaction, so those two statements are marked non-transactional and
        the executor runs them outside the surrounding transaction.

        Args:
            target: The desired table schema.
            copy_from: The current table schema, used to determine which
                columns can carry data across.
            description: Human-readable summary for plan output.

        Returns:
            The statements, in execution order: pragma off, create temp table,
            copy, drop, rename, pragma on.

        Warning:
            Indexes on the original table are destroyed by the ``DROP TABLE``
            and must be recreated by the caller. The operation layer does this
            automatically; direct callers of this method must not forget it.

        Example:
            >>> backend.rebuild_table(new_state, copy_from=old_state)
        """
        temp_name = f"__aq_new_{target.db_table}"
        staged = target.evolve(db_table=temp_name)

        shared = [
            column.column
            for column in target.columns.values()
            if column.generated is None and copy_from.column_by_db_name(column.column) is not None
        ]
        columns_sql = self.quote_all(tuple(shared))
        label = description or f"Rebuild table {target.db_table}"

        statements: list[Statement] = [
            Statement(
                sql="PRAGMA foreign_keys=OFF;",
                description="Suspend foreign-key enforcement for table rebuild",
                transactional=False,
            )
        ]
        statements.extend(self.create_table(staged))
        if shared:
            statements.append(
                Statement(
                    sql=(
                        f"INSERT INTO {self.quote(temp_name)} ({columns_sql}) "
                        f"SELECT {columns_sql} FROM {self.quote(target.db_table)};"
                    ),
                    description=f"{label}: copy {len(shared)} column(s)",
                )
            )
        statements.append(
            Statement(
                sql=f"DROP TABLE {self.quote(target.db_table)};",
                description=f"{label}: drop original",
                destructive=True,
            )
        )
        statements.append(
            Statement(
                sql=f"ALTER TABLE {self.quote(temp_name)} RENAME TO {self.quote(target.db_table)};",
                description=f"{label}: install rebuilt table",
            )
        )
        for index in target.indexes:
            statements.extend(self.create_index(target.db_table, index))
        statements.append(
            Statement(
                sql="PRAGMA foreign_keys=ON;",
                description="Restore foreign-key enforcement",
                transactional=False,
            )
        )
        return statements


register_backend(SQLiteBackend(), aliases=("sqlite3",))

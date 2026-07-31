"""
Aquilia migrations -- backend dispatch.

This is the **only** layer of this migration system permitted to know about
SQL dialects. Operations describe *what* changes; a :class:`SchemaBackend`
decides *how* to express that change for a particular database.

Why this layer exists
---------------------
Scattering dialect knowledge across operation classes as inline
``if dialect == "sqlite"`` branches has structural consequences, not cosmetic
ones:

* ``CreateIndex`` emitted ``IF NOT EXISTS`` unconditionally, which MySQL and
  Oracle reject -- while ``index.py``, a few files away, got it right. Two
  code paths, one correct.
* ``AlterField`` handled PostgreSQL, emitted a comment for SQLite, and
  returned an empty list for MySQL and Oracle -- a silent no-op that reported
  success while changing nothing.
* Identifier quoting was a hardcoded ``"`` everywhere, which is wrong on MySQL
  unless ``ANSI_QUOTES`` happens to be enabled.
* Adding a fifth dialect meant editing every operation class.

Centralizing dialect behavior behind a capability-declaring interface makes
each of those a single-site concern, and -- critically -- makes *unsupported*
an explicit, inspectable state rather than an accidental silence.

Capability model
----------------
Each backend declares what it can do via :class:`BackendCapabilities`.
Operations consult capabilities and choose a strategy: emit directly, emit an
equivalent alternative (a partial ``UNIQUE`` constraint becomes a unique
index), rebuild the table (SQLite ``ALTER COLUMN``), or raise a
:class:`~aquilia.faults.domains.MigrationFault` explaining precisely what the
target database cannot do. What never happens is a silent no-op.

Example
-------
::

    from aquilia.models.migration.backends import get_backend

    backend = get_backend("postgresql")
    backend.quote("select")            # '"select"'
    backend.capabilities.alter_column  # True
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ....faults.domains import MigrationFault

if TYPE_CHECKING:
    from ..schema import ColumnState, IndexState, TableState

__all__ = [
    "BackendCapabilities",
    "Statement",
    "SchemaBackend",
    "register_backend",
    "get_backend",
    "known_dialects",
]


# ── Statement ───────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class Statement:
    """One executable SQL statement, with the metadata needed to run it safely.

    Backends return these rather than bare strings so the executor knows how to
    handle each one without re-parsing SQL text. Inferring intent by checking
    whether a string starts with ``--`` silently skips a legitimate statement
    that begins with a comment.

    Attributes:
        sql: The SQL text. Empty for a pure-Python operation.
        params: Bind parameters. DDL rarely takes parameters, but data
            migrations emitted by ``RunSQL`` do, and passing them separately
            keeps them out of the SQL string where they could not be escaped
            safely.
        description: Human-readable summary, shown by ``aq db plan``.
        transactional: Whether the statement may run inside a transaction.
            Some DDL cannot -- PostgreSQL rejects ``CREATE INDEX CONCURRENTLY``
            inside one -- and the executor splits the batch accordingly.
        destructive: Whether applying this loses data. Surfaced in plan output
            so a reviewer sees the risk before approving.
    """

    sql: str
    params: tuple[Any, ...] = ()
    description: str = ""
    transactional: bool = True
    destructive: bool = False

    def __str__(self) -> str:
        """Return the raw SQL, for logging and plan output."""
        return self.sql


# ── Capabilities ────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class BackendCapabilities:
    """Declares what a backend's SQL dialect supports.

    Operations branch on these flags instead of on dialect names, so adding a
    backend never requires touching an operation, and an operation never has to
    guess. Defaults describe a broadly capable SQL database; individual
    backends override what they lack.

    Attributes:
        alter_column_type: Supports changing a column's type in place.
        alter_column_null: Supports toggling ``NOT NULL`` in place.
        alter_column_default: Supports setting/dropping a default in place.
        drop_column: Supports ``ALTER TABLE ... DROP COLUMN``.
        rename_column: Supports ``ALTER TABLE ... RENAME COLUMN``.
        add_constraint: Supports adding a table constraint after creation.
        drop_constraint: Supports ``ALTER TABLE ... DROP CONSTRAINT``.
        check_constraints: Enforces ``CHECK`` constraints.
        exclusion_constraints: Supports ``EXCLUDE`` constraints.
        deferrable_constraints: Supports ``DEFERRABLE INITIALLY DEFERRED``.
        partial_indexes: Supports ``CREATE INDEX ... WHERE (...)``.
        expression_indexes: Supports indexing an expression rather than a column.
        index_methods: Access methods available via ``USING``. Anything not
            listed is downgraded to the default B-tree.
        index_opclasses: Supports per-column operator classes on an index.
        covering_indexes: Supports ``INCLUDE (...)`` on an index.
        index_if_not_exists: Supports ``IF NOT EXISTS`` on ``CREATE INDEX``.
        table_if_not_exists: Supports ``IF NOT EXISTS`` on ``CREATE TABLE``.
        generated_columns: Supports ``GENERATED ALWAYS AS (...)``.
        stored_generated_columns: Supports the ``STORED`` variant specifically.
        column_comments: Supports per-column comments.
        table_comments: Supports per-table comments.
        collations: Supports per-column ``COLLATE``.
        tablespaces: Supports ``TABLESPACE`` placement.
        transactional_ddl: DDL participates in transactions and rolls back on
            failure. Where ``False`` (MySQL, Oracle), a failed migration leaves
            partial schema changes applied and the runner must warn.
        table_rebuild_required: Whether in-place column alteration is emulated
            by rebuilding the table (SQLite).
        supports_returning: Supports ``RETURNING``.
        max_identifier_length: Longest permitted identifier; names are hashed
            and truncated beyond it.
    """

    alter_column_type: bool = True
    alter_column_null: bool = True
    alter_column_default: bool = True
    drop_column: bool = True
    rename_column: bool = True
    add_constraint: bool = True
    drop_constraint: bool = True
    check_constraints: bool = True
    exclusion_constraints: bool = False
    deferrable_constraints: bool = False
    partial_indexes: bool = True
    expression_indexes: bool = True
    index_methods: frozenset[str] = frozenset({"BTREE"})
    index_opclasses: bool = False
    covering_indexes: bool = False
    index_if_not_exists: bool = True
    table_if_not_exists: bool = True
    generated_columns: bool = True
    stored_generated_columns: bool = True
    column_comments: bool = False
    table_comments: bool = False
    collations: bool = True
    tablespaces: bool = False
    transactional_ddl: bool = True
    table_rebuild_required: bool = False
    supports_returning: bool = True
    max_identifier_length: int = 63


# ── Backend base ────────────────────────────────────────────────────────────


class SchemaBackend:
    """Base class for dialect-specific DDL generation.

    A backend translates immutable schema state into SQL. It is stateless and
    reusable; :func:`get_backend` returns a shared instance per dialect.

    Subclasses override :attr:`dialect`, :attr:`capabilities`, and whichever
    rendering hooks differ. The base implementation targets standard SQL and is
    correct for PostgreSQL with only small adjustments.

    Attributes:
        dialect: Canonical dialect name (``"postgresql"``, ``"sqlite"``, ...).
        capabilities: What this dialect supports.
        quote_char: Identifier quoting character.
    """

    dialect: str = "sql"
    capabilities: BackendCapabilities = BackendCapabilities()
    quote_char: str = '"'

    # ── Identifiers and literals ────────────────────────────────────────

    def quote(self, identifier: str) -> str:
        """Quote an identifier for this dialect, escaping embedded quote characters.

        Args:
            identifier: A table, column, index, or constraint name.

        Returns:
            The quoted identifier, e.g. ``'"user"'`` or ``'`user`'``.

        Raises:
            MigrationFault: If *identifier* contains a NUL byte, which would
                truncate the statement at the driver boundary.

        Example:
            >>> get_backend("mysql").quote("order")
            '`order`'
        """
        if "\x00" in identifier:
            raise MigrationFault(
                migration="schema-backend",
                reason=f"Identifier {identifier!r} contains a NUL byte and cannot be quoted safely.",
            )
        q = self.quote_char
        escaped = identifier.replace(q, q * 2)
        return f"{q}{escaped}{q}"

    def quote_all(self, identifiers: tuple[str, ...] | list[str]) -> str:
        """Quote and comma-join a sequence of identifiers.

        Args:
            identifiers: Names to quote.

        Returns:
            A comma-separated quoted list, e.g. ``'"a", "b"'``.
        """
        return ", ".join(self.quote(i) for i in identifiers)

    def literal(self, value: Any, column: ColumnState | None = None) -> str:
        """Render a Python value as a SQL literal for a ``DEFAULT`` clause.

        Args:
            value: The value to render. ``Enum`` members are unwrapped to their
                underlying value first, so a default of ``Status.ACTIVE``
                renders as ``'active'`` rather than an unusable ``repr``.
            column: The target column, consulted so that a boolean default on
                an integer-typed column renders as ``0``/``1`` rather than
                ``TRUE``/``FALSE``.

        Returns:
            A SQL literal fragment.

        Raises:
            MigrationFault: If *value* has no safe SQL literal representation
                (a list, dict, or arbitrary object). Falling back to
                ``repr(value)``, producing SQL that either failed to parse or,
                worse, parsed into something unintended.
        """
        from datetime import date, datetime, time
        from decimal import Decimal
        from enum import Enum

        if isinstance(value, Enum):
            value = value.value

        if value is None:
            return "NULL"
        if isinstance(value, bool):
            return self._boolean_literal(value, column)
        if isinstance(value, (int, float, Decimal)):
            return str(value)
        if isinstance(value, str):
            return self._string_literal(value)
        if isinstance(value, (datetime, date, time)):
            return self._string_literal(value.isoformat())
        if isinstance(value, bytes):
            return self._bytes_literal(value)

        raise MigrationFault(
            migration="schema-backend",
            reason=(
                f"Cannot render {type(value).__name__} value {value!r} as a SQL "
                f"DEFAULT literal. Use a scalar default (str, int, float, bool, "
                f"Decimal, date/time, bytes, or Enum), or a callable default -- "
                f"callables are applied in Python at INSERT time and need no DDL."
            ),
        )

    def _string_literal(self, value: str) -> str:
        """Quote a string literal, doubling embedded single quotes."""
        return "'" + value.replace("'", "''") + "'"

    def _bytes_literal(self, value: bytes) -> str:
        """Render bytes as a hex literal in this dialect's syntax."""
        return f"X'{value.hex()}'"

    def _boolean_literal(self, value: bool, column: ColumnState | None) -> str:
        """Render a boolean, respecting the target column's actual SQL type."""
        return "TRUE" if value else "FALSE"

    def truncate_identifier(self, name: str) -> str:
        """Shorten *name* to fit :attr:`BackendCapabilities.max_identifier_length`.

        A hash suffix keeps truncated names unique and deterministic, so two
        long distinct names never collapse onto the same identifier.

        Args:
            name: The proposed identifier.

        Returns:
            *name* unchanged if it fits, otherwise a deterministic shortening.
        """
        limit = self.capabilities.max_identifier_length
        if len(name) <= limit:
            return name
        import hashlib

        digest = hashlib.sha256(name.encode()).hexdigest()[:8]
        return f"{name[: limit - 9]}_{digest}"

    # ── Column rendering ────────────────────────────────────────────────

    def column_type(self, column: ColumnState) -> str:
        """Return the SQL type for *column* in this dialect.

        Delegates to the reconstructed :class:`~aquilia.models.fields_module.Field`,
        so a custom field's own ``sql_type()`` is honoured automatically.

        A foreign-key column is a special case: its field resolves its type from
        the *referenced* primary key, which for an auto-field is an
        identity-generating type (PostgreSQL ``SERIAL``, Oracle identity). The
        referencing column must store the same underlying integer without
        generating its own sequence, so identity types are demoted to their
        plain equivalents via :meth:`_storage_type`.

        Args:
            column: The column state.

        Returns:
            The dialect-specific SQL type string.
        """
        sql_type = column.sql_type(self.dialect)
        if column.reference is not None and not column.auto_increment:
            return self._storage_type(sql_type)
        return sql_type

    def _storage_type(self, sql_type: str) -> str:
        """Demote an identity-generating type to the plain type that stores its values.

        Args:
            sql_type: A resolved SQL type, possibly an identity type.

        Returns:
            The equivalent non-identity storage type, unchanged if it is
            already one.
        """
        return sql_type

    def column_definition(self, column: ColumnState, *, inline_reference: bool = True) -> str:
        """Render a full column definition for use inside ``CREATE TABLE``.

        Assembles, in order: quoted name, type, generated-column clause,
        collation, primary key and auto-increment, ``UNIQUE``, ``NOT NULL``,
        ``DEFAULT``, an inline ``REFERENCES`` clause, and a comment.

        Args:
            column: The column to render.
            inline_reference: Whether to emit the column's foreign key inline.
                Set ``False`` when the reference must be added separately to
                break a circular table dependency.

        Returns:
            A SQL column-definition fragment.

        Example:
            >>> backend.column_definition(email_column)
            '"email" VARCHAR(255) NOT NULL UNIQUE'
        """
        parts = [self.quote(column.column), self.column_type(column)]

        if column.generated is not None:
            parts.append(self._generated_clause(column))
            # A generated column takes no default, no NOT NULL, and no
            # auto-increment: its value is always computed.
            if column.unique and not column.primary_key:
                parts.append("UNIQUE")
            return " ".join(parts)

        if column.collation and self.capabilities.collations:
            parts.append(f"COLLATE {self.quote(column.collation)}")

        if column.primary_key:
            parts.extend(self._primary_key_clause(column))
        else:
            if column.unique:
                parts.append("UNIQUE")
            if not column.null:
                parts.append("NOT NULL")

        default_sql = self._default_clause(column)
        if default_sql:
            parts.append(default_sql)

        if inline_reference and column.reference is not None and column.reference.db_constraint:
            parts.append(self._references_clause(column.reference))

        comment = self._inline_column_comment(column)
        if comment:
            parts.append(comment)

        return " ".join(parts)

    def _generated_clause(self, column: ColumnState) -> str:
        """Render the ``GENERATED ALWAYS AS (...)`` clause for a computed column.

        Raises:
            MigrationFault: If the backend does not support generated columns.
                Emitting the column without its expression would create a
                permanently-NULL column, which is worse than failing.
        """
        if not self.capabilities.generated_columns:
            raise MigrationFault(
                migration="schema-backend",
                reason=(
                    f"{self.dialect} does not support generated columns, required by "
                    f"column {column.column!r}. Remove the GeneratedField or target a "
                    f"database that supports GENERATED ALWAYS AS."
                ),
            )
        stored = column.generated_stored and self.capabilities.stored_generated_columns
        mode = "STORED" if stored else "VIRTUAL"
        return f"GENERATED ALWAYS AS ({column.generated}) {mode}"

    def _primary_key_clause(self, column: ColumnState) -> list[str]:
        """Render the primary-key and auto-increment keywords for a column."""
        return ["PRIMARY KEY"]

    def _default_clause(self, column: ColumnState) -> str:
        """Render the ``DEFAULT ...`` clause, or ``""`` when there is none."""
        from ..schema import NOT_PROVIDED

        if column.default is NOT_PROVIDED:
            return ""
        return f"DEFAULT {self.literal(column.default, column)}"

    def _references_clause(self, reference: Any) -> str:
        """Render an inline ``REFERENCES table(column) ON DELETE ... ON UPDATE ...``."""
        clause = (
            f"REFERENCES {self.quote(reference.table)} ({self.quote(reference.column)}) "
            f"ON DELETE {reference.on_delete} ON UPDATE {reference.on_update}"
        )
        if reference.deferrable and self.capabilities.deferrable_constraints:
            clause += " DEFERRABLE INITIALLY DEFERRED"
        return clause

    def _inline_column_comment(self, column: ColumnState) -> str:
        """Render an inline column comment, or ``""`` where unsupported."""
        return ""

    # ── Table DDL ───────────────────────────────────────────────────────

    def create_table(self, table: TableState, *, deferred_columns: frozenset[str] = frozenset()) -> list[Statement]:
        """Render the statements that create *table*.

        Emits one ``CREATE TABLE`` with inline column definitions and table
        constraints, followed by any out-of-line statements the dialect
        requires (comments on PostgreSQL, for instance).

        Args:
            table: The table state to create.
            deferred_columns: Database column names whose foreign keys must be
                added separately by a later ``AddConstraint``, to break a
                circular dependency between tables.

        Returns:
            The statements, in execution order.
        """
        from ..schema import (
            CheckConstraintState,
            ForeignKeyConstraintState,
            PrimaryKeyConstraintState,
            UniqueConstraintState,
        )

        body: list[str] = []
        composite_pk = any(isinstance(c, PrimaryKeyConstraintState) for c in table.constraints)

        for column in table.columns.values():
            effective = column.evolve(primary_key=False) if composite_pk and column.primary_key else column
            body.append(
                self.column_definition(
                    effective,
                    inline_reference=column.column not in deferred_columns,
                )
            )

        for constraint in table.constraints:
            if isinstance(constraint, UniqueConstraintState) and constraint.requires_index:
                # Partial or expression-based uniqueness cannot be a table
                # constraint on any dialect; it is emitted as a unique index by
                # create_index() instead.
                continue
            if isinstance(constraint, CheckConstraintState) and not self.capabilities.check_constraints:
                continue
            if isinstance(constraint, ForeignKeyConstraintState) and set(constraint.columns) & deferred_columns:
                continue
            rendered = self.constraint_definition(constraint)
            if rendered:
                body.append(rendered)

        ine = "IF NOT EXISTS " if self.capabilities.table_if_not_exists else ""
        columns_sql = ",\n  ".join(body)
        sql = f"CREATE TABLE {ine}{self.quote(table.db_table)} (\n  {columns_sql}\n)"
        sql += self._create_table_suffix(table)

        statements = [Statement(sql=sql + ";", description=f"Create table {table.db_table}")]
        statements.extend(self._table_comment_statements(table))
        return statements

    def _create_table_suffix(self, table: TableState) -> str:
        """Render dialect-specific trailing clauses (engine, tablespace, charset)."""
        tablespace = table.options.get("tablespace")
        if tablespace and self.capabilities.tablespaces:
            return f" TABLESPACE {self.quote(tablespace)}"
        return ""

    def _table_comment_statements(self, table: TableState) -> list[Statement]:
        """Render separate statements for table and column comments, where supported."""
        return []

    def drop_table(self, db_table: str, *, cascade: bool = False) -> list[Statement]:
        """Render the statement that drops a table.

        Args:
            db_table: Table name.
            cascade: Also drop dependent objects, where supported.

        Returns:
            A single destructive ``DROP TABLE`` statement.
        """
        sql = f"DROP TABLE IF EXISTS {self.quote(db_table)}"
        if cascade:
            sql += " CASCADE"
        return [Statement(sql=sql + ";", description=f"Drop table {db_table}", destructive=True)]

    def rename_table(self, old: str, new: str) -> list[Statement]:
        """Render the statement that renames a table.

        Args:
            old: Current table name.
            new: New table name.

        Returns:
            A single ``ALTER TABLE ... RENAME TO`` statement.
        """
        return [
            Statement(
                sql=f"ALTER TABLE {self.quote(old)} RENAME TO {self.quote(new)};",
                description=f"Rename table {old} to {new}",
            )
        ]

    # ── Column DDL ──────────────────────────────────────────────────────

    def add_column(self, db_table: str, column: ColumnState) -> list[Statement]:
        """Render the statements that add a column to an existing table.

        Args:
            db_table: Table to alter.
            column: The column to add.

        Returns:
            The statements, in execution order.

        Raises:
            MigrationFault: If the column is ``NOT NULL`` with no default and
                the table may hold rows. Every SQL database rejects that
                combination on a non-empty table; catching it at plan time
                explains the problem, rather than emitting the statement and letting
                it fail against production.
        """
        from ..schema import NOT_PROVIDED

        if not column.null and column.default is NOT_PROVIDED and column.generated is None:
            raise MigrationFault(
                migration="schema-backend",
                reason=(
                    f"Cannot add NOT NULL column {column.column!r} to existing table "
                    f"{db_table!r} without a default. Existing rows would have no value "
                    f"for it. Either give the field a default, make it null=True, or "
                    f"split this into three migrations: add nullable, backfill via "
                    f"RunPython, then alter to NOT NULL."
                ),
            )
        return [
            Statement(
                sql=f"ALTER TABLE {self.quote(db_table)} ADD COLUMN {self.column_definition(column)};",
                description=f"Add column {db_table}.{column.column}",
            )
        ]

    def drop_column(self, db_table: str, db_column: str) -> list[Statement]:
        """Render the statements that drop a column.

        Args:
            db_table: Table to alter.
            db_column: Database column name to drop.

        Returns:
            A single destructive statement.

        Raises:
            MigrationFault: If the dialect cannot drop columns.
        """
        if not self.capabilities.drop_column:
            raise MigrationFault(
                migration="schema-backend",
                reason=f"{self.dialect} does not support DROP COLUMN.",
            )
        return [
            Statement(
                sql=f"ALTER TABLE {self.quote(db_table)} DROP COLUMN {self.quote(db_column)};",
                description=f"Drop column {db_table}.{db_column}",
                destructive=True,
            )
        ]

    def rename_column(self, db_table: str, old: str, new: str) -> list[Statement]:
        """Render the statements that rename a column.

        Args:
            db_table: Table to alter.
            old: Current column name.
            new: New column name.

        Returns:
            A single ``RENAME COLUMN`` statement.

        Raises:
            MigrationFault: If the dialect cannot rename columns.
        """
        if not self.capabilities.rename_column:
            raise MigrationFault(
                migration="schema-backend",
                reason=f"{self.dialect} does not support RENAME COLUMN.",
            )
        return [
            Statement(
                sql=(f"ALTER TABLE {self.quote(db_table)} RENAME COLUMN {self.quote(old)} TO {self.quote(new)};"),
                description=f"Rename column {db_table}.{old} to {new}",
            )
        ]

    def alter_column(self, table: TableState, old: ColumnState, new: ColumnState) -> list[Statement]:
        """Render the statements that change a column's definition.

        Emits only the sub-changes that actually differ: type, nullability, and
        default are independent clauses. An ``AlterField`` carrying only a new type
        would discard every other detected difference.

        Args:
            table: The table being altered, needed by backends that emulate
                this by rebuilding the whole table.
            old: The column's current state.
            new: Its desired state.

        Returns:
            The statements, in execution order. Empty when nothing differs.

        Raises:
            MigrationFault: If a required alteration is unsupported and cannot
                be emulated.
        """
        from ..schema import NOT_PROVIDED

        statements: list[str] = []
        quoted_table = self.quote(table.db_table)
        quoted_column = self.quote(new.column)

        if self.column_type(old) != self.column_type(new):
            if not self.capabilities.alter_column_type:
                raise MigrationFault(
                    migration="schema-backend",
                    reason=f"{self.dialect} cannot change the type of column {new.column!r} in place.",
                )
            statements.append(f"ALTER TABLE {quoted_table} ALTER COLUMN {quoted_column} TYPE {self.column_type(new)}")

        if old.null != new.null:
            if not self.capabilities.alter_column_null:
                raise MigrationFault(
                    migration="schema-backend",
                    reason=f"{self.dialect} cannot change nullability of column {new.column!r} in place.",
                )
            action = "DROP NOT NULL" if new.null else "SET NOT NULL"
            statements.append(f"ALTER TABLE {quoted_table} ALTER COLUMN {quoted_column} {action}")

        if old.default != new.default:
            if not self.capabilities.alter_column_default:
                raise MigrationFault(
                    migration="schema-backend",
                    reason=f"{self.dialect} cannot change the default of column {new.column!r} in place.",
                )
            if new.default is NOT_PROVIDED:
                statements.append(f"ALTER TABLE {quoted_table} ALTER COLUMN {quoted_column} DROP DEFAULT")
            else:
                literal = self.literal(new.default, new)
                statements.append(f"ALTER TABLE {quoted_table} ALTER COLUMN {quoted_column} SET DEFAULT {literal}")

        rendered = [
            Statement(sql=sql + ";", description=f"Alter column {table.db_table}.{new.column}") for sql in statements
        ]

        # A single-column UNIQUE is a constraint, not part of the column
        # definition, so no ALTER COLUMN clause can toggle it. It is added and
        # dropped as a unique index instead.
        if old.unique != new.unique and not new.primary_key:
            from ..schema import IndexState, auto_index_name

            index = IndexState(
                name=auto_index_name(table.db_table, (new.column,), unique=True),
                columns=(new.column,),
                unique=True,
            )
            if new.unique:
                rendered.extend(self.create_index(table.db_table, index))
            else:
                rendered.extend(self.drop_index(table.db_table, index.name))

        return rendered

    # ── Index DDL ───────────────────────────────────────────────────────

    def create_index(self, db_table: str, index: IndexState) -> list[Statement]:
        """Render the statements that create an index.

        Downgrades an unsupported access method to the dialect default rather
        than failing, since a B-tree index is always a correct -- if slower --
        substitute. A partial index whose predicate the dialect cannot express
        *does* fail, because silently indexing every row changes the meaning of
        a unique partial index.

        Args:
            db_table: Table to index.
            index: The index definition.

        Returns:
            A single ``CREATE INDEX`` statement.

        Raises:
            MigrationFault: If the index requires a partial predicate or an
                expression key the dialect does not support.
        """
        if index.condition and not self.capabilities.partial_indexes:
            raise MigrationFault(
                migration="schema-backend",
                reason=(
                    f"{self.dialect} does not support partial indexes, required by index "
                    f"{index.name!r} on {db_table!r}. Remove the `condition` or target a "
                    f"database that supports WHERE on CREATE INDEX."
                ),
            )
        if index.expressions and not self.capabilities.expression_indexes:
            raise MigrationFault(
                migration="schema-backend",
                reason=(
                    f"{self.dialect} does not support expression indexes, required by "
                    f"index {index.name!r} on {db_table!r}."
                ),
            )

        unique = "UNIQUE " if index.unique else ""
        ine = "IF NOT EXISTS " if self.capabilities.index_if_not_exists else ""
        name = self.truncate_identifier(index.name)

        keys: list[str] = []
        for position, column in enumerate(index.columns):
            key = self.quote(column)
            if self.capabilities.index_opclasses and position < len(index.opclasses) and index.opclasses[position]:
                key += f" {index.opclasses[position]}"
            keys.append(key)
        # Expressions are trusted developer SQL, emitted verbatim. They are
        # parenthesized only when not already wrapped, so a plain `LOWER(x)`
        # does not become `((LOWER(x)))`.
        for expression in index.expressions:
            text = expression.strip()
            keys.append(text if _is_parenthesized(text) else f"({text})")

        using = ""
        if index.method != "BTREE" and index.method in self.capabilities.index_methods:
            using = f" USING {index.method}"

        sql = f"CREATE {unique}INDEX {ine}{self.quote(name)} ON {self.quote(db_table)}{using} ({', '.join(keys)})"

        if index.include and self.capabilities.covering_indexes:
            sql += f" INCLUDE ({self.quote_all(index.include)})"
        if index.tablespace and self.capabilities.tablespaces:
            sql += f" TABLESPACE {self.quote(index.tablespace)}"
        if index.condition:
            sql += f" WHERE ({index.condition})"

        return [Statement(sql=sql + ";", description=f"Create index {name} on {db_table}")]

    def drop_index(self, db_table: str, name: str) -> list[Statement]:
        """Render the statements that drop an index.

        Args:
            db_table: Table the index belongs to. Required on MySQL, where
                ``DROP INDEX`` must be qualified; ignored elsewhere.
            name: Index name.

        Returns:
            A single ``DROP INDEX`` statement.
        """
        return [
            Statement(
                sql=f"DROP INDEX IF EXISTS {self.quote(self.truncate_identifier(name))};",
                description=f"Drop index {name}",
            )
        ]

    # ── Constraint DDL ──────────────────────────────────────────────────

    def constraint_definition(self, constraint: Any) -> str:
        """Render a constraint as an inline ``CREATE TABLE`` body fragment.

        Args:
            constraint: Any :class:`~aquilia.models.migration.schema.ConstraintState`.

        Returns:
            The SQL fragment, or ``""`` if this constraint must be emitted as
            an index instead.

        Raises:
            MigrationFault: If the dialect cannot express this constraint kind.
        """
        from ..schema import (
            CheckConstraintState,
            ExclusionConstraintState,
            ForeignKeyConstraintState,
            PrimaryKeyConstraintState,
            UniqueConstraintState,
        )

        name = self.quote(self.truncate_identifier(constraint.name))

        if isinstance(constraint, CheckConstraintState):
            return f"CONSTRAINT {name} CHECK ({constraint.check})"

        if isinstance(constraint, UniqueConstraintState):
            if constraint.requires_index:
                return ""
            clause = f"CONSTRAINT {name} UNIQUE ({self.quote_all(constraint.columns)})"
            if constraint.deferrable and self.capabilities.deferrable_constraints:
                clause += " DEFERRABLE INITIALLY DEFERRED"
            return clause

        if isinstance(constraint, PrimaryKeyConstraintState):
            return f"CONSTRAINT {name} PRIMARY KEY ({self.quote_all(constraint.columns)})"

        if isinstance(constraint, ForeignKeyConstraintState):
            clause = (
                f"CONSTRAINT {name} FOREIGN KEY ({self.quote_all(constraint.columns)}) "
                f"REFERENCES {self.quote(constraint.target)} ({self.quote_all(constraint.target_columns)}) "
                f"ON DELETE {constraint.on_delete} ON UPDATE {constraint.on_update}"
            )
            if constraint.deferrable and self.capabilities.deferrable_constraints:
                clause += " DEFERRABLE INITIALLY DEFERRED"
            return clause

        if isinstance(constraint, ExclusionConstraintState):
            if not self.capabilities.exclusion_constraints:
                raise MigrationFault(
                    migration="schema-backend",
                    reason=(
                        f"{self.dialect} does not support EXCLUDE constraints, required by "
                        f"{constraint.name!r}. Exclusion constraints are PostgreSQL-only; "
                        f"enforce this rule in application code for other backends."
                    ),
                )
            pairs = ", ".join(f"{self.quote(col)} WITH {op}" for col, op in constraint.expressions)
            clause = f"CONSTRAINT {name} EXCLUDE USING {constraint.method} ({pairs})"
            if constraint.condition:
                clause += f" WHERE ({constraint.condition})"
            if constraint.deferrable and self.capabilities.deferrable_constraints:
                clause += " DEFERRABLE INITIALLY DEFERRED"
            return clause

        raise MigrationFault(
            migration="schema-backend",
            reason=f"Unsupported constraint type {type(constraint).__name__}.",
        )

    def add_constraint(self, db_table: str, constraint: Any) -> list[Statement]:
        """Render the statements that add a constraint to an existing table.

        A partial or expression-based unique constraint is emitted as a unique
        index, which is the only form any dialect accepts. This follows from the
        constraint's own structure rather than from a regex over generated SQL.

        Args:
            db_table: Table to alter.
            constraint: The constraint to add.

        Returns:
            The statements, in execution order.

        Raises:
            MigrationFault: If the dialect cannot add constraints after table
                creation and no index-based equivalent exists.
        """
        from ..schema import IndexState, UniqueConstraintState

        if isinstance(constraint, UniqueConstraintState) and constraint.requires_index:
            return self.create_index(
                db_table,
                IndexState(
                    name=constraint.name,
                    columns=constraint.columns,
                    expressions=constraint.expressions,
                    unique=True,
                    condition=constraint.condition,
                    include=constraint.include,
                ),
            )

        if not self.capabilities.add_constraint:
            if isinstance(constraint, UniqueConstraintState):
                return self.create_index(
                    db_table,
                    IndexState(name=constraint.name, columns=constraint.columns, unique=True),
                )
            raise MigrationFault(
                migration="schema-backend",
                reason=(
                    f"{self.dialect} cannot add constraint {constraint.name!r} to an "
                    f"existing table. Declare it when the table is created, or recreate "
                    f"the table with the constraint in place."
                ),
            )

        definition = self.constraint_definition(constraint)
        if not definition:
            return []
        return [
            Statement(
                sql=f"ALTER TABLE {self.quote(db_table)} ADD {definition};",
                description=f"Add constraint {constraint.name} on {db_table}",
            )
        ]

    def drop_constraint(self, db_table: str, name: str) -> list[Statement]:
        """Render the statements that drop a named constraint.

        Args:
            db_table: Table to alter.
            name: Constraint name.

        Returns:
            A single ``DROP CONSTRAINT`` statement.

        Raises:
            MigrationFault: If the dialect cannot drop constraints.
        """
        if not self.capabilities.drop_constraint:
            raise MigrationFault(
                migration="schema-backend",
                reason=(
                    f"{self.dialect} cannot drop constraint {name!r} from table {db_table!r}. "
                    f"Recreating the table without the constraint is the only option."
                ),
            )
        return [
            Statement(
                sql=(
                    f"ALTER TABLE {self.quote(db_table)} DROP CONSTRAINT {self.quote(self.truncate_identifier(name))};"
                ),
                description=f"Drop constraint {name} on {db_table}",
                destructive=True,
            )
        ]


# ── Registry ────────────────────────────────────────────────────────────────

_BACKENDS: dict[str, SchemaBackend] = {}
_ALIASES: dict[str, str] = {
    "postgres": "postgresql",
    "psql": "postgresql",
    "pg": "postgresql",
    "sqlite3": "sqlite",
    "mariadb": "mysql",
}


def register_backend(backend: SchemaBackend, *, aliases: tuple[str, ...] = ()) -> None:
    """Register a schema backend under its dialect name.

    Third-party backends register themselves at import time, which is what
    makes the migration system extensible to databases Aquilia does not ship
    support for -- no operation class needs to change.

    Args:
        backend: The backend instance to register.
        aliases: Extra names resolving to the same backend (e.g. ``"postgres"``).

    Example:
        >>> register_backend(CockroachBackend(), aliases=("crdb",))
    """
    _BACKENDS[backend.dialect] = backend
    for alias in aliases:
        _ALIASES[alias] = backend.dialect


def get_backend(dialect: str) -> SchemaBackend:
    """Resolve a dialect name to its registered backend.

    Args:
        dialect: Dialect name or alias, case-insensitive.

    Returns:
        The shared backend instance for that dialect.

    Raises:
        MigrationFault: If no backend is registered for *dialect*. Falling back
            to a generic backend would emit SQL that is merely plausible for
            the target database -- that is how ``IF NOT EXISTS`` ends up emitted for
            MySQL, which rejects it.

    Example:
        >>> get_backend("pg").dialect
        'postgresql'
    """
    _ensure_builtins()
    key = (dialect or "").strip().lower()
    key = _ALIASES.get(key, key)
    backend = _BACKENDS.get(key)
    if backend is None:
        raise MigrationFault(
            migration="schema-backend",
            reason=(
                f"No migration backend registered for dialect {dialect!r}. "
                f"Known dialects: {', '.join(sorted(_BACKENDS))}. Register a custom "
                f"backend with aquilia.models.migration.backends.register_backend()."
            ),
        )
    return backend


def known_dialects() -> tuple[str, ...]:
    """Return the sorted names of all registered dialects."""
    _ensure_builtins()
    return tuple(sorted(_BACKENDS))


_BUILTINS_LOADED = False


def _is_parenthesized(text: str) -> bool:
    """Return whether *text* is already wrapped in one matching pair of parentheses.

    Used to avoid double-wrapping an index expression that the developer
    already parenthesized -- ``LOWER(x)`` must become ``(LOWER(x))``, but
    ``(a + b)`` must stay as it is rather than becoming ``((a + b))``.

    Args:
        text: A stripped SQL expression.

    Returns:
        ``True`` when the outermost characters are a matching parenthesis pair
        enclosing the entire expression.
    """
    if not text.startswith("(") or not text.endswith(")"):
        return False
    depth = 0
    for position, char in enumerate(text):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return position == len(text) - 1
    return False


def _ensure_builtins() -> None:
    """Import and register the built-in backends on first use.

    Deferred rather than done at package import so that importing
    :mod:`aquilia.models` does not pay for four backend modules that a given
    process may never use.
    """
    global _BUILTINS_LOADED
    if _BUILTINS_LOADED:
        return
    _BUILTINS_LOADED = True
    from . import mysql, oracle, postgresql, sqlite  # noqa: F401  -- registration side effect

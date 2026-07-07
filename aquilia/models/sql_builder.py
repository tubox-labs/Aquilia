"""
Aquilia SQL Builder -- safe, parameterized SQL generation.

Provides a fluent builder API that produces parameterized SQL
and bind-parameter lists. All *values* passed through ``where(...)``,
``values(...)``, ``set(...)``, etc. are collected into a separate params
list and bound with ``?`` placeholders -- never interpolated into the SQL
string -- to prevent SQL injection.

Identifiers (table names, column names, and raw SQL fragments passed to
``where()``/``having()``/``join(..., on=...)``) are a different story:
they cannot be parameterized in standard SQL, so builders interpolate
them directly into the generated string, double-quoting simple names
(``"col"``) ANSI-style. **Identifiers and raw clause strings must come
from trusted, internal sources only** (model/field names defined in
code) -- never directly from request input -- since nothing here escapes
or validates them beyond the quoting itself.

Usage:
    from aquilia.models.sql_builder import SQLBuilder

    sql, params = (
        SQLBuilder()
        .select("id", "name", "email")
        .from_table("users")
        .where("active = ?", True)
        .where("age > ?", 18)
        .order_by("name")
        .limit(10)
        .build()
    )
    # sql = 'SELECT "id", "name", "email" FROM "users" WHERE (active = ?) AND (age > ?) ORDER BY "name" ASC LIMIT 10'
    # params = [True, 18]
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

__all__ = [
    "SQLBuilder",
    "InsertBuilder",
    "UpdateBuilder",
    "DeleteBuilder",
    "CreateTableBuilder",
    "UpsertBuilder",
    "UpsertIgnoreBuilder",
]


class SQLBuilder:
    """
    SELECT query builder with safe parameter binding.

    Fluent/chainable: every setter returns ``self`` so calls can be
    strung together and terminated with :meth:`build` (or
    :meth:`build_count` for a ``COUNT(*)`` variant of the same query).
    Nothing is executed until ``build()`` is called -- the builder just
    accumulates clause fragments and parameters.

    Column/table identifiers are wrapped in double quotes unless they
    look like a raw SQL expression (see :func:`_is_raw`), in which case
    they are emitted verbatim so aggregate/function expressions
    (``COUNT(*)``, ``table.column``) work. WHERE/HAVING clauses passed to
    :meth:`where`/:meth:`having` are always emitted verbatim (never
    quoted) since they're arbitrary SQL fragments, not single identifiers.
    """

    def __init__(self):
        """Create an empty builder with no table/columns/clauses set yet -- configure via the chainable setters, then call ``build()``."""
        self._columns: list[str] = []
        self._table: str = ""
        self._table_alias: str | None = None
        self._joins: list[tuple[str, str, str]] = []  # (type, table, on)
        self._join_params: list[Any] = []
        self._wheres: list[str] = []
        self._params: list[Any] = []
        self._group_by: list[str] = []
        self._having: list[str] = []
        self._having_params: list[Any] = []
        self._order_by: list[str] = []
        self._limit_val: int | None = None
        self._offset_val: int | None = None
        self._distinct: bool = False

    def select(self, *columns: str) -> SQLBuilder:
        """Set the columns to SELECT. No args (or never calling this) means ``SELECT *``."""
        self._columns = list(columns)
        return self

    def from_table(self, table: str, alias: str | None = None) -> SQLBuilder:
        """Set the FROM table, optionally with an alias (``FROM "table" "alias"``)."""
        self._table = table
        self._table_alias = alias
        return self

    def distinct(self) -> SQLBuilder:
        """Add a DISTINCT modifier to the SELECT clause."""
        self._distinct = True
        return self

    def join(
        self,
        table: str,
        on: str,
        join_type: str = "INNER",
        params: list[Any] | None = None,
    ) -> SQLBuilder:
        """
        Add a JOIN clause: ``<join_type> JOIN "<table>" ON <on>``.

        ``on`` is emitted verbatim (not quoted) since it's a full boolean
        expression, not a single identifier -- write it as raw SQL, e.g.
        ``'"posts"."author_id" = "users"."id"'``. If the ON clause itself
        needs bound values (uncommon), pass them via ``params``; they are
        appended to the query's parameter list ahead of the WHERE params,
        matching the position of the JOIN clause in the emitted SQL.
        """
        self._joins.append((join_type, table, on))
        if params:
            self._join_params.extend(params)
        return self

    def left_join(self, table: str, on: str, params: list[Any] | None = None) -> SQLBuilder:
        """Add a LEFT JOIN clause. Equivalent to ``join(table, on, "LEFT", params)``."""
        return self.join(table, on, "LEFT", params)

    def right_join(self, table: str, on: str, params: list[Any] | None = None) -> SQLBuilder:
        """Add a RIGHT JOIN clause. Equivalent to ``join(table, on, "RIGHT", params)``."""
        return self.join(table, on, "RIGHT", params)

    def where(self, clause: str, *args: Any) -> SQLBuilder:
        """
        Add a WHERE condition, ANDed with any other WHERE conditions.

        ``clause`` is raw SQL (parenthesized individually and joined with
        ``AND`` by :meth:`build`), e.g. ``where("age > ?", 18)``. Calling
        ``where()`` multiple times adds multiple ANDed conditions; there
        is no OR support at this level -- write the OR logic directly
        inside a single ``clause`` string if needed.
        """
        self._wheres.append(clause)
        self._params.extend(args)
        return self

    def where_in(self, column: str, values: Sequence[Any]) -> SQLBuilder:
        """
        Add a ``"column" IN (?, ?, ...)`` WHERE condition, with one bound
        parameter per value.

        Edge case: if ``values`` is empty, adds the literal condition
        ``1 = 0`` instead of emitting ``IN ()`` (invalid/always-surprising
        SQL in most dialects) -- the query becomes unconditionally
        false/matches no rows, which is almost always the desired
        behavior for "match any of these zero ids".
        """
        if not values:
            self._wheres.append("1 = 0")  # Always false
            return self
        placeholders = ", ".join("?" for _ in values)
        self._wheres.append(f'"{column}" IN ({placeholders})')
        self._params.extend(values)
        return self

    def group_by(self, *columns: str) -> SQLBuilder:
        """Add one or more columns to GROUP BY (cumulative across calls)."""
        self._group_by.extend(columns)
        return self

    def having(self, clause: str, *args: Any) -> SQLBuilder:
        """
        Add a HAVING condition (ANDed with other HAVING conditions), for
        filtering on aggregates after GROUP BY. Same semantics as
        :meth:`where` but for the HAVING clause.
        """
        self._having.append(clause)
        self._having_params.extend(args)
        return self

    def order_by(self, *fields: str) -> SQLBuilder:
        """
        Add ORDER BY columns.

        Prefix a field name with ``-`` for descending order:
        ``order_by("-created_at", "name")`` produces
        ``ORDER BY "created_at" DESC, "name" ASC``. Multiple calls are
        cumulative (columns from each call are appended in order).
        """
        for f in fields:
            if f.startswith("-"):
                self._order_by.append(f'"{f[1:]}" DESC')
            else:
                self._order_by.append(f'"{f}" ASC')
        return self

    def limit(self, n: int) -> SQLBuilder:
        """Set LIMIT n. ``n`` is coerced with ``int()`` at build time and interpolated directly (not bound)."""
        self._limit_val = n
        return self

    def offset(self, n: int) -> SQLBuilder:
        """Set OFFSET n. ``n`` is coerced with ``int()`` at build time and interpolated directly (not bound)."""
        self._offset_val = n
        return self

    def build(self) -> tuple[str, list[Any]]:
        """
        Build the final SQL string and parameter list.

        Assembles clauses in standard SQL order (SELECT, FROM, JOINs,
        WHERE, GROUP BY, HAVING, ORDER BY, LIMIT/OFFSET), omitting any
        clause that wasn't configured. Parameters are collected in the
        same order their clauses appear in the SQL (JOIN params, then
        WHERE params, then HAVING params) so positional ``?`` binding
        lines up correctly.

        Returns:
            Tuple of ``(sql_string, params_list)`` -- pass both directly
            to a DB-API-style ``execute(sql, params)`` call.
        """
        parts: list[str] = []
        params: list[Any] = []

        # SELECT
        distinct = "DISTINCT " if self._distinct else ""
        cols = ", ".join(f'"{c}"' if not _is_raw(c) else c for c in self._columns) if self._columns else "*"
        parts.append(f"SELECT {distinct}{cols}")

        # FROM
        table_ref = f'"{self._table}"'
        if self._table_alias:
            table_ref += f' "{self._table_alias}"'
        parts.append(f"FROM {table_ref}")

        # JOINs
        for join_type, join_table, join_on in self._joins:
            parts.append(f'{join_type} JOIN "{join_table}" ON {join_on}')
        params.extend(self._join_params)

        # WHERE
        if self._wheres:
            parts.append("WHERE " + " AND ".join(f"({w})" for w in self._wheres))
            params.extend(self._params)

        # GROUP BY
        if self._group_by:
            cols = ", ".join(f'"{c}"' for c in self._group_by)
            parts.append(f"GROUP BY {cols}")

        # HAVING
        if self._having:
            parts.append("HAVING " + " AND ".join(f"({h})" for h in self._having))
            params.extend(self._having_params)

        # ORDER BY
        if self._order_by:
            parts.append("ORDER BY " + ", ".join(self._order_by))

        # LIMIT / OFFSET
        if self._limit_val is not None:
            parts.append(f"LIMIT {int(self._limit_val)}")
        if self._offset_val is not None:
            parts.append(f"OFFSET {int(self._offset_val)}")

        return " ".join(parts), params

    def build_count(self) -> tuple[str, list[Any]]:
        """
        Build a ``SELECT COUNT(*)`` version of this query, for getting a
        row count without fetching/deserializing every column.

        Reuses this builder's FROM/JOIN/WHERE configuration but ignores
        SELECT columns, DISTINCT, GROUP BY, HAVING, ORDER BY, and
        LIMIT/OFFSET entirely -- those don't affect (or aren't meaningful
        for) a plain row count. Note this means calling ``build_count()``
        on a builder configured with GROUP BY does NOT produce one count
        per group; it counts all matching rows as a single number.

        Returns:
            Tuple of ``(sql_string, params_list)``.
        """
        parts: list[str] = ["SELECT COUNT(*)"]
        params: list[Any] = []

        table_ref = f'"{self._table}"'
        if self._table_alias:
            table_ref += f' "{self._table_alias}"'
        parts.append(f"FROM {table_ref}")

        for join_type, join_table, join_on in self._joins:
            parts.append(f'{join_type} JOIN "{join_table}" ON {join_on}')
        params.extend(self._join_params)

        if self._wheres:
            parts.append("WHERE " + " AND ".join(f"({w})" for w in self._wheres))
            params.extend(self._params)

        return " ".join(parts), params


class InsertBuilder:
    """
    INSERT query builder.

    Usage:
        sql, params = InsertBuilder("users").from_dict({"name": "Alice", "email": "a@example.com"}).build()
        # sql = 'INSERT INTO "users" ("name", "email") VALUES (?, ?)'
        # params = ["Alice", "a@example.com"]
    """

    def __init__(self, table: str):
        """Create an INSERT builder targeting *table* with no columns/values set yet."""
        self._table = table
        self._columns: list[str] = []
        self._values: list[Any] = []
        self._returning: str | None = None

    def columns(self, *cols: str) -> InsertBuilder:
        """Set the column names for the INSERT, in the same order as the values passed to :meth:`values`."""
        self._columns = list(cols)
        return self

    def values(self, *vals: Any) -> InsertBuilder:
        """Set the values for the INSERT, positionally matching the columns set via :meth:`columns`."""
        self._values = list(vals)
        return self

    def from_dict(self, data: dict[str, Any]) -> InsertBuilder:
        """Set columns and values from a dict in one call (keys become columns, in dict iteration order)."""
        self._columns = list(data.keys())
        self._values = list(data.values())
        return self

    def returning(self, column: str) -> InsertBuilder:
        """Add a ``RETURNING "column"`` clause (PostgreSQL/SQLite 3.35+; not supported on MySQL)."""
        self._returning = column
        return self

    def build(self) -> tuple[str, list[Any]]:
        """
        Build ``INSERT INTO "table" (cols...) VALUES (?, ...)``, with an
        optional trailing ``RETURNING "col"`` if :meth:`returning` was set.

        Returns:
            Tuple of ``(sql_string, params_list)`` where ``params_list``
            is exactly the values passed to :meth:`values`/:meth:`from_dict`,
            in column order.
        """
        col_names = ", ".join(f'"{c}"' for c in self._columns)
        placeholders = ", ".join("?" for _ in self._columns)
        sql = f'INSERT INTO "{self._table}" ({col_names}) VALUES ({placeholders})'
        if self._returning:
            sql += f' RETURNING "{self._returning}"'
        return sql, list(self._values)

    def build_many(self, rows: list[dict[str, Any]]) -> tuple[str, list[list[Any]]]:
        """
        Build a single parameterized INSERT statement for use with
        ``executemany``, inserting multiple rows in one round-trip.

        Column names/order are taken from ``rows[0].keys()`` only.
        Subsequent rows are matched to those same columns via
        ``row.get(column)`` -- if a later row is missing a key present in
        the first row, that column is silently bound as ``None`` for that
        row rather than raising; any keys in later rows that aren't in
        the first row's key set are silently ignored. Callers relying on
        every row sharing identical keys as the first row will get a
        NULL for any that don't.

        Args:
            rows: Non-empty list of ``{column: value}`` dicts to insert.

        Returns:
            Tuple of ``(sql_string, params_list)`` where ``params_list``
            is a list of per-row parameter lists, suitable for
            ``cursor.executemany(sql, params_list)``.

        Raises:
            QueryFault: If ``rows`` is empty (there is no first row to
                derive columns from).
        """
        if not rows:
            from aquilia.faults.domains import QueryFault

            raise QueryFault(message="No rows to insert")
        cols = list(rows[0].keys())
        col_names = ", ".join(f'"{c}"' for c in cols)
        placeholders = ", ".join("?" for _ in cols)
        sql = f'INSERT INTO "{self._table}" ({col_names}) VALUES ({placeholders})'
        params_list = [[row.get(c) for c in cols] for row in rows]
        return sql, params_list


class UpdateBuilder:
    """
    UPDATE query builder.

    Usage:
        sql, params = UpdateBuilder("users").set(name="Bob").where("id = ?", 1).build()
        # sql = 'UPDATE "users" SET "name" = ? WHERE (id = ?)'
        # params = ["Bob", 1]
    """

    def __init__(self, table: str):
        """Create an UPDATE builder targeting *table* with no assignments/WHERE clauses set yet."""
        self._table = table
        self._sets: dict[str, Any] = {}
        self._wheres: list[str] = []
        self._params: list[Any] = []

    def set(self, **kwargs: Any) -> UpdateBuilder:
        """
        Set columns to update via keyword arguments (``set(name="Bob")``).

        Multiple calls merge into the same dict of pending assignments --
        setting the same column again overwrites its previous value
        (dict semantics), it doesn't add a duplicate ``SET`` clause. Note
        keyword arguments can't express column names that aren't valid
        Python identifiers; use :meth:`set_dict` for those.
        """
        self._sets.update(kwargs)
        return self

    def set_dict(self, data: dict[str, Any]) -> UpdateBuilder:
        """Set columns to update from a ``{column: value}`` dict. Merges with any prior `set`/`set_dict` calls."""
        self._sets.update(data)
        return self

    def where(self, clause: str, *args: Any) -> UpdateBuilder:
        """Add a WHERE condition, ANDed with any other WHERE conditions (same semantics as ``SQLBuilder.where``)."""
        self._wheres.append(clause)
        self._params.extend(args)
        return self

    def build(self) -> tuple[str, list[Any]]:
        """
        Build ``UPDATE "table" SET "col" = ?, ... [WHERE (...) AND ...]``.

        Params are ordered SET values first, then WHERE values, matching
        their position in the generated SQL.

        Caveat: if no WHERE clause was added, this updates every row in
        the table -- there is no built-in guard against an unconditional
        UPDATE; callers must add a ``where()`` when one is needed.

        Returns:
            Tuple of ``(sql_string, params_list)``.
        """
        set_parts = [f'"{k}" = ?' for k in self._sets]
        set_params = list(self._sets.values())
        sql = f'UPDATE "{self._table}" SET {", ".join(set_parts)}'
        params = set_params.copy()
        if self._wheres:
            sql += " WHERE " + " AND ".join(f"({w})" for w in self._wheres)
            params.extend(self._params)
        return sql, params


class DeleteBuilder:
    """
    DELETE query builder.

    Usage:
        sql, params = DeleteBuilder("users").where("id = ?", 1).build()
        # sql = 'DELETE FROM "users" WHERE (id = ?)'
        # params = [1]
    """

    def __init__(self, table: str):
        self._table = table
        self._wheres: list[str] = []
        self._params: list[Any] = []

    def where(self, clause: str, *args: Any) -> DeleteBuilder:
        """Add a WHERE condition, ANDed with any other WHERE conditions (same semantics as ``SQLBuilder.where``)."""
        self._wheres.append(clause)
        self._params.extend(args)
        return self

    def build(self) -> tuple[str, list[Any]]:
        """
        Build ``DELETE FROM "table" [WHERE (...) AND ...]``.

        Caveat: if no WHERE clause was added, this deletes every row in
        the table -- there is no built-in guard against an unconditional
        DELETE; callers must add a ``where()`` when one is needed.

        Returns:
            Tuple of ``(sql_string, params_list)``.
        """
        sql = f'DELETE FROM "{self._table}"'
        if self._wheres:
            sql += " WHERE " + " AND ".join(f"({w})" for w in self._wheres)
        return sql, list(self._params)


class CreateTableBuilder:
    """
    CREATE TABLE DDL builder.

    Unlike the query builders above, this emits a single DDL string (no
    bound parameters -- column/constraint definitions are structural SQL,
    not data) via :meth:`build`. Column and constraint definitions are
    passed in as pre-rendered SQL fragments (e.g. from
    ``Field.sql_column_def()``); this class only handles assembling them
    into the surrounding ``CREATE TABLE (...)`` statement.

    Usage:
        builder = CreateTableBuilder("users")
        builder.column('"id" INTEGER PRIMARY KEY')
        builder.column('"email" VARCHAR(255) NOT NULL')
        builder.constraint('UNIQUE ("email")')
        sql = builder.build()
    """

    def __init__(self, table: str, if_not_exists: bool = True):
        """Create a builder for *table*; ``if_not_exists`` controls whether ``build()`` emits ``IF NOT EXISTS``."""
        self._table = table
        self._if_not_exists = if_not_exists
        self._columns: list[str] = []
        self._constraints: list[str] = []

    def column(self, definition: str) -> CreateTableBuilder:
        """Append a pre-rendered column definition (e.g. ``'"name" VARCHAR(150) NOT NULL'``)."""
        self._columns.append(definition)
        return self

    def constraint(self, definition: str) -> CreateTableBuilder:
        """Append a pre-rendered table-level constraint (e.g. ``'UNIQUE ("email")'``, ``'PRIMARY KEY ("a", "b")'``)."""
        self._constraints.append(definition)
        return self

    def build(self) -> str:
        """Render ``CREATE TABLE [IF NOT EXISTS] "table" (\\n  col1,\\n  col2,\\n  constraint1\\n);`` -- columns first, then constraints, comma-separated in insertion order."""
        ine = "IF NOT EXISTS " if self._if_not_exists else ""
        body = ",\n  ".join(self._columns + self._constraints)
        return f'CREATE TABLE {ine}"{self._table}" (\n  {body}\n);'


class AlterTableBuilder:
    """
    ALTER TABLE DDL builder -- dialect-aware.

    Supports ADD COLUMN, DROP COLUMN, RENAME COLUMN, RENAME TABLE,
    ADD CONSTRAINT, DROP CONSTRAINT operations.

    Usage:
        alter = AlterTableBuilder("users")
        alter.add_column('"bio" TEXT')
        alter.rename_column("name", "full_name")
        for stmt in alter.build():
            await db.execute(stmt)
    """

    def __init__(self, table: str, dialect: str = "sqlite"):
        """Create a builder targeting *table* on *dialect*; each op method appends one statement, retrieved via ``build()``."""
        self._table = table
        self._dialect = dialect
        self._ops: list[str] = []

    def add_column(self, column_def: str) -> AlterTableBuilder:
        """Add a column."""
        self._ops.append(f'ALTER TABLE "{self._table}" ADD COLUMN {column_def};')
        return self

    def drop_column(self, column: str) -> AlterTableBuilder:
        """Drop a column (SQLite 3.35+, PostgreSQL, MySQL)."""
        self._ops.append(f'ALTER TABLE "{self._table}" DROP COLUMN "{column}";')
        return self

    def rename_column(self, old_name: str, new_name: str) -> AlterTableBuilder:
        """Rename a column (SQLite 3.25+, PostgreSQL, MySQL 8+)."""
        self._ops.append(f'ALTER TABLE "{self._table}" RENAME COLUMN "{old_name}" TO "{new_name}";')
        return self

    def rename_to(self, new_name: str) -> AlterTableBuilder:
        """Rename the table."""
        if self._dialect == "mysql":
            self._ops.append(f'RENAME TABLE "{self._table}" TO "{new_name}";')
        else:
            self._ops.append(f'ALTER TABLE "{self._table}" RENAME TO "{new_name}";')
        self._table = new_name
        return self

    def add_constraint(self, constraint_sql: str) -> AlterTableBuilder:
        """Add a constraint."""
        self._ops.append(f'ALTER TABLE "{self._table}" ADD {constraint_sql};')
        return self

    def drop_constraint(self, name: str) -> AlterTableBuilder:
        """Drop a constraint (not supported on SQLite)."""
        if self._dialect == "sqlite":
            self._ops.append(f'-- SQLite: Cannot drop constraint "{name}" via ALTER TABLE')
        else:
            self._ops.append(f'ALTER TABLE "{self._table}" DROP CONSTRAINT "{name}";')
        return self

    def alter_column_type(self, column: str, new_type: str) -> AlterTableBuilder:
        """Change column type (PostgreSQL only; generates comment for SQLite)."""
        if self._dialect == "sqlite":
            self._ops.append(f'-- SQLite: Cannot alter column type for "{self._table}"."{column}"')
        elif self._dialect == "postgresql":
            self._ops.append(f'ALTER TABLE "{self._table}" ALTER COLUMN "{column}" TYPE {new_type};')
        elif self._dialect == "mysql":
            self._ops.append(f'ALTER TABLE "{self._table}" MODIFY COLUMN "{column}" {new_type};')
        return self

    def set_not_null(self, column: str) -> AlterTableBuilder:
        """Set NOT NULL on a column."""
        if self._dialect == "postgresql":
            self._ops.append(f'ALTER TABLE "{self._table}" ALTER COLUMN "{column}" SET NOT NULL;')
        elif self._dialect == "sqlite":
            self._ops.append(f'-- SQLite: Cannot alter NOT NULL for "{self._table}"."{column}"')
        return self

    def drop_not_null(self, column: str) -> AlterTableBuilder:
        """Drop NOT NULL from a column."""
        if self._dialect == "postgresql":
            self._ops.append(f'ALTER TABLE "{self._table}" ALTER COLUMN "{column}" DROP NOT NULL;')
        elif self._dialect == "sqlite":
            self._ops.append(f'-- SQLite: Cannot alter NOT NULL for "{self._table}"."{column}"')
        return self

    def set_default(self, column: str, default_value: str) -> AlterTableBuilder:
        """Set a default value on a column."""
        if self._dialect in ("postgresql", "mysql"):
            self._ops.append(f'ALTER TABLE "{self._table}" ALTER COLUMN "{column}" SET DEFAULT {default_value};')
        elif self._dialect == "sqlite":
            self._ops.append(f'-- SQLite: Cannot alter default for "{self._table}"."{column}"')
        return self

    def drop_default(self, column: str) -> AlterTableBuilder:
        """Drop the default value from a column."""
        if self._dialect in ("postgresql", "mysql"):
            self._ops.append(f'ALTER TABLE "{self._table}" ALTER COLUMN "{column}" DROP DEFAULT;')
        elif self._dialect == "sqlite":
            self._ops.append(f'-- SQLite: Cannot alter default for "{self._table}"."{column}"')
        return self

    def build(self) -> list[str]:
        """Return the list of ALTER TABLE DDL statements."""
        return self._ops.copy()


class UpsertBuilder:
    """
    INSERT ... ON CONFLICT (upsert) query builder -- dialect-aware.

    Generates:
    - SQLite/PostgreSQL: INSERT ... ON CONFLICT ... DO UPDATE SET ...
    - MySQL: INSERT ... ON DUPLICATE KEY UPDATE ...

    Usage:
        upsert = UpsertBuilder("users", dialect="postgresql")
        upsert.columns("id", "name", "email")
        upsert.values(1, "Alice", "alice@example.com")
        upsert.conflict_target("id")
        upsert.update_columns("name", "email")
        sql, params = upsert.build()
    """

    def __init__(self, table: str, dialect: str = "sqlite"):
        """Create an upsert builder for *table*, rendering SQL for *dialect* (``"mysql"`` gets ``ON DUPLICATE KEY UPDATE``; every other dialect gets ``ON CONFLICT ... DO UPDATE SET``)."""
        self._table = table
        self._dialect = dialect
        self._columns: list[str] = []
        self._values: list[Any] = []
        self._conflict_columns: list[str] = []
        self._update_columns: list[str] = []

    def columns(self, *cols: str) -> UpsertBuilder:
        """Set the column names for the INSERT, in the same order as the values passed to :meth:`values`."""
        self._columns = list(cols)
        return self

    def values(self, *vals: Any) -> UpsertBuilder:
        """Set the values for the INSERT, positionally matching the columns set via :meth:`columns`."""
        self._values = list(vals)
        return self

    def from_dict(self, data: dict[str, Any]) -> UpsertBuilder:
        """Set columns and values from a dict."""
        self._columns = list(data.keys())
        self._values = list(data.values())
        return self

    def conflict_target(self, *columns: str) -> UpsertBuilder:
        """Set the conflict detection columns (unique constraint)."""
        self._conflict_columns = list(columns)
        return self

    def update_columns(self, *columns: str) -> UpsertBuilder:
        """Set columns to update on conflict."""
        self._update_columns = list(columns)
        return self

    def build(self) -> tuple[str, list[Any]]:
        """Render the dialect-appropriate upsert statement.

        MySQL: ``INSERT INTO "table" (cols) VALUES (?, ...) ON DUPLICATE
        KEY UPDATE "col" = VALUES("col"), ...`` (``conflict_target()`` is
        ignored -- MySQL infers the conflicting key itself). Every other
        dialect: ``INSERT INTO "table" (cols) VALUES (?, ...) ON CONFLICT
        (conflict_cols) DO UPDATE SET "col" = EXCLUDED."col", ...``.

        Returns:
            Tuple of ``(sql_string, params_list)`` where ``params_list``
            is exactly the values passed to :meth:`values`/:meth:`from_dict`.
        """
        col_names = ", ".join(f'"{c}"' for c in self._columns)
        placeholders = ", ".join("?" for _ in self._columns)
        params = list(self._values)

        if self._dialect == "mysql":
            # MySQL: INSERT ... ON DUPLICATE KEY UPDATE ...
            update_parts = ", ".join(f'"{c}" = VALUES("{c}")' for c in self._update_columns)
            sql = (
                f'INSERT INTO "{self._table}" ({col_names}) VALUES ({placeholders}) '
                f"ON DUPLICATE KEY UPDATE {update_parts}"
            )
        else:
            # SQLite / PostgreSQL: INSERT ... ON CONFLICT (...) DO UPDATE SET ...
            conflict_cols = ", ".join(f'"{c}"' for c in self._conflict_columns)
            update_parts = ", ".join(f'"{c}" = EXCLUDED."{c}"' for c in self._update_columns)
            sql = (
                f'INSERT INTO "{self._table}" ({col_names}) VALUES ({placeholders}) '
                f"ON CONFLICT ({conflict_cols}) DO UPDATE SET {update_parts}"
            )

        return sql, params


class UpsertIgnoreBuilder:
    """
    INSERT ... ON CONFLICT DO NOTHING query builder -- dialect-aware.

    Generates:
    - SQLite/PostgreSQL: INSERT ... ON CONFLICT (...) DO NOTHING
    - MySQL: INSERT IGNORE INTO ...

    Used by find_or_create() for atomic insert-or-skip semantics.

    Usage:
        builder = UpsertIgnoreBuilder("users", dialect="postgresql")
        builder.columns("id", "email", "name")
        builder.values(1, "alice@example.com", "Alice")
        builder.conflict_target("email")
        sql, params = builder.build()
    """

    def __init__(self, table: str, dialect: str = "sqlite"):
        """Create an insert-or-skip builder for *table*, rendering SQL for *dialect* (``"mysql"`` gets ``INSERT IGNORE``; every other dialect gets ``ON CONFLICT ... DO NOTHING``)."""
        self._table = table
        self._dialect = dialect
        self._columns: list[str] = []
        self._values: list[Any] = []
        self._conflict_columns: list[str] = []

    def columns(self, *cols: str) -> UpsertIgnoreBuilder:
        """Set the column names for the INSERT."""
        self._columns = list(cols)
        return self

    def values(self, *vals: Any) -> UpsertIgnoreBuilder:
        """Set the values for the INSERT."""
        self._values = list(vals)
        return self

    def from_dict(self, data: dict[str, Any]) -> UpsertIgnoreBuilder:
        """Set columns and values from a dict."""
        self._columns = list(data.keys())
        self._values = list(data.values())
        return self

    def conflict_target(self, *columns: str) -> UpsertIgnoreBuilder:
        """Set the conflict detection columns (unique constraint)."""
        self._conflict_columns = list(columns)
        return self

    def build(self) -> tuple[str, list[Any]]:
        """Build the SQL statement and parameters."""
        col_names = ", ".join(f'"{c}"' for c in self._columns)
        placeholders = ", ".join("?" for _ in self._columns)
        params = list(self._values)

        if self._dialect == "mysql":
            # MySQL: INSERT IGNORE INTO ...
            sql = f'INSERT IGNORE INTO "{self._table}" ({col_names}) VALUES ({placeholders})'
        else:
            # SQLite / PostgreSQL: INSERT ... ON CONFLICT (...) DO NOTHING
            conflict_cols = ", ".join(f'"{c}"' for c in self._conflict_columns)
            sql = (
                f'INSERT INTO "{self._table}" ({col_names}) VALUES ({placeholders}) '
                f"ON CONFLICT ({conflict_cols}) DO NOTHING"
            )

        return sql, params


def _is_raw(col: str) -> bool:
    """Check if a column reference is a raw expression (contains parens, *, etc)."""
    return any(c in col for c in ("(", ")", "*", " ", "."))

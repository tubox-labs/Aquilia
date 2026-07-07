"""
Aquilia Migration DSL -- declarative, human-readable migration operations.

Provides a clean, Aquilia-native DSL for expressing schema changes as
composable Python objects. Each operation knows how to compile itself
to SQL for any supported backend (SQLite, PostgreSQL, MySQL).

DSL Primitives:
    CreateModel      -- Create a new table with columns
    DropModel        -- Drop a table
    RenameModel      -- Rename a table
    AddField         -- Add a column to a table
    RemoveField      -- Remove a column from a table
    AlterField       -- Change column type/constraints
    RenameField      -- Rename a column
    CreateIndex      -- Create an index
    DropIndex        -- Drop an index
    AddConstraint    -- Add a constraint
    RemoveConstraint -- Drop a constraint
    RunSQL           -- Execute raw SQL (forward + reverse)
    RunPython        -- Execute a Python callable

Usage in migration files:

    from aquilia.models.migration_dsl import (
        Migration, CreateModel, AddField, CreateIndex, RunSQL,
        columns as C,
    )

    class Meta:
        revision = "20260217_210454"
        slug = "order_orderevent_orderitem_and_7_more"
        models = ["Order", "OrderEvent", "OrderItem", ...]

    operations = [
        CreateModel(
            name="User",
            table="users",
            fields=[
                C.auto("id"),
                C.uuid("uuid", unique=True),
                C.varchar("email", 255, unique=True),
                C.varchar("username", 150, unique=True),
                C.varchar("password_hash", 255),
                C.varchar("first_name", 100, default=""),
                C.varchar("last_name", 100, default=""),
                C.varchar("role", 20, default="customer"),
                C.boolean("is_active", default=True),
                C.boolean("is_verified", default=False),
                C.varchar("avatar_url", 500, null=True),
                C.text("bio", null=True),
                C.varchar("phone", 20, null=True),
                C.text("preferences", default=""),
                C.timestamp("last_login_at", null=True),
                C.integer("login_count", default=0),
                C.timestamp("created_at"),
                C.timestamp("updated_at"),
            ],
        ),
        CreateIndex("idx_users_email", "users", ["email"]),
        CreateIndex("idx_users_username", "users", ["username"]),
        CreateIndex("idx_users_role_is_active", "users", ["role", "is_active"]),
    ]
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

# ── Sentinel for distinguishing 'no default' from None ──────────────────────


# Map Python-style on_delete/on_update constants to valid SQL keywords.
# E.g. "SET_NULL" → "SET NULL", "DO_NOTHING" → "NO ACTION".
_ON_DELETE_SQL_MAP: dict[str, str] = {
    "CASCADE": "CASCADE",
    "SET_NULL": "SET NULL",
    "SET NULL": "SET NULL",
    "SETNULL": "SET NULL",
    "SET_DEFAULT": "SET DEFAULT",
    "SET DEFAULT": "SET DEFAULT",
    "SETDEFAULT": "SET DEFAULT",
    "RESTRICT": "RESTRICT",
    "NO_ACTION": "NO ACTION",
    "NO ACTION": "NO ACTION",
    "DO_NOTHING": "NO ACTION",
    "DO NOTHING": "NO ACTION",
    "DONOTHING": "NO ACTION",
    "PROTECT": "RESTRICT",
}


def _normalize_fk_action(action: str) -> str:
    """Normalize a Python on_delete/on_update constant to valid SQL.

    Converts underscored Python-style constants (``SET_NULL``) to their
    SQL equivalents (``SET NULL``).  Unknown values pass through unchanged.

    Args:
        action: A Django/Aquilia-style constant such as ``"CASCADE"``,
            ``"SET_NULL"``, ``"DO_NOTHING"``, or ``"PROTECT"`` (case-insensitive,
            surrounding whitespace tolerated).

    Returns:
        The equivalent SQL keyword phrase (e.g. ``"SET NULL"``). If ``action``
        is not a recognized constant, it is returned unchanged so callers can
        pass through already-valid SQL.
    """
    return _ON_DELETE_SQL_MAP.get(action.upper().strip(), action)


class _SentinelType:
    """Singleton sentinel used to distinguish 'no default was given' from an
    explicit default of ``None``.

    ``ColumnDef.default`` (and related builder kwargs) need three distinct
    states: "no DEFAULT clause at all", "DEFAULT NULL", and "DEFAULT <value>".
    Using ``None`` for the first case would collide with the second, so this
    sentinel fills that gap. Only one instance ever exists (see ``_SENTINEL``
    below); identity comparison (``is _SENTINEL``) is used throughout the
    module to test for "no default".
    """

    _instance = None

    def __new__(cls):
        """Return the single shared instance, creating it on first use."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self):
        """Return a readable placeholder for debugging/repr output."""
        return "<NO_DEFAULT>"

    def __bool__(self):
        """Always falsy, so ``if col.default:`` treats 'no default' as absent."""
        return False


_SENTINEL = _SentinelType()


def _format_default(value: Any, dialect: str = "sqlite", col_type: str = "") -> str:
    """Format a Python value as a SQL ``DEFAULT`` literal for the given dialect.

    Args:
        value: The Python value to render (``None``, ``bool``, ``int``, ``float``,
            ``str``, or any other object as a last resort).
        dialect: Target SQL dialect -- only ``"postgresql"`` gets special
            handling for booleans; all other dialects fall through to the
            0/1 integer convention.
        col_type: The resolved SQL column type (e.g. ``"BOOLEAN"``, ``"INTEGER"``),
            used only to decide how to render Python ``bool`` values -- PostgreSQL
            renders ``TRUE``/``FALSE`` for actual ``BOOLEAN`` columns but must use
            ``0``/``1`` for boolean defaults stored in ``INTEGER`` columns (to avoid
            a type-mismatch error).

    Returns:
        A SQL literal fit for use directly after ``DEFAULT`` (already quoted for
        strings, with embedded single quotes doubled for safe escaping).

    Note:
        ``bool`` is checked before ``int``/``float`` because in Python
        ``isinstance(True, int)`` is also ``True`` -- the ordering here is load
        bearing.
    """
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        # Only use TRUE/FALSE on actual BOOLEAN columns in PostgreSQL;
        # for INTEGER columns (e.g. from C.integer(..., default=True)),
        # always use 0/1 to avoid PG type-mismatch errors.
        if dialect == "postgresql" and col_type.upper() in ("BOOLEAN", ""):
            return "TRUE" if value else "FALSE"
        return str(int(value))
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        escaped = value.replace("'", "''")
        return f"'{escaped}'"
    return repr(value)


# ── Column Definition Helper ────────────────────────────────────────────────


@dataclass
class ColumnDef:
    """
    A column definition in the DSL.

    Encapsulates the full definition of a database column including
    type, constraints, references, and defaults. This is the basic unit
    used by ``CreateModel.fields`` and ``AddField.column``, and is normally
    constructed via the ``C``/``columns`` builder (see ``_ColumnBuilder``)
    rather than instantiated directly.

    Attributes:
        name: Column name.
        col_type: Base SQL type as written in SQLite terms, e.g. ``"VARCHAR(255)"``,
            ``"INTEGER"``, ``"TIMESTAMP"``. Dialect-specific rendering happens in
            ``_resolve_type``/``to_sql``, so this stays dialect-neutral.
        primary_key: Whether this column is the table's primary key.
        autoincrement: Whether the primary key auto-increments (SERIAL/AUTOINCREMENT/
            AUTO_INCREMENT/IDENTITY depending on dialect). Only meaningful when
            ``primary_key`` is also ``True``.
        unique: Whether to add a ``UNIQUE`` constraint (ignored if ``primary_key``
            is set, since primary keys are already unique).
        nullable: Whether the column allows ``NULL``. When ``False`` (the default)
            and the column is not a primary key, ``NOT NULL`` is emitted.
        default: The column's default value, or the ``_SENTINEL`` marker (the
            dataclass default) meaning "no ``DEFAULT`` clause at all". Use
            ``None`` explicitly to mean ``DEFAULT NULL``.
        references: ``(table, column)`` tuple for an inline foreign key, or
            ``None`` for a plain column.
        on_delete: SQL ``ON DELETE`` action, only emitted when ``references``
            is set. Accepts either raw SQL (``"CASCADE"``) or Python-style
            constants normalized via ``_normalize_fk_action`` (``"SET_NULL"``).
        on_update: SQL ``ON UPDATE`` action, same rules as ``on_delete``.
    """

    name: str
    col_type: str  # e.g. "VARCHAR(255)", "INTEGER", "TIMESTAMP"
    primary_key: bool = False
    autoincrement: bool = False
    unique: bool = False
    nullable: bool = False
    default: Any = _SENTINEL  # sentinel to distinguish from None
    references: tuple[str, str] | None = None  # (table, column)
    on_delete: str = "CASCADE"
    on_update: str = "CASCADE"

    def to_sql(self, dialect: str = "sqlite") -> str:
        """Compile this column to a full SQL column-definition fragment.

        Assembles, in order: quoted name, resolved type, ``UNIQUE`` (if
        applicable), ``PRIMARY KEY`` (+ dialect-specific auto-increment
        keyword), ``NOT NULL``, ``DEFAULT ...`` (skipped on MySQL for
        TEXT/BLOB/JSON/GEOMETRY types, which don't allow literal defaults),
        and a ``REFERENCES ... ON DELETE ... ON UPDATE ...`` clause.

        Args:
            dialect: Target SQL dialect -- one of ``"sqlite"``, ``"postgresql"``,
                ``"mysql"``, ``"oracle"``. Controls type resolution, auto-increment
                syntax, and default-value quirks.

        Returns:
            A single SQL fragment suitable for use inside a ``CREATE TABLE`` or
            ``ALTER TABLE ... ADD COLUMN`` statement, e.g.
            ``'"email" VARCHAR(255) UNIQUE NOT NULL'``.

        Example:
            >>> ColumnDef("age", "INTEGER", default=0).to_sql()
            '"age" INTEGER NOT NULL DEFAULT 0'
        """
        parts = [f'"{self.name}"', self._resolve_type(dialect)]

        if self.unique and not self.primary_key:
            parts.append("UNIQUE")
        if self.primary_key:
            parts.append("PRIMARY KEY")
            if self.autoincrement:
                if dialect == "postgresql":
                    pass  # SERIAL/BIGSERIAL type handles auto-increment
                elif dialect == "mysql":
                    parts.append("AUTO_INCREMENT")
                elif dialect == "oracle":
                    pass  # IDENTITY column handled in _resolve_type
                else:
                    parts.append("AUTOINCREMENT")
        if not self.nullable and not self.primary_key:
            parts.append("NOT NULL")
        if self.default is not _SENTINEL:
            resolved_type = self._resolve_type(dialect)
            # MySQL does not allow DEFAULT on TEXT/BLOB/JSON columns.
            _no_default = dialect == "mysql" and resolved_type.upper() in (
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
            )
            if not _no_default:
                parts.append(f"DEFAULT {_format_default(self.default, dialect, resolved_type)}")
        if self.references:
            ref_table, ref_col = self.references
            parts.append(f'REFERENCES "{ref_table}"("{ref_col}")')
            parts.append(f"ON DELETE {_normalize_fk_action(self.on_delete)}")
            parts.append(f"ON UPDATE {_normalize_fk_action(self.on_update)}")

        return " ".join(parts)

    def _resolve_type(self, dialect: str) -> str:
        """Resolve ``col_type`` to the correct SQL type for a specific dialect.

        Handles two concerns:

        1. Auto-increment primary keys: maps the SQLite-flavored ``col_type``
           (``INTEGER``/``BIGINT``) to ``SERIAL``/``BIGSERIAL`` (PostgreSQL),
           plain ``INTEGER``/``BIGINT`` (MySQL, which relies on the separate
           ``AUTO_INCREMENT`` keyword added in ``to_sql``), or
           ``NUMBER(10|19) GENERATED ALWAYS AS IDENTITY`` (Oracle).
        2. Plain type translation for non-autoincrement columns: e.g.
           ``BLOB`` → ``BYTEA`` on PostgreSQL, ``BOOLEAN``/``BIGINT`` → ``INTEGER``
           on MySQL and SQLite, ``VARCHAR(n)`` → ``VARCHAR2(n)`` on Oracle, etc.

        Args:
            dialect: Target SQL dialect.

        Returns:
            The dialect-specific SQL type string. Falls back to ``self.col_type``
            unchanged if no dialect-specific mapping applies.
        """
        t = self.col_type
        if self.autoincrement and self.primary_key:
            if dialect == "postgresql":
                return "BIGSERIAL" if "BIG" in t.upper() else "SERIAL"
            elif dialect == "mysql":
                return "BIGINT" if "BIG" in t.upper() else "INTEGER"
            elif dialect == "oracle":
                base = "NUMBER(19)" if "BIG" in t.upper() else "NUMBER(10)"
                return f"{base} GENERATED ALWAYS AS IDENTITY"
        # Dialect-specific type mappings for non-autoincrement columns
        if dialect == "postgresql":
            upper = t.upper()
            if upper == "BLOB":
                return "BYTEA"
            if upper == "REAL":
                return "DOUBLE PRECISION"
            if upper == "BIGINT":
                return "BIGINT"
            if upper == "TIMESTAMP":
                return "TIMESTAMP WITH TIME ZONE"
        elif dialect == "oracle":
            upper = t.upper()
            if upper == "INTEGER":
                return "NUMBER(10)"
            if upper == "BIGINT":
                return "NUMBER(19)"
            if upper == "SMALLINT":
                return "NUMBER(5)"
            if upper == "BLOB":
                return "BLOB"
            if upper == "TEXT":
                return "CLOB"
            if upper == "REAL" or upper == "FLOAT":
                return "BINARY_DOUBLE"
            if upper == "BOOLEAN":
                return "NUMBER(1)"
            if upper.startswith("VARCHAR("):
                return upper.replace("VARCHAR(", "VARCHAR2(")
            if upper == "TIMESTAMP":
                return "TIMESTAMP WITH TIME ZONE"
        elif dialect == "mysql":
            upper = t.upper()
            if upper == "BOOLEAN":
                return "INTEGER"
            if upper == "BIGINT":
                return "INTEGER"
        elif dialect == "sqlite":
            upper = t.upper()
            if upper == "BIGINT":
                return "INTEGER"
            if upper == "BOOLEAN":
                return "INTEGER"
        return t

    def to_snapshot(self) -> dict[str, Any]:
        """Serialize this column to a snapshot-compatible dict.

        Produces the same shape consumed by ``schema_snapshot.py`` and
        ``from_snapshot`` below. Only non-default/non-empty attributes are
        included (e.g. ``"unique"`` is omitted entirely when ``False``) to
        keep snapshot JSON/SURP files compact.

        Returns:
            A dict with keys among ``name``, ``type``, ``primary_key``,
            ``autoincrement``, ``unique``, ``nullable``, ``default``,
            ``references`` (``{"table": ..., "column": ...}``), ``on_delete``,
            ``on_update``.
        """
        d: dict[str, Any] = {
            "name": self.name,
            "type": self.col_type,
        }
        if self.primary_key:
            d["primary_key"] = True
        if self.autoincrement:
            d["autoincrement"] = True
        if self.unique:
            d["unique"] = True
        if self.nullable:
            d["nullable"] = True
        if self.default is not _SENTINEL:
            d["default"] = self.default
        if self.references:
            d["references"] = {"table": self.references[0], "column": self.references[1]}
            d["on_delete"] = self.on_delete
            d["on_update"] = self.on_update
        return d

    @classmethod
    def from_snapshot(cls, data: dict[str, Any]) -> ColumnDef:
        """Deserialize a ``ColumnDef`` from a snapshot dict (inverse of ``to_snapshot``).

        Args:
            data: A dict as produced by ``to_snapshot``, with at least
                ``"name"`` and ``"type"`` keys; all other keys are optional
                and default to their ``ColumnDef`` field defaults.

        Returns:
            A reconstructed ``ColumnDef``. If ``data`` has no ``"default"``
            key, ``default`` resolves to ``_SENTINEL`` (no default clause),
            matching the dataclass default.
        """
        ref = data.get("references")
        return cls(
            name=data["name"],
            col_type=data["type"],
            primary_key=data.get("primary_key", False),
            autoincrement=data.get("autoincrement", False),
            unique=data.get("unique", False),
            nullable=data.get("nullable", False),
            default=data.get("default", _SENTINEL),
            references=(ref["table"], ref["column"]) if ref else None,
            on_delete=data.get("on_delete", "CASCADE"),
            on_update=data.get("on_update", "CASCADE"),
        )


# ── Column Builder (C namespace) ────────────────────────────────────────────


class _ColumnBuilder:
    """
    Fluent column builder -- the ``columns`` (aliased as ``C``) namespace.

    Usage:
        from aquilia.models.migration_dsl import columns as C

        C.auto("id")
        C.varchar("email", 255, unique=True)
        C.integer("age", null=True)
        C.foreign_key("user_id", "users", "id", on_delete="CASCADE")
    """

    @staticmethod
    def auto(name: str = "id") -> ColumnDef:
        """Auto-incrementing ``INTEGER`` primary key (the default ``id`` column)."""
        return ColumnDef(name=name, col_type="INTEGER", primary_key=True, autoincrement=True)

    @staticmethod
    def bigauto(name: str = "id") -> ColumnDef:
        """Auto-incrementing ``BIGINT`` primary key, for tables expecting >2^31 rows."""
        return ColumnDef(name=name, col_type="BIGINT", primary_key=True, autoincrement=True)

    @staticmethod
    def integer(
        name: str, *, null: bool = False, unique: bool = False, primary_key: bool = False, default: Any = _SENTINEL
    ) -> ColumnDef:
        """A plain ``INTEGER`` column.

        Args:
            name: Column name.
            null: Allow ``NULL`` values.
            unique: Add a ``UNIQUE`` constraint.
            primary_key: Make this the (non-auto-incrementing) primary key.
            default: Default value, or omit for no ``DEFAULT`` clause.
        """
        return ColumnDef(
            name=name, col_type="INTEGER", nullable=null, unique=unique, primary_key=primary_key, default=default
        )

    @staticmethod
    def biginteger(
        name: str, *, null: bool = False, unique: bool = False, primary_key: bool = False, default: Any = _SENTINEL
    ) -> ColumnDef:
        """A ``BIGINT`` column, for values exceeding 32-bit range. See ``integer`` for args."""
        return ColumnDef(
            name=name, col_type="BIGINT", nullable=null, unique=unique, primary_key=primary_key, default=default
        )

    @staticmethod
    def varchar(
        name: str,
        length: int = 255,
        *,
        null: bool = False,
        unique: bool = False,
        primary_key: bool = False,
        default: Any = _SENTINEL,
    ) -> ColumnDef:
        """A ``VARCHAR(length)`` column.

        Args:
            name: Column name.
            length: Maximum character length (default 255).
            null: Allow ``NULL`` values.
            unique: Add a ``UNIQUE`` constraint.
            primary_key: Make this the primary key.
            default: Default value, or omit for no ``DEFAULT`` clause.
        """
        return ColumnDef(
            name=name,
            col_type=f"VARCHAR({length})",
            nullable=null,
            unique=unique,
            primary_key=primary_key,
            default=default,
        )

    @staticmethod
    def text(name: str, *, null: bool = False, primary_key: bool = False, default: Any = _SENTINEL) -> ColumnDef:
        """An unbounded ``TEXT`` column."""
        return ColumnDef(name=name, col_type="TEXT", nullable=null, primary_key=primary_key, default=default)

    @staticmethod
    def boolean(name: str, *, null: bool = False, primary_key: bool = False, default: Any = _SENTINEL) -> ColumnDef:
        """A ``BOOLEAN`` column (stored as ``INTEGER`` 0/1 on SQLite/MySQL)."""
        return ColumnDef(name=name, col_type="BOOLEAN", nullable=null, primary_key=primary_key, default=default)

    @staticmethod
    def real(name: str, *, null: bool = False, primary_key: bool = False, default: Any = _SENTINEL) -> ColumnDef:
        """A floating-point ``REAL`` column (``DOUBLE PRECISION`` on PostgreSQL)."""
        return ColumnDef(name=name, col_type="REAL", nullable=null, primary_key=primary_key, default=default)

    @staticmethod
    def decimal(
        name: str,
        max_digits: int = 10,
        decimal_places: int = 2,
        *,
        null: bool = False,
        primary_key: bool = False,
        default: Any = _SENTINEL,
    ) -> ColumnDef:
        """A fixed-precision ``DECIMAL(max_digits, decimal_places)`` column.

        Args:
            name: Column name.
            max_digits: Total number of significant digits.
            decimal_places: Digits after the decimal point.
            null: Allow ``NULL`` values.
            primary_key: Make this the primary key.
            default: Default value, or omit for no ``DEFAULT`` clause.
        """
        return ColumnDef(
            name=name,
            col_type=f"DECIMAL({max_digits},{decimal_places})",
            nullable=null,
            primary_key=primary_key,
            default=default,
        )

    @staticmethod
    def timestamp(name: str, *, null: bool = False, primary_key: bool = False, default: Any = _SENTINEL) -> ColumnDef:
        """A ``TIMESTAMP`` column (rendered as ``TIMESTAMP WITH TIME ZONE`` on PostgreSQL/Oracle)."""
        return ColumnDef(name=name, col_type="TIMESTAMP", nullable=null, primary_key=primary_key, default=default)

    @staticmethod
    def date(name: str, *, null: bool = False, primary_key: bool = False, default: Any = _SENTINEL) -> ColumnDef:
        """A ``DATE``-only column (no time component)."""
        return ColumnDef(name=name, col_type="DATE", nullable=null, primary_key=primary_key, default=default)

    @staticmethod
    def time(name: str, *, null: bool = False, primary_key: bool = False, default: Any = _SENTINEL) -> ColumnDef:
        """A ``TIME``-only column (no date component)."""
        return ColumnDef(name=name, col_type="TIME", nullable=null, primary_key=primary_key, default=default)

    @staticmethod
    def uuid(
        name: str, *, null: bool = False, unique: bool = False, primary_key: bool = False, default: Any = _SENTINEL
    ) -> ColumnDef:
        """A UUID column, stored as ``VARCHAR(36)`` (its canonical hyphenated text form)."""
        return ColumnDef(
            name=name, col_type="VARCHAR(36)", nullable=null, unique=unique, primary_key=primary_key, default=default
        )

    @staticmethod
    def blob(name: str, *, null: bool = False, primary_key: bool = False) -> ColumnDef:
        """A ``BLOB`` column for arbitrary binary data. No ``default`` support (see ``ColumnDef.to_sql``)."""
        return ColumnDef(name=name, col_type="BLOB", nullable=null, primary_key=primary_key)

    @staticmethod
    def json(name: str, *, null: bool = False, primary_key: bool = False, default: Any = _SENTINEL) -> ColumnDef:
        """A JSON-valued column, stored as ``TEXT`` (dialect-neutral; no native JSON type is used)."""
        return ColumnDef(name=name, col_type="TEXT", nullable=null, primary_key=primary_key, default=default)

    @staticmethod
    def foreign_key(
        name: str,
        ref_table: str,
        ref_column: str = "id",
        *,
        col_type: str = "INTEGER",
        null: bool = False,
        on_delete: str = "CASCADE",
        on_update: str = "CASCADE",
    ) -> ColumnDef:
        """A column with an inline ``REFERENCES`` foreign-key constraint.

        Args:
            name: Column name (e.g. ``"user_id"``).
            ref_table: Name of the referenced table.
            ref_column: Name of the referenced column (default ``"id"``).
            col_type: SQL type of the FK column -- must match the referenced
                column's type (default ``"INTEGER"``).
            null: Allow ``NULL`` (i.e. an optional relationship).
            on_delete: ``ON DELETE`` action -- accepts raw SQL or Python-style
                constants (``"CASCADE"``, ``"SET_NULL"``, ``"RESTRICT"``, etc.),
                normalized by ``_normalize_fk_action``.
            on_update: ``ON UPDATE`` action, same rules as ``on_delete``.

        Example:
            >>> C.foreign_key("user_id", "users", on_delete="SET_NULL", null=True)
        """
        return ColumnDef(
            name=name,
            col_type=col_type,
            nullable=null,
            references=(ref_table, ref_column),
            on_delete=on_delete,
            on_update=on_update,
        )


columns = _ColumnBuilder()
C = columns  # Short alias


# ── Operation Base ──────────────────────────────────────────────────────────


class Operation:
    """Base class for all migration operations.

    Every DSL operation (``CreateModel``, ``AddField``, ``RunSQL``, etc.)
    subclasses this and implements ``to_sql`` (required) and, where the
    change can be undone mechanically, ``reverse_sql``. ``Migration.compile_upgrade``/
    ``compile_downgrade`` iterate over a list of ``Operation`` instances and
    call these methods to produce the SQL executed by ``MigrationRunner``.
    """

    reversible: bool = True

    def to_sql(self, dialect: str = "sqlite") -> list[str]:
        """Compile this operation to one or more forward SQL statements.

        Args:
            dialect: Target SQL dialect (``"sqlite"``, ``"postgresql"``,
                ``"mysql"``, ``"oracle"``).

        Returns:
            A list of complete SQL statement strings (each including its
            trailing ``;``), in the order they must be executed. Comment-only
            lines (starting with ``--``) may be included to document a
            dialect limitation instead of emitting SQL.

        Raises:
            NotImplementedError: Base implementation; subclasses must override.
        """
        raise NotImplementedError

    def reverse_sql(self, dialect: str = "sqlite") -> list[str]:
        """Compile the reverse (rollback) of this operation to SQL.

        Args:
            dialect: Target SQL dialect.

        Returns:
            A list of SQL statements that undo this operation's effect.

        Raises:
            NotImplementedError: If the operation cannot be mechanically
                reversed (the default for any subclass that doesn't override
                this method) -- e.g. dropping a table or column loses the
                original definition, so there's nothing to regenerate from.
                ``Migration.compile_downgrade`` catches this and emits an
                explanatory SQL comment instead of failing.
        """
        raise NotImplementedError(f"{type(self).__name__} is not reversible")

    def describe(self) -> str:
        """Return a short, human-readable one-line description of this operation.

        Used in ``aq db`` CLI output (status/plan) and in
        ``Migration.describe()``'s operation listing. Subclasses generally
        override this to include the model/table/column names involved;
        the base implementation just returns the class name.
        """
        return type(self).__name__

    def to_snapshot_delta(self) -> dict[str, Any]:
        """Describe the snapshot change this operation implies, if any.

        Reserved for future use by tooling that wants to apply an operation's
        effect directly to an in-memory snapshot dict without recomputing a
        full diff. The base implementation returns an empty dict (no-op);
        no subclass currently overrides it.
        """
        return {}


# ── CreateModel ─────────────────────────────────────────────────────────────


@dataclass
class CreateModel(Operation):
    """
    Create a new database table.

    Compiles to a single ``CREATE TABLE IF NOT EXISTS`` statement with one
    column definition per entry in ``fields`` (see ``ColumnDef.to_sql``).
    Reversing this operation drops the table -- safe as long as the table
    was actually created by this migration (it uses ``DROP TABLE IF EXISTS``).

    Usage:
        CreateModel(
            name="User",
            table="users",
            fields=[
                C.auto("id"),
                C.varchar("email", 255, unique=True),
                C.boolean("is_active", default=True),
            ],
        )
    """

    name: str  # Model/class name
    table: str  # Database table name
    fields: list[ColumnDef] = field(default_factory=list)

    def to_sql(self, dialect: str = "sqlite") -> list[str]:
        """Return a single ``CREATE TABLE IF NOT EXISTS "<table>" (...)`` statement."""
        col_defs = ",\n  ".join(f.to_sql(dialect) for f in self.fields)
        return [f'CREATE TABLE IF NOT EXISTS "{self.table}" (\n  {col_defs}\n);']

    def reverse_sql(self, dialect: str = "sqlite") -> list[str]:
        """Return a ``DROP TABLE IF EXISTS "<table>"`` statement (data loss)."""
        return [f'DROP TABLE IF EXISTS "{self.table}";']

    def describe(self) -> str:
        """e.g. ``"CreateModel(User, table=users, 4 fields)"``."""
        return f"CreateModel({self.name}, table={self.table}, {len(self.fields)} fields)"


# ── DropModel ───────────────────────────────────────────────────────────────


@dataclass
class DropModel(Operation):
    """Drop a table, permanently discarding its data.

    Not auto-reversible: once a table is dropped, its column definitions
    are gone, so there's nothing to regenerate a ``CreateModel`` from.
    ``Migration.compile_downgrade`` catches the ``NotImplementedError`` and
    emits a comment; if this migration needs to be rollback-safe, provide
    an explicit ``CreateModel`` (with the original schema) in a companion
    operation or a bespoke reverse migration.
    """

    name: str
    table: str

    def to_sql(self, dialect: str = "sqlite") -> list[str]:
        """Return a ``DROP TABLE IF EXISTS "<table>"`` statement."""
        return [f'DROP TABLE IF EXISTS "{self.table}";']

    def reverse_sql(self, dialect: str = "sqlite") -> list[str]:
        """Always raises -- see class docstring for why this can't be automated."""
        raise NotImplementedError("DropModel is not auto-reversible -- provide a CreateModel")

    def describe(self) -> str:
        """e.g. ``"DropModel(User, table=users)"``."""
        return f"DropModel({self.name}, table={self.table})"


# ── RenameModel ─────────────────────────────────────────────────────────────


@dataclass
class RenameModel(Operation):
    """Rename a table (preserves data).

    Tracks both the model-level name (for readability in migration diffs
    and ``describe()`` output) and the actual database table name -- these
    can differ when a model overrides ``Meta.table_name`` separately from
    its class name. Fully reversible: renaming back is symmetric.
    """

    old_name: str
    new_name: str
    old_table: str
    new_table: str

    def to_sql(self, dialect: str = "sqlite") -> list[str]:
        """Return an ``ALTER TABLE ... RENAME TO ...`` statement (old → new)."""
        return [f'ALTER TABLE "{self.old_table}" RENAME TO "{self.new_table}";']

    def reverse_sql(self, dialect: str = "sqlite") -> list[str]:
        """Return the symmetric rename statement (new → old)."""
        return [f'ALTER TABLE "{self.new_table}" RENAME TO "{self.old_table}";']

    def describe(self) -> str:
        """e.g. ``"RenameModel(OldUser → User)"``."""
        return f"RenameModel({self.old_name} → {self.new_name})"


# ── AddField ────────────────────────────────────────────────────────────────


@dataclass
class AddField(Operation):
    """Add a column to an existing table.

    Reversing drops the newly-added column again (data loss for that
    column only). Note that the reverse statement is emitted unconditionally
    even on dialects/older SQLite versions that historically lacked
    ``DROP COLUMN`` support -- callers targeting such environments should
    verify rollback compatibility separately.
    """

    model_name: str
    table: str
    column: ColumnDef = field(default_factory=lambda: ColumnDef(name="", col_type=""))

    def to_sql(self, dialect: str = "sqlite") -> list[str]:
        """Return an ``ALTER TABLE ... ADD COLUMN <column definition>`` statement."""
        return [f'ALTER TABLE "{self.table}" ADD COLUMN {self.column.to_sql(dialect)};']

    def reverse_sql(self, dialect: str = "sqlite") -> list[str]:
        """Return an ``ALTER TABLE ... DROP COLUMN "<name>"`` statement."""
        return [f'ALTER TABLE "{self.table}" DROP COLUMN "{self.column.name}";']

    def describe(self) -> str:
        """e.g. ``"AddField(User.bio)"``."""
        return f"AddField({self.model_name}.{self.column.name})"


# ── RemoveField ─────────────────────────────────────────────────────────────


@dataclass
class RemoveField(Operation):
    """Remove a column from an existing table.

    Not auto-reversible: the column's original type/constraints/default are
    not retained on this operation (only its name), so there is nothing to
    rebuild an ``AddField`` from automatically.
    """

    model_name: str
    table: str
    column_name: str

    def to_sql(self, dialect: str = "sqlite") -> list[str]:
        """Return an ``ALTER TABLE ... DROP COLUMN "<name>"`` statement."""
        return [f'ALTER TABLE "{self.table}" DROP COLUMN "{self.column_name}";']

    def reverse_sql(self, dialect: str = "sqlite") -> list[str]:
        """Always raises -- the removed column's definition isn't retained here."""
        raise NotImplementedError("RemoveField is not auto-reversible")

    def describe(self) -> str:
        """e.g. ``"RemoveField(User.legacy_flag)"``."""
        return f"RemoveField({self.model_name}.{self.column_name})"


# ── AlterField ──────────────────────────────────────────────────────────────


@dataclass
class AlterField(Operation):
    """
    Alter a column's type, nullability, or default value.

    Only ``new_type``/``nullable``/``new_default``/``drop_default`` fields
    that are explicitly set produce SQL; unset fields (``None`` for
    ``new_type``/``nullable``, ``_SENTINEL`` for ``new_default``) are left
    untouched.

    Dialect support:
        - **PostgreSQL**: full support via separate ``ALTER COLUMN ... TYPE``
          / ``SET``/``DROP NOT NULL`` / ``SET``/``DROP DEFAULT`` clauses.
        - **SQLite**: not supported (SQLite lacks ``ALTER COLUMN``, even on
          3.35+ which added ``DROP COLUMN``). ``to_sql`` emits a ``--``
          comment instead of SQL; a full table rebuild (create new table,
          copy data, drop old, rename) would be required to actually apply
          this change.
        - **MySQL/Oracle**: not currently implemented here -- ``to_sql``
          returns an empty statement list for these dialects (unlike SQLite,
          no comment is emitted either), so this operation is effectively a
          silent no-op on MySQL/Oracle targets.

    This operation has no ``reverse_sql`` override, so it inherits the base
    class's "always raises ``NotImplementedError``" behavior and is treated
    as not-reversible during rollback.
    """

    model_name: str
    table: str
    column_name: str
    new_type: str | None = None
    nullable: bool | None = None
    new_default: Any = _SENTINEL
    drop_default: bool = False

    def to_sql(self, dialect: str = "sqlite") -> list[str]:
        """Compile the requested changes to dialect-specific ``ALTER COLUMN``
        statements (PostgreSQL), a limitation comment (SQLite), or nothing
        (MySQL/Oracle -- see class docstring)."""
        stmts: list[str] = []
        if dialect == "sqlite":
            stmts.append(
                f"-- SQLite: ALTER COLUMN not supported for "
                f'"{self.table}"."{self.column_name}". Requires table rebuild.'
            )
            return stmts

        if dialect == "postgresql":
            if self.new_type:
                stmts.append(f'ALTER TABLE "{self.table}" ALTER COLUMN "{self.column_name}" TYPE {self.new_type};')
            if self.nullable is True:
                stmts.append(f'ALTER TABLE "{self.table}" ALTER COLUMN "{self.column_name}" DROP NOT NULL;')
            elif self.nullable is False:
                stmts.append(f'ALTER TABLE "{self.table}" ALTER COLUMN "{self.column_name}" SET NOT NULL;')
            if self.drop_default:
                stmts.append(f'ALTER TABLE "{self.table}" ALTER COLUMN "{self.column_name}" DROP DEFAULT;')
            elif self.new_default is not _SENTINEL:
                stmts.append(
                    f'ALTER TABLE "{self.table}" ALTER COLUMN '
                    f'"{self.column_name}" SET DEFAULT '
                    f"{_format_default(self.new_default, dialect)};"
                )
        return stmts

    def describe(self) -> str:
        """e.g. ``"AlterField(User.age)"``."""
        return f"AlterField({self.model_name}.{self.column_name})"


# ── RenameField ─────────────────────────────────────────────────────────────


@dataclass
class RenameField(Operation):
    """Rename a column (preserves data). Fully reversible."""

    model_name: str
    table: str
    old_name: str
    new_name: str

    def to_sql(self, dialect: str = "sqlite") -> list[str]:
        """Return an ``ALTER TABLE ... RENAME COLUMN ... TO ...`` statement (old → new)."""
        return [f'ALTER TABLE "{self.table}" RENAME COLUMN "{self.old_name}" TO "{self.new_name}";']

    def reverse_sql(self, dialect: str = "sqlite") -> list[str]:
        """Return the symmetric rename statement (new → old)."""
        return [f'ALTER TABLE "{self.table}" RENAME COLUMN "{self.new_name}" TO "{self.old_name}";']

    def describe(self) -> str:
        """e.g. ``"RenameField(User.name → full_name)"``."""
        return f"RenameField({self.model_name}.{self.old_name} → {self.new_name})"


# ── CreateIndex ─────────────────────────────────────────────────────────────


@dataclass
class CreateIndex(Operation):
    """Create a database index, optionally unique and/or partial.

    ``condition`` adds a ``WHERE (...)`` clause for a partial index (only
    rows matching the condition are indexed). MySQL does not support partial
    indexes, so ``condition`` is silently ignored when ``dialect == "mysql"``.
    """

    name: str
    table: str
    columns: list[str] = field(default_factory=list)
    unique: bool = False
    condition: str | None = None  # Partial index WHERE clause

    def to_sql(self, dialect: str = "sqlite") -> list[str]:
        """Return a ``CREATE [UNIQUE] INDEX IF NOT EXISTS ... ON ... (cols) [WHERE ...]`` statement."""
        u = "UNIQUE " if self.unique else ""
        cols = ", ".join(f'"{c}"' for c in self.columns)
        sql = f'CREATE {u}INDEX IF NOT EXISTS "{self.name}" ON "{self.table}" ({cols})'
        if self.condition and dialect != "mysql":
            sql += f" WHERE ({self.condition})"
        return [sql + ";"]

    def reverse_sql(self, dialect: str = "sqlite") -> list[str]:
        """Return a ``DROP INDEX IF EXISTS "<name>"`` statement."""
        return [f'DROP INDEX IF EXISTS "{self.name}";']

    def describe(self) -> str:
        """e.g. ``"CreateIndex(idx_users_email, users, ['email'])"``."""
        return f"CreateIndex({self.name}, {self.table}, {self.columns})"


# ── DropIndex ───────────────────────────────────────────────────────────────


@dataclass
class DropIndex(Operation):
    """Drop a database index.

    ``table`` is required on MySQL, where ``DROP INDEX`` must be qualified
    with ``ON <table>`` (unlike SQLite/PostgreSQL, where index names are
    unique database-wide). This operation has no ``reverse_sql`` override --
    recreating a dropped index would need its original column list and
    uniqueness flag, which aren't retained here -- so it's treated as
    not-reversible during rollback.
    """

    name: str
    table: str | None = None  # Required for MySQL

    def to_sql(self, dialect: str = "sqlite") -> list[str]:
        """Return a ``DROP INDEX`` statement, qualified with ``ON "<table>"`` on MySQL."""
        if dialect == "mysql" and self.table:
            return [f'DROP INDEX "{self.name}" ON "{self.table}";']
        return [f'DROP INDEX IF EXISTS "{self.name}";']

    def describe(self) -> str:
        """e.g. ``"DropIndex(idx_users_email)"``."""
        return f"DropIndex({self.name})"


# ── AddConstraint ───────────────────────────────────────────────────────────


@dataclass
class AddConstraint(Operation):
    """Add a table-level constraint from a raw SQL constraint fragment.

    ``constraint_sql`` is a hand-written SQL fragment such as
    ``'CONSTRAINT "uq_email" UNIQUE ("email")'`` or
    ``'CHECK (price >= 0)'``. Because SQLite cannot add most constraint
    types via ``ALTER TABLE`` after table creation, ``to_sql`` special-cases
    ``UNIQUE`` constraints by translating them into an equivalent
    ``CREATE UNIQUE INDEX`` (which SQLite *does* support), covering both
    plain-column and expression-based unique constraints. Any other
    constraint kind (``CHECK``, ``EXCLUDE``, etc.) on SQLite falls back to
    an unapplied ``--`` comment, since SQLite has no equivalent mechanism
    post-creation.
    """

    table: str
    constraint_sql: str

    def to_sql(self, dialect: str = "sqlite") -> list[str]:
        """Compile the constraint, translating ``UNIQUE`` constraints to an
        index on SQLite (or wherever the constraint targets an expression
        rather than a plain column list), and emitting plain
        ``ALTER TABLE ... ADD <constraint_sql>`` everywhere else.

        Behavior:
            1. Tries to match ``CONSTRAINT "name" UNIQUE (exprs)`` (named) or
               a bare ``UNIQUE (exprs)`` fragment via regex.
            2. If no name was given, synthesizes one as
               ``uidx_<table>_<sanitized-expression>``.
            3. If the dialect is SQLite, or the unique expression contains a
               function call/expression (detected by the presence of ``(``
               inside the matched columns), emits
               ``CREATE UNIQUE INDEX [IF NOT EXISTS] "<name>" ON "<table>" (exprs)``
               instead of an ``ALTER TABLE ... ADD CONSTRAINT``, since
               non-SQLite dialects can express these as functional unique
               indexes too.
            4. Otherwise (SQLite, non-UNIQUE constraint): returns a ``--``
               comment noting the constraint could not be applied.
            5. Otherwise (non-SQLite): returns a plain
               ``ALTER TABLE "<table>" ADD <constraint_sql>;`` statement.

        This operation has no ``reverse_sql`` override; use
        ``RemoveConstraint`` explicitly if a migration needs to be
        reversible.
        """
        import re

        # Match UNIQUE constraint SQL format
        match = re.search(
            r'CONSTRAINT\s+["\']([^"\']+)["\']\s+UNIQUE\s*\((.+)\)', self.constraint_sql, re.IGNORECASE | re.DOTALL
        )
        match_no_name = None
        if not match:
            match_no_name = re.search(r"UNIQUE\s*\((.+)\)", self.constraint_sql, re.IGNORECASE | re.DOTALL)

        if match or match_no_name:
            if match:
                index_name = match.group(1)
                exprs = match.group(2)
            else:
                exprs = match_no_name.group(1)
                clean_expr = re.sub(r"[^a-zA-Z0-9_]", "_", exprs).strip("_")
                index_name = f"uidx_{self.table}_{clean_expr}"

            # If dialect is SQLite OR the UNIQUE constraint contains an expression (has '('),
            # we must translate it to CREATE UNIQUE INDEX.
            if dialect == "sqlite" or "(" in exprs:
                ine = "" if dialect in ("mysql", "oracle") else " IF NOT EXISTS"
                return [f'CREATE UNIQUE INDEX{ine} "{index_name}" ON "{self.table}" ({exprs});']

        if dialect == "sqlite":
            return [f"-- SQLite: Cannot add check/exclude constraint via ALTER TABLE: {self.constraint_sql};"]

        return [f'ALTER TABLE "{self.table}" ADD {self.constraint_sql};']

    def describe(self) -> str:
        """e.g. ``"AddConstraint(products)"``."""
        return f"AddConstraint({self.table})"


# ── RemoveConstraint ────────────────────────────────────────────────────────


@dataclass
class RemoveConstraint(Operation):
    """Remove a named constraint from a table.

    Not supported on SQLite -- SQLite has no ``ALTER TABLE ... DROP
    CONSTRAINT``, so ``to_sql`` emits an unapplied ``--`` comment there.
    This operation has no ``reverse_sql`` override; the constraint's
    original definition isn't retained here, so it's treated as
    not-reversible during rollback.
    """

    table: str
    name: str

    def to_sql(self, dialect: str = "sqlite") -> list[str]:
        """Return an ``ALTER TABLE ... DROP CONSTRAINT "<name>"`` statement,
        or a ``--`` comment on SQLite (unsupported)."""
        if dialect == "sqlite":
            return [f'-- SQLite: Cannot drop constraint "{self.name}" via ALTER TABLE;']
        return [f'ALTER TABLE "{self.table}" DROP CONSTRAINT "{self.name}";']

    def describe(self) -> str:
        """e.g. ``"RemoveConstraint(products.uq_sku)"``."""
        return f"RemoveConstraint({self.table}.{self.name})"


# ── RunSQL ──────────────────────────────────────────────────────────────────


@dataclass
class RunSQL(Operation):
    """
    Execute raw SQL statements (forward and optionally reverse).

    Use this as an escape hatch for schema/data changes that don't map
    cleanly onto the other DSL operations -- e.g. seeding lookup data,
    creating views, or dialect-specific DDL. ``sql``/``reverse`` accept
    either a single SQL string or a list of statements executed in order.
    If ``reverse`` is left empty, ``reverse_sql`` returns an empty list
    (not an error) -- rollback silently does nothing for this operation
    rather than failing, so reversibility is opt-in via the ``reverse``
    argument.

    Usage:
        RunSQL(
            sql="INSERT INTO config (key, val) VALUES ('version', '1.0');",
            reverse_sql="DELETE FROM config WHERE key = 'version';",
        )

        RunSQL(
            sql=[
                "CREATE VIEW active_users AS SELECT * FROM users WHERE is_active=1;",
                "CREATE VIEW admin_users AS SELECT * FROM users WHERE role='admin';",
            ],
        )
    """

    sql: str | list[str] = ""
    reverse: str | list[str] = ""

    def to_sql(self, dialect: str = "sqlite") -> list[str]:
        """Return ``sql`` as a list of statements (dialect is ignored -- the
        SQL is used verbatim as provided by the caller)."""
        if isinstance(self.sql, list):
            return self.sql
        return [self.sql] if self.sql else []

    def reverse_sql(self, dialect: str = "sqlite") -> list[str]:
        """Return ``reverse`` as a list of statements, or ``[]`` if none was given."""
        if isinstance(self.reverse, list):
            return self.reverse
        return [self.reverse] if self.reverse else []

    def describe(self) -> str:
        """e.g. ``"RunSQL(INSERT INTO config (key, val) VALUES ('versio...)"`` (truncated preview)."""
        preview = (self.sql if isinstance(self.sql, str) else self.sql[0]) if self.sql else "(empty)"
        return f"RunSQL({preview[:60]}...)"


# ── RunPython ───────────────────────────────────────────────────────────────


@dataclass
class RunPython(Operation):
    """
    Execute a Python callable as a data migration step (no SQL of its own).

    Use this for data migrations that can't be expressed as SQL alone --
    e.g. transforming data using application logic, calling external
    services, or complex conditional backfills. ``forward``/``reverse`` are
    invoked by ``MigrationRunner`` with the live ``AquiliaDatabase``
    connection as their sole argument; both sync and async callables are
    supported (the runner awaits coroutine functions).

    Caveats:
        - ``to_sql``/``reverse_sql`` always return ``[]`` -- this operation
          produces no SQL text; ``MigrationRunner`` special-cases
          ``RunPython`` operations (via ``Migration.get_python_ops``) and
          invokes ``forward``/``reverse`` directly instead.
        - ``reversible`` is hardcoded to ``True`` regardless of whether
          ``reverse`` is actually set. If ``reverse`` is ``None`` and a
          rollback reaches this operation, the runner's rollback loop will
          skip invoking it (since ``py_op.forward``/``reverse`` are checked
          for truthiness before calling) rather than raising -- so an
          irreversible ``RunPython`` step silently does nothing on
          rollback instead of erroring like other non-reversible operations.
    """

    forward: Callable | None = None
    reverse: Callable | None = None

    reversible = True

    def to_sql(self, dialect: str = "sqlite") -> list[str]:
        """Always returns ``[]`` -- execution is handled by the runner, not SQL."""
        return []  # Not SQL -- handled by runner

    def reverse_sql(self, dialect: str = "sqlite") -> list[str]:
        """Always returns ``[]`` -- see ``to_sql``."""
        return []

    def describe(self) -> str:
        """e.g. ``"RunPython(populate_slugs)"``, or ``"RunPython((none))"`` if unset."""
        name = self.forward.__name__ if self.forward else "(none)"
        return f"RunPython({name})"


# ── Migration Container ────────────────────────────────────────────────────


@dataclass
class Migration:
    """
    Container for a set of migration operations with metadata.

    This is the top-level object in a DSL migration file -- the module-level
    ``operations`` list plus a ``Meta`` class (``revision``, ``slug``,
    ``models``, optionally ``dependencies``) are assembled into a
    ``Migration`` instance by ``migration_runner._build_migration_from_module``
    before being applied.

    Attributes:
        revision: Timestamp-based revision ID (``YYYYMMDD_HHMMSS``), also
            used as the migration file's primary sort key and the value
            recorded in the ``aquilia_migrations`` tracking table.
        slug: Human-readable suffix describing the change, used to build the
            migration filename (``<revision>_<slug>.py``).
        models: Names of models affected by this migration (informational --
            shown in ``describe()`` and CLI output).
        dependencies: Revision IDs of migrations that must be applied before
            this one (currently informational bookkeeping; ordering is
            actually driven by filename/revision sort order, not this list).
        operations: The ordered list of ``Operation`` instances that make up
            this migration.

    Usage:
        migration = Migration(
            revision="20260217_210454",
            slug="initial_schema",
            models=["User", "Order", "Product"],
            operations=[
                CreateModel(...),
                CreateIndex(...),
            ],
        )
    """

    revision: str
    slug: str
    models: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    operations: list[Operation] = field(default_factory=list)

    def compile_upgrade(self, dialect: str = "sqlite") -> list[str]:
        """Compile all operations, in declared order, to forward SQL statements.

        Args:
            dialect: Target SQL dialect passed through to each operation's
                ``to_sql``.

        Returns:
            A flat list of SQL statements (including any ``--`` comments
            emitted for unsupported dialect-specific operations) to execute
            in order to apply this migration.
        """
        stmts: list[str] = []
        for op in self.operations:
            stmts.extend(op.to_sql(dialect))
        return stmts

    def compile_downgrade(self, dialect: str = "sqlite") -> list[str]:
        """Compile all operations, in *reverse* declared order, to rollback SQL.

        Args:
            dialect: Target SQL dialect passed through to each operation's
                ``reverse_sql``.

        Returns:
            A flat list of SQL statements that undo this migration, in the
            correct (reverse) order. Operations that raise
            ``NotImplementedError`` (i.e. cannot be mechanically reversed,
            such as ``DropModel`` or ``RemoveField``) do not abort the whole
            downgrade -- instead, a ``-- <description> is not auto-reversible``
            comment is inserted in their place so the rest of the rollback
            can still be inspected/executed.
        """
        stmts: list[str] = []
        for op in reversed(self.operations):
            try:
                stmts.extend(op.reverse_sql(dialect))
            except NotImplementedError:
                stmts.append(f"-- {op.describe()} is not auto-reversible")
        return stmts

    def get_python_ops(self) -> list[RunPython]:
        """Return all ``RunPython`` operations in this migration, in declared order.

        Used by ``MigrationRunner`` to invoke data-migration callables
        separately from the SQL statements produced by ``compile_upgrade``
        (``RunPython.to_sql`` always returns ``[]``, so these operations
        would otherwise be silently skipped).
        """
        return [op for op in self.operations if isinstance(op, RunPython)]

    def describe(self) -> str:
        """Return a multi-line human-readable summary of this migration.

        Includes the revision/slug header, affected model names, and a
        bulleted list of each operation's ``describe()`` output. Used by
        the ``aq db`` CLI (e.g. ``sqlmigrate``/status output) to preview a
        migration without applying it.
        """
        lines = [
            f"Migration {self.revision} ({self.slug})",
            f"  Models: {', '.join(self.models)}",
            f"  Operations ({len(self.operations)}):",
        ]
        for op in self.operations:
            lines.append(f"    - {op.describe()}")
        return "\n".join(lines)


# ── Utility: Convert raw-SQL migration to DSL ──────────────────────────────


def raw_sql_to_operations(upgrade_sql: str, downgrade_sql: str = "") -> list[Operation]:
    """
    Convert raw SQL strings into a list of ``RunSQL`` operations.

    This is a compatibility helper for adapting existing raw-SQL migration
    files (the ``migrations.py`` legacy system's ``upgrade()``/``downgrade()``
    string bodies) into the DSL's ``operations`` list format.

    Args:
        upgrade_sql: The forward SQL to run, as a single string (may itself
            contain multiple statements, but is passed through as-is since
            no statement splitting is performed).
        downgrade_sql: The corresponding rollback SQL, or empty string if
            the migration has no reverse.

    Returns:
        A single-element list containing one ``RunSQL`` operation, or an
        empty list if ``upgrade_sql`` is blank/whitespace-only.
    """
    ops: list[Operation] = []
    if upgrade_sql.strip():
        ops.append(RunSQL(sql=upgrade_sql.strip(), reverse=downgrade_sql.strip()))
    return ops

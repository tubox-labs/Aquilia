"""
Aquilia Schema Snapshot & Diff Engine.

Provides:
- ModelSnapshot: captures the current state of all Model subclasses
- SchemaDiff: computes the difference between two snapshots
- Rename heuristics for detecting renamed models/fields
- DSL operation generation from diffs

The snapshot is a JSON-serializable dict describing every model, field,
index, and constraint in the current codebase.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from .migration_dsl import (
    _SENTINEL,
    AddConstraint,
    AddField,
    AlterField,
    ColumnDef,
    CreateIndex,
    CreateModel,
    DropIndex,
    DropModel,
    Operation,
    RemoveConstraint,
    RemoveField,
    RenameField,
    RenameModel,
    _normalize_fk_action,
)

logger = logging.getLogger("aquilia.models.schema_snapshot")


# ── Snapshot Format ─────────────────────────────────────────────────────────


SNAPSHOT_VERSION = 1


def _compile_schema_expression(expr: Any, model_cls: type | None = None, dialect: str = "sqlite") -> str:
    """Render a query-expression object (``F``, ``Value``, ``Func``, ``CombinedExpression``, ``RawSQL``, or any ``Expression`` with ``as_sql``) as inline SQL text for use in a schema artifact (index/constraint DDL, snapshot diffing).

    Unlike normal query compilation, this produces a single self-contained
    SQL string with parameters inlined (quoted/escaped in place, via naive
    ``'`` doubling) rather than a ``(sql, params)`` pair -- appropriate for
    DDL contexts like ``CREATE INDEX ... (expression)`` where there's no
    query executor to bind parameters against. A bare string is treated as
    a field name if it matches one on *model_cls* (quoted as an
    identifier), otherwise returned as-is. Any other non-``Expression``
    value is stringified. Falls back to ``str(expr)`` if a generic
    expression's own ``as_sql()`` raises.
    """
    from aquilia.models.expression import CombinedExpression, Expression, F, Func, RawSQL, Value

    if isinstance(expr, str):
        if model_cls and hasattr(model_cls, "_fields") and expr in model_cls._fields:
            return f'"{expr}"'
        return expr

    if not isinstance(expr, Expression):
        return str(expr)

    if isinstance(expr, F):
        if "__" in expr.name:
            parts = expr.name.split("__")
            if len(parts) == 2:
                return f'"{parts[0]}"."{parts[1]}"'
        return f'"{expr.name}"'

    if isinstance(expr, Value):
        val = expr.value
        if val is None:
            return "NULL"
        if isinstance(val, str):
            if model_cls and hasattr(model_cls, "_fields") and val in model_cls._fields:
                return f'"{val}"'
            escaped = val.replace("'", "''")
            return f"'{escaped}'"
        return str(val)

    if isinstance(expr, Func):
        arg_sqls = [_compile_schema_expression(arg, model_cls, dialect) for arg in expr.args]
        return f"{expr.function}({', '.join(arg_sqls)})"

    if isinstance(expr, CombinedExpression):
        lhs = _compile_schema_expression(expr.lhs, model_cls, dialect)
        rhs = _compile_schema_expression(expr.rhs, model_cls, dialect)
        return f"({lhs} {expr.connector} {rhs})"

    if isinstance(expr, RawSQL):
        sql = expr.sql
        if expr.params:
            for param in expr.params:
                if isinstance(param, str):
                    escaped = param.replace("'", "''")
                    sql = sql.replace("?", f"'{escaped}'", 1)
                else:
                    sql = sql.replace("?", str(param), 1)
        return sql

    try:
        sql, params = expr.as_sql(dialect)
        if params:
            for p in params:
                if isinstance(p, str):
                    escaped = p.replace("'", "''")
                    sql = sql.replace("?", f"'{escaped}'", 1)
                else:
                    sql = sql.replace("?", str(p), 1)
        return sql
    except Exception:
        return str(expr)


def _make_serializable(val: Any, model_cls: type | None = None, dialect: str = "sqlite") -> Any:
    """Recursively walk *val* (list/dict/tuple/scalar), compiling any ``Expression`` found into inline SQL text via ``_compile_schema_expression`` so the result is JSON-serializable for storage in a snapshot file."""
    from aquilia.models.expression import Expression

    if isinstance(val, Expression):
        return _compile_schema_expression(val, model_cls, dialect)
    if isinstance(val, list):
        return [_make_serializable(item, model_cls, dialect) for item in val]
    if isinstance(val, dict):
        return {k: _make_serializable(v, model_cls, dialect) for k, v in val.items()}
    if isinstance(val, tuple):
        return tuple(_make_serializable(item, model_cls, dialect) for item in val)
    return val


def _resolve_db_column_name(model_cls: type | None, field_or_name: Any) -> str:
    """Resolve a model field name or expression to its underlying DB column name.

    Purpose:
        Maps model attribute names (e.g., 'user') to actual database column
        names (e.g., 'user_id') when generating indexes and constraints.

    Lifecycle:
        Invoked during snapshot creation (``create_snapshot()``) when inspecting
        indexes and constraints declared on a Model subclass.

    Execution Order:
        1. Check if field_or_name is a string matching an attribute in model_cls._fields.
        2. Extract column_name, db_column, or name attribute from the Field instance.
        3. Fall back to field_or_name verbatim if not an attribute or not a string.

    Parameters:
        model_cls (type | None): The Model class owning the field.
        field_or_name (Any): Attribute name string or expression object.

    Returns:
        str: Actual database column name string (e.g., 'user_id').

    Exceptions:
        None directly raised.

    Notes:
        Ensures foreign keys and custom column names are correctly mapped for DDL generation.

    Internal Behaviour:
        Inspects model_cls._fields descriptor dictionary for column_name overrides.

    Edge Cases:
        - Non-string expressions pass through to str().
        - Non-existent attribute names pass through unchanged.

    Examples:
        >>> _resolve_db_column_name(UserRoleModel, "user")
        'user_id'
    """
    if isinstance(field_or_name, str):
        if model_cls and hasattr(model_cls, "_fields") and field_or_name in model_cls._fields:
            fld = model_cls._fields[field_or_name]
            return (
                getattr(fld, "column_name", None)
                or getattr(fld, "db_column", None)
                or getattr(fld, "name", None)
                or field_or_name
            )
        return field_or_name
    return str(field_or_name)


def _resolve_target_table(to_ref: Any, model_classes: list | None = None) -> str:
    """Resolve a foreign key target reference to its actual database table name.

    Purpose:
        Prevents FK reference mismatches (e.g., referencing 'usersmodel' instead of 'users')
        by querying target model metadata or registry lookups.

    Lifecycle:
        Invoked during foreign key field serialization in ``_serialize_field()``.

    Execution Order:
        1. Check if to_ref is a Model class subclass -> return _meta.table_name.
        2. Match string reference against model_classes list by class name or table_name.
        3. Query ModelRegistry for matching class name.
        4. Apply PascalCase to snake_case table name fallback.

    Parameters:
        to_ref (Any): Target reference (Model subclass or string like 'UserModel').
        model_classes (list | None): List of Model classes passed to snapshot creation.

    Returns:
        str: Target database table name (e.g., 'users').

    Exceptions:
        None directly raised.

    Notes:
        Guarantees that foreign key references in DSL migration operations resolve
        to actual DB table names rather than un-pluralized class name stubs.

    Internal Behaviour:
        Inspects _meta.table_name on resolved Model subclasses.

    Edge Cases:
        - Model classes ending in 'Model' (e.g. UserModel) strip 'Model' suffix in fallback.

    Examples:
        >>> _resolve_target_table("UserModel", [UserModel])
        'users'
    """
    if isinstance(to_ref, type) and hasattr(to_ref, "_meta"):
        return getattr(to_ref._meta, "table_name", to_ref.__name__.lower())

    if isinstance(to_ref, str):
        target_name = to_ref.split(".")[-1]
        if model_classes:
            for m in model_classes:
                if m.__name__ == target_name:
                    return getattr(m._meta, "table_name", target_name.lower())
                if hasattr(m, "_meta") and getattr(m._meta, "table_name", None) == target_name:
                    return target_name
        try:
            from .registry import ModelRegistry

            reg_cls = ModelRegistry.get(target_name)
            if reg_cls and hasattr(reg_cls, "_meta"):
                return getattr(reg_cls._meta, "table_name", target_name.lower())
        except Exception:
            pass

        import re

        base_name = target_name[:-5] if target_name.endswith("Model") and len(target_name) > 5 else target_name
        snake = re.sub(r"(?<!^)(?=[A-Z])", "_", base_name).lower()
        if not snake.endswith("s"):
            snake = f"{snake}s"
        return snake

    return str(to_ref).lower()


def create_snapshot(model_classes: list) -> dict[str, Any]:
    """
    Create a schema snapshot from a list of Model subclasses.

    Returns a JSON-serializable dict with the full schema state.

    Format:
        {
            "version": 1,
            "checksum": "<sha256>",
            "models": {
                "User": {
                    "table": "users",
                    "fields": {
                        "id": {"type": "INTEGER", "primary_key": true, ...},
                        "email": {"type": "VARCHAR(255)", "unique": true, ...},
                    },
                    "indexes": [
                        {"name": "idx_users_email", "columns": ["email"], "unique": false},
                    ],
                    "meta": {
                        "ordering": ["-created_at"],
                        "abstract": false,
                        "managed": true,
                    }
                }
            }
        }
    """
    from .fields_module import Index as ModelIndex

    models_data: dict[str, Any] = {}

    for model_cls in model_classes:
        meta = model_cls._meta
        if meta.abstract:
            continue
        if not meta.managed:
            continue

        name = model_cls.__name__
        table = meta.table_name

        # Serialize fields
        fields_data: dict[str, Any] = {}
        for field_name, fld in model_cls._fields.items():
            fld_info = _serialize_field(fld, model_classes=model_classes)
            fields_data[field_name] = fld_info

        # Serialize indexes from Meta
        indexes_data: list[dict[str, Any]] = []
        for idx in getattr(meta, "indexes", []):
            raw_fields = []
            idx_name = None
            if hasattr(idx, "deconstruct"):
                idx_data = idx.deconstruct()
                raw_fields = idx_data.get("fields") or idx_data.get("columns", [])
                idx_name = idx_data.get("name")
            elif isinstance(idx, ModelIndex):
                raw_fields = idx.fields if hasattr(idx, "fields") else []
                idx_name = getattr(idx, "name", None)

            if isinstance(raw_fields, str):
                raw_fields = [raw_fields]
            elif isinstance(raw_fields, (tuple, set)):
                raw_fields = list(raw_fields)

            resolved_cols = []
            for f in raw_fields:
                from aquilia.models.expression import Expression

                if isinstance(f, Expression):
                    resolved_cols.append(_compile_schema_expression(f, model_cls))
                else:
                    resolved_cols.append(_resolve_db_column_name(model_cls, f))

            idx_name = idx_name or _auto_index_name(table, resolved_cols)
            indexes_data.append(
                {
                    "name": idx_name,
                    "columns": resolved_cols,
                    "unique": getattr(idx, "unique", False),
                }
            )

        # Add indexes from individual field db_index=True
        for field_name, fld in model_cls._fields.items():
            if getattr(fld, "db_index", False) and not getattr(fld, "primary_key", False):
                col_name = getattr(fld, "column_name", None) or getattr(fld, "db_column", None) or field_name
                idx_name = _auto_index_name(table, [col_name])
                # Avoid duplicates
                if not any(i["name"] == idx_name for i in indexes_data):
                    indexes_data.append(
                        {
                            "name": idx_name,
                            "columns": [col_name],
                            "unique": getattr(fld, "unique", False),
                        }
                    )

        # Serialize constraints from Meta
        constraints_data: list[dict[str, Any]] = []
        for constraint in getattr(meta, "constraints", []):
            if hasattr(constraint, "deconstruct"):
                c_data = constraint.deconstruct()
            else:
                c_data = {
                    "type": type(constraint).__name__,
                    "name": getattr(constraint, "name", None),
                }
            if c_data.get("type") == "UniqueConstraint" and "fields" in c_data:
                c_fields = c_data["fields"]
                if isinstance(c_fields, str):
                    c_fields = [c_fields]
                elif isinstance(c_fields, (tuple, set)):
                    c_fields = list(c_fields)
                c_data["fields"] = [_resolve_db_column_name(model_cls, f) for f in c_fields]
            constraints_data.append(_make_serializable(c_data, model_cls))

        meta_data = {
            "ordering": list(meta.ordering) if meta.ordering else [],
            "abstract": meta.abstract,
            "managed": meta.managed,
        }

        models_data[name] = {
            "table": table,
            "fields": fields_data,
            "indexes": indexes_data,
            "constraints": constraints_data,
            "meta": meta_data,
        }

    snapshot = {
        "version": SNAPSHOT_VERSION,
        "models": models_data,
    }
    snapshot["checksum"] = _compute_checksum(snapshot)
    return snapshot


def _table_to_class_name(table_name: str) -> str:
    """Convert a table name to a PascalCase class name."""
    parts = table_name.replace("-", "_").split("_")
    return "".join(part.capitalize() for part in parts if part)


async def create_snapshot_from_db(db, model_classes: list | None = None) -> dict[str, Any]:
    """
    Create a schema snapshot from an active database connection.

    Introspects the database metadata and maps it to a standard Aquilia
    schema snapshot.
    """
    tables = await db.get_tables()
    models_data = {}

    # Exclude internal tracking table
    tables = [t for t in tables if not t.startswith("sqlite_") and t != "aquilia_migrations"]

    table_to_class = {}
    if model_classes:
        for cls in model_classes:
            if hasattr(cls, "_meta") and hasattr(cls._meta, "table_name"):
                table_to_class[cls._meta.table_name] = cls.__name__

    for table in tables:
        columns = await db.get_columns(table)
        indexes_data = []

        try:
            indexes_raw = await db._adapter.get_indexes(table)
            for idx in indexes_raw:
                indexes_data.append(
                    {
                        "name": idx["name"],
                        "columns": idx.get("columns", []),
                        "unique": idx.get("unique", False),
                    }
                )
        except Exception:
            pass

        fields_data = {}
        pk_columns = set()
        unique_columns = set()

        if db.dialect == "sqlite":
            for col in columns:
                if col.primary_key:
                    pk_columns.add(col.name)
        elif db.dialect in ("postgresql", "mysql"):
            try:
                rows = await db.fetch_all(
                    """
                    SELECT tc.constraint_type, kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    WHERE tc.table_name = ?
                    """,
                    [table],
                )
                for r in rows:
                    c_type = r["constraint_type"]
                    col_name = r["column_name"]
                    if c_type == "PRIMARY KEY":
                        pk_columns.add(col_name)
                    elif c_type == "UNIQUE":
                        unique_columns.add(col_name)
            except Exception:
                pass

        # Check unique indexes for single columns
        for idx in indexes_data:
            if idx["unique"] and len(idx["columns"]) == 1:
                unique_columns.add(idx["columns"][0])

        for col in columns:
            is_pk = col.name in pk_columns
            is_unique = col.name in unique_columns

            field_class = "CharField"
            t_upper = col.data_type.upper()
            if "INT" in t_upper:
                if "BIGINT" in t_upper:
                    field_class = "BigIntegerField"
                else:
                    field_class = "IntegerField"
            elif "TEXT" in t_upper or "CLOB" in t_upper:
                field_class = "TextField"
            elif "REAL" in t_upper or "FLOAT" in t_upper or "DOUBLE" in t_upper:
                field_class = "FloatField"
            elif "DECIMAL" in t_upper or "NUMERIC" in t_upper:
                field_class = "DecimalField"
            elif "BOOL" in t_upper:
                field_class = "BooleanField"
            elif "BLOB" in t_upper:
                field_class = "BinaryField"
            elif "DATE" in t_upper:
                if "TIME" in t_upper:
                    field_class = "DateTimeField"
                else:
                    field_class = "DateField"
            elif "TIME" in t_upper:
                field_class = "TimeField"
            elif "TIMESTAMP" in t_upper:
                field_class = "DateTimeField"
            elif "JSON" in t_upper:
                field_class = "JSONField"

            field_info = {
                "field_class": field_class,
                "type": t_upper,
            }
            if col.nullable and not is_pk:
                field_info["nullable"] = True
            if is_pk:
                field_info["primary_key"] = True
            if is_unique and not is_pk:
                field_info["unique"] = True
            if col.default is not None:
                field_info["default"] = col.default

            # Extract max_length from type string if present
            import re

            m = re.search(r"\((\d+)\)", t_upper)
            if m and "DECIMAL" not in t_upper and "NUMERIC" not in t_upper:
                field_info["max_length"] = int(m.group(1))
            elif col.max_length:
                field_info["max_length"] = col.max_length

            fields_data[col.name] = field_info

        # Resolve foreign keys
        try:
            fks = await db._adapter.get_foreign_keys(table)
            for fk in fks:
                col_name = fk["from_column"]
                if col_name in fields_data:
                    ref_table = fk["to_table"]
                    ref_model = table_to_class.get(ref_table, _table_to_class_name(ref_table))
                    fields_data[col_name]["references"] = {
                        "model": ref_model,
                        "table": ref_table,
                        "column": fk["to_column"],
                    }
                    fields_data[col_name]["on_delete"] = fk.get("on_delete", "CASCADE")
                    fields_data[col_name]["on_update"] = fk.get("on_update", "CASCADE")
        except Exception:
            pass

        model_name = table_to_class.get(table, _table_to_class_name(table))
        models_data[model_name] = {
            "table": table,
            "fields": fields_data,
            "indexes": indexes_data,
            "meta": {
                "ordering": [],
                "abstract": False,
                "managed": True,
            },
        }

    snapshot = {
        "version": SNAPSHOT_VERSION,
        "models": models_data,
    }
    snapshot["checksum"] = _compute_checksum(snapshot)
    return snapshot


def _serialize_field(fld, model_classes: list | None = None) -> dict[str, Any]:
    """Serialize a single Field instance to a snapshot dict.

    Purpose:
        Transforms an ORM ``Field`` descriptor instance into a JSON-serializable
        dictionary for schema snapshot storage and diff comparison.

    Lifecycle:
        Invoked during schema snapshot creation (``create_snapshot()``) when
        inspecting registered model fields.

    Execution Order:
        1. Create dictionary with ``field_class`` name.
        2. Resolve SQL type via ``_field_to_sql_type()``.
        3. Extract boolean flags (``primary_key``, ``unique``, ``nullable``).
        4. Normalize default values (unwrapping Enum members/EnumField defaults).
        5. Extract field-specific options (``max_length``, FK references, decimal params).

    Parameters:
        fld (Field): The model field instance to serialize.
        model_classes (list | None): List of Model classes passed to snapshot creation.

    Returns:
        dict[str, Any]: JSON-serializable dictionary containing field metadata.

    Exceptions:
        None directly raised. Serialization errors fallback gracefully.

    Notes:
        Guarantees that Enum defaults (e.g. ``UserStatus.ACTIVE``) are unwrapped to
        primitive DB-storable scalars (string or int) rather than stringified enum reprs.

    Internal Behaviour:
        Calls ``fld.to_db(val)`` for ``EnumField`` or accesses ``val.value``/``val.name``
        for raw ``Enum`` member instances before verifying JSON safety via ``json.dumps``.

    Edge Cases:
        - Callable defaults are serialized as ``<callable:name>``.
        - Enum instances are unwrapped to underlying primitive values.
        - Unset or None defaults are preserved or omitted.

    Examples:
        >>> field = EnumField(enum_class=UserStatus, default=UserStatus.ACTIVE)
        >>> _serialize_field(field)["default"]
        'active'
    """
    from enum import Enum

    from .fields.enum_field import EnumField
    from .fields_module import (
        UNSET,
        ForeignKey,
        OneToOneField,
    )

    info: dict[str, Any] = {
        "field_class": type(fld).__name__,
    }

    # SQL type
    sql_type = _field_to_sql_type(fld, model_classes=model_classes)
    info["type"] = sql_type

    # Constraints
    if getattr(fld, "primary_key", False):
        info["primary_key"] = True
    if getattr(fld, "unique", False):
        info["unique"] = True
    if getattr(fld, "null", False):
        info["nullable"] = True
    if hasattr(fld, "default") and fld.default is not None:
        if fld.default is not UNSET:
            val = fld.default
            if isinstance(fld, EnumField):
                val = fld.to_db(val)
            elif isinstance(val, Enum):
                val = val.name if getattr(fld, "store_name", False) else val.value

            if isinstance(val, Enum):
                val = val.name if getattr(fld, "store_name", False) else val.value

            try:
                # Only serialize JSON-safe defaults
                json.dumps(val)
                info["default"] = val
            except (TypeError, ValueError):
                if callable(val):
                    info["default"] = f"<callable:{val.__name__}>"
                elif isinstance(val, Enum):
                    info["default"] = val.value
                else:
                    info["default"] = str(val)

    # Max length
    if hasattr(fld, "max_length") and fld.max_length:
        info["max_length"] = fld.max_length

    # FK reference
    if isinstance(fld, (ForeignKey, OneToOneField)):
        ref_table = _resolve_target_table(fld.to, model_classes)
        to_name = fld.to if isinstance(fld.to, str) else getattr(fld.to, "__name__", str(fld.to))
        target_col = "id"
        related = getattr(fld, "related_model", None)
        if related is None and fld.to is not None:
            if isinstance(fld.to, type):
                related = fld.to
            elif isinstance(fld.to, str) and model_classes:
                target_cls_name = fld.to.split(".")[-1]
                for m in model_classes:
                    if m.__name__ == target_cls_name:
                        related = m
                        break
        if related is not None and hasattr(related, "_fields") and hasattr(related, "_pk_attr"):
            pk_attr = getattr(related, "_pk_attr", "id")
            pk_fld = related._fields.get(pk_attr)
            if pk_fld is not None:
                target_col = getattr(pk_fld, "column_name", None) or getattr(pk_fld, "name", None) or "id"

        info["references"] = {"model": to_name, "table": ref_table, "column": target_col}
        info["on_delete"] = getattr(fld, "on_delete", "CASCADE")
        info["on_update"] = getattr(fld, "on_update", "CASCADE")

    # Decimal params
    if hasattr(fld, "max_digits") and fld.max_digits:
        info["max_digits"] = fld.max_digits
    if hasattr(fld, "decimal_places") and fld.decimal_places is not None:
        info["decimal_places"] = fld.decimal_places

    # Column name override
    col = getattr(fld, "column_name", None) or getattr(fld, "name", None)
    if col:
        info["column"] = col

    return info


def _field_to_sql_type(fld, model_classes: list | None = None) -> str:
    """Map a Field instance to its SQL type string.

    Purpose:
        Determines the canonical SQL data type representation for an ORM field.

    Lifecycle:
        Invoked during model field snapshotting in ``_serialize_field()``.

    Execution Order:
        1. Check if field is ForeignKey / OneToOneField (resolve related PK type).
        2. Check if field is EnumField or implements ``sql_type()``.
        3. Match field class against built-in type_map.
        4. Match character fields with max_length.
        5. Fallback to "TEXT".

    Parameters:
        fld (Field): The field instance whose SQL type is being resolved.
        model_classes (list | None): List of Model classes passed to snapshot creation.

    Returns:
        str: SQL column type (e.g., "VARCHAR(50)", "INTEGER", "TEXT", "TIMESTAMP").

    Exceptions:
        None directly raised.

    Notes:
        Correctly delegates to ``EnumField.sql_type()`` for enum fields.

    Internal Behaviour:
        Invokes ``fld.sql_type()`` if available, falling back to class hierarchy checks.

    Edge Cases:
        - Unbound foreign keys fall back to "INTEGER".
        - Custom user fields with ``sql_type()`` are supported automatically.

    Examples:
        >>> field = EnumField(enum_class=UserStatus, max_length=50)
        >>> _field_to_sql_type(field)
        'VARCHAR(50)'
    """
    from .fields.enum_field import EnumField
    from .fields_module import (
        AutoField,
        BigAutoField,
        BigIntegerField,
        BinaryField,
        BooleanField,
        CharField,
        DateField,
        DateTimeField,
        DecimalField,
        DurationField,
        EmailField,
        FileField,
        FloatField,
        ForeignKey,
        ImageField,
        IntegerField,
        JSONField,
        OneToOneField,
        SlugField,
        SmallIntegerField,
        TextField,
        TimeField,
        URLField,
        UUIDField,
    )

    if isinstance(fld, (ForeignKey, OneToOneField)):
        related = getattr(fld, "related_model", None)
        if related is None and fld.to is not None:
            if isinstance(fld.to, type):
                related = fld.to
            elif isinstance(fld.to, str):
                target_name = fld.to.split(".")[-1]
                if model_classes:
                    for m in model_classes:
                        if m.__name__ == target_name:
                            related = m
                            break
                if related is None:
                    try:
                        from .registry import ModelRegistry

                        related = ModelRegistry.get(target_name)
                    except Exception:
                        pass
        if related is not None and hasattr(related, "_fields") and hasattr(related, "_pk_attr"):
            pk_field = related._fields.get(related._pk_attr)
            if pk_field is not None:
                return _field_to_sql_type(pk_field, model_classes=model_classes)
        return "INTEGER"

    if isinstance(fld, EnumField):
        return fld.sql_type()

    if hasattr(fld, "sql_type") and callable(fld.sql_type):
        try:
            return fld.sql_type()
        except Exception:
            pass

    type_map = {
        AutoField: "INTEGER",
        BigAutoField: "INTEGER",
        IntegerField: "INTEGER",
        BigIntegerField: "INTEGER",
        SmallIntegerField: "INTEGER",
        FloatField: "REAL",
        BooleanField: "BOOLEAN",
        BinaryField: "BLOB",
        JSONField: "TEXT",
        DateField: "DATE",
        TimeField: "TIME",
        DateTimeField: "TIMESTAMP",
        DurationField: "INTEGER",
        UUIDField: "VARCHAR(36)",
    }

    for cls, sql_type in type_map.items():
        if isinstance(fld, cls):
            return sql_type

    if isinstance(fld, (CharField, SlugField, EmailField, URLField, FileField, ImageField)):
        ml = getattr(fld, "max_length", 255) or 255
        return f"VARCHAR({ml})"

    if isinstance(fld, TextField):
        return "TEXT"

    if isinstance(fld, DecimalField):
        md = getattr(fld, "max_digits", 10) or 10
        dp = getattr(fld, "decimal_places", 2) or 2
        return f"DECIMAL({md},{dp})"

    return "TEXT"


def _auto_index_name(table: str, columns: list[str]) -> str:
    """Generate a deterministic index name."""
    cols = "_".join(columns)
    return f"idx_{table}_{cols}"


def _compute_checksum(snapshot: dict[str, Any]) -> str:
    """Compute a stable checksum of the snapshot (excluding checksum field)."""
    data = {k: v for k, v in snapshot.items() if k != "checksum"}
    raw = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def save_snapshot(snapshot: dict[str, Any], path: Path) -> None:
    """Write snapshot to file atomically via ArtifactStore backend (JSONFileBackend)."""
    from aquilia.artifacts.backends.json_file import JSONFileBackend
    from aquilia.artifacts.canonical import bare_fingerprint
    from aquilia.artifacts.envelope import ArtifactEnvelope

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fp = bare_fingerprint(snapshot, exclude_keys=frozenset({"checksum"}))
    envelope = ArtifactEnvelope.build(
        artifact_type="schema_snapshot", key="main", schema_version="1.0", payload=snapshot, fingerprint=fp
    )
    JSONFileBackend().write_sync(path, envelope.to_dict())


def load_snapshot(path: Path) -> dict[str, Any] | None:
    """Load and verify snapshot from file."""
    from aquilia.artifacts.backends.json_file import JSONFileBackend
    from aquilia.artifacts.envelope import ArtifactEnvelope

    path = Path(path)
    if not path.exists():
        return None
    try:
        raw = JSONFileBackend().read_sync(path)
        if raw is None:
            return None

        if isinstance(raw, dict) and raw.get("format") == "aquilia-artifact":
            envelope = ArtifactEnvelope.from_dict(raw)
            data = envelope.payload
        else:
            data = raw

        if not isinstance(data, dict):
            return None

        # Verify checksum on load (fixes write-but-never-verify pattern, §5.2)
        stored_checksum = data.get("checksum")
        if stored_checksum:
            expected = _compute_checksum(data)
            if expected != stored_checksum:
                logger.warning(
                    "Schema snapshot at %s has checksum mismatch "
                    "(stored=%r, computed=%r). "
                    "The file may be corrupt; proceeding with caution.",
                    path,
                    stored_checksum,
                    expected,
                )
        return data
    except (OSError, Exception) as exc:
        logger.warning("Failed to load snapshot %s: %s", path, exc)
        return None


# ── Schema Diff Engine ──────────────────────────────────────────────────────

# Rename detection threshold: similarity ratio above this triggers rename
RENAME_THRESHOLD = 0.6


@dataclass
class SchemaDiff:
    """Result of comparing two snapshots."""

    added_models: list[str] = field(default_factory=list)
    removed_models: list[str] = field(default_factory=list)
    renamed_models: list[tuple[str, str]] = field(default_factory=list)  # (old, new)
    altered_models: dict[str, ModelDiff] = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        """True if any model was added, removed, renamed, or altered between the two snapshots compared."""
        return bool(self.added_models or self.removed_models or self.renamed_models or self.altered_models)


@dataclass
class ModelDiff:
    """Changes within a single model."""

    added_fields: list[str] = field(default_factory=list)
    removed_fields: list[str] = field(default_factory=list)
    renamed_fields: list[tuple[str, str]] = field(default_factory=list)
    altered_fields: list[str] = field(default_factory=list)  # fields with changed type/constraints
    added_indexes: list[dict[str, Any]] = field(default_factory=list)
    removed_indexes: list[dict[str, Any]] = field(default_factory=list)
    added_constraints: list[dict[str, Any]] = field(default_factory=list)
    removed_constraints: list[dict[str, Any]] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        """True if this model has any added/removed/renamed/altered field, index, or constraint."""
        return bool(
            self.added_fields
            or self.removed_fields
            or self.renamed_fields
            or self.altered_fields
            or self.added_indexes
            or self.removed_indexes
            or self.added_constraints
            or self.removed_constraints
        )


def compute_diff(old_snapshot: dict[str, Any], new_snapshot: dict[str, Any]) -> SchemaDiff:
    """
    Compute the diff between two schema snapshots.

    Includes heuristics for detecting renames (models and fields)
    to avoid data-loss migrations.
    """
    old_models = old_snapshot.get("models", {})
    new_models = new_snapshot.get("models", {})

    old_names = set(old_models.keys())
    new_names = set(new_models.keys())

    diff = SchemaDiff()

    # Detect renames vs add/remove
    purely_added = new_names - old_names
    purely_removed = old_names - new_names

    renamed_pairs: list[tuple[str, str]] = []
    if purely_added and purely_removed:
        renamed_pairs = _detect_model_renames(old_models, new_models, purely_removed, purely_added)
        for old_name, new_name in renamed_pairs:
            purely_removed.discard(old_name)
            purely_added.discard(new_name)

    diff.added_models = sorted(purely_added)
    diff.removed_models = sorted(purely_removed)
    diff.renamed_models = renamed_pairs

    # Diff models that exist in both snapshots (including renamed)
    common_pairs: list[tuple[str, str]] = []
    for name in old_names & new_names:
        common_pairs.append((name, name))
    for old_name, new_name in renamed_pairs:
        common_pairs.append((old_name, new_name))

    for old_name, new_name in common_pairs:
        model_diff = _diff_model(old_models[old_name], new_models[new_name])
        if model_diff.has_changes:
            diff.altered_models[new_name] = model_diff

    return diff


def _detect_model_renames(
    old_models: dict,
    new_models: dict,
    removed: set[str],
    added: set[str],
) -> list[tuple[str, str]]:
    """
    Detect likely model renames using table-name and field-structure similarity.

    Heuristics:
    1. Same table name → definite rename
    2. High field-structure similarity → probable rename
    """
    pairs: list[tuple[str, str]] = []
    used_old: set[str] = set()
    used_new: set[str] = set()

    # Pass 1: exact table name match
    for old_name in list(removed):
        old_table = old_models[old_name].get("table", "")
        for new_name in list(added):
            new_table = new_models[new_name].get("table", "")
            if old_table and old_table == new_table:
                pairs.append((old_name, new_name))
                used_old.add(old_name)
                used_new.add(new_name)
                break

    # Pass 2: field similarity
    remaining_old = removed - used_old
    remaining_new = added - used_new
    if remaining_old and remaining_new:
        for old_name in list(remaining_old):
            old_fields = set(old_models[old_name].get("fields", {}).keys())
            best_match = None
            best_score = 0.0

            for new_name in remaining_new:
                new_fields = set(new_models[new_name].get("fields", {}).keys())
                if not old_fields and not new_fields:
                    continue
                # Jaccard similarity
                intersection = old_fields & new_fields
                union = old_fields | new_fields
                score = len(intersection) / len(union) if union else 0
                if score > best_score:
                    best_score = score
                    best_match = new_name

            if best_match and best_score >= RENAME_THRESHOLD:
                pairs.append((old_name, best_match))
                remaining_new.discard(best_match)

    return pairs


def _diff_model(old_model: dict, new_model: dict) -> ModelDiff:
    """Diff two model snapshots."""
    diff = ModelDiff()

    old_fields = old_model.get("fields", {})
    new_fields = new_model.get("fields", {})

    old_field_names = set(old_fields.keys())
    new_field_names = set(new_fields.keys())

    # Detect field renames
    added_fields = new_field_names - old_field_names
    removed_fields = old_field_names - new_field_names

    renamed_pairs: list[tuple[str, str]] = []
    if added_fields and removed_fields:
        renamed_pairs = _detect_field_renames(old_fields, new_fields, removed_fields, added_fields)
        for old_name, new_name in renamed_pairs:
            removed_fields.discard(old_name)
            added_fields.discard(new_name)

    diff.added_fields = sorted(added_fields)
    diff.removed_fields = sorted(removed_fields)
    diff.renamed_fields = renamed_pairs

    # Detect altered fields (common fields with changed properties)
    common = old_field_names & new_field_names
    for name in sorted(common):
        if _field_changed(old_fields[name], new_fields[name]):
            diff.altered_fields.append(name)

    # Diff indexes
    old_indexes = {i["name"]: i for i in old_model.get("indexes", [])}
    new_indexes = {i["name"]: i for i in new_model.get("indexes", [])}

    for name in sorted(set(new_indexes) - set(old_indexes)):
        diff.added_indexes.append(new_indexes[name])
    for name in sorted(set(old_indexes) - set(new_indexes)):
        diff.removed_indexes.append(old_indexes[name])

    # Diff constraints
    old_constraints = {c["name"]: c for c in old_model.get("constraints", []) if c.get("name")}
    new_constraints = {c["name"]: c for c in new_model.get("constraints", []) if c.get("name")}

    for name in sorted(set(new_constraints) - set(old_constraints)):
        diff.added_constraints.append(new_constraints[name])
    for name in sorted(set(old_constraints) - set(new_constraints)):
        diff.removed_constraints.append(old_constraints[name])

    return diff


def _detect_field_renames(
    old_fields: dict,
    new_fields: dict,
    removed: set[str],
    added: set[str],
) -> list[tuple[str, str]]:
    """Detect field renames using type similarity."""
    pairs: list[tuple[str, str]] = []
    used_new: set[str] = set()

    for old_name in list(removed):
        old_type = old_fields[old_name].get("type", "")
        best_match = None
        best_score = 0.0

        for new_name in added - used_new:
            new_type = new_fields[new_name].get("type", "")
            # Same type is a strong signal
            score = 1.0 if old_type == new_type else 0.0
            # Name similarity adds signal
            name_sim = SequenceMatcher(None, old_name, new_name).ratio()
            score = (score * 0.7) + (name_sim * 0.3)

            if score > best_score:
                best_score = score
                best_match = new_name

        if best_match and best_score >= RENAME_THRESHOLD:
            pairs.append((old_name, best_match))
            used_new.add(best_match)

    return pairs


def _field_changed(old_field: dict, new_field: dict) -> bool:
    """Check if a field's schema-relevant properties changed."""
    keys = ("type", "primary_key", "unique", "nullable", "default", "max_length", "references")
    return any(old_field.get(k) != new_field.get(k) for k in keys)


def _topologically_sort_models(
    added_models: list[str],
    models_data: dict[str, Any],
) -> list[str]:
    """Topologically sort added model names so referenced tables are created before tables with FKs referencing them.

    Purpose:
        Prevents foreign key creation failures during migration execution by ordering
        CreateModel operations dependency-first.

    Lifecycle:
        Invoked inside diff_to_operations() when generating CreateModel operations.

    Execution Order:
        1. Map table_name -> model_name for all added models.
        2. Construct dependency graph by scanning fields' 'references' metadata.
        3. Run post-order depth-first traversal to compute valid topological order.
        4. Detect and break self-referential / cyclic dependencies gracefully.

    Parameters:
        added_models (list[str]): List of added model names.
        models_data (dict[str, Any]): Dictionary of model schema metadata from snapshot.

    Returns:
        list[str]: Model names sorted in topological dependency order.

    Exceptions:
        None directly raised.

    Notes:
        Guarantees that tables referenced by foreign keys exist before dependent tables are created.

    Internal Behaviour:
        Builds an in-degree / adjacency graph of table references and applies post-order DFS.

    Edge Cases:
        - Self-referential models (Model A -> Model A) ignore self-loops.
        - Circular dependencies (Model A -> Model B -> Model A) fall back gracefully without recursion error.

    Examples:
        >>> _topologically_sort_models(['UserEmailVerificationModel', 'UserModel'], models_data)
        ['UserModel', 'UserEmailVerificationModel']
    """
    if len(added_models) <= 1:
        return added_models

    table_to_model = {}
    for m_name in added_models:
        m_info = models_data.get(m_name, {})
        t_name = m_info.get("table", m_name.lower())
        table_to_model[t_name] = m_name

    deps: dict[str, set[str]] = {m: set() for m in added_models}
    for m_name in added_models:
        m_info = models_data.get(m_name, {})
        fields = m_info.get("fields", {})
        for f_info in fields.values():
            ref = f_info.get("references")
            if ref and isinstance(ref, dict):
                ref_table = ref.get("table")
                if ref_table and ref_table in table_to_model:
                    target_m = table_to_model[ref_table]
                    if target_m != m_name:
                        deps[m_name].add(target_m)

    sorted_models: list[str] = []
    visited: set[str] = set()
    visiting: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            return
        if node not in visited:
            visiting.add(node)
            for dep in sorted(deps[node]):
                visit(dep)
            visiting.remove(node)
            visited.add(node)
            sorted_models.append(node)

    for m_name in sorted(added_models):
        if m_name not in visited:
            visit(m_name)

    return sorted_models


# ── Generate Operations from Diff ───────────────────────────────────────────


def diff_to_operations(
    diff: SchemaDiff,
    old_snapshot: dict[str, Any],
    new_snapshot: dict[str, Any],
) -> list[Operation]:
    """
    Convert a SchemaDiff into a list of DSL operations.

    This is the core of makemigrations -- it takes the delta between
    the previous snapshot and the current models, then emits the
    minimal set of operations to bring the schema up to date.
    """
    ops: list[Operation] = []
    new_models = new_snapshot.get("models", {})
    old_models = old_snapshot.get("models", {})

    # 1. Renamed models
    for old_name, new_name in diff.renamed_models:
        old_table = old_models[old_name]["table"]
        new_table = new_models[new_name]["table"]
        if old_table != new_table:
            ops.append(
                RenameModel(
                    old_name=old_name,
                    new_name=new_name,
                    old_table=old_table,
                    new_table=new_table,
                )
            )

    # 2. Removed models
    for name in diff.removed_models:
        table = old_models[name]["table"]
        ops.append(DropModel(name=name, table=table))

    # 3. Added models (topologically sorted to respect foreign key dependencies)
    sorted_added_models = _topologically_sort_models(diff.added_models, new_models)
    for name in sorted_added_models:
        model_data = new_models[name]
        fields = _snapshot_fields_to_column_defs(model_data["fields"])
        ops.append(CreateModel(name=name, table=model_data["table"], fields=fields))

        # Add indexes for new models
        for idx in model_data.get("indexes", []):
            ops.append(
                CreateIndex(
                    name=idx["name"],
                    table=model_data["table"],
                    columns=idx["columns"],
                    unique=idx.get("unique", False),
                )
            )

        # Add constraints for new models
        for c in model_data.get("constraints", []):
            c_type = c.get("type")
            c_name = c.get("name")
            if c_type == "CheckConstraint":
                sql = f'CONSTRAINT "{c_name}" CHECK ({c.get("check")})'
            elif c_type == "UniqueConstraint":
                fields_sql = ", ".join(f'"{f}"' if not ("(" in f or '"' in f) else f for f in c.get("fields", []))
                sql = f'CONSTRAINT "{c_name}" UNIQUE ({fields_sql})' if c_name else f"UNIQUE ({fields_sql})"
            elif c_type == "ExclusionConstraint":
                exprs = ", ".join(f'"{col}" WITH {op}' for col, op in c.get("expressions", []))
                sql = f'CONSTRAINT "{c_name}" EXCLUDE USING {c.get("index_type", "GIST")} ({exprs})'
                if c.get("condition"):
                    sql += f" WHERE ({c.get('condition')})"
            else:
                continue
            ops.append(AddConstraint(table=model_data["table"], constraint_sql=sql))

    # 4. Altered models
    for model_name, model_diff in diff.altered_models.items():
        model_data = new_models[model_name]
        table = model_data["table"]

        # Renamed fields
        for old_fname, new_fname in model_diff.renamed_fields:
            ops.append(
                RenameField(
                    model_name=model_name,
                    table=table,
                    old_name=old_fname,
                    new_name=new_fname,
                )
            )

        # Removed fields
        for fname in model_diff.removed_fields:
            ops.append(RemoveField(model_name=model_name, table=table, column_name=fname))

        # Added fields
        for fname in model_diff.added_fields:
            fld_data = model_data["fields"][fname]
            col = _snapshot_field_to_column_def(fname, fld_data)
            ops.append(AddField(model_name=model_name, table=table, column=col))

        # Altered fields
        for fname in model_diff.altered_fields:
            fld_data = model_data["fields"][fname]
            ops.append(
                AlterField(
                    model_name=model_name,
                    table=table,
                    column_name=getattr(fld_data, "get", lambda k, d=None: d)("column", fname),
                    new_type=fld_data.get("type"),
                )
            )

        # Added indexes
        for idx in model_diff.added_indexes:
            ops.append(
                CreateIndex(
                    name=idx["name"],
                    table=table,
                    columns=idx["columns"],
                    unique=idx.get("unique", False),
                )
            )

        # Removed indexes
        for idx in model_diff.removed_indexes:
            ops.append(DropIndex(name=idx["name"], table=table))

        # Added constraints
        for c in model_diff.added_constraints:
            c_type = c.get("type")
            c_name = c.get("name")
            if c_type == "CheckConstraint":
                sql = f'CONSTRAINT "{c_name}" CHECK ({c.get("check")})'
            elif c_type == "UniqueConstraint":
                fields_sql = ", ".join(f'"{f}"' if not ("(" in f or '"' in f) else f for f in c.get("fields", []))
                sql = f'CONSTRAINT "{c_name}" UNIQUE ({fields_sql})' if c_name else f"UNIQUE ({fields_sql})"
            elif c_type == "ExclusionConstraint":
                exprs = ", ".join(f'"{col}" WITH {op}' for col, op in c.get("expressions", []))
                sql = f'CONSTRAINT "{c_name}" EXCLUDE USING {c.get("index_type", "GIST")} ({exprs})'
                if c.get("condition"):
                    sql += f" WHERE ({c.get('condition')})"
            else:
                continue
            ops.append(AddConstraint(table=table, constraint_sql=sql))

        # Removed constraints
        for c in model_diff.removed_constraints:
            if c.get("name"):
                ops.append(RemoveConstraint(table=table, name=c["name"]))

    return ops


def _snapshot_fields_to_column_defs(fields_data: dict[str, Any]) -> list[ColumnDef]:
    """Convert snapshot field dicts to ColumnDef objects."""
    defs: list[ColumnDef] = []
    for name, data in fields_data.items():
        defs.append(_snapshot_field_to_column_def(name, data))
    return defs


def _snapshot_field_to_column_def(name: str, data: dict[str, Any]) -> ColumnDef:
    """Convert a single snapshot field dict to a ColumnDef."""
    col_name = data.get("column", name)
    col_type = data.get("type", "TEXT")

    ref = data.get("references")
    references = None
    on_delete = "CASCADE"
    on_update = "CASCADE"
    if ref and isinstance(ref, dict):
        # Accept both {"table": "..."} and {"model": "..."} — the serializer
        # now always writes both keys, but legacy snapshots may have only "model".
        ref_table = ref.get("table")
        if not ref_table and "model" in ref:
            ref_table = ref["model"].lower()
        if ref_table:
            references = (ref_table, ref.get("column", "id"))
            on_delete = _normalize_fk_action(data.get("on_delete", "CASCADE"))
            on_update = _normalize_fk_action(data.get("on_update", "CASCADE"))

    default = data.get("default", _SENTINEL)
    if default is not _SENTINEL and default is not None:
        from enum import Enum
        if isinstance(default, Enum):
            default = default.value
        elif isinstance(default, str) and default.startswith("<callable:"):
            default = _SENTINEL  # Can't serialize callables

    return ColumnDef(
        name=col_name,
        col_type=col_type,
        primary_key=data.get("primary_key", False),
        autoincrement=data.get("primary_key", False) and "INT" in col_type.upper(),
        unique=data.get("unique", False),
        nullable=data.get("nullable", False),
        default=default,
        references=references,
        on_delete=on_delete,
        on_update=on_update,
    )

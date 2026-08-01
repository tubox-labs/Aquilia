"""
Aquilia migrations -- Python source generation.

Renders operations as *real Python objects*: a generated migration names the
same :class:`~aquilia.models.fields_module.Field`, index, and constraint classes
a developer writes in a model, and reads as ordinary code.

Why not a serialized dict
-------------------------
The obvious way to write an operation to disk is to serialize it::

    operations = [
        Operation.from_dict({
            "operation": "CreateModel",
            "model": "Post",
            "table": {"columns": [{"field_class": "CharField", ...}], ...},
        }),
    ]

That round-trips exactly, and it is unreadable. It defeats every tool a Python
developer has: no editor completes a dict key, no type checker catches a
misspelled one, and a reviewer cannot see at a glance whether a column is
nullable. A migration is a permanent, reviewable artifact -- often the only
record of *why* a schema looks the way it does -- so it should be written in the
same vocabulary as the models it came from::

    operations = [
        CreateModel(
            model="Post",
            table=TableState.of(
                "Post",
                "posts",
                columns=[
                    ColumnState.of("id", fields.AutoField(primary_key=True)),
                    ColumnState.of("title", fields.CharField(max_length=200)),
                ],
            ),
        ),
    ]

Exactness is not sacrificed for readability. Both forms are built from the same
:class:`~aquilia.models.migration.schema.ColumnState`; the difference is that
this one reaches it by calling the field's own constructor. The round-trip test
is the same either way: reading back a generated file must produce operations
equal to the ones written.

Determinism
-----------
Every mapping is emitted in sorted key order, every default-valued argument is
omitted, and no clock or hostname enters the rendered body. Regenerating from
unchanged models produces a byte-identical file, which is what makes "no
changes detected" mean something.
"""

from __future__ import annotations

import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any

from aquilia.faults.domains import MigrationFault
from aquilia.models.migration.schema import (
    NOT_PROVIDED,
    CheckConstraintState,
    ColumnState,
    ConstraintState,
    ExclusionConstraintState,
    ForeignKeyConstraintState,
    IndexState,
    ManyToManyState,
    NotProvided,
    PrimaryKeyConstraintState,
    Reference,
    TableState,
    UniqueConstraintState,
)

if TYPE_CHECKING:
    from aquilia.models.migration.operations import Operation

__all__ = [
    "render_value",
    "render_column",
    "render_table",
    "render_operation",
    "render_operations",
    "collect_imports",
]

_INDENT = "    "
_WRAP = 96


# ── Primitive values ────────────────────────────────────────────────────────


def render_value(value: Any, *, indent: int = 0) -> str:
    """Render a Python value as deterministic, re-parsable source text.

    Args:
        value: The value to render.
        indent: Current indentation depth, in levels of four spaces.

    Returns:
        Source text that evaluates back to an equal value.

    Raises:
        MigrationFault: If *value* has no deterministic source representation.
            Falling back to ``repr()`` would emit ``<object at 0x7f...>`` for an
            arbitrary object -- source that neither parses nor is stable between
            runs.

    Example:
        >>> render_value({"b": 1, "a": 2})
        '{"a": 2, "b": 1}'
    """
    if isinstance(value, NotProvided):
        return "NOT_PROVIDED"
    if value is None or isinstance(value, bool):
        return repr(value)
    if isinstance(value, Enum):
        return render_value(value.value, indent=indent)
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, Decimal):
        return f'Decimal("{value}")'
    if isinstance(value, str):
        return render_string(value)
    if isinstance(value, bytes):
        return repr(value)
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return f"datetime.{type(value).__name__}.fromisoformat({render_string(value.isoformat())})"
    if isinstance(value, (list, tuple)):
        return _render_sequence(list(value), indent=indent)
    if isinstance(value, (set, frozenset)):
        return _render_sequence(sorted(value, key=repr), indent=indent)
    if isinstance(value, dict):
        return _render_mapping(value, indent=indent)

    raise MigrationFault(
        migration="codegen",
        reason=(
            f"Cannot render {type(value).__name__} value {value!r} into a migration "
            f"file. Migration data must be representable as source: str, int, float, "
            f"bool, None, Decimal, bytes, date/time, Enum, or a list/dict of those."
        ),
    )


def render_string(value: str) -> str:
    """Render a string with a stable quote choice, preferring double quotes."""
    if '"' in value and "'" not in value:
        return f"'{value}'"
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    escaped = escaped.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    return f'"{escaped}"'


def _render_sequence(items: list[Any], *, indent: int) -> str:
    """Render a list, breaking across lines when a single line would be long."""
    if not items:
        return "[]"
    parts = [render_value(item, indent=indent + 1) for item in items]
    return _join(parts, "[", "]", indent=indent)


def _render_mapping(value: dict[Any, Any], *, indent: int) -> str:
    """Render a dict with keys in sorted order, breaking lines when long."""
    if not value:
        return "{}"
    parts = [f"{render_string(str(key))}: {render_value(value[key], indent=indent + 1)}" for key in sorted(value)]
    return _join(parts, "{", "}", indent=indent)


def _join(parts: list[str], open_char: str, close_char: str, *, indent: int) -> str:
    """Join rendered parts on one line, or one-per-line when too long."""
    single = open_char + ", ".join(parts) + close_char
    if len(single) + indent * 4 <= _WRAP and "\n" not in single:
        return single
    pad = _INDENT * (indent + 1)
    closing = _INDENT * indent
    body = ",\n".join(f"{pad}{part}" for part in parts)
    return f"{open_char}\n{body},\n{closing}{close_char}"


def _call(name: str, args: list[str], *, indent: int) -> str:
    """Render a constructor call, wrapping arguments when the line would be long."""
    if not args:
        return f"{name}()"
    single = f"{name}(" + ", ".join(args) + ")"
    if len(single) + indent * 4 <= _WRAP and "\n" not in single:
        return single
    pad = _INDENT * (indent + 1)
    closing = _INDENT * indent
    body = ",\n".join(f"{pad}{arg}" for arg in args)
    return f"{name}(\n{body},\n{closing})"


# ── Fields ──────────────────────────────────────────────────────────────────

# Keys that ColumnState promotes out of field_kwargs into its own attributes.
# They are passed to the field constructor from those attributes instead, so
# emitting them from field_kwargs too would duplicate the argument.
_PROMOTED = frozenset({"type", "primary_key", "unique", "null", "db_index", "db_column", "default"})

# Arguments a field constructor takes positionally rather than by keyword.
_POSITIONAL: dict[str, tuple[str, ...]] = {
    "ForeignKey": ("to",),
    "OneToOneField": ("to",),
    "ManyToManyField": ("to",),
}


def render_field(column: ColumnState, *, indent: int = 0) -> str:
    """Render the field constructor call that produced *column*.

    Emits only arguments that differ from the field's own defaults, so a plain
    column renders as ``fields.TextField()`` rather than a line of redundant
    ``null=False, unique=False, primary_key=False`` noise.

    Args:
        column: The column whose field to render.
        indent: Current indentation depth.

    Returns:
        Source text such as ``fields.CharField(max_length=200, db_index=True)``.

    Raises:
        MigrationFault: If a field argument cannot be rendered as source.

    Example:
        >>> render_field(ColumnState.of("title", CharField(max_length=200)))
        'fields.CharField(max_length=200)'
    """
    args: list[str] = []

    for name in _POSITIONAL.get(column.field_class, ()):
        if name == "to" and column.reference is not None:
            args.append(render_string(column.reference.model))
        elif name in column.field_kwargs:
            args.append(render_value(column.field_kwargs[name], indent=indent + 1))

    skip = _PROMOTED | set(_POSITIONAL.get(column.field_class, ()))
    for key in sorted(column.field_kwargs):
        if key in skip:
            continue
        value = column.field_kwargs[key]
        if key == "output_field" and isinstance(value, dict):
            args.append(f"output_field={_render_nested_field(value, indent=indent + 1)}")
            continue
        # deconstruct() emits related_name=None for relation fields that never
        # set one; it has no schema meaning and only adds noise.
        if key == "related_name" and value is None:
            continue
        args.append(f"{key}={render_value(value, indent=indent + 1)}")

    # Defaults live on ColumnState, but the field must be constructed with them
    # so a rebuilt field reports the same SQL column definition.
    if column.primary_key and not _defaults_primary_key(column.field_class):
        args.append("primary_key=True")
    if column.unique:
        args.append("unique=True")
    if column.null:
        args.append("null=True")
    if column.db_index:
        args.append("db_index=True")
    if column.default is not NOT_PROVIDED:
        args.append(f"default={render_value(column.default, indent=indent + 1)}")

    if column.reference is not None:
        if column.reference.on_delete != "CASCADE":
            args.append(f"on_delete={render_string(column.reference.on_delete)}")
        if column.reference.on_update != "CASCADE":
            args.append(f"on_update={render_string(column.reference.on_update)}")
        if not column.reference.db_constraint:
            args.append("db_constraint=False")

    # GeneratedField requires `expression` at construction. The state promotes it
    # out of field_kwargs, so it must be put back on the field itself rather than
    # passed alongside it -- a bare GeneratedField() does not construct.
    if column.generated is not None and column.field_class == "GeneratedField":
        args.append(f"expression={render_string(column.generated)}")
        if not column.generated_stored:
            args.append("db_persist=False")

    return _call(f"fields.{column.field_class}", args, indent=indent)


def _defaults_primary_key(field_class: str) -> bool:
    """Return whether this field class already defaults to ``primary_key=True``.

    The auto-field classes do, so emitting ``primary_key=True`` for them would be
    redundant -- and emitting it for anything else would be wrong.
    """
    return field_class in ("AutoField", "BigAutoField", "SmallAutoField")


def _render_nested_field(data: dict[str, Any], *, indent: int) -> str:
    """Render a nested field, as carried by ``GeneratedField.output_field``."""
    field_class = data.get("type", "TextField")
    args = [
        f"{key}={render_value(data[key], indent=indent + 1)}"
        for key in sorted(data)
        if key not in _PROMOTED or key == "default"
    ]
    return _call(f"fields.{field_class}", args, indent=indent)


# ── Schema state ────────────────────────────────────────────────────────────


def render_reference(reference: Reference, *, indent: int = 0) -> str:
    """Render a :class:`~aquilia.models.migration.schema.Reference` constructor call."""
    args = [
        f"model={render_string(reference.model)}",
        f"table={render_string(reference.table)}",
    ]
    if reference.column != "id":
        args.append(f"column={render_string(reference.column)}")
    if reference.on_delete != "CASCADE":
        args.append(f"on_delete={render_string(reference.on_delete)}")
    if reference.on_update != "CASCADE":
        args.append(f"on_update={render_string(reference.on_update)}")
    if reference.deferrable:
        args.append("deferrable=True")
    if not reference.db_constraint:
        args.append("db_constraint=False")
    return _call("Reference", args, indent=indent)


def render_column(column: ColumnState, *, indent: int = 0) -> str:
    """Render a column as a :meth:`ColumnState.of` call around a real field.

    Args:
        column: The column to render.
        indent: Current indentation depth.

    Returns:
        Source text such as
        ``ColumnState.of("title", fields.CharField(max_length=200))``.

    Raises:
        MigrationFault: If a field argument cannot be rendered as source.

    Example:
        >>> render_column(ColumnState.of("id", AutoField(primary_key=True)))
        'ColumnState.of("id", fields.AutoField())'
    """
    args = [render_string(column.name), render_field(column, indent=indent + 1)]

    if column.column != column.name:
        args.append(f"column={render_string(column.column)}")
    if column.reference is not None:
        args.append(f"reference={render_reference(column.reference, indent=indent + 1)}")
    # A GeneratedField already carries its own expression; ColumnState.of() reads
    # it back off the field, so repeating it here would be redundant. Any other
    # field class needs it stated explicitly.
    if column.generated is not None and column.field_class != "GeneratedField":
        args.append(f"generated={render_string(column.generated)}")
        if not column.generated_stored:
            args.append("generated_stored=False")
    if column.collation:
        args.append(f"collation={render_string(column.collation)}")
    if column.comment:
        args.append(f"comment={render_string(column.comment)}")

    return _call("ColumnState.of", args, indent=indent)


def render_index(index: IndexState, *, indent: int = 0) -> str:
    """Render an :class:`~aquilia.models.migration.schema.IndexState` constructor call."""
    args = [f"name={render_string(index.name)}"]
    if index.columns:
        args.append(f"columns={_render_str_tuple(index.columns)}")
    if index.expressions:
        args.append(f"expressions={_render_str_tuple(index.expressions)}")
    if index.unique:
        args.append("unique=True")
    if index.method != "BTREE":
        args.append(f"method={render_string(index.method)}")
    if index.condition:
        args.append(f"condition={render_string(index.condition)}")
    if index.opclasses:
        args.append(f"opclasses={_render_str_tuple(index.opclasses)}")
    if index.include:
        args.append(f"include={_render_str_tuple(index.include)}")
    if index.tablespace:
        args.append(f"tablespace={render_string(index.tablespace)}")
    if index.comment:
        args.append(f"comment={render_string(index.comment)}")
    return _call("IndexState", args, indent=indent)


def render_constraint(constraint: ConstraintState, *, indent: int = 0) -> str:
    """Render a constraint as its concrete state class's constructor call.

    Args:
        constraint: Any constraint state.
        indent: Current indentation depth.

    Returns:
        Source text such as
        ``CheckConstraintState(name="ck_price", check="price > 0")``.

    Raises:
        MigrationFault: If the constraint is of a kind this renderer does not
            know. Emitting a partial constraint would silently weaken a
            data-integrity guarantee.
    """
    if isinstance(constraint, CheckConstraintState):
        return _call(
            "CheckConstraintState",
            [f"name={render_string(constraint.name)}", f"check={render_string(constraint.check)}"],
            indent=indent,
        )

    if isinstance(constraint, UniqueConstraintState):
        args = [f"name={render_string(constraint.name)}"]
        if constraint.columns:
            args.append(f"columns={_render_str_tuple(constraint.columns)}")
        if constraint.expressions:
            args.append(f"expressions={_render_str_tuple(constraint.expressions)}")
        if constraint.condition:
            args.append(f"condition={render_string(constraint.condition)}")
        if constraint.deferrable:
            args.append("deferrable=True")
        if constraint.include:
            args.append(f"include={_render_str_tuple(constraint.include)}")
        return _call("UniqueConstraintState", args, indent=indent)

    if isinstance(constraint, PrimaryKeyConstraintState):
        return _call(
            "PrimaryKeyConstraintState",
            [f"name={render_string(constraint.name)}", f"columns={_render_str_tuple(constraint.columns)}"],
            indent=indent,
        )

    if isinstance(constraint, ForeignKeyConstraintState):
        args = [
            f"name={render_string(constraint.name)}",
            f"columns={_render_str_tuple(constraint.columns)}",
            f"target={render_string(constraint.target)}",
            f"target_columns={_render_str_tuple(constraint.target_columns)}",
        ]
        if constraint.on_delete != "CASCADE":
            args.append(f"on_delete={render_string(constraint.on_delete)}")
        if constraint.on_update != "CASCADE":
            args.append(f"on_update={render_string(constraint.on_update)}")
        if constraint.deferrable:
            args.append("deferrable=True")
        return _call("ForeignKeyConstraintState", args, indent=indent)

    if isinstance(constraint, ExclusionConstraintState):
        pairs = ", ".join(f"({render_string(col)}, {render_string(op)})" for col, op in constraint.expressions)
        args = [
            f"name={render_string(constraint.name)}",
            f"expressions=({pairs}{',' if len(constraint.expressions) == 1 else ''})",
        ]
        if constraint.method != "GIST":
            args.append(f"method={render_string(constraint.method)}")
        if constraint.condition:
            args.append(f"condition={render_string(constraint.condition)}")
        if constraint.deferrable:
            args.append("deferrable=True")
        return _call("ExclusionConstraintState", args, indent=indent)

    raise MigrationFault(
        migration="codegen",
        reason=(
            f"Cannot render constraint of type {type(constraint).__name__} into a "
            f"migration file. Supported: CheckConstraintState, UniqueConstraintState, "
            f"PrimaryKeyConstraintState, ForeignKeyConstraintState, "
            f"ExclusionConstraintState."
        ),
    )


def render_m2m(relation: ManyToManyState, *, indent: int = 0) -> str:
    """Render a :class:`~aquilia.models.migration.schema.ManyToManyState` constructor call."""
    args = [
        f"name={render_string(relation.name)}",
        f"table={render_string(relation.table)}",
        f"source_column={render_string(relation.source_column)}",
        f"target_column={render_string(relation.target_column)}",
        f"source_table={render_string(relation.source_table)}",
        f"target_table={render_string(relation.target_table)}",
    ]
    if relation.source_target_column != "id":
        args.append(f"source_target_column={render_string(relation.source_target_column)}")
    if relation.target_target_column != "id":
        args.append(f"target_target_column={render_string(relation.target_target_column)}")
    if relation.through:
        args.append(f"through={render_string(relation.through)}")
    return _call("ManyToManyState", args, indent=indent)


def render_table(table: TableState, *, indent: int = 0) -> str:
    """Render a table as a :meth:`TableState.of` call with a column list.

    Args:
        table: The table to render.
        indent: Current indentation depth.

    Returns:
        Source text for the constructor call.

    Raises:
        MigrationFault: If a column, index, or constraint cannot be rendered.
    """
    args = [render_string(table.model), render_string(table.db_table)]

    if table.columns:
        rendered = [render_column(column, indent=indent + 2) for column in table.columns.values()]
        args.append(f"columns={_join(rendered, '[', ']', indent=indent + 1)}")
    if table.indexes:
        rendered = [render_index(index, indent=indent + 2) for index in table.indexes]
        args.append(f"indexes={_join(rendered, '[', ']', indent=indent + 1)}")
    if table.constraints:
        rendered = [render_constraint(c, indent=indent + 2) for c in table.constraints]
        args.append(f"constraints={_join(rendered, '[', ']', indent=indent + 1)}")
    if table.m2m:
        rendered = [render_m2m(relation, indent=indent + 2) for relation in table.m2m]
        args.append(f"m2m={_join(rendered, '[', ']', indent=indent + 1)}")
    if table.options:
        args.append(f"options={_render_mapping(table.options, indent=indent + 1)}")

    return _call("TableState.of", args, indent=indent)


def _render_str_tuple(values: tuple[str, ...]) -> str:
    """Render a tuple of strings, with the trailing comma a 1-tuple requires."""
    if not values:
        return "()"
    if len(values) == 1:
        return f"({render_string(values[0])},)"
    return "(" + ", ".join(render_string(v) for v in values) + ")"


# ── Operations ──────────────────────────────────────────────────────────────

# How each operation's dataclass fields are rendered. A field absent from this
# map is rendered with render_value(), which covers the plain str/bool/tuple
# fields; anything holding schema state needs its own renderer so it emits a
# constructor call rather than a dict.
_FIELD_RENDERERS = {
    "table": render_table,
    "old_table": render_table,
    "new_table": render_table,
    "field": render_column,
    "old_field": render_column,
    "new_field": render_column,
    "index": render_index,
    "old_index": render_index,
    "new_index": render_index,
    "constraint": render_constraint,
    "old_constraint": render_constraint,
    "new_constraint": render_constraint,
    "relation": render_m2m,
}


def render_operation(operation: Operation, *, indent: int = 0) -> str:
    """Render one operation as its constructor call.

    Arguments equal to the operation's declared default are omitted, so an
    operation renders as the minimal expression that reconstructs it.

    Args:
        operation: The operation to render.
        indent: Current indentation depth.

    Returns:
        Source text such as ``AddField(model="User", field=ColumnState.of(...))``.

    Raises:
        MigrationFault: If a value in the operation cannot be rendered as source.

    Example:
        >>> render_operation(RemoveField(model="User", field=bio))
        'RemoveField(model="User", field=ColumnState.of("bio", fields.TextField()))'
    """
    from dataclasses import MISSING
    from dataclasses import fields as dataclass_fields

    from aquilia.models.migration.operations import RunPython, RunSQL

    if isinstance(operation, (RunSQL, RunPython)):
        return _render_special(operation, indent=indent)

    args: list[str] = []
    for spec in dataclass_fields(operation):
        value = getattr(operation, spec.name)

        default = spec.default
        if default is MISSING and spec.default_factory is not MISSING:  # type: ignore[misc]
            default = spec.default_factory()  # type: ignore[misc]
        if default is not MISSING and value == default:
            continue

        renderer = _FIELD_RENDERERS.get(spec.name)
        if renderer is not None:
            args.append(f"{spec.name}={renderer(value, indent=indent + 1)}")
        else:
            args.append(f"{spec.name}={render_value(value, indent=indent + 1)}")

    return _call(type(operation).__name__, args, indent=indent)


def _render_special(operation: Any, *, indent: int) -> str:
    """Render :class:`RunSQL` or :class:`RunPython`.

    ``RunPython`` holds callables, which have no literal form. They are emitted
    as bare names and imported at the top of the file, so the generated module
    references the same function object the operation was built with.

    Raises:
        MigrationFault: If a ``RunPython`` callable is a lambda or a nested
            function, neither of which can be imported by name at apply time.
    """
    from aquilia.models.migration.operations import RunPython

    args: list[str] = []

    if isinstance(operation, RunPython):
        if operation.code is not None:
            args.append(f"code={_callable_name(operation.code)}")
        if operation.reverse_code is not None:
            args.append(f"reverse_code={_callable_name(operation.reverse_code)}")
        if operation.state_operations:
            nested = [render_operation(op, indent=indent + 2) for op in operation.state_operations]
            args.append(f"state_operations={_join(nested, '[', ']', indent=indent + 1)}")
        if not operation.atomic_statements:
            args.append("atomic_statements=False")
        return _call("RunPython", args, indent=indent)

    if operation.sql:
        args.append(f"sql={render_value(operation.sql, indent=indent + 1)}")
    if operation.reverse_sql:
        args.append(f"reverse_sql={render_value(operation.reverse_sql, indent=indent + 1)}")
    if operation.state_operations:
        nested = [render_operation(op, indent=indent + 2) for op in operation.state_operations]
        args.append(f"state_operations={_join(nested, '[', ']', indent=indent + 1)}")
    if operation.dialects:
        args.append(f"dialects={_render_str_tuple(operation.dialects)}")
    if operation.params:
        args.append(f"params={render_value(list(operation.params), indent=indent + 1)}")
    if not operation.atomic_statements:
        args.append("atomic_statements=False")
    return _call("RunSQL", args, indent=indent)


def _callable_name(fn: Any) -> str:
    """Return the expression a generated module uses to reference a callable.

    A module-level function renders as its bare name; a static method renders as
    the dotted path from the name that gets imported, e.g. ``RunPython.noop``.

    Raises:
        MigrationFault: If the callable cannot be imported by name.
    """
    module = getattr(fn, "__module__", None)
    qualname = getattr(fn, "__qualname__", None)
    if not module or not qualname or "<locals>" in qualname or qualname == "<lambda>":
        raise MigrationFault(
            migration="codegen",
            reason=(
                f"RunPython callable {fn!r} cannot be written into a migration file: it "
                f"must be a module-level function so the migration can import it when "
                f"applied. Lambdas and nested functions are not importable by name."
            ),
        )
    return qualname


def render_operations(operations: tuple[Operation, ...] | list[Operation]) -> str:
    """Render the ``operations`` list of a migration file.

    Args:
        operations: The operations to render, in application order.

    Returns:
        Source text for the assignment, e.g. ``operations = [...]``.

    Raises:
        MigrationFault: If an operation contains an unrenderable value.
    """
    if not operations:
        return "operations: list[Operation] = []"
    lines = ["operations: list[Operation] = ["]
    for operation in operations:
        lines.append(f"{_INDENT}{render_operation(operation, indent=1)},")
    lines.append("]")
    return "\n".join(lines)


# ── Imports ─────────────────────────────────────────────────────────────────

_SCHEMA_NAMES = {
    "ColumnState",
    "TableState",
    "IndexState",
    "Reference",
    "CheckConstraintState",
    "UniqueConstraintState",
    "PrimaryKeyConstraintState",
    "ForeignKeyConstraintState",
    "ExclusionConstraintState",
    "ManyToManyState",
    "NOT_PROVIDED",
}


def collect_imports(operations: tuple[Operation, ...] | list[Operation], body: str) -> list[str]:
    """Return the import lines a rendered migration body needs.

    Only what the body actually references is imported, so a migration that adds
    one column does not carry a wall of unused imports -- and lint stays clean
    without a blanket ``noqa``.

    Args:
        operations: The operations that were rendered.
        body: The rendered ``operations`` source, scanned for the names it uses.

    Returns:
        Import lines, in the order they should appear in the file.

    Example:
        >>> collect_imports(ops, body)
        ['from aquilia.models import fields',
         'from aquilia.models.migration.operations import AddField, Operation',
         'from aquilia.models.migration.schema import ColumnState']
    """
    lines: list[str] = []

    if "datetime." in body:
        lines.append("import datetime")
    if "Decimal(" in body:
        lines.append("from decimal import Decimal")
    if lines:
        lines.append("")

    # Third-party/first-party block, isort-ordered so generated files pass the
    # same lint as hand-written ones.
    block: list[str] = []
    if "fields." in body:
        block.append("from aquilia.models import fields")

    operation_names = {type(operation).__name__ for operation in operations}
    operation_names.update(_nested_operation_names(operations))
    # `Operation` itself is referenced by the list's type annotation.
    operation_names.add("Operation")
    block.append(_import_line("aquilia.models.migration.operations", sorted(operation_names)))

    schema_names = sorted(name for name in _SCHEMA_NAMES if _references(body, name))
    if schema_names:
        block.append(_import_line("aquilia.models.migration.schema", schema_names))

    block.extend(_callable_imports(operations, already=operation_names | set(schema_names)))
    lines.extend(sorted(block, key=lambda line: line.split(" import ")[0]))

    return lines


def _import_line(module: str, names: list[str]) -> str:
    """Render a ``from ... import ...``, wrapping in parentheses when too long.

    Generated files are linted alongside hand-written ones, so an import list
    that would exceed the line limit is wrapped rather than left for a formatter
    to fix after the fact.
    """
    single = f"from {module} import {', '.join(names)}"
    if len(single) <= 120:
        return single
    body = ",\n".join(f"{_INDENT}{name}" for name in names)
    return f"from {module} import (\n{body},\n)"


def _references(body: str, name: str) -> bool:
    """Return whether *body* uses *name* as an identifier rather than a substring."""
    index = body.find(name)
    while index != -1:
        before = body[index - 1] if index else " "
        after_index = index + len(name)
        after = body[after_index] if after_index < len(body) else " "
        if not (before.isalnum() or before == "_") and not (after.isalnum() or after == "_"):
            return True
        index = body.find(name, index + 1)
    return False


def _nested_operation_names(operations: Any) -> set[str]:
    """Return operation class names appearing inside ``state_operations``."""
    names: set[str] = set()
    for operation in operations:
        nested = getattr(operation, "state_operations", ())
        for inner in nested:
            names.add(type(inner).__name__)
            names.update(_nested_operation_names([inner]))
    return names


def _callable_imports(operations: Any, *, already: set[str]) -> list[str]:
    """Return import lines for every ``RunPython`` callable, merged per module.

    A callable is referenced by its qualified name, so what gets imported is the
    *root* of that name -- ``RunPython`` for ``RunPython.noop``, ``backfill`` for
    a plain function. Roots from the same module share one import line.

    Args:
        operations: The operations that were rendered.
        already: Names the operation and schema imports already bring in. A
            static method of an operation class resolves through the name that
            is already imported, so importing it again from the defining
            submodule would shadow it with a duplicate.
    """
    from aquilia.models.migration.operations import RunPython

    by_module: dict[str, set[str]] = {}

    def collect(ops: Any) -> None:
        for operation in ops:
            if isinstance(operation, RunPython):
                for fn in (operation.code, operation.reverse_code):
                    if fn is None:
                        continue
                    root = _callable_name(fn).split(".")[0]
                    if root not in already:
                        by_module.setdefault(fn.__module__, set()).add(root)
            collect(getattr(operation, "state_operations", ()))

    collect(operations)
    return [_import_line(module, sorted(by_module[module])) for module in sorted(by_module)]

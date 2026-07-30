"""
Aquilia Migration File Generator -- creates DSL migration files.

Generates human-readable Python-DSL migration files from schema diffs.
This replaces the old raw-SQL migration generator.
"""

from __future__ import annotations

import datetime
import logging
import re
from pathlib import Path

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
    RunSQL,
)
from .schema_snapshot import (
    SchemaDiff,
    compute_diff,
    create_snapshot,
    diff_to_operations,
    load_snapshot,
    save_snapshot,
)

logger = logging.getLogger("aquilia.models.migration_gen")


def _generate_revision() -> str:
    """Generate a timestamp-based revision ID."""
    now = datetime.datetime.now(datetime.timezone.utc)
    return now.strftime("%Y%m%d_%H%M%S")


def _slugify(name: str) -> str:
    """Convert a model name to a migration slug.

    Note:
        This function is currently unused elsewhere in this module --
        ``generate_dsl_migration`` builds its slug inline from
        ``_affected_model_names`` instead of calling this. It also appears
        to have its ``re.sub`` arguments swapped (``repl`` and ``string``
        are reversed compared to the equivalent, actively-used
        ``migrations.py::_slugify``), so as written it does not sanitize
        non-alphanumeric characters out of ``name`` -- it only lowercases
        it. Left as-is per the docs-only scope of this pass; flagged here
        for a future behavioral fix.
    """
    return re.sub(r"[^a-z0-9]+", name.lower(), "_").strip("_")


def generate_dsl_migration(
    model_classes: list,
    migrations_dir: str | Path,
    snapshot_path: str | Path | None = None,
    slug: str | None = None,
) -> Path | None:
    """
    Generate a DSL migration file from the diff between the current
    snapshot and the current model definitions.

    Steps:
    1. Load the previous snapshot (or start from empty)
    2. Create a new snapshot from current model classes
    3. Compute the diff
    4. Generate DSL operations from the diff
    5. Write the migration file
    6. Save the new snapshot

    Args:
        model_classes: List of Model subclass classes
        migrations_dir: Directory to write migration file
        snapshot_path: Path to schema_snapshot.json (default: migrations_dir/schema_snapshot.json)
        slug: Optional slug for filename

    Returns:
        Path to generated migration file, or None if no changes detected.
    """
    mdir = Path(migrations_dir)
    mdir.mkdir(parents=True, exist_ok=True)

    snap_path = Path(snapshot_path) if snapshot_path else mdir / "schema_snapshot.json"

    # Load old snapshot from JSON format
    old_snapshot = None
    if snap_path.exists():
        old_snapshot = load_snapshot(snap_path)
    if old_snapshot is None:
        old_snapshot = {"version": 1, "models": {}, "checksum": ""}

    # Create new snapshot
    new_snapshot = create_snapshot(model_classes)

    # Compute diff
    diff = compute_diff(old_snapshot, new_snapshot)

    if not diff.has_changes:
        return None

    # Generate operations from diff
    operations = diff_to_operations(diff, old_snapshot, new_snapshot)

    if not operations:
        return None

    # Build revision, slug, and dependencies
    rev = _generate_revision()
    model_names = _affected_model_names(diff)

    # Collect previous migration revision ID as dependency if available
    dependencies: list[str] = []
    existing_files = sorted(mdir.glob("*.py"))
    for f in existing_files:
        if f.name.endswith(".py") and not f.name.startswith("__"):
            parts = f.name.split("_", 2)
            if len(parts) >= 2 and parts[0].isdigit() and len(parts[0]) == 8:
                prev_rev = f"{parts[0]}_{parts[1]}"
                dependencies = [prev_rev]

    if not slug:
        if len(model_names) <= 3:
            slug = "_".join(n.lower() for n in model_names)
        else:
            slug = "_".join(n.lower() for n in model_names[:3])
            slug += f"_and_{len(model_names) - 3}_more"

    # Generate file content
    content = _render_migration_file(rev, slug, model_names, operations, dependencies=dependencies)

    filename = f"{rev}_{slug}.py"
    filepath = mdir / filename

    # TWO-PHASE WRITE FIX: save snapshot FIRST, then write migration file.
    save_snapshot(new_snapshot, snap_path)
    filepath.write_text(content, encoding="utf-8")

    return filepath


def _affected_model_names(diff: SchemaDiff) -> list[str]:
    """Collect the sorted, de-duplicated set of model names touched by a diff.

    Combines added, removed, renamed (using the new name), and altered
    model names from ``diff`` into a single flat list. Used both to build
    the migration's ``Meta.models`` list and to derive its default slug.

    Args:
        diff: The ``SchemaDiff`` to summarize.

    Returns:
        Sorted list of unique model names.
    """
    names: list[str] = []
    names.extend(diff.added_models)
    names.extend(diff.removed_models)
    for _old, new in diff.renamed_models:
        names.append(new)
    names.extend(diff.altered_models.keys())
    return sorted(set(names))


def _render_migration_file(
    revision: str,
    slug: str,
    model_names: list[str],
    operations: list[Operation],
    dependencies: list[str] | None = None,
) -> str:
    """Render a complete DSL migration file as Python source text.

    Purpose:
        Renders a full, syntactically valid Python source module for a DSL migration.

    Lifecycle:
        Invoked at the end of ``generate_dsl_migration()``.

    Execution Order:
        1. Format module docstring with revision, timestamp, and affected model names.
        2. Deduplicate operation types and render imports.
        3. Format ``Meta`` class carrying ``revision``, ``slug``, ``models``, and ``dependencies``.
        4. Format ``operations`` list.

    Parameters:
        revision (str): Timestamp-based revision ID string.
        slug (str): Migration slug identifier string.
        model_names (list[str]): List of affected model names.
        operations (list[Operation]): List of DSL operations.
        dependencies (list[str] | None): List of prerequisite migration revision IDs.

    Returns:
        str: Ready-to-write Python source code.
    """
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    models_str = ", ".join(model_names)
    deps = dependencies or []

    # Build imports
    op_types = set(type(op).__name__ for op in operations)
    imports = sorted(op_types)
    imports_line = ", ".join(imports)

    lines = [
        '"""',
        f"Migration: {revision}_{slug}",
        f"Generated: {now}",
        f"Models: {models_str}",
        '"""',
        "",
        "from aquilia.models.migration_dsl import (",
        f"    {imports_line},",
        "    columns as C,",
        ")",
        "",
        "",
        "class Meta:",
        f'    revision = "{revision}"',
        f'    slug = "{slug}"',
        f"    models = {model_names!r}",
        f"    dependencies = {deps!r}",
        "",
        "",
    ]

    # Render operations list
    lines.append("operations = [")
    for op in operations:
        lines.append(_render_operation(op))
    lines.append("]")
    lines.append("")

    return "\n".join(lines)


def _render_operation(op: Operation) -> str:
    """Render a single ``Operation`` instance as a Python source-code call.

    Dispatches on the concrete operation type and emits a multi-line,
    ready-to-read constructor call (e.g. ``CreateModel(name=..., table=...,
    fields=[...])``) matching the literal argument values on ``op``, using
    ``repr()`` (via ``!r``) for safe literal formatting of strings/lists.
    ``CreateModel``/``AddField`` additionally render their ``ColumnDef``
    values via ``_render_column_def``.

    Args:
        op: The operation to render. Must be one of the concrete DSL
            operation types imported at the top of this module.

    Returns:
        A string containing one or more indented lines of Python source,
        always ending in a trailing comma (so it can be placed directly
        inside the generated ``operations = [...]`` list). For an
        unrecognized operation type, returns a ``# Unknown operation: ...``
        comment instead of raising.
    """
    if isinstance(op, CreateModel):
        field_lines = []
        for f in op.fields:
            field_lines.append(f"            {_render_column_def(f)},")
        fields_str = "\n".join(field_lines)
        return (
            f"    CreateModel(\n"
            f"        name={op.name!r},\n"
            f"        table={op.table!r},\n"
            f"        fields=[\n"
            f"{fields_str}\n"
            f"        ],\n"
            f"    ),"
        )
    elif isinstance(op, DropModel):
        return f"    DropModel(name={op.name!r}, table={op.table!r}),"
    elif isinstance(op, RenameModel):
        return (
            f"    RenameModel(\n"
            f"        old_name={op.old_name!r}, new_name={op.new_name!r},\n"
            f"        old_table={op.old_table!r}, new_table={op.new_table!r},\n"
            f"    ),"
        )
    elif isinstance(op, AddField):
        return (
            f"    AddField(\n"
            f"        model_name={op.model_name!r}, table={op.table!r},\n"
            f"        column={_render_column_def(op.column)},\n"
            f"    ),"
        )
    elif isinstance(op, RemoveField):
        return f"    RemoveField(model_name={op.model_name!r}, table={op.table!r}, column_name={op.column_name!r}),"
    elif isinstance(op, AlterField):
        return (
            f"    AlterField(\n"
            f"        model_name={op.model_name!r}, table={op.table!r},\n"
            f"        column_name={op.column_name!r}, new_type={op.new_type!r},\n"
            f"    ),"
        )
    elif isinstance(op, RenameField):
        return (
            f"    RenameField(\n"
            f"        model_name={op.model_name!r}, table={op.table!r},\n"
            f"        old_name={op.old_name!r}, new_name={op.new_name!r},\n"
            f"    ),"
        )
    elif isinstance(op, CreateIndex):
        return (
            f"    CreateIndex(\n"
            f"        name={op.name!r}, table={op.table!r},\n"
            f"        columns={op.columns!r}, unique={op.unique!r},\n"
            f"    ),"
        )
    elif isinstance(op, DropIndex):
        t = f", table={op.table!r}" if op.table else ""
        return f"    DropIndex(name={op.name!r}{t}),"
    elif isinstance(op, AddConstraint):
        return f"    AddConstraint(\n        table={op.table!r},\n        constraint_sql={op.constraint_sql!r},\n    ),"
    elif isinstance(op, RemoveConstraint):
        return f"    RemoveConstraint(table={op.table!r}, name={op.name!r}),"
    elif isinstance(op, RunSQL):
        return f"    RunSQL(sql={op.sql!r}),"
    else:
        return f"    # Unknown operation: {op.describe()}"


def _render_column_def(col: ColumnDef) -> str:
    """Render a ``ColumnDef`` as the equivalent ``C.xxx(...)`` builder call.

    Purpose:
        Inverts the ``_ColumnBuilder``/``C`` helpers in ``migration_dsl.py``:
        given a fully-formed ``ColumnDef``, infers which ``C.*`` factory method
        would have produced it and renders that call with the relevant kwargs
        (``null``, ``unique``, ``primary_key``, ``default``) reconstructed from
        the column's attributes.

    Lifecycle:
        Invoked by ``_render_operation()`` during migration file source code
        rendering (``generate_dsl_migration()``).

    Execution Order:
        1. Check for auto-increment primary key -> ``C.auto()``.
        2. Reconstruct column attribute kwargs (``null``, ``unique``, ``primary_key``, ``default``).
        3. Unwrap Enum member defaults to scalar primitives.
        4. Render foreign key references or match SQL column type to ``C.*`` builder method.

    Parameters:
        col (ColumnDef): The column definition instance to render.

    Returns:
        str: A single-line Python code snippet such as ``'C.varchar("status", 50, default="active")'``.

    Exceptions:
        None directly raised.

    Notes:
        Guarantees that Enum defaults (e.g. ``UserStatus.ACTIVE``) are unwrapped to
        valid Python scalar literals (e.g. ``'active'`` or ``1``) rather than invalid
        repr strings like ``<UserStatus.ACTIVE: 'active'>``.

    Internal Behaviour:
        Checks ``isinstance(def_val, Enum)`` and unwraps to ``def_val.value`` before
        applying string formatting via ``!r``.

    Edge Cases:
        - Auto-increment columns ignore explicit defaults.
        - Enum instances are unwrapped to primitive values.
        - Unknown column types fall back to ``C.text(...)``.

    Examples:
        >>> col = ColumnDef(name="status", col_type="VARCHAR(50)", default=UserStatus.ACTIVE)
        >>> _render_column_def(col)
        'C.varchar("status", 50, default=\\'active\\')'
    """
    from enum import Enum

    if col.primary_key and col.autoincrement:
        return f'C.auto("{col.name}")'

    # Determine builder method
    t = col.col_type.upper()
    kwargs: list[str] = []

    if col.nullable:
        kwargs.append("null=True")
    if col.unique:
        kwargs.append("unique=True")
    if col.primary_key:
        kwargs.append("primary_key=True")
    if col.default is not _SENTINEL:
        def_val = col.default
        if isinstance(def_val, Enum):
            def_val = def_val.value
        kwargs.append(f"default={def_val!r}")

    kwargs_str = ", ".join(kwargs)

    if col.references:
        ref_table, ref_col = col.references
        parts = [f'"{col.name}"', f'"{ref_table}"', f'"{ref_col}"']
        if col.col_type != "INTEGER":
            parts.append(f'col_type="{col.col_type}"')
        if col.nullable:
            parts.append("null=True")
        if col.on_delete != "CASCADE":
            parts.append(f'on_delete="{col.on_delete}"')
        if col.on_update != "CASCADE":
            parts.append(f'on_update="{col.on_update}"')
        return f"C.foreign_key({', '.join(parts)})"

    if t == "BOOLEAN":
        extra = f", {kwargs_str}" if kwargs_str else ""
        return f'C.boolean("{col.name}"{extra})'
    elif "VARCHAR" in t:
        import re

        m = re.search(r"\((\d+)\)", t)
        length = m.group(1) if m else "255"
        extra = f", {kwargs_str}" if kwargs_str else ""
        return f'C.varchar("{col.name}", {length}{extra})'
    elif t == "TEXT":
        extra = f", {kwargs_str}" if kwargs_str else ""
        return f'C.text("{col.name}"{extra})'
    elif t == "INTEGER":
        extra = f", {kwargs_str}" if kwargs_str else ""
        return f'C.integer("{col.name}"{extra})'
    elif "DECIMAL" in t:
        import re

        m = re.search(r"\((\d+),\s*(\d+)\)", t)
        if m:
            extra = f", {kwargs_str}" if kwargs_str else ""
            return f'C.decimal("{col.name}", {m.group(1)}, {m.group(2)}{extra})'
        extra = f", {kwargs_str}" if kwargs_str else ""
        return f'C.decimal("{col.name}"{extra})'
    elif t == "TIMESTAMP":
        extra = f", {kwargs_str}" if kwargs_str else ""
        return f'C.timestamp("{col.name}"{extra})'
    elif t == "REAL":
        extra = f", {kwargs_str}" if kwargs_str else ""
        return f'C.real("{col.name}"{extra})'
    elif t == "BLOB":
        return f'C.blob("{col.name}")'
    elif t == "DATE":
        extra = f", {kwargs_str}" if kwargs_str else ""
        return f'C.date("{col.name}"{extra})'
    elif t == "TIME":
        extra = f", {kwargs_str}" if kwargs_str else ""
        return f'C.time("{col.name}"{extra})'
    elif t in ("VARCHAR(36)",) or "UUID" in t:
        extra = f", {kwargs_str}" if kwargs_str else ""
        return f'C.uuid("{col.name}"{extra})'
    else:
        extra = f", {kwargs_str}" if kwargs_str else ""
        return f'C.text("{col.name}"{extra})'

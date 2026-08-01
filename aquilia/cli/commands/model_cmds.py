"""
Model CLI Commands -- aq db makemigrations, aq db migrate, aq db dump, aq db shell.

Integrates model discovery, migration generation/execution, schema inspection,
and interactive REPL with the Aquilia CLI system.

Discovers pure-Python Model subclasses from:
  - modules/*/models/ packages
  - modules/*/models.py files
  - models/ at workspace root
"""

from __future__ import annotations

import asyncio
import contextlib
import importlib
import importlib.util
import sys
import types
from pathlib import Path

import click

from aquilia.models.base import ModelRegistry
from aquilia.models.migration import MigrationEngine
from aquilia.models.migration.autodetect import detect_changes
from aquilia.models.migration.executor import MigrationExecutor
from aquilia.models.migration.schema import ProjectState
from aquilia.models.migration.serializer import revision_from_path

# ── Discovery Helpers ─────────────────────────────────────────────────────────


def _has_admin_integration() -> bool:
    """Detect if admin integration is enabled in workspace.py."""
    import re as _re

    workspace_file = Path.cwd() / "workspace.py"
    if not workspace_file.exists():
        return False
    try:
        text = workspace_file.read_text(encoding="utf-8")
        # Match Integration.admin( that is NOT commented out
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if _re.search(r"Integration\.admin\s*\(", stripped):
                return True
    except Exception:
        pass
    return False


def _discover_admin_models(verbose: bool = False) -> list:
    """
    Import and return all admin ORM models from aquilia.admin.models.

    These models (AdminUser, AdminAuditEntry, AdminAPIKey, AdminPreference)
    live in the framework package and are not discovered by _find_model_files
    which only scans the workspace.
    """
    try:
        from aquilia.admin.models import (
            _HAS_ORM,
            AdminAPIKey,
            AdminAuditEntry,
            AdminPreference,
            AdminUser,
        )
        from aquilia.models.base import Model

        if not _HAS_ORM:
            return []

        admin_models = [
            AdminUser,
            AdminAuditEntry,
            AdminAPIKey,
            AdminPreference,
        ]
        # Only return actual Model subclasses
        result = [m for m in admin_models if isinstance(m, type) and issubclass(m, Model) and m is not Model]
        if verbose:
            for m in result:
                click.echo(
                    click.style(
                        f"  Found admin model: {m.__name__} (table={m._meta.table_name})",
                        fg="magenta",
                    )
                )
        return result
    except Exception:
        return []


def _find_model_files(search_dirs: list[str] | None = None) -> list[Path]:
    """
    Find all Python model files in the workspace.

    Searches (in order):
    1. Explicit directories if provided
    2. modules/*/models/ packages (__init__.py + siblings)
    3. modules/*/models.py single-file models
    4. models/ at workspace root
    """
    found: list[Path] = []
    cwd = Path.cwd()

    if search_dirs:
        for d in search_dirs:
            p = Path(d)
            if p.is_dir():
                for pyf in sorted(p.glob("**/*.py")):
                    if not pyf.name.startswith("_"):
                        found.append(pyf)
                # Also include __init__.py in model packages
                for init in sorted(p.glob("**/__init__.py")):
                    if init not in found:
                        found.append(init)
    else:
        # modules/*/models/ packages -- prefer __init__.py as entry point
        for init in sorted(cwd.glob("modules/*/models/__init__.py")):
            found.append(init)
        # Non-init siblings inside model packages (additional model files)
        for pyf in sorted(cwd.glob("modules/*/models/*.py")):
            if pyf.name.startswith("_"):
                continue
            if pyf not in found:
                found.append(pyf)
        # modules/*/models.py single-file modules
        for pyf in sorted(cwd.glob("modules/*/models.py")):
            if pyf not in found:
                found.append(pyf)
        # Root models/ directory
        for init in sorted(cwd.glob("models/__init__.py")):
            if init not in found:
                found.append(init)
        for pyf in sorted(cwd.glob("models/*.py")):
            if pyf.name.startswith("_"):
                continue
            if pyf not in found:
                found.append(pyf)

    return list(dict.fromkeys(found))  # dedupe preserving order


def _import_model_module(py_path: Path) -> types.ModuleType | None:
    """
    Import a Python model file using proper package-aware imports.

    Computes a dotted module path relative to cwd so that relative
    imports within model packages work correctly.
    """
    cwd = Path.cwd()

    try:
        rel = py_path.relative_to(cwd)
    except ValueError:
        rel = None

    if rel is not None:
        # Build dotted module name:
        # modules/products/models/__init__.py → modules.products.models
        parts = list(rel.with_suffix("").parts)
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        dotted = ".".join(parts)

        # Ensure cwd is on sys.path
        cwd_str = str(cwd)
        if cwd_str not in sys.path:
            sys.path.insert(0, cwd_str)

        # Bootstrap parent packages in sys.modules so relative imports resolve
        for i in range(1, len(parts)):
            parent_dotted = ".".join(parts[:i])
            if parent_dotted not in sys.modules:
                parent_path = cwd / Path(*parts[:i])
                init_file = parent_path / "__init__.py"
                if init_file.is_file():
                    parent_spec = importlib.util.spec_from_file_location(
                        parent_dotted,
                        str(init_file),
                        submodule_search_locations=[str(parent_path)],
                    )
                    if parent_spec and parent_spec.loader:
                        parent_mod = importlib.util.module_from_spec(parent_spec)
                        sys.modules[parent_dotted] = parent_mod
                        with contextlib.suppress(Exception):
                            parent_spec.loader.exec_module(parent_mod)
                else:
                    # Create a namespace package stub
                    ns_mod = types.ModuleType(parent_dotted)
                    ns_mod.__path__ = [str(parent_path)]
                    ns_mod.__package__ = parent_dotted
                    sys.modules[parent_dotted] = ns_mod

        # Import the actual module
        if dotted in sys.modules:
            return sys.modules[dotted]
        return importlib.import_module(dotted)
    else:
        # Fallback for files outside workspace
        module_name = f"_aquilia_cli_models_{py_path.stem}_{id(py_path)}"
        spec = importlib.util.spec_from_file_location(module_name, str(py_path))
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod


def _discover_models(
    search_dirs: list[str] | None = None,
    app: str | None = None,
    verbose: bool = False,
    ignore_errors: bool = False,
) -> list:
    """
    Discover all Model subclasses in the workspace.

    When admin integration is enabled in workspace.py, admin models
    (ContentType, AdminPermission, AdminGroup, AdminUser, AdminLogEntry,
    AdminSession) are automatically included via the built-in
    admin model discovery.

    Args:
        search_dirs: Explicit directories to search
        app: Filter to a specific module/app name
        verbose: Print discovery details

    Returns:
        List of Model subclass classes
    """
    try:
        from aquilia.models.base import Model
    except ImportError:
        click.echo(click.style("Model system not available.", fg="red"))
        return []

    py_files = _find_model_files(search_dirs)

    # Filter by app if specified
    if app:
        py_files = [f for f in py_files if f"modules/{app}/" in str(f) or f"modules/{app}\\" in str(f)]

    discovered = []
    seen_names: set = set()

    # ── Include admin models when admin integration is enabled ────────────
    if not app and _has_admin_integration():
        admin_models = _discover_admin_models(verbose=verbose)
        for m in admin_models:
            if m.__name__ not in seen_names:
                discovered.append(m)
                seen_names.add(m.__name__)

    for py_path in py_files:
        try:
            mod = _import_model_module(py_path)
            if mod is None:
                continue

            for attr_name in dir(mod):
                attr = getattr(mod, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, Model)
                    and attr is not Model
                    and not getattr(getattr(attr, "_meta", None), "abstract", False)
                    and attr.__name__ not in seen_names
                ):
                    discovered.append(attr)
                    seen_names.add(attr.__name__)
                    if verbose:
                        click.echo(
                            click.style(
                                f"  Found model: {attr.__name__} (table={attr._meta.table_name})",
                                fg="blue",
                            )
                        )
        except Exception as e:
            if not ignore_errors:
                import traceback

                error_details = traceback.format_exc()
                click.secho(f"\nError: Failed to import or process model file: {py_path}", fg="red", bold=True)
                click.secho(f"{error_details}", fg="red")
                raise click.ClickException(
                    f"Failed to load model from {py_path}. Please fix the syntax/import errors before continuing."
                )

            if verbose:
                click.echo(click.style(f"  ! Failed to import {py_path}: {e}", fg="yellow"))
            continue

    return discovered


# ── Commands ──────────────────────────────────────────────────────────────────


def cmd_makemigrations(
    app: str | None = None,
    migrations_dir: str = "migrations",
    verbose: bool = False,
    slug: str | None = None,
    dry_run: bool = False,
) -> list[Path]:
    """Generate a migration for the difference between the snapshot and the models.

    Args:
        app: Restrict discovery to one module, by name.
        migrations_dir: Where migration files and the state snapshot live.
        verbose: Print each discovered model.
        slug: Filename suffix. Derived from the affected models when omitted.
        dry_run: Report what would be generated without writing anything.

    Returns:
        The paths written -- a single-element list, or empty when the models
        already match the snapshot or *dry_run* was set.

    Raises:
        MigrationFault: If the models cannot be snapshotted, or an operation
            cannot be rendered as Python source.

    Example:
        >>> cmd_makemigrations(app="blog", slug="add_bio")
        [PosixPath('migrations/20260730_143000_add_bio.py')]
    """
    if verbose:
        click.echo(click.style("Scanning for models...", fg="cyan"))

    models = _discover_models(app=app, verbose=verbose)

    if not models:
        click.echo(
            click.style(
                f"No models found{f' for app {app!r}' if app else ''}. Define Model subclasses in modules/*/models/.",
                fg="yellow",
            )
        )
        return []

    engine = MigrationEngine(migrations_dir)
    generated = engine.make_migrations(models, slug=slug, dry_run=dry_run)

    if generated is None:
        click.echo(click.style("No model changes detected.", fg="yellow"))
        return []

    model_names = ", ".join(m.__name__ for m in models)
    click.echo(
        click.style(
            f"Generated migration: {generated.name} ({len(models)} model(s): {model_names})",
            fg="green",
        )
    )
    click.echo(click.style(f"  Schema snapshot: {engine.snapshot_path}", dim=True))
    return [generated]


def cmd_migrate(
    migrations_dir: str = "migrations",
    database_url: str = "sqlite:///db.sqlite3",
    target: str | None = None,
    verbose: bool = False,
    fake: bool = False,
    plan: bool = False,
    database: str | None = None,
) -> list[str]:
    """
    Apply pending migrations to the database.

    Supports both DSL and legacy migrations. The runner auto-detects
    the migration format.

    Args:
        fake: Mark as applied without executing SQL
        plan: Preview SQL only (dry-run)
        database: Database alias for multi-db setups

    Returns:
        List of applied revision IDs
    """

    async def _run() -> list[str]:
        from aquilia.db import AquiliaDatabase

        db = AquiliaDatabase(database_url)
        await db.connect()
        try:
            engine = MigrationEngine(migrations_dir)

            if plan:
                statements = await engine.plan(db, target=target)
                if statements:
                    click.echo(click.style("-- Migration Plan (dry-run):", fg="cyan"))
                    for statement in statements:
                        if statement.destructive:
                            click.echo(click.style(f"-- DESTRUCTIVE: {statement.description}", fg="red"))
                        click.echo(statement.sql)
                else:
                    click.echo(click.style("No pending migrations.", fg="yellow"))
                return []

            if target:
                results = await engine.migrate(db, target=target, fake=fake)
                action = "Faked rollback of" if fake else "Rolled back"
                if results:
                    click.echo(click.style(f"{action} {len(results)} migration(s) to {target}", fg="green"))
                else:
                    click.echo(click.style("Nothing to rollback.", fg="yellow"))
            else:
                results = await engine.migrate(db, fake=fake)
                action = "Faked" if fake else "Applied"
                if results:
                    click.echo(click.style(f"{action} {len(results)} migration(s)", fg="green"))
                else:
                    click.echo(click.style("No pending migrations.", fg="yellow"))

            if verbose:
                for result in results:
                    for note in result.diagnostics:
                        click.echo(click.style(f"  {note}", dim=True))

            status = await engine.status(db)
            return list(status.applied)
        finally:
            await db.disconnect()

    return asyncio.run(_run())


def cmd_model_dump(
    emit: str = "python",
    output_dir: str | None = None,
    verbose: bool = False,
) -> str | None:
    """
    Dump model schema information.

    Generates DDL (CREATE TABLE, indexes, constraints) for all
    discovered Model subclasses.

    Args:
        emit: Output format -- 'python' for annotated schema, 'sql' for raw DDL.
        output_dir: Directory to write output files (if set).
        verbose: Verbose output.

    Returns:
        Generated source string or None.
    """
    models = _discover_models(verbose=verbose)

    if not models:
        click.echo(click.style("No models found in workspace.", fg="yellow"))
        return None

    parts: list[str] = []

    if emit == "sql":
        # Raw SQL DDL
        sql_lines = ["-- Aquilia Model Schema", "--"]
        for model_cls in models:
            sql_lines.append(f"\n-- Model: {model_cls.__name__}")
            sql_lines.append(f"-- Table: {model_cls._meta.table_name}")
            try:
                sql_lines.append(model_cls.generate_create_table_sql() + ";")
                for idx_sql in model_cls.generate_index_sql():
                    sql_lines.append(idx_sql + ";")
                for m2m_sql in model_cls.generate_m2m_sql():
                    sql_lines.append(m2m_sql + ";")
            except Exception as e:
                sql_lines.append(f"-- Error generating DDL: {e}")
        parts.append("\n".join(sql_lines))
    else:
        # Annotated Python-style schema overview
        py_lines = ['"""Aquilia Model Schema -- auto-generated."""', ""]
        for model_cls in models:
            py_lines.append(f"# ── {model_cls.__name__} ──")
            py_lines.append(f"# Table: {model_cls._meta.table_name}")
            meta = model_cls._meta
            if hasattr(meta, "ordering") and meta.ordering:
                py_lines.append(f"# Ordering: {meta.ordering}")

            # Fields
            py_lines.append("# Fields:")
            for name, field in model_cls._meta.fields.items():
                col = getattr(field, "column_name", name)
                ftype = type(field).__name__
                extras = []
                if getattr(field, "primary_key", False):
                    extras.append("PK")
                if getattr(field, "unique", False):
                    extras.append("UNIQUE")
                if getattr(field, "null", False):
                    extras.append("NULL")
                if getattr(field, "default", None) is not None:
                    extras.append(f"default={field.default!r}")
                extra_str = f" [{', '.join(extras)}]" if extras else ""
                py_lines.append(f"#   {name} ({col}): {ftype}{extra_str}")

            # DDL
            try:
                ddl = model_cls.generate_create_table_sql()
                py_lines.append("\n# DDL:")
                for line in ddl.split("\n"):
                    py_lines.append(f"# {line}")
            except Exception as e:
                py_lines.append(f"# DDL Error: {e}")

            py_lines.append("")
        parts.append("\n".join(py_lines))

    source = "\n\n".join(parts)

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        ext = ".sql" if emit == "sql" else ".py"
        outfile = out / f"schema{ext}"
        outfile.write_text(source, encoding="utf-8")
        click.echo(click.style(f"Schema written to {outfile}", fg="green"))
    else:
        click.echo(source)

    return source


def _configure_shell_line_editor(namespace: dict[str, object]) -> bool:
    """
    Configure readline/libedit so shell editing behaves like a normal REPL.

    This prevents control-sequence leakage (for example ``^?``) when users
    press Backspace/Delete in terminals that emit different key codes.
    """
    try:
        import readline
    except Exception:
        return False

    # Try to enable completion with shell-local symbols.
    with contextlib.suppress(Exception):
        import rlcompleter

        readline.set_completer(rlcompleter.Completer(namespace).complete)

    # GNU readline and libedit accept different subsets of bindings.
    for binding in (
        "tab: complete",
        '"\\C-?": backward-delete-char',
        '"\\C-h": backward-delete-char',
        '"\\e[3~": delete-char',
    ):
        with contextlib.suppress(Exception):
            readline.parse_and_bind(binding)

    return True


def cmd_shell(
    database_url: str = "sqlite:///db.sqlite3",
    verbose: bool = False,
) -> None:
    """
    Launch an async REPL with models and database pre-loaded.

    All discovered Model subclasses, Q query builder, and ModelRegistry
    are available in the shell namespace.
    """
    click.echo(click.style("Aquilia Model Shell", fg="cyan", bold=True))
    click.echo(click.style("Type 'exit()' or Ctrl+D to quit.\n", dim=True))

    async def _setup():
        from aquilia.db import AquiliaDatabase, set_database

        db = AquiliaDatabase(database_url)
        await db.connect()
        set_database(db)

        # Wire models to database
        try:
            from aquilia.models.base import ModelRegistry

            ModelRegistry.set_database(db)
        except ImportError:
            pass

        models = _discover_models(verbose=verbose)
        return db, models

    try:
        import code

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        db, models = loop.run_until_complete(_setup())

        # Build namespace
        ns = {
            "db": db,
            "asyncio": asyncio,
            "loop": loop,
        }

        # Add Model classes
        model_names = []
        for model_cls in models:
            ns[model_cls.__name__] = model_cls
            model_names.append(model_cls.__name__)

        # Add Q and ModelRegistry
        try:
            from aquilia.models.base import ModelRegistry, Q

            ns["Q"] = Q
            ns["ModelRegistry"] = ModelRegistry
        except ImportError:
            pass

        model_display = ", ".join(model_names) or "(none)"
        click.echo(f"Models loaded: {model_display}")
        click.echo(f"Database: {database_url}")
        click.echo(
            click.style(
                "Tip: Use loop.run_until_complete(Product.get(pk=1)) for async ops\n",
                dim=True,
            )
        )

        _configure_shell_line_editor(ns)

        code.interact(local=ns, banner="")

        loop.run_until_complete(db.disconnect())
        loop.close()
    except (ImportError, Exception) as e:
        click.echo(click.style(f"Shell error: {e}", fg="red"))


# ── New Commands ──────────────────────────────────────────────────────────────


def cmd_inspectdb(
    database_url: str = "sqlite:///db.sqlite3",
    tables: list[str] | None = None,
    verbose: bool = False,
) -> str:
    """
    Introspect an existing database and generate Model classes.

    Reads the database schema and emits Python Model definitions
    that can be pasted into a models.py file.

    Args:
        database_url: Database connection URL
        tables: Specific tables to inspect (None = all)
        verbose: Verbose output

    Returns:
        Generated Python source code
    """

    async def _run() -> str:
        from aquilia.db import AquiliaDatabase

        db = AquiliaDatabase(database_url)
        await db.connect()

        try:
            # Get table list
            if database_url.startswith("sqlite"):
                rows = await db.fetch_all(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
                )
                all_tables = [row["name"] for row in rows]
            else:
                all_tables = []

            if tables:
                all_tables = [t for t in all_tables if t in tables]

            if not all_tables:
                return "# No tables found in database."

            lines = [
                '"""',
                "Auto-generated Model definitions from database introspection.",
                "",
                f"Database: {database_url}",
                '"""',
                "",
                "from aquilia.models import Model",
                "from aquilia.models.fields import (",
                "    CharField, IntegerField, FloatField, BooleanField,",
                "    TextField, DateTimeField, DecimalField, BigIntegerField,",
                "    BinaryField, JSONField,",
                ")",
                "",
                "",
            ]

            for table_name in all_tables:
                if verbose:
                    click.echo(click.style(f"  Inspecting: {table_name}", fg="blue"))

                # Get table schema
                if database_url.startswith("sqlite"):
                    col_rows = await db.fetch_all(f'PRAGMA table_info("{table_name}")')
                else:
                    col_rows = []

                class_name = _table_to_class_name(table_name)
                lines.append(f"class {class_name}(Model):")
                lines.append(f'    table = "{table_name}"')
                lines.append("")

                for col in col_rows:
                    col_name = col["name"]
                    col_type = col["type"].upper()
                    notnull = col["notnull"]
                    pk = col["pk"]
                    default_val = col["dflt_value"]

                    if pk:
                        # Skip auto-PK -- Model adds it automatically
                        continue

                    field_type, field_args = _sql_type_to_field(col_type, notnull, default_val)
                    lines.append(f"    {col_name} = {field_type}({field_args})")

                lines.append("")
                lines.append("    class Meta:")
                lines.append(f'        verbose_name = "{class_name}"')
                lines.append("")
                lines.append("")

            return "\n".join(lines)
        finally:
            await db.disconnect()

    return asyncio.run(_run())


def cmd_showmigrations(
    migrations_dir: str = "migrations",
    database_url: str = "sqlite:///db.sqlite3",
    verbose: bool = False,
) -> list[dict]:
    """
    Show all migrations and their applied status against the database.

    Connects to the real database to check the aquilia_migrations tracking
    table.  Falls back to a file-only listing when the DB doesn't exist or
    the tracking table hasn't been created yet.

    Returns:
        List of dicts with keys: name, file, applied
    """

    migrations_path = Path(migrations_dir)

    if not migrations_path.is_dir():
        click.echo(click.style(f"No migrations directory: {migrations_dir}", fg="yellow"))
        return []

    # Collect on-disk migration files
    files = sorted(p for p in migrations_path.glob("*.py") if not p.name.startswith("_"))

    if not files:
        click.echo(click.style("  No migrations found.", fg="yellow"))
        return []

    # Try to get applied set from the database
    applied_set: set[str] = set()

    async def _fetch_applied() -> set[str]:
        from aquilia.db import AquiliaDatabase

        db = AquiliaDatabase(database_url)
        try:
            await db.connect()
            return set(await MigrationExecutor(db).applied_revisions())
        except Exception:
            return set()
        finally:
            with contextlib.suppress(Exception):
                await db.disconnect()

    with contextlib.suppress(Exception):
        applied_set = asyncio.run(_fetch_applied())

    results: list[dict] = []
    for pyf in files:
        name = pyf.stem
        # The tracking table stores revisions, not filenames, so match on the
        # revision parsed out of the filename rather than on the stem.
        is_applied = revision_from_path(pyf) in applied_set
        info = {
            "name": name,
            "file": str(pyf),
            "applied": is_applied,
        }
        results.append(info)
        marker = click.style("[X]", fg="green") if is_applied else click.style("[ ]", fg="yellow")
        click.echo(f"  {marker} {name}")

    return results


def cmd_sqlmigrate(
    migration_name: str,
    migrations_dir: str = "migrations",
    verbose: bool = False,
    database: str | None = None,
    dialect: str | None = None,
) -> str | None:
    """
    Display the SQL statements for a specific migration.

    Operations are compiled against the migration's own predecessor state, so
    an ``AlterField`` shows the SQL it would really emit rather than SQL derived
    from the current models. For a migration whose operations cannot be
    compiled, the raw source is shown instead.

    Args:
        migration_name: Name of the migration file (without .py)
        migrations_dir: Directory containing migration files
        database: Database alias -- unused today, reserved for multi-db
        dialect: Target SQL dialect. Defaults to ``sqlite``; pass the dialect the
            migration will really run against to see backend-specific DDL.

    Returns:
        SQL string or None
    """

    migrations_path = Path(migrations_dir)
    target = migrations_path / f"{migration_name}.py"

    if not target.is_file():
        # Try partial match
        candidates = list(migrations_path.glob(f"*{migration_name}*.py"))
        if len(candidates) == 1:
            target = candidates[0]
        elif len(candidates) > 1:
            click.echo(click.style(f"Ambiguous: {[c.stem for c in candidates]}", fg="yellow"))
            return None
        else:
            click.echo(click.style(f"Migration not found: {migration_name}", fg="red"))
            return None

    # Compile the migration's operations against the state its predecessors left
    # behind. Anything that fails to compile falls through to the raw source.
    try:
        from aquilia.models.migration import MigrationEngine
        from aquilia.models.migration.backends import get_backend
        from aquilia.models.migration.executor import compile_operations
        from aquilia.models.migration.serializer import load_migration_module

        node = load_migration_module(target)
        engine = MigrationEngine(migrations_dir)
        graph = engine.load_graph()
        # State before this migration: everything ordered ahead of it.
        order = graph.order()
        predecessors = order[: order.index(node.revision)] if node.revision in order else ()
        state = engine.state_for(predecessors)

        statements = compile_operations(node.operations, state, get_backend(dialect or "sqlite"))
        if statements:
            body = "\n".join(f"{statement.sql};" for statement in statements)
            output = f"-- SQL for migration: {target.stem} ({dialect or 'sqlite'})\n\n{body}"
            click.echo(output)
            return output
    except Exception as exc:
        if verbose:
            click.echo(click.style(f"  Could not compile operations: {exc}", fg="yellow"))

    click.echo(click.style(f"-- Migration: {target.stem}", fg="cyan"))
    source = target.read_text(encoding="utf-8")
    click.echo(source)
    return source


def cmd_db_status(
    database_url: str = "sqlite:///db.sqlite3",
    verbose: bool = False,
) -> dict:
    """
    Show database status -- tables, row counts, schema details.

    Returns:
        Dict with database status information
    """

    async def _run() -> dict:
        from aquilia.db import AquiliaDatabase

        db = AquiliaDatabase(database_url)
        await db.connect()

        try:
            status = {
                "url": database_url,
                "tables": [],
                "total_tables": 0,
            }

            if database_url.startswith("sqlite"):
                rows = await db.fetch_all(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
                )
                for row in rows:
                    table_name = row["name"]
                    count_row = await db.fetch_one(f'SELECT COUNT(*) as cnt FROM "{table_name}"')
                    count = count_row["cnt"] if count_row else 0

                    col_rows = await db.fetch_all(f'PRAGMA table_info("{table_name}")')
                    col_count = len(col_rows)

                    table_info = {
                        "name": table_name,
                        "rows": count,
                        "columns": col_count,
                    }
                    status["tables"].append(table_info)

                    # Display
                    row_str = click.style(f"{count:>8} rows", fg="cyan")
                    col_str = click.style(f"{col_count} columns", dim=True)
                    click.echo(f"  {table_name:<30} {row_str}  ({col_str})")

                status["total_tables"] = len(status["tables"])

            click.echo(
                click.style(
                    f"\n  Total: {status['total_tables']} table(s), {sum(t['rows'] for t in status['tables'])} row(s)",
                    fg="green",
                    bold=True,
                )
            )

            return status
        finally:
            await db.disconnect()

    return asyncio.run(_run())


# ── Internal Helpers ──────────────────────────────────────────────────────────


def _table_to_class_name(table_name: str) -> str:
    """Convert a table name to a PascalCase class name."""
    # users → User, order_items → OrderItem
    parts = table_name.replace("-", "_").split("_")
    return "".join(part.capitalize() for part in parts if part)


def _sql_type_to_field(col_type: str, notnull: int, default_val: str | None) -> tuple:
    """Map an SQL column type to an Aquilia field type + args."""
    args: list[str] = []

    if not notnull:
        args.append("null=True")
    if default_val is not None and default_val not in ("NULL", ""):
        args.append(f"default={default_val}")

    col_upper = col_type.upper()

    if "INT" in col_upper:
        if "BIGINT" in col_upper:
            return "BigIntegerField", ", ".join(args)
        return "IntegerField", ", ".join(args)
    elif "CHAR" in col_upper or "VARCHAR" in col_upper:
        # Extract max_length from VARCHAR(N)
        import re

        m = re.search(r"\((\d+)\)", col_type)
        if m:
            args.insert(0, f"max_length={m.group(1)}")
        else:
            args.insert(0, "max_length=255")
        return "CharField", ", ".join(args)
    elif "TEXT" in col_upper or "CLOB" in col_upper:
        return "TextField", ", ".join(args)
    elif "REAL" in col_upper or "FLOAT" in col_upper or "DOUBLE" in col_upper:
        return "FloatField", ", ".join(args)
    elif "DECIMAL" in col_upper or "NUMERIC" in col_upper:
        return "DecimalField", ", ".join(args)
    elif "BOOL" in col_upper:
        return "BooleanField", ", ".join(args)
    elif "BLOB" in col_upper:
        return "BinaryField", ", ".join(args)
    elif "DATETIME" in col_upper or "TIMESTAMP" in col_upper:
        return "DateTimeField", ", ".join(args)
    elif "JSON" in col_upper:
        return "JSONField", ", ".join(args)
    else:
        return "CharField", "max_length=255" + (", " + ", ".join(args) if args else "")


# ── New Database Commands ───────────────────────────────────────────────────


def cmd_history(
    database_url: str = "sqlite:///db.sqlite3",
    migrations_dir: str = "migrations",
    verbose: bool = False,
) -> list[dict]:
    """Show migration history with application timestamps and checksums."""

    async def _run():
        from aquilia.db import AquiliaDatabase

        db = AquiliaDatabase(database_url)
        await db.connect()
        try:
            records = await MigrationExecutor(db).applied_records()
            if not records:
                click.echo(click.style("No migrations have been applied yet.", fg="yellow"))
                return []

            click.echo(click.style("Migration History:", fg="cyan", bold=True))
            click.echo(f"{'Revision':<18} | {'Slug':<40} | {'Applied At':<25} | {'Checksum':<10}")
            click.echo("-" * 101)
            for rec in records:
                applied_str = str(rec.applied_at)[:19] if rec.applied_at else "Unknown"
                click.echo(f"{rec.revision:<18} | {rec.slug:<40} | {applied_str:<25} | {rec.checksum:<10}")
            return [
                {
                    "revision": rec.revision,
                    "slug": rec.slug,
                    "checksum": rec.checksum,
                    "applied_at": str(rec.applied_at),
                }
                for rec in records
            ]
        finally:
            await db.disconnect()

    return asyncio.run(_run())


def parse_timestamp(ts_str: str) -> datetime.datetime:
    import datetime

    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d",
    ):
        try:
            return datetime.datetime.strptime(ts_str, fmt).replace(tzinfo=datetime.timezone.utc)
        except ValueError:
            continue
    raise ValueError(f"Could not parse timestamp: {ts_str}")


def normalize_db_timestamp(ts: Any) -> datetime.datetime:
    import datetime

    if isinstance(ts, datetime.datetime):
        if ts.tzinfo is None:
            return ts.replace(tzinfo=datetime.timezone.utc)
        return ts.astimezone(datetime.timezone.utc)
    if isinstance(ts, str):
        cleaned = ts.replace("Z", "").replace(" ", "T")
        for fmt in (
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
        ):
            try:
                return datetime.datetime.strptime(cleaned, fmt).replace(tzinfo=datetime.timezone.utc)
            except ValueError:
                continue
    return datetime.datetime.now(datetime.timezone.utc)


def cmd_rollback(
    database_url: str = "sqlite:///db.sqlite3",
    migrations_dir: str = "migrations",
    target: str | None = None,
    step: int | None = None,
    timestamp: str | None = None,
    fake: bool = False,
    plan: bool = False,
    verbose: bool = False,
) -> list[str]:
    """Roll back migrations by target revision, step count, or timestamp.

    Args:
        database_url: Database to roll back.
        migrations_dir: Directory holding the migration files.
        target: Roll back everything applied after this revision. ``"zero"``
            rolls back everything.
        step: Roll back this many migrations from the most recent.
        timestamp: Roll back everything applied after this time.
        fake: Update the tracking table without executing any SQL.
        plan: Show what would run without executing it.
        verbose: Print per-migration diagnostics.

    Returns:
        The revisions that were rolled back.

    Raises:
        click.ClickException: If no rollback target can be determined, or the
            requested target is not among the applied migrations.
    """

    async def _run() -> list[str]:
        from aquilia.db import AquiliaDatabase

        db = AquiliaDatabase(database_url)
        await db.connect()
        try:
            engine = MigrationEngine(migrations_dir)
            status = await engine.status(db)
            applied = list(status.applied)

            if not applied:
                click.echo(click.style("No applied migrations found to rollback.", fg="yellow"))
                return []

            final_target = _resolve_rollback_target(applied, target, step, timestamp)
            if final_target is None:
                raise click.ClickException("Could not determine rollback target.")
            if final_target != "zero" and final_target not in applied:
                raise click.ClickException(f"Target '{final_target}' is not in applied migrations.")

            if plan:
                click.echo(click.style(f"-- Rollback Plan to target: '{final_target}' (dry-run):", fg="cyan"))
                statements = await engine.plan(db, target=final_target)
                if not statements:
                    click.echo("No migrations would be rolled back.")
                    return []
                for statement in statements:
                    if statement.destructive:
                        click.echo(click.style(f"-- DESTRUCTIVE: {statement.description}", fg="red"))
                    click.echo(click.style(f"  {statement.sql}", dim=True))
                return []

            before = set(applied)
            results = await engine.migrate(db, target=final_target, fake=fake)
            after = set((await engine.status(db)).applied)
            rolled_back = [revision for revision in applied if revision in before - after]

            action = "Faked rollback of" if fake else "Rolled back"
            if rolled_back:
                click.echo(
                    click.style(
                        f"{action} {len(rolled_back)} migration(s) to target '{final_target}'",
                        fg="green",
                    )
                )
            else:
                click.echo(click.style("Nothing to rollback.", fg="yellow"))

            if verbose:
                for result in results:
                    for note in result.diagnostics:
                        click.echo(click.style(f"  {note}", dim=True))

            return rolled_back
        finally:
            await db.disconnect()

    return asyncio.run(_run())


def _resolve_rollback_target(
    applied: list[str],
    target: str | None,
    step: int | None,
    timestamp: str | None,
) -> str | None:
    """Determine which revision to roll back to.

    Exactly one of *target*, *step*, or *timestamp* selects the destination;
    when none is given, a single migration is rolled back.

    Args:
        applied: Applied revisions, in application order.
        target: An explicit target revision, or ``"zero"``.
        step: Number of migrations to reverse from the most recent.
        timestamp: Roll back everything applied after this time.

    Returns:
        The target revision, or ``"zero"`` to reverse everything.

    Raises:
        click.ClickException: If *step* is not positive, or *timestamp* cannot
            be parsed.
    """
    if target is not None:
        return target

    if step is not None:
        if step <= 0:
            raise click.ClickException("Step count must be greater than 0.")
        if step >= len(applied):
            return "zero"
        return applied[len(applied) - step - 1]

    if timestamp is not None:
        try:
            target_time = parse_timestamp(timestamp)
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
        resolved = "zero"
        for revision in applied:
            revision_time = normalize_db_timestamp(revision.split("_", 2)[0] + "_" + revision.split("_", 2)[1])
            if revision_time is not None and revision_time <= target_time:
                resolved = revision
        return resolved

    return "zero" if len(applied) == 1 else applied[-2]


def cmd_check(
    database_url: str = "sqlite:///db.sqlite3",
    migrations_dir: str = "migrations",
    verbose: bool = False,
) -> bool:
    """Validate migration integrity, naming conventions, and checksums."""

    async def _run() -> bool:
        from aquilia.db import AquiliaDatabase

        db = AquiliaDatabase(database_url)
        await db.connect()
        try:
            engine = MigrationEngine(migrations_dir)
            click.echo(click.style("Checking migration system health...", fg="cyan", bold=True))

            mdir = Path(migrations_dir)
            if not mdir.exists():
                click.echo(click.style("  [OK] No migrations directory exists yet.", fg="green"))
                return True

            migration_files = sorted(mdir.glob("*.py"))
            invalid_names = []
            rev_map = {}
            for path in migration_files:
                if path.name.startswith("__"):
                    continue
                rev = revision_from_path(path)
                if not rev or rev == path.stem:
                    invalid_names.append(path.name)
                else:
                    if rev in rev_map:
                        rev_map[rev].append(path.name)
                    else:
                        rev_map[rev] = [path.name]

            passed = True
            if invalid_names:
                click.secho(
                    "  [ERROR] Invalid migration naming format (should be YYYYMMDD_HHMMSS_slug.py):",
                    fg="red",
                    bold=True,
                )
                for name in invalid_names:
                    click.echo(f"    - {name}")
                passed = False
            else:
                click.echo(click.style("  [OK] Migration file naming conventions look good.", fg="green"))

            duplicates = {rev: files for rev, files in rev_map.items() if len(files) > 1}
            if duplicates:
                click.secho("  [ERROR] Conflicting/duplicate migration revisions found:", fg="red", bold=True)
                for rev, files in duplicates.items():
                    click.echo(f"    - Revision {rev} is defined in multiple files: {', '.join(files)}")
                passed = False
            else:
                click.echo(click.style("  [OK] No revision conflicts detected.", fg="green"))

            mismatches = await engine.verify_checksums(db)
            if mismatches:
                click.secho("  [ERROR] Migration integrity/checksum verification failed:", fg="red", bold=True)
                for m in mismatches:
                    click.echo(f"    - Revision {m['revision']}: {m['reason']}")
                passed = False
            else:
                click.echo(click.style("  [OK] All applied migration checksums verified successfully.", fg="green"))

            if passed:
                click.secho("\nMigration health check PASSED.", fg="green", bold=True)
            else:
                click.secho(
                    "\nMigration health check FAILED. Please resolve the issues highlighted above.", fg="red", bold=True
                )
            return passed
        finally:
            await db.disconnect()

    return asyncio.run(_run())


def cmd_diff(
    database_url: str = "sqlite:///db.sqlite3",
    migrations_dir: str = "migrations",
    compare: str = "models",
    verbose: bool = False,
) -> bool:
    """Report schema drift between the live database and the models or snapshot.

    Introspects the database into a :class:`ProjectState` and diffs it against
    the target state, then prints the operations that would close the gap. Those
    are the same operations ``makemigrations`` would emit, so the report says
    what to *do* about the drift rather than only that it exists.

    Args:
        database_url: Database to introspect.
        migrations_dir: Where the state snapshot lives, for ``compare="snapshot"``.
        compare: ``"models"`` to diff against the workspace models,
            ``"snapshot"`` to diff against the recorded snapshot.
        verbose: Print per-model discovery detail.

    Returns:
        ``True`` when the database matches the target, ``False`` on drift or when
        the comparison could not be made.
    """

    models = _discover_models(verbose=verbose, ignore_errors=True)

    async def _run() -> bool:
        from aquilia.db import AquiliaDatabase

        db = AquiliaDatabase(database_url)
        await db.connect()
        try:
            click.echo(click.style(f"Computing schema diff ({compare} vs database)...", fg="cyan"))
            live = await ProjectState.from_database(db, model_classes=models)

            if compare == "models":
                if not models:
                    click.secho("No models found in the workspace code to compare.", fg="yellow")
                    return False
                target = ProjectState.from_models(models)
            else:
                engine = MigrationEngine(migrations_dir)
                if not engine.snapshot_path.exists():
                    click.secho(f"No schema snapshot file found at {engine.snapshot_path}.", fg="yellow")
                    return False
                target = engine.load_snapshot()
                if not target.tables:
                    click.secho("Schema snapshot is empty -- nothing to compare against.", fg="yellow")
                    return False

            # Rename inference is off: a rename is indistinguishable from a
            # drop-plus-add when one side was introspected, and guessing wrong
            # here would report data-preserving drift as destructive.
            operations = detect_changes(live, target, infer_renames=False)

            if not operations:
                click.secho("Database and schema are in sync. No drift detected.", fg="green", bold=True)
                return True

            click.secho(f"Drift detected -- {len(operations)} change(s) needed:\n", fg="yellow", bold=True)
            click.echo(click.style("--- database (active)", fg="red", bold=True))
            click.echo(click.style("+++ schema (target)", fg="green", bold=True))
            click.echo()
            for operation in operations:
                click.echo(f"  {click.style('+', fg='green')} {operation.describe()}")
            click.echo()
            click.secho(
                "Run `aq db makemigrations` to record these changes as a migration.",
                dim=True,
            )
            return False
        finally:
            await db.disconnect()

    return asyncio.run(_run())


def cmd_seed(
    database_url: str = "sqlite:///db.sqlite3",
    seed_file: str | None = None,
    verbose: bool = False,
) -> None:
    """Seed the database using a Python script."""
    import importlib.util
    import inspect

    seed_path = None
    if seed_file:
        p = Path(seed_file)
        if p.is_file():
            seed_path = p
    else:
        for candidate in ("seeds.py", "db/seeds.py"):
            p = Path.cwd() / candidate
            if p.is_file():
                seed_path = p
                break

    if not seed_path:
        click.echo("No seed script found. Creating template seeds.py at workspace root...")
        template = (
            '"""\nAquilia Database Seeds.\n"""\n\n'
            "import asyncio\n"
            "# from modules.products.models import Product\n\n"
            "async def seed(db):\n"
            '    """Write database seeding logic here."""\n'
            '    click_echo = __import__("click").echo\n'
            '    click_echo("Seeding database...")\n'
            "    # Example:\n"
            '    # await Product.create(name="Gizmo", price=9.99)\n'
            '    click_echo("Seeding completed successfully!")\n'
        )
        Path("seeds.py").write_text(template, encoding="utf-8")
        click.secho("Created template seeds.py. Edit it to define seeds, then run `aq db seed`.", fg="green")
        return

    click.echo(f"Running seed script: {seed_path}")

    async def _run():
        from aquilia.db import AquiliaDatabase, set_database

        db = AquiliaDatabase(database_url)
        await db.connect()
        set_database(db)

        try:
            ModelRegistry.set_database(db)
        except Exception:
            pass
        _discover_models(verbose=verbose, ignore_errors=True)

        try:
            spec = importlib.util.spec_from_file_location("aquilia_seeds", seed_path)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)

                func = getattr(mod, "seed", getattr(mod, "run", None))
                if func is None:
                    raise click.ClickException("Seed file must define a `seed(db)` or `run(db)` function.")

                if inspect.iscoroutinefunction(func):
                    await func(db)
                else:
                    func(db)
                click.secho("Seeding complete.", fg="green", bold=True)
            else:
                raise click.ClickException(f"Failed to load seed file: {seed_path}")
        except Exception as e:
            import traceback

            click.secho(f"Error during seeding:\n{traceback.format_exc()}", fg="red")
            raise click.ClickException(f"Seeding failed: {e}")
        finally:
            await db.disconnect()

    asyncio.run(_run())


def cmd_reset(
    database_url: str = "sqlite:///db.sqlite3",
    migrations_dir: str = "migrations",
    verbose: bool = False,
    yes: bool = False,
) -> None:
    """Reset the database: drop all tables and re-apply all migrations."""
    if not yes:
        click.confirm(
            click.style(
                "WARNING: This will drop ALL tables in the database. Are you sure?",
                fg="red",
                bold=True,
            ),
            abort=True,
        )

    async def _run():
        from aquilia.db import AquiliaDatabase

        db = AquiliaDatabase(database_url)
        await db.connect()
        try:
            dialect = db.dialect
            tables = await db.get_tables()
            tables = [t for t in tables if not t.startswith("sqlite_")]

            if tables:
                click.echo(f"Dropping {len(tables)} table(s)...")
                async with db.transaction():
                    if dialect == "sqlite":
                        await db.execute("PRAGMA foreign_keys = OFF;")
                    elif dialect == "mysql":
                        await db.execute("SET FOREIGN_KEY_CHECKS = 0;")

                    for table in tables:
                        if verbose:
                            click.echo(f"  Dropping table: {table}")
                        if dialect == "postgresql":
                            await db.execute(f'DROP TABLE "{table}" CASCADE;')
                        else:
                            await db.execute(f'DROP TABLE "{table}";')

                    if dialect == "sqlite":
                        await db.execute("PRAGMA foreign_keys = ON;")
                    elif dialect == "mysql":
                        await db.execute("SET FOREIGN_KEY_CHECKS = 1;")
                click.secho("All tables dropped successfully.", fg="green")
            else:
                click.echo("No tables found to drop.")

            click.echo("Re-applying all migrations...")
            # Dropping the tables also dropped the tracking table, so every
            # migration is pending again. When the tracking table survived (a
            # dialect where the drop was skipped), its rows must be cleared --
            # otherwise `migrate` sees nothing pending and leaves an empty
            # database that reports itself as fully migrated.
            engine = MigrationEngine(migrations_dir)
            remaining = await db.get_tables()
            if "aquilia_migrations" in remaining:
                await db.execute('DELETE FROM "aquilia_migrations"')
            results = await engine.migrate(db)
            click.secho(
                f"Applied {len(results)} migration(s). Database reset complete.",
                fg="green",
                bold=True,
            )
        finally:
            await db.disconnect()

    asyncio.run(_run())


def cmd_flush(
    database_url: str = "sqlite:///db.sqlite3",
    verbose: bool = False,
    yes: bool = False,
) -> None:
    """Flush all data from tables (excluding tracking tables) without dropping schema."""
    if not yes:
        click.confirm(
            click.style(
                "WARNING: This will delete ALL data in all tables. The schema will be kept. Are you sure?",
                fg="red",
                bold=True,
            ),
            abort=True,
        )

    async def _run():
        from aquilia.db import AquiliaDatabase

        db = AquiliaDatabase(database_url)
        await db.connect()
        try:
            dialect = db.dialect
            tables = await db.get_tables()
            tables = [t for t in tables if not t.startswith("sqlite_") and t != "aquilia_migrations"]

            if not tables:
                click.echo("No user tables found to flush.")
                return

            click.echo(f"Flushing data from {len(tables)} table(s)...")

            if dialect == "sqlite":
                async with db.transaction():
                    await db.execute("PRAGMA foreign_keys = OFF;")
                    for table in tables:
                        if verbose:
                            click.echo(f"  Truncating (delete) table: {table}")
                        await db.execute(f'DELETE FROM "{table}";')
                        try:
                            await db.execute("DELETE FROM sqlite_sequence WHERE name = ?", [table])
                        except Exception:
                            pass
                    await db.execute("PRAGMA foreign_keys = ON;")
            elif dialect == "postgresql":
                table_list = ", ".join(f'"{t}"' for t in tables)
                if verbose:
                    click.echo(f"  Truncating tables with cascade: {table_list}")
                await db.execute(f"TRUNCATE TABLE {table_list} RESTART IDENTITY CASCADE;")
            elif dialect == "mysql":
                async with db.transaction():
                    await db.execute("SET FOREIGN_KEY_CHECKS = 0;")
                    for table in tables:
                        if verbose:
                            click.echo(f"  Truncating table: {table}")
                        await db.execute(f'TRUNCATE TABLE "{table}";')
                    await db.execute("SET FOREIGN_KEY_CHECKS = 1;")
            else:
                async with db.transaction():
                    for table in tables:
                        if verbose:
                            click.echo(f"  Deleting from table: {table}")
                        await db.execute(f'DELETE FROM "{table}";')

            click.secho("Database flushed successfully.", fg="green", bold=True)
        finally:
            await db.disconnect()

    asyncio.run(_run())

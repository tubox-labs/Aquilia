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
    use_dsl: bool = True,
    migration_format: str = "surp",
) -> list[Path]:
    """
    Generate migration files from Python Model definitions.

    If use_dsl=True (default), uses the new DSL system with schema
    snapshot diffing and rename detection. Otherwise, uses the legacy
    raw-SQL migration generator.

    Args:
        migration_format: "surp" (default) for SURP binary format,
                          "python" for human-readable DSL files.

    Returns:
        List of generated migration file paths
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

    if use_dsl:
        # New DSL migration generation with snapshot diffing
        from aquilia.models.migration_gen import generate_dsl_migration

        generated = generate_dsl_migration(
            model_classes=models,
            migrations_dir=migrations_dir,
        )

        if generated is None:
            click.echo(click.style("No model changes detected.", fg="yellow"))
            return []

        # SURP snapshot is now saved by default within generate_dsl_migration
        # No need to write a separate JSON snapshot

        model_names = ", ".join(m.__name__ for m in models)
        click.echo(
            click.style(
                f"Generated DSL migration: {generated.name} ({len(models)} model(s): {model_names})",
                fg="green",
            )
        )
        snap_path = Path(migrations_dir) / "schema_snapshot.surp"
        click.echo(
            click.style(
                f"  Schema snapshot: {snap_path}",
                dim=True,
            )
        )
        return [generated]
    else:
        # Legacy raw-SQL migration generation
        from aquilia.models.migrations import generate_migration_from_models

        generated = generate_migration_from_models(
            model_classes=models,
            migrations_dir=migrations_dir,
        )

        model_names = ", ".join(m.__name__ for m in models)
        click.echo(
            click.style(
                f"Generated migration: {generated.name} ({len(models)} model(s): {model_names})",
                fg="green",
            )
        )
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
    from aquilia.db import AquiliaDatabase
    from aquilia.models.migration_runner import MigrationRunner

    async def _run() -> list[str]:
        db = AquiliaDatabase(database_url)
        await db.connect()
        try:
            runner = MigrationRunner(db, migrations_dir, dialect=db.dialect)

            if plan:
                # Dry-run: just show SQL
                stmts = await runner.plan(target=target)
                if stmts:
                    click.echo(click.style("-- Migration Plan (dry-run):", fg="cyan"))
                    for sql in stmts:
                        click.echo(sql)
                else:
                    click.echo(click.style("No pending migrations.", fg="yellow"))
                return []

            if target:
                revs = await runner.migrate(target=target, fake=fake)
                action = "Faked rollback of" if fake else "Rolled back"
                if revs:
                    click.echo(
                        click.style(
                            f"{action} {len(revs)} migration(s) to {target}",
                            fg="green",
                        )
                    )
                else:
                    click.echo(click.style("Nothing to rollback.", fg="yellow"))
            else:
                revs = await runner.migrate(fake=fake)
                action = "Faked" if fake else "Applied"
                if revs:
                    click.echo(
                        click.style(
                            f"{action} {len(revs)} migration(s)",
                            fg="green",
                        )
                    )
                else:
                    click.echo(click.style("No pending migrations.", fg="yellow"))
            return revs
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

    from aquilia.db import AquiliaDatabase, set_database

    async def _setup():
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
    from aquilia.db import AquiliaDatabase

    async def _run() -> str:
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
    from aquilia.db import AquiliaDatabase
    from aquilia.models.migration_runner import MigrationRunner

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
        db = AquiliaDatabase(database_url)
        try:
            await db.connect()
            runner = MigrationRunner(db, migrations_dir, dialect=db.dialect)
            return set(await runner.get_applied())
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
        is_applied = name in applied_set
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
) -> str | None:
    """
    Display the SQL statements for a specific migration.

    For DSL migrations the operations are compiled to SQL for the
    current dialect (defaults to ``sqlite``).  For legacy migrations,
    SQL is extracted from the source via regex or the raw source is
    displayed.

    Args:
        migration_name: Name of the migration file (without .py)
        migrations_dir: Directory containing migration files
        database: Database alias -- unused today, reserved for multi-db

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

    # Try DSL compilation first
    try:
        from aquilia.models.migration_runner import (
            _build_migration_from_module,
            _extract_revision,
            _load_migration_module,
        )

        rev = _extract_revision(target) or target.stem
        module = _load_migration_module(target, rev)
        if hasattr(module, "operations"):
            migration_obj = _build_migration_from_module(module)
            stmts = migration_obj.compile_upgrade("sqlite")
            if stmts:
                output = f"-- SQL for migration: {target.stem}\n\n"
                output += "\n".join(stmts)
                click.echo(output)
                return output
    except Exception:
        pass

    # Fallback: extract SQL from legacy migration source via regex
    source = target.read_text(encoding="utf-8")

    import re

    sql_statements = re.findall(
        r'(?:execute|executescript)\s*\(\s*["\']+(.*?)["\']+\s*\)',
        source,
        re.DOTALL,
    )
    sql_statements += re.findall(
        r'(?:execute|executescript)\s*\(\s*"""(.*?)"""\s*\)',
        source,
        re.DOTALL,
    )
    sql_statements += re.findall(
        r"(?:execute|executescript)\s*\(\s*'''(.*?)'''\s*\)",
        source,
        re.DOTALL,
    )

    if sql_statements:
        output = f"-- SQL for migration: {target.stem}\n"
        for sql in sql_statements:
            output += f"\n{sql.strip()};\n"
        click.echo(output)
        return output
    else:
        click.echo(click.style(f"-- Migration: {target.stem}", fg="cyan"))
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
    from aquilia.db import AquiliaDatabase

    async def _run() -> dict:
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
    from aquilia.db import AquiliaDatabase
    from aquilia.models.migration_runner import MigrationRunner

    async def _run():
        db = AquiliaDatabase(database_url)
        await db.connect()
        try:
            runner = MigrationRunner(db, migrations_dir, dialect=db.dialect)
            records = await runner.get_applied_records()
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
    """Rollback migrations by target, step count, or timestamp."""
    from aquilia.db import AquiliaDatabase
    from aquilia.models.migration_runner import MigrationRunner

    async def _run() -> list[str]:
        db = AquiliaDatabase(database_url)
        await db.connect()
        try:
            runner = MigrationRunner(db, migrations_dir, dialect=db.dialect)
            applied = await runner.get_applied()

            if not applied:
                click.echo(click.style("No applied migrations found to rollback.", fg="yellow"))
                return []

            final_target = None

            if target is not None:
                final_target = target
            elif step is not None:
                if step <= 0:
                    raise click.ClickException("Step count must be greater than 0.")
                if step >= len(applied):
                    final_target = "zero"
                else:
                    final_target = applied[len(applied) - step - 1]
            elif timestamp is not None:
                try:
                    target_time = parse_timestamp(timestamp)
                except ValueError as e:
                    raise click.ClickException(str(e))

                applied_records = await runner.get_applied_records()
                final_target = "zero"
                for rec in applied_records:
                    rec_time = normalize_db_timestamp(rec.applied_at)
                    if rec_time <= target_time:
                        final_target = rec.revision
            else:
                # Default rollback of 1 step
                if len(applied) == 1:
                    final_target = "zero"
                else:
                    final_target = applied[-2]

            if final_target is None:
                raise click.ClickException("Could not determine rollback target.")

            if plan:
                click.echo(click.style(f"-- Rollback Plan to target: '{final_target}' (dry-run):", fg="cyan"))
                if final_target == "zero":
                    to_rollback = list(reversed(applied))
                else:
                    if final_target not in applied:
                        raise click.ClickException(f"Target '{final_target}' is not in applied migrations.")
                    idx = applied.index(final_target)
                    to_rollback = list(reversed(applied[idx + 1 :]))

                if not to_rollback:
                    click.echo("No migrations would be rolled back.")
                    return []

                for rev in to_rollback:
                    click.echo(f"  - Would rollback migration: {rev}")
                    path = runner._find_migration_file(rev)
                    if path:
                        try:
                            from aquilia.models.migration_runner import (
                                _build_migration_from_module,
                                _load_migration_module,
                            )

                            module = _load_migration_module(path, rev)
                            if hasattr(module, "operations"):
                                migration_obj = _build_migration_from_module(module)
                                stmts = migration_obj.compile_downgrade(db.dialect)
                                for sql in stmts:
                                    click.echo(click.style(f"      {sql}", dim=True))
                        except Exception:
                            pass
                return []

            # Perform rollback
            revs = await runner.migrate(target=final_target, fake=fake)
            action = "Faked rollback of" if fake else "Rolled back"
            if revs:
                click.echo(click.style(f"{action} {len(revs)} migration(s) to target '{final_target}'", fg="green"))
            else:
                click.echo(click.style("Nothing to rollback.", fg="yellow"))
            return revs
        finally:
            await db.disconnect()

    return asyncio.run(_run())


def cmd_check(
    database_url: str = "sqlite:///db.sqlite3",
    migrations_dir: str = "migrations",
    verbose: bool = False,
) -> bool:
    """Validate migration integrity, naming conventions, and checksums."""
    from aquilia.db import AquiliaDatabase
    from aquilia.models.migration_runner import MigrationRunner, _extract_revision

    async def _run() -> bool:
        db = AquiliaDatabase(database_url)
        await db.connect()
        try:
            runner = MigrationRunner(db, migrations_dir, dialect=db.dialect)
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
                rev = _extract_revision(path)
                if not rev:
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

            mismatches = await runner.verify_checksums()
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


def _serialize_snapshot_model_to_lines(model_name: str, model_data: dict) -> list[str]:
    """Serialize snapshot model metadata to a list of Python class lines for diffing."""
    lines = []
    table = model_data.get("table", "")
    lines.append(f"class {model_name}(Model):")
    lines.append(f"    # Table: {table}")

    # Fields
    fields = model_data.get("fields", {})
    # Sort fields alphabetically with 'id' first
    sorted_fields = sorted(fields.keys(), key=lambda k: (0 if k == "id" else 1, k))
    for fld_name in sorted_fields:
        fld = fields[fld_name]
        fld_cls = fld.get("field_class", "Field")
        details = []
        if fld.get("primary_key"):
            details.append("primary_key=True")
        if fld.get("max_length"):
            details.append(f"max_length={fld['max_length']}")
        if fld.get("nullable"):
            details.append("nullable=True")
        if fld.get("unique"):
            details.append("unique=True")

        default = fld.get("default")
        if default is not None:
            details.append(f"default={repr(default)}")

        if fld.get("references"):
            ref = fld["references"]
            details.append(f"to='{ref.get('model')}'")

        lines.append(f"    {fld_name} = {fld_cls}({', '.join(details)})")

    # Indexes
    indexes = model_data.get("indexes", [])
    for idx in sorted(indexes, key=lambda i: i.get("name", "")):
        uniq_str = ", unique=True" if idx.get("unique") else ""
        cols = ", ".join(repr(c) for c in idx.get("columns", []))
        lines.append(f"    # Index: {idx['name']} on [{cols}]{uniq_str}")

    return lines


def cmd_diff(
    database_url: str = "sqlite:///db.sqlite3",
    migrations_dir: str = "migrations",
    compare: str = "models",
    verbose: bool = False,
) -> bool:
    """Compare database vs code models or database vs migration snapshot."""
    from aquilia.db import AquiliaDatabase
    from aquilia.models.schema_snapshot import (
        compute_diff,
        create_snapshot,
        create_snapshot_from_db,
        load_snapshot,
    )

    models = _discover_models(verbose=verbose, ignore_errors=True)

    async def _run() -> bool:
        db = AquiliaDatabase(database_url)
        await db.connect()
        try:
            click.echo(click.style(f"Computing schema diff ({compare} vs database)...", fg="cyan"))
            db_snapshot = await create_snapshot_from_db(db, model_classes=models)

            if compare == "models":
                if not models:
                    click.secho("No models found in the workspace code to compare.", fg="yellow")
                    return False
                target_snapshot = create_snapshot(models)
            else:
                snap_path = Path(migrations_dir) / "schema_snapshot.surp"
                if not snap_path.exists():
                    click.secho(f"No schema snapshot file found at {snap_path}.", fg="yellow")
                    return False
                target_snapshot = load_snapshot(snap_path)
                if not target_snapshot:
                    click.secho("Could not load schema snapshot.", fg="red")
                    return False

            diff = compute_diff(db_snapshot, target_snapshot)

            if not diff.has_changes:
                click.secho("Database and schema are completely in sync! No drift detected.", fg="green", bold=True)
                return True

            click.secho("Drift/Diff detected between database and schema:\n", fg="yellow", bold=True)

            click.echo(click.style("--- database (active)", fg="red", bold=True))
            click.echo(click.style("+++ schema (target)", fg="green", bold=True))
            click.echo()

            import difflib

            # Print added models
            if diff.added_models:
                for m in diff.added_models:
                    new_lines = _serialize_snapshot_model_to_lines(m, target_snapshot["models"][m])
                    diff_lines = list(
                        difflib.unified_diff([], new_lines, n=1000, fromfile="database", tofile="schema", lineterm="")
                    )
                    for line in diff_lines[3:]:
                        if line.startswith("+"):
                            click.echo(click.style(line, fg="green"))
                        elif line.startswith("-"):
                            click.echo(click.style(line, fg="red"))
                        else:
                            click.echo(click.style(line, fg="white"))
                    click.echo()

            # Print removed models
            if diff.removed_models:
                for m in diff.removed_models:
                    old_lines = _serialize_snapshot_model_to_lines(m, db_snapshot["models"][m])
                    diff_lines = list(
                        difflib.unified_diff(old_lines, [], n=1000, fromfile="database", tofile="schema", lineterm="")
                    )
                    for line in diff_lines[3:]:
                        if line.startswith("+"):
                            click.echo(click.style(line, fg="green"))
                        elif line.startswith("-"):
                            click.echo(click.style(line, fg="red"))
                        else:
                            click.echo(click.style(line, fg="white"))
                    click.echo()

            # Print renamed models
            if diff.renamed_models:
                for old, new in diff.renamed_models:
                    old_lines = _serialize_snapshot_model_to_lines(old, db_snapshot["models"][old])
                    new_lines = _serialize_snapshot_model_to_lines(new, target_snapshot["models"][new])
                    diff_lines = list(
                        difflib.unified_diff(
                            old_lines, new_lines, n=1000, fromfile="database", tofile="schema", lineterm=""
                        )
                    )
                    for line in diff_lines[3:]:
                        if line.startswith("+"):
                            click.echo(click.style(line, fg="green"))
                        elif line.startswith("-"):
                            click.echo(click.style(line, fg="red"))
                        else:
                            click.echo(click.style(line, fg="white"))
                    click.echo()

            # Print altered models
            if diff.altered_models:
                for m in diff.altered_models:
                    old_lines = _serialize_snapshot_model_to_lines(m, db_snapshot["models"][m])
                    new_lines = _serialize_snapshot_model_to_lines(m, target_snapshot["models"][m])
                    diff_lines = list(
                        difflib.unified_diff(
                            old_lines, new_lines, n=1000, fromfile="database", tofile="schema", lineterm=""
                        )
                    )
                    for line in diff_lines[3:]:
                        if line.startswith("+"):
                            click.echo(click.style(line, fg="green"))
                        elif line.startswith("-"):
                            click.echo(click.style(line, fg="red"))
                        else:
                            click.echo(click.style(line, fg="white"))
                    click.echo()

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

    from aquilia.db import AquiliaDatabase, set_database
    from aquilia.models.base import ModelRegistry

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

    from aquilia.db import AquiliaDatabase
    from aquilia.models.migration_runner import MigrationRunner

    async def _run():
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
            runner = MigrationRunner(db, migrations_dir, dialect=dialect)
            revs = await runner.migrate()
            click.secho(f"Applied {len(revs)} migration(s). Database reset complete.", fg="green", bold=True)
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

    from aquilia.db import AquiliaDatabase

    async def _run():
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

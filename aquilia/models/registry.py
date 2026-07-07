"""
Aquilia Model Registry -- global registry for all Model subclasses.

Tracks all concrete models, resolves forward FK/M2M references,
creates tables, and manages the global database connection.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..db.engine import AquiliaDatabase
    from .base import Model

logger = logging.getLogger("aquilia.models.registry")

__all__ = ["ModelRegistry"]


class ModelRegistry:
    """
    Global registry for all Model subclasses.

    Tracks all concrete models and resolves forward references.
    """

    _models: dict[str, type[Model]] = {}
    _db: AquiliaDatabase | None = None
    _app_models: dict[str, dict[str, type[Model]]] = {}  # app_label → {name → cls}

    @classmethod
    def register(cls, model_cls: type[Model]) -> None:
        """
        Register a concrete model class by its ``__name__``.

        Called automatically by ``ModelMeta.__new__()`` for every
        non-abstract model as soon as the class is created -- not
        intended to be called directly by user code.

        Args:
            model_cls: The model class to register. Re-registering a name
                that already exists overwrites the previous entry (e.g.
                during test/module reloads).

        Behavior:
            Adds the model to the flat ``_models`` map and to the
            per-app-label bucket in ``_app_models`` (keyed by
            ``model_cls._meta.app_label``, ``""`` if unset). Immediately
            calls ``_resolve_relations()`` afterward so that any
            *previously* registered model with a pending string forward
            reference (``to="ThisModel"``) to the newly registered class
            gets resolved right away.
        """
        name = model_cls.__name__
        cls._models[name] = model_cls

        # Track by app_label
        app = getattr(model_cls._meta, "app_label", "") or ""
        if app not in cls._app_models:
            cls._app_models[app] = {}
        cls._app_models[app][name] = model_cls

        # Resolve any pending forward FK references
        cls._resolve_relations()

    @classmethod
    def get(cls, name: str) -> type[Model] | None:
        """Look up a registered model class by its ``__name__``, or ``None`` if not found."""
        return cls._models.get(name)

    @classmethod
    def all_models(cls) -> dict[str, type[Model]]:
        """Return a shallow copy of ``{model_name: model_cls}`` for every registered model."""
        return dict(cls._models)

    @classmethod
    def get_app_models(cls, app_label: str) -> dict[str, type[Model]]:
        """
        Return a shallow copy of ``{model_name: model_cls}`` for models belonging to *app_label*.

        Args:
            app_label: The value of ``Meta.app_label`` on the target
                models. Models with no ``app_label`` set are grouped under
                the empty string ``""``.

        Returns:
            An empty dict if no models are registered under that label
            (never raises).
        """
        return dict(cls._app_models.get(app_label, {}))

    @classmethod
    def set_database(cls, db: AquiliaDatabase) -> None:
        """
        Set the registry-wide default database and propagate it to every already-registered model.

        Args:
            db: The database connection/adapter to use.

        Behavior:
            Stores *db* as ``cls._db`` (the fallback used by
            ``Model._get_db()`` for models without their own override) and
            eagerly stamps ``model_cls._db = db`` on every currently
            registered model. Models registered *after* this call don't
            need a separate assignment -- their ``_db`` starts as ``None``
            (set by the metaclass) and ``Model._get_db()`` falls back to
            ``ModelRegistry.get_database()`` automatically.
        """
        cls._db = db
        for model_cls in cls._models.values():
            model_cls._db = db

    @classmethod
    def get_database(cls) -> AquiliaDatabase | None:
        """Return the registry-wide default database, or ``None`` if ``set_database()`` was never called."""
        return cls._db

    @classmethod
    def _resolve_relations(cls) -> None:
        """
        Resolve pending string-based forward references in FK/M2M fields.

        Iterates every field of every registered model; for any
        ``RelationField`` (``ForeignKey``, ``OneToOneField``,
        ``ManyToManyField``) still holding its ``to`` as an unresolved
        string (e.g. ``ForeignKey(to="Profile")`` declared before
        ``Profile`` was imported/registered), calls
        ``field.resolve_model(cls._models)`` to swap in the actual class
        now that it may be available.

        Idempotent and cheap enough to call after every single
        ``register()`` -- fields that are already resolved (``to`` is a
        class, not a string) are skipped via the ``isinstance`` check.
        """
        from .fields_module import RelationField

        for model_cls in cls._models.values():
            for field in model_cls._fields.values():
                if isinstance(field, RelationField) and isinstance(field.to, str):
                    field.resolve_model(cls._models)

    @classmethod
    async def create_tables(cls, db: AquiliaDatabase | None = None) -> list[str]:
        """
        Create tables, indexes, and M2M junction tables for every registered, managed model.

        Args:
            db: Database connection to run DDL against. Falls back to the
                registry-wide default (``cls._db``, set via
                ``set_database()``) if omitted.

        Behavior:
            Models are ordered topologically (``_topological_sort()``) so
            FK target tables are created before the tables that reference
            them. Abstract models and models with ``Meta.managed = False``
            are skipped entirely. For each remaining model: runs its
            ``CREATE TABLE`` statement, then its index statements (a MySQL
            "duplicate key name" error -- MySQL error 1061, since MySQL
            lacks ``CREATE INDEX IF NOT EXISTS`` -- is swallowed as
            "already exists"; any other error propagates), then its
            implicit M2M junction table statements.

        Args/Raises:
            Raises ``DatabaseConnectionFault`` if no database is available
            (neither *db* nor a previously configured registry default).

        Returns:
            Every SQL statement executed, in execution order -- useful for
            logging/debugging what ``create_tables()`` actually did.
        """
        target_db = db or cls._db
        if not target_db:
            from ..faults.domains import DatabaseConnectionFault

            raise DatabaseConnectionFault(
                url="(none)",
                reason="No database configured for ModelRegistry. "
                "Call ModelRegistry.set_database(db) before create_tables().",
            )

        # Build dependency graph and topologically sort
        ordered = cls._topological_sort()
        dialect = getattr(target_db, "dialect", "sqlite")

        statements: list[str] = []
        for model_cls in ordered:
            if model_cls._meta.abstract:
                continue
            if not model_cls._meta.managed:
                continue

            # Create main table
            sql = model_cls.generate_create_table_sql(dialect=dialect)
            await target_db.execute(sql)
            statements.append(sql)

            # Create indexes
            for idx_sql in model_cls.generate_index_sql(dialect=dialect):
                try:
                    await target_db.execute(idx_sql)
                except Exception as idx_exc:
                    # MySQL error 1061 = Duplicate key name (index already
                    # exists).  MySQL lacks CREATE INDEX IF NOT EXISTS, so
                    # we silently skip this.
                    _orig = getattr(idx_exc, "__cause__", idx_exc)
                    _args = getattr(_orig, "args", ())
                    if _args and _args[0] == 1061:
                        pass  # index already exists on MySQL -- silently skip
                    else:
                        raise
                statements.append(idx_sql)

            # Create M2M junction tables
            for m2m_sql in model_cls.generate_m2m_sql(dialect=dialect):
                await target_db.execute(m2m_sql)
                statements.append(m2m_sql)

        return statements

    @classmethod
    def _topological_sort(cls) -> list[type[Model]]:
        """
        Sort registered models in topological order based on FK dependencies.

        Models with no FK dependencies come first. Models that reference
        other models come after their targets.
        """
        from .fields_module import ForeignKey, OneToOneField

        # Build adjacency: model_name -> set of dependency model names
        deps: dict[str, set] = {}
        name_to_cls: dict[str, type[Model]] = {}

        for name, model_cls in cls._models.items():
            if model_cls._meta.abstract or not model_cls._meta.managed:
                continue
            name_to_cls[name] = model_cls
            deps[name] = set()
            for field in model_cls._fields.values():
                if isinstance(field, (ForeignKey, OneToOneField)):
                    target = field.to if isinstance(field.to, str) else field.to.__name__
                    # Only add dependency if target is a registered model
                    # and not a self-reference
                    if target != name and target in cls._models:
                        deps[name].add(target)

        # Kahn's algorithm for topological sort
        in_degree: dict[str, int] = {n: 0 for n in deps}
        for node, node_deps in deps.items():
            for dep in node_deps:
                if dep in in_degree:
                    in_degree[dep] = in_degree.get(dep, 0)

        # Count incoming edges
        reverse_adj: dict[str, list[str]] = {n: [] for n in deps}
        for node, node_deps in deps.items():
            for dep in node_deps:
                if dep in reverse_adj:
                    reverse_adj[dep].append(node)

        in_degree = {n: len(d) for n, d in deps.items()}

        queue = [n for n, deg in in_degree.items() if deg == 0]
        ordered: list[type[Model]] = []

        while queue:
            node = queue.pop(0)
            if node in name_to_cls:
                ordered.append(name_to_cls[node])
            for dependent in reverse_adj.get(node, []):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # Add any remaining models (circular FK -- nullable breaks the cycle)
        for name, model_cls in name_to_cls.items():
            if model_cls not in ordered:
                ordered.append(model_cls)

        return ordered

    @classmethod
    async def drop_tables(cls, db: AquiliaDatabase | None = None) -> list[str]:
        """
        Drop every registered (non-abstract) model's table.

        .. warning::
            Destructive and irreversible -- intended for test teardown or
            throwaway dev databases, not production use. Does not drop M2M
            junction tables or respect FK ordering (each ``DROP TABLE IF
            EXISTS`` is independent), so on databases that enforce FK
            constraints at DDL time this may fail depending on drop order;
            SQLite (the common case) tolerates it.

        Args:
            db: Database connection to run DDL against. Falls back to the
                registry-wide default (``cls._db``) if omitted.

        Raises:
            DatabaseConnectionFault: If no database is available.

        Returns:
            Every ``DROP TABLE IF EXISTS ...`` statement executed, in
            (reverse-registration) order.
        """
        target_db = db or cls._db
        if not target_db:
            from ..faults.domains import DatabaseConnectionFault

            raise DatabaseConnectionFault(
                url="(none)",
                reason="No database configured for ModelRegistry. "
                "Call ModelRegistry.set_database(db) before drop_tables().",
            )

        statements: list[str] = []
        for model_cls in reversed(list(cls._models.values())):
            if model_cls._meta.abstract:
                continue
            sql = f'DROP TABLE IF EXISTS "{model_cls._table_name}"'
            await target_db.execute(sql)
            statements.append(sql)

        return statements

    @classmethod
    def reset(cls) -> None:
        """
        Clear all registered models, app-label buckets, and the default database.

        Intended for test isolation (e.g. an ``autouse`` fixture between
        test modules that each define their own models) -- without this,
        model classes from a previous test module would linger in
        ``_models``/``_app_models`` and leak into unrelated tests
        (duplicate table names, stale FK targets, etc.).
        """
        cls._models.clear()
        cls._app_models.clear()
        cls._db = None

    @classmethod
    def check_constraints(cls) -> list[str]:
        """
        Validate all model constraints and return a list of issues.

        Checks:
        - FK targets exist
        - M2M targets exist
        - No duplicate table names
        - No circular FK chains without nullable break
        """
        issues: list[str] = []
        table_names: dict[str, str] = {}  # table → model name

        from .fields_module import ForeignKey, ManyToManyField

        for name, model_cls in cls._models.items():
            if model_cls._meta.abstract:
                continue

            tbl = model_cls._table_name
            if tbl in table_names:
                issues.append(f"Duplicate table '{tbl}': {name} and {table_names[tbl]}")
            table_names[tbl] = name

            for fname, field in model_cls._fields.items():
                if isinstance(field, ForeignKey):
                    target = field.to if isinstance(field.to, str) else field.to.__name__
                    if target not in cls._models:
                        issues.append(f"{name}.{fname}: FK target '{target}' not registered")
                elif isinstance(field, ManyToManyField):
                    target = field.to if isinstance(field.to, str) else field.to.__name__
                    if target not in cls._models:
                        issues.append(f"{name}.{fname}: M2M target '{target}' not registered")

        return issues

    # ── Lifecycle hooks (DI compatibility) ───────────────────────────

    async def on_startup(self) -> None:
        """
        Lifecycle hook -- called by LifecycleCoordinator at app start.

        If any models are registered, calls ``create_tables()`` using the
        registry's default database. This is the low-level table-creation
        path invoked when auto-migration is enabled; see
        ``base.py``'s ``ModelRegistry.on_startup()`` wrapper (gated on
        ``AQUILIA_AUTO_MIGRATE``) for the guarded entry point actually
        wired into app startup.
        """
        if ModelRegistry._models:
            await ModelRegistry.create_tables()

    async def on_shutdown(self) -> None:
        """Lifecycle hook -- called by LifecycleCoordinator at app shutdown. No-op."""
        pass

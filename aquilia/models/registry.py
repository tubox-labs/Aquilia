"""
Aquilia Model Registry -- global thread-safe registry for all Model subclasses.

Tracks all concrete models, resolves forward FK/M2M references,
creates tables, and manages the global database connection with full
thread safety and cache invalidation.
"""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..db.engine import AquiliaDatabase
    from .base import Model

logger = logging.getLogger("aquilia.models.registry")

__all__ = ["ModelRegistry"]


class ModelRegistry:
    """
    Global thread-safe registry for all Model subclasses.

    Tracks all concrete models, resolves pending forward/reverse references,
    manages registry-wide database defaults, and coordinates DDL operations
    such as table creation and teardown.

    Lifecycle:
        1. Class declaration: ``ModelMeta.__new__()`` automatically registers
           non-abstract models via ``ModelRegistry.register(model_cls)``.
        2. Database configuration: ``ModelRegistry.set_database(db)`` binds
           the connection adapter to registered models.
        3. Application startup: ``create_tables()`` or ``on_startup()`` initializes
           database schema in topological dependency order.
        4. Application teardown / testing: ``reset()`` clears all registered
           state and cached relation maps between test runs.

    Execution Order:
        Registration -> Relation Resolution -> DB Assignment -> DDL Execution / Queries.

    Thread Safety:
        All class-level mutations and queries on ``_models``, ``_app_models``, and
        ``_db`` are guarded by an reentrant thread lock (``_lock``).
    """

    _models: dict[str, type[Model]] = {}
    _db: AquiliaDatabase | None = None
    _app_models: dict[str, dict[str, type[Model]]] = {}  # app_label → {name → cls}
    _lock: threading.RLock = threading.RLock()

    @classmethod
    def register(cls, model_cls: type[Model]) -> None:
        """
        Register a concrete model class by its ``__name__``.

        Called automatically by ``ModelMeta.__new__()`` for every non-abstract
        model as soon as the class is created.

        Purpose:
            Add the model class to global lookups, bucket it under its
            ``app_label``, invalidate stale reverse relation caches across
            already-registered models, and resolve pending string foreign keys.

        Lifecycle:
            Executed during module import when model classes are defined.

        Execution Order:
            1. Acquire thread lock.
            2. Update ``_models`` and ``_app_models``.
            3. Invalidate ``_reverse_fk_cache`` and ``_reverse_relation_cache`` on existing models.
            4. Execute ``_resolve_relations()``.

        Parameters:
            model_cls (type[Model]): The concrete model class to register. Re-registering
                a model with an existing name overwrites the previous entry (e.g., during reloads).

        Return Value:
            None.

        Exceptions:
            None.

        Notes:
            Thread-safe. Re-entrant lock avoids deadlocks if nested registrations occur.

        Internal Behaviour:
            Maintains two dictionaries: a flat name -> class map (``_models``) and a
            two-level app_label -> name -> class map (``_app_models``).

        Edge Cases:
            - Duplicate model names overwrite previous registrations.
            - Abstract models are ignored by metaclass callers.

        Examples:
            >>> class User(Model):
            ...     name = CharField(max_length=100)
            >>> ModelRegistry.get("User") is User
            True
        """
        with cls._lock:
            name = model_cls.__name__

            # Invalidate reverse relation caches across all previously registered models
            for existing_cls in cls._models.values():
                if hasattr(existing_cls, "_clear_reverse_relation_caches"):
                    existing_cls._clear_reverse_relation_caches()
                else:
                    existing_cls._reverse_fk_cache = None
                    existing_cls._reverse_relation_cache = None

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
        """
        Look up a registered model class by its ``__name__``.

        Purpose:
            Retrieve a model class from the registry using its name.

        Lifecycle:
            Called at runtime during query building, relation resolution, or contract serialization.

        Execution Order:
            Acquires lock and performs dict lookup.

        Parameters:
            name (str): Unqualified model class name (e.g., ``"User"``).

        Return Value:
            type[Model] | None: Registered model class or None if not registered.

        Exceptions:
            None.

        Notes:
            Thread-safe. Returns shallow reference.

        Internal Behaviour:
            Queries ``cls._models`` under lock.

        Edge Cases:
            Case-sensitive lookup matching ``model_cls.__name__``.

        Examples:
            >>> user_cls = ModelRegistry.get("User")
        """
        with cls._lock:
            return cls._models.get(name)

    @classmethod
    def all_models(cls) -> dict[str, type[Model]]:
        """
        Return a shallow copy of all registered models.

        Purpose:
            Provide a safe snapshot of all currently registered models.

        Lifecycle:
            Called during migration generation, schema snapshotting, and relationship resolution.

        Execution Order:
            Acquires lock and copies ``cls._models``.

        Parameters:
            None.

        Return Value:
            dict[str, type[Model]]: Copy of ``{model_name: model_cls}``.

        Exceptions:
            None.

        Notes:
            Thread-safe. Modifying the returned dict does not affect the registry.

        Internal Behaviour:
            Returns ``dict(cls._models)`` under lock.

        Edge Cases:
            Returns an empty dict if no models are registered.

        Examples:
            >>> models = ModelRegistry.all_models()
        """
        with cls._lock:
            return dict(cls._models)

    @classmethod
    def get_app_models(cls, app_label: str) -> dict[str, type[Model]]:
        """
        Return a shallow copy of models belonging to a specific app_label.

        Purpose:
            Retrieve models grouped under an application namespace (``Meta.app_label``).

        Lifecycle:
            Used during modular app setup, CLI inspection, and admin panel generation.

        Execution Order:
            Acquires lock and copies target app dictionary.

        Parameters:
            app_label (str): Target application label string.

        Return Value:
            dict[str, type[Model]]: Copy of ``{model_name: model_cls}`` for the app.

        Exceptions:
            None.

        Notes:
            Thread-safe. Models with no app_label are stored under ``""``.

        Internal Behaviour:
            Queries ``cls._app_models.get(app_label, {})`` under lock.

        Edge Cases:
            Returns empty dict if app_label is unknown.

        Examples:
            >>> auth_models = ModelRegistry.get_app_models("auth")
        """
        with cls._lock:
            return dict(cls._app_models.get(app_label, {}))

    @classmethod
    def set_database(cls, db: AquiliaDatabase) -> None:
        """
        Set the registry-wide default database connection.

        Purpose:
            Bind an active database connection engine to the registry and propagate
            it to all registered model classes.

        Lifecycle:
            Called during framework initialization (``AquiliaRuntime.configure`` / ``workspace.py``).

        Execution Order:
            1. Acquire thread lock.
            2. Update ``cls._db``.
            3. Iterate all registered models and set ``model_cls._db = db``.

        Parameters:
            db (AquiliaDatabase): Connected database adapter instance.

        Return Value:
            None.

        Exceptions:
            None.

        Notes:
            Thread-safe. Stamped models will default to this database unless overridden.

        Internal Behaviour:
            Updates ``_db`` and propagates to ``cls._models.values()``.

        Edge Cases:
            Passing None is discouraged; use ``reset()`` to clear database state.

        Examples:
            >>> ModelRegistry.set_database(db)
        """
        with cls._lock:
            cls._db = db
            for model_cls in cls._models.values():
                model_cls._db = db

    @classmethod
    def get_database(cls) -> AquiliaDatabase | None:
        """
        Return the registry-wide default database instance.

        Purpose:
            Fetch the default database engine currently registered.

        Lifecycle:
            Invoked by ``Model._get_db()`` when an instance/model has no explicit ``_db`` set.

        Execution Order:
            Acquires lock and returns ``cls._db``.

        Parameters:
            None.

        Return Value:
            AquiliaDatabase | None: Configured database engine or None.

        Exceptions:
            None.

        Notes:
            Thread-safe.

        Internal Behaviour:
            Reads ``cls._db`` under lock.

        Edge Cases:
            Returns None if ``set_database()`` was never called.

        Examples:
            >>> db = ModelRegistry.get_database()
        """
        with cls._lock:
            return cls._db

    @classmethod
    def _resolve_relations(cls) -> None:
        """
        Resolve pending string-based forward references in FK/M2M fields.

        Purpose:
            Resolve lazy string targets (e.g. ``ForeignKey("User")``) into actual
            class references once target models become registered.

        Lifecycle:
            Executed automatically after every model registration.

        Execution Order:
            Iterates through registered models and fields under thread lock.

        Parameters:
            None.

        Return Value:
            None.

        Exceptions:
            None.

        Notes:
            Internal helper. Thread-safe and idempotent.

        Internal Behaviour:
            Calls ``field.resolve_model(cls._models)`` for unresolved fields.

        Edge Cases:
            Unregistered targets remain strings until their class is registered.

        Examples:
            >>> ModelRegistry._resolve_relations()
        """
        from .fields_module import RelationField

        with cls._lock:
            models_snapshot = dict(cls._models)
            for model_cls in models_snapshot.values():
                for field in model_cls._fields.values():
                    if isinstance(field, RelationField) and isinstance(field.to, str):
                        field.resolve_model(models_snapshot)

    @classmethod
    async def create_tables(cls, db: AquiliaDatabase | None = None) -> list[str]:
        """
        Create tables, indexes, and M2M junction tables for all managed models.

        Purpose:
            Execute DDL statements to create database structures in topological order.

        Lifecycle:
            Called during application startup or test setup.

        Execution Order:
            1. Resolve target database connection.
            2. Topologically sort models based on FK relationships.
            3. Execute ``CREATE TABLE``, indexes, and M2M junction tables.

        Parameters:
            db (AquiliaDatabase | None): Optional database engine override.

        Return Value:
            list[str]: Executed DDL SQL statements in order.

        Exceptions:
            DatabaseConnectionFault: Raised if no database engine is configured.

        Notes:
            Async operation. Thread-safe snapshot of models is used.

        Internal Behaviour:
            Iterates topologically sorted models and calls ``target_db.execute()``.

        Edge Cases:
            MySQL error 1061 (duplicate key) on index creation is safely ignored.

        Examples:
            >>> statements = await ModelRegistry.create_tables(db)
        """
        with cls._lock:
            target_db = db or cls._db
            ordered = cls._topological_sort()

        if not target_db:
            from ..faults.domains import DatabaseConnectionFault

            raise DatabaseConnectionFault(
                url="(none)",
                reason="No database configured for ModelRegistry. "
                "Call ModelRegistry.set_database(db) before create_tables().",
            )

        dialect = getattr(target_db, "dialect", "sqlite")
        statements: list[str] = []

        async with target_db.transaction():
            for model_cls in ordered:
                if model_cls._meta.abstract or not model_cls._meta.managed:
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
                        _orig = getattr(idx_exc, "__cause__", idx_exc)
                        _args = getattr(_orig, "args", ())
                        if _args and _args[0] == 1061:
                            pass
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
        Sort registered models topologically based on foreign key dependencies.

        Purpose:
            Ensure target models are created before referencing models in DDL statements.

        Lifecycle:
            Used internally by ``create_tables()``.

        Execution Order:
            Builds dependency DAG using Kahn's algorithm under thread lock.

        Parameters:
            None.

        Return Value:
            list[type[Model]]: Dependency-ordered list of model classes.

        Exceptions:
            None.

        Notes:
            Circular FK dependencies are broken gracefully.

        Internal Behaviour:
            Inspects ``ForeignKey`` and ``OneToOneField`` definitions.

        Edge Cases:
            Self-referencing models do not block topological ordering.
        """
        from .fields_module import ForeignKey, OneToOneField

        with cls._lock:
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
                        if target != name and target in cls._models:
                            deps[name].add(target)

            in_degree: dict[str, int] = {n: len(d) for n, d in deps.items()}
            reverse_adj: dict[str, list[str]] = {n: [] for n in deps}
            for node, node_deps in deps.items():
                for dep in node_deps:
                    if dep in reverse_adj:
                        reverse_adj[dep].append(node)

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

            for name, model_cls in name_to_cls.items():
                if model_cls not in ordered:
                    ordered.append(model_cls)

            return ordered

    @classmethod
    async def drop_tables(cls, db: AquiliaDatabase | None = None) -> list[str]:
        """
        Drop all registered model tables.

        Purpose:
            Teardown database schema for test cleanup or isolated environments.

        Lifecycle:
            Invoked in test suite teardowns.

        Execution Order:
            Iterates registered models in reverse order and executes ``DROP TABLE IF EXISTS``.

        Parameters:
            db (AquiliaDatabase | None): Optional database engine override.

        Return Value:
            list[str]: List of executed ``DROP TABLE`` SQL statements.

        Exceptions:
            DatabaseConnectionFault: If no database is available.

        Notes:
            Destructive action.

        Internal Behaviour:
            Issues DDL for each registered non-abstract model.

        Edge Cases:
            SQLite ignores foreign key drop constraints; database specific behaviors apply.
        """
        with cls._lock:
            target_db = db or cls._db
            models_snapshot = list(cls._models.values())

        if not target_db:
            from ..faults.domains import DatabaseConnectionFault

            raise DatabaseConnectionFault(
                url="(none)",
                reason="No database configured for ModelRegistry. "
                "Call ModelRegistry.set_database(db) before drop_tables().",
            )

        statements: list[str] = []
        for model_cls in reversed(models_snapshot):
            if model_cls._meta.abstract:
                continue
            sql = f'DROP TABLE IF EXISTS "{model_cls._table_name}"'
            await target_db.execute(sql)
            statements.append(sql)

        return statements

    @classmethod
    def reset(cls) -> None:
        """
        Clear all registered models, app-label maps, database engines, and caches.

        Purpose:
            Reset registry state completely for test isolation.

        Lifecycle:
            Called between test executions or suite teardown fixtures.

        Execution Order:
            1. Acquire thread lock.
            2. Invalidate reverse relation caches on existing models.
            3. Clear ``_models``, ``_app_models``, and set ``_db = None``.

        Parameters:
            None.

        Return Value:
            None.

        Exceptions:
            None.

        Notes:
            Thread-safe.

        Internal Behaviour:
            Wipes all registry internal maps.

        Edge Cases:
            Safe to call repeatedly on empty registry.
        """
        with cls._lock:
            for model_cls in cls._models.values():
                if hasattr(model_cls, "_clear_reverse_relation_caches"):
                    model_cls._clear_reverse_relation_caches()
                else:
                    model_cls._reverse_fk_cache = None
                    model_cls._reverse_relation_cache = None
            cls._models.clear()
            cls._app_models.clear()
            cls._db = None

    @classmethod
    def check_constraints(cls) -> list[str]:
        """
        Validate registered models for table name collisions or unresolvable relationships.

        Purpose:
            Perform pre-flight sanity checks on registered model metadata.

        Lifecycle:
            Called during framework validation or CLI diagnostic commands.

        Execution Order:
            Inspects all registered models and fields under thread lock.

        Parameters:
            None.

        Return Value:
            list[str]: List of human-readable issue descriptions (empty if valid).

        Exceptions:
            None.

        Notes:
            Thread-safe read.

        Internal Behaviour:
            Checks duplicate table names and unregistered FK/M2M targets.

        Edge Cases:
            Validates string targets against registered names.
        """
        issues: list[str] = []
        table_names: dict[str, str] = {}

        from .fields_module import ForeignKey, ManyToManyField

        with cls._lock:
            models_snapshot = dict(cls._models)

        for name, model_cls in models_snapshot.items():
            if model_cls._meta.abstract:
                continue

            tbl = model_cls._table_name
            if tbl in table_names:
                issues.append(f"Duplicate table '{tbl}': {name} and {table_names[tbl]}")
            table_names[tbl] = name

            for fname, field in model_cls._fields.items():
                if isinstance(field, ForeignKey):
                    target = field.to if isinstance(field.to, str) else field.to.__name__
                    if target not in models_snapshot:
                        issues.append(f"{name}.{fname}: FK target '{target}' not registered")
                elif isinstance(field, ManyToManyField):
                    target = field.to if isinstance(field.to, str) else field.to.__name__
                    if target not in models_snapshot:
                        issues.append(f"{name}.{fname}: M2M target '{target}' not registered")

        return issues

    async def on_startup(self) -> None:
        """
        Lifecycle hook called at application startup by LifecycleCoordinator.

        Purpose:
            Trigger table creation during application boot if models are present.

        Lifecycle:
            Invoked during ASGI lifespan startup.

        Execution Order:
            Checks for registered models and calls ``create_tables()``.

        Parameters:
            None.

        Return Value:
            None.

        Exceptions:
            DatabaseConnectionFault: If no database engine is configured.

        Notes:
            Async.

        Internal Behaviour:
            Delegates to ``ModelRegistry.create_tables()``.
        """
        if ModelRegistry.all_models():
            await ModelRegistry.create_tables()

    async def on_shutdown(self) -> None:
        """
        Lifecycle hook called at application shutdown by LifecycleCoordinator.

        Purpose:
            Perform cleanup tasks upon app shutdown.

        Lifecycle:
            Invoked during ASGI lifespan shutdown.

        Execution Order:
            No-op by default.

        Parameters:
            None.

        Return Value:
            None.

        Exceptions:
            None.
        """
        pass

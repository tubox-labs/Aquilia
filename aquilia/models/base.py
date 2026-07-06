"""
Aquilia Model Base -- Pure Python, metaclass-driven, async-first ORM.

Async-first model architecture with chainable query syntax.

Usage:
    from aquilia.models import Model
    from aquilia.models.fields import CharField, IntegerField, DateTimeField

    class User(Model):
        table = "users"

        name = CharField(max_length=150)
        email = CharField(max_length=255, unique=True)
        age = IntegerField(null=True)
        created_at = DateTimeField(auto_now_add=True)

        class Meta:
            ordering = ["-created_at"]
            indexes = [
                Index(fields=["email", "name"]),
            ]

    # Aquilia QuerySet API (async-terminal)
    users = await User.objects.filter(active=True).order("-created_at").all()
    user  = await User.objects.get(pk=1)
    count = await User.objects.filter(age__gt=18).count()
    await User.objects.filter(pk=1).update(name="Bob")
"""

from __future__ import annotations

import datetime
import decimal
import hashlib
import json
import logging
import uuid
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
)

from .deletion import (
    OnDeleteHandler,
)
from .fields_module import (
    AutoField,
    BigAutoField,
    CharField,
    Field,
    FieldValidationError,
    ForeignKey,
    ManyToManyField,
    OneToOneField,
)
from .manager import Manager
from .relations import RelatedNotLoaded
from .signals import (
    m2m_changed,
    post_delete,
    post_init,
    post_save,
    pre_delete,
    pre_init,
    pre_save,
)
from .sql_builder import CreateTableBuilder, DeleteBuilder, InsertBuilder, UpdateBuilder

if TYPE_CHECKING:
    from typing_extensions import Self

    from ..db.engine import AquiliaDatabase
    from .manager import RelatedManager

logger = logging.getLogger("aquilia.models")


# ── Model Options -- delegate to options.py ───────────────────────────────────
# Keep this import for backward compatibility; the canonical Options is
# in options.py (imported by metaclass.py).

from .options import Options

# ── Model Registry -- delegate to registry.py ────────────────────────────────
# Keep ModelRegistry importable from base.py for backward compat, but the
# canonical implementation lives in registry.py.
from .registry import ModelRegistry as _CanonicalRegistry


class _ModelRegistryMeta(type):
    """Metaclass for ModelRegistry that forwards attribute access to the canonical registry."""

    @property
    def _models(cls) -> dict[str, type[Model]]:
        return _CanonicalRegistry._models

    @_models.setter
    def _models(cls, value):
        _CanonicalRegistry._models = value

    @property
    def _db(cls):
        return _CanonicalRegistry._db

    @_db.setter
    def _db(cls, value):
        _CanonicalRegistry._db = value

    @property
    def _app_models(cls):
        return _CanonicalRegistry._app_models

    @_app_models.setter
    def _app_models(cls, value):
        _CanonicalRegistry._app_models = value


class ModelRegistry(metaclass=_ModelRegistryMeta):
    """
    Backward-compatible wrapper around registry.ModelRegistry.

    All calls are forwarded to the canonical registry in registry.py.
    Class attributes (_models, _db) are live properties that always
    reflect the canonical registry's state.
    """

    @classmethod
    def register(cls, model_cls: type[Model]) -> None:
        _CanonicalRegistry.register(model_cls)

    @classmethod
    def get(cls, name: str) -> type[Model] | None:
        return _CanonicalRegistry.get(name)

    @classmethod
    def all_models(cls) -> dict[str, type[Model]]:
        return _CanonicalRegistry.all_models()

    @classmethod
    def set_database(cls, db: AquiliaDatabase) -> None:
        _CanonicalRegistry.set_database(db)

    @classmethod
    def get_database(cls) -> AquiliaDatabase | None:
        return _CanonicalRegistry.get_database()

    @classmethod
    def _resolve_relations(cls) -> None:
        _CanonicalRegistry._resolve_relations()

    @classmethod
    async def create_tables(cls, db: AquiliaDatabase | None = None) -> list[str]:
        return await _CanonicalRegistry.create_tables(db)

    @classmethod
    def reset(cls) -> None:
        _CanonicalRegistry.reset()

    # ── Lifecycle hooks (DI compatibility) ───────────────────────────

    async def on_startup(self) -> None:
        """
        Lifecycle hook -- called by LifecycleCoordinator at app start.

        If AQUILIA_AUTO_MIGRATE=1 is set, tables are created automatically.
        Otherwise, the startup guard checks that the DB exists and
        migrations are applied; if not, it fails the startup with a
        yellow warning directing the developer to run migrations.
        """
        import os

        auto = os.environ.get("AQUILIA_AUTO_MIGRATE", "").strip() in ("1", "true", "yes")

        if auto and _CanonicalRegistry._models:
            await _CanonicalRegistry.create_tables()
        # If not auto, the startup guard in server.py handles the check.

    async def on_shutdown(self) -> None:
        pass


# ── Model Metaclass -- delegate to metaclass.py ──────────────────────────────
# Import the canonical ModelMeta for backward compatibility.

from .metaclass import ModelMeta

# ── Q (Query Builder) -- delegate to query.py ─────────────────────────────────
# The canonical Q class lives in query.py. Import it here for backward compat.
from .query import Q

# ── Deferred-field guard (only()/defer()) ─────────────────────────────────────
#
# Fields are plain instance attributes (no descriptors) for zero per-access
# overhead on the common, fully-loaded path -- see fields_module.py. That
# means an instance with an attribute never set falls through to the
# class-level Field object itself (declared in the model body), not a
# Python AttributeError. To make accessing an only()/defer()-excluded field
# raise instead of silently exposing that Field metadata object (or, prior
# to this fix, a silent None indistinguishable from a real NULL), only
# instances that actually have deferred fields get their __class__ swapped
# to a small cached per-model subclass carrying a guarding
# __getattribute__. Fully-loaded instances (the overwhelming common case)
# never pay this cost -- their __class__ is untouched.
_deferred_guard_cache: dict[type, type] = {}


def _deferred_guard_class(model_cls: type) -> type:
    """Return (and cache) a subclass of *model_cls* that raises
    DeferredFieldAccessFault when a deferred field is read."""
    # Avoid double-wrapping if already a guard variant.
    base_cls = getattr(model_cls, "__deferred_guard_base__", model_cls)
    variant = _deferred_guard_cache.get(base_cls)
    if variant is not None:
        return variant

    def _guarded_getattribute(self: Any, name: str) -> Any:
        value = object.__getattribute__(self, name)
        if isinstance(value, Field):
            deferred = object.__getattribute__(self, "__dict__").get("_deferred_fields")
            if deferred and name in deferred:
                from ..faults.domains import DeferredFieldAccessFault

                raise DeferredFieldAccessFault(model=base_cls.__name__, field_name=name)
        return value

    variant = type(
        f"{base_cls.__name__}__Deferred",
        (base_cls,),
        {
            "__getattribute__": _guarded_getattribute,
            "__deferred_guard_base__": base_cls,
            "__deferred_guard__": True,
        },
    )
    _deferred_guard_cache[base_cls] = variant
    return variant


# ── Model Base Class ─────────────────────────────────────────────────────────


class Model(metaclass=ModelMeta):
    """
    Aquilia Model base class -- pure Python, async-first ORM.

    Async-first syntax with chainable query API.

    Define models by subclassing and declaring fields:

        class User(Model):
            table = "users"                # or: table_name = "users"
                                           # or: __tablename__ = "users"

            name = CharField(max_length=150)
            email = EmailField(unique=True)
            active = BooleanField(default=True)
            created_at = DateTimeField(auto_now_add=True)

            class Meta:
                ordering = ["-created_at"]
                get_latest_by = "created_at"

    API -- via objects Manager:
        user  = await User.objects.create(name="Alice", email="alice@test.com")
        user  = await User.objects.get(pk=1)
        users = await User.objects.filter(active=True).order("-created_at").all()
        await User.objects.filter(pk=1).update(name="Bob")
        await User.objects.filter(pk=1).delete()

    API -- Aquilia shorthand (class-level convenience):
        user  = await User.create(name="Alice", email="alice@test.com")
        user  = await User.get(pk=1)
        users = await User.query().filter(active=True).all()

    Relationships:
        posts  = await user.related("posts")   # reverse FK (related_name or default `_set` name)
        author = await post.related("author")   # forward FK
        tags   = await post.related("tags")     # M2M

        # Reverse relations can also be accessed lazily/chainably instead
        # of via the eager-list related() above:
        recent = await user.related_manager("posts").filter(
            published=True,
        ).order("-created_at").first()

    Forward ForeignKey/OneToOneField access without an eager load
    (select_related()/prefetch_related()/related()) returns a
    RelatedNotLoaded sentinel, not the raw stored id -- see
    aquilia.models.relations.RelatedNotLoaded and ForeignKey's docstring
    (aquilia/models/fields_module.py) for the full contract. This is
    deliberate: Aquilia's DB layer is entirely async, and Python's
    descriptor protocol can't run a hidden query synchronously the way
    Django's ForwardManyToOneDescriptor does, so hydration is always
    explicit and awaited.
    """

    # Class-level attributes set by metaclass
    _fields: ClassVar[dict[str, Field]] = {}
    _m2m_fields: ClassVar[dict[str, ManyToManyField]] = {}
    _meta: ClassVar[Options]
    _table_name: ClassVar[str] = ""
    _pk_name: ClassVar[str] = "id"
    _pk_attr: ClassVar[str] = "id"
    _column_names: ClassVar[list[str]] = []
    _attr_names: ClassVar[list[str]] = []
    _non_m2m_fields: ClassVar[list[tuple[str, Field]]] = []
    _col_to_attr: ClassVar[dict[str, tuple[str, Field]]] = {}
    _reverse_fk_cache: ClassVar[list[tuple[type[Model], str, str]] | None] = None
    _reverse_relation_cache: ClassVar[dict[str, tuple[type[Model], str, str, bool]] | None] = None
    _db: ClassVar[AquiliaDatabase | None] = None
    _using_db: str | None = None  # per-instance DB alias

    # Default Manager -- provides User.objects.filter(...) etc.
    # Auto-injected by metaclass if not declared; annotated here (as a
    # declaration-only ClassVar, never actually assigned at this line) so
    # IDEs (Pylance, mypy, PyCharm) resolve .objects without errors.
    #
    # Manager[Self] -- not Manager[Model] -- is what makes every concrete
    # subclass automatically get its own manager/queryset typing: accessing
    # `UserModel.objects` binds Self to UserModel, so `.filter(...)` returns
    # `Q[UserModel]` and `.first()` returns `UserModel | None` with full
    # field autocomplete, without each model needing its own annotation.
    objects: ClassVar[Manager[Self]]

    def __init__(self, **kwargs: Any):
        """Create a model instance (in-memory, not persisted)."""
        pre_init.send_sync(sender=self.__class__, kwargs=kwargs)
        for attr_name, field in self._non_m2m_fields:
            if attr_name in kwargs:
                setattr(self, attr_name, kwargs[attr_name])
            elif field.column_name in kwargs:
                setattr(self, attr_name, kwargs[field.column_name])
            elif field.has_default():
                setattr(self, attr_name, field.get_default())
            else:
                setattr(self, attr_name, None)
        post_init.send_sync(sender=self.__class__, instance=self)

    def __repr__(self) -> str:
        pk_val = getattr(self, self._pk_attr, "?")
        return f"<{self.__class__.__name__} pk={pk_val}>"

    def __str__(self) -> str:
        """
        Human-readable representation. Override in subclass for custom display.

        Default: tries the first CharField value, then falls back to repr.
        """
        for attr_name, field in self._fields.items():
            if isinstance(field, CharField) and not field.primary_key:
                val = getattr(self, attr_name, None)
                if val is not None:
                    return str(val)
        return repr(self)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            # NotImplemented (not False) so Python falls back to *other*'s
            # own __eq__ when it knows how to compare itself against a
            # Model -- e.g. a RelatedNotLoaded sentinel comparing by pk.
            # Without this, dirty-field tracking would flag a FK as
            # "changed" any time related()/select_related() replaces an
            # unhydrated sentinel with the equivalent hydrated instance.
            return NotImplemented
        return bool(getattr(self, self._pk_attr) == getattr(other, other._pk_attr))

    def __hash__(self) -> int:
        return hash((self.__class__.__name__, getattr(self, self._pk_attr, None)))

    # ── pk property ──────────────────────────────────────────────────

    @property
    def pk(self) -> Any:
        """Shortcut for accessing the primary key value."""
        return getattr(self, self._pk_attr, None)

    @pk.setter
    def pk(self, value: Any) -> None:
        """Set the primary key value."""
        setattr(self, self._pk_attr, value)

    # ── Class-level DB ───────────────────────────────────────────────

    @classmethod
    def _get_db(cls) -> AquiliaDatabase:
        """Get database connection."""
        db = cls._db or ModelRegistry.get_database()
        if db is None:
            from ..db.engine import get_database

            db = get_database()

        from .query import QuerySetDatabaseWrapper

        return QuerySetDatabaseWrapper(db, cls.__name__)

    # ── CRUD API ─────────────────────────────────────────────────────

    @classmethod
    async def create(cls, **data: Any) -> Self:
        """
        Create and persist a new record.

        Usage:
            user = await User.create(name="Alice", email="alice@test.com")
        """
        db = cls._get_db()
        dialect = getattr(db, "dialect", "sqlite")
        instance = cls(**data)

        # Signal: pre_save (created=True)
        await pre_save.send(sender=cls, instance=instance, created=True)

        # Process fields: defaults, auto_now_add, pre_save hooks
        # Apply defaults and pre_save BEFORE validation so auto fields
        # (auto_now_add, defaults) are populated before full_clean()
        final_data: dict[str, Any] = {}
        for attr_name, field in cls._non_m2m_fields:
            value = getattr(instance, attr_name, None)

            # Skip auto-PKs
            if field.primary_key and isinstance(field, (AutoField, BigAutoField)) and value is None:
                continue

            # pre_save hook (auto_now_add, etc.)
            if hasattr(field, "pre_save"):
                value = field.pre_save(instance, is_create=True)
                if value is not None:
                    setattr(instance, attr_name, value)

            # Apply default if still None
            if value is None and field.has_default():
                value = field.get_default()
                setattr(instance, attr_name, value)

            if value is not None:
                # Convert to DB format
                db_value = field.to_db(value, dialect=dialect)
                final_data[field.column_name] = db_value
            elif not field.null and not field.primary_key:
                # Required field with no value
                if not field.has_default():
                    final_data[field.column_name] = None  # Let DB handle

        # Validate AFTER defaults and auto-fields are applied
        instance.full_clean()

        if not final_data:
            from ..faults.domains import QueryFault

            raise QueryFault(
                model=cls.__name__,
                operation="create",
                reason="Cannot create record with empty data",
            )

        # Use InsertBuilder from sql_builder for safe, consistent SQL generation
        builder = InsertBuilder(cls._table_name).from_dict(final_data)
        sql, values = builder.build()
        cursor = await db.execute(sql, values)

        pk_field = cls._fields[cls._pk_attr]
        if isinstance(pk_field, (AutoField, BigAutoField)) and cursor.lastrowid:
            setattr(instance, cls._pk_attr, cursor.lastrowid)

        # Signal: post_save (created=True)
        await post_save.send(sender=cls, instance=instance, created=True)

        return instance

    @classmethod
    async def get(cls, pk: Any = None, **filters: Any) -> Self:
        """
        Get a single record by PK or filters.

        Raises ``ModelNotFoundFault`` when the record does not exist.
        Use ``get_or_none()`` if you prefer a None return.

        Usage:
            user = await User.get(pk=1)
            user = await User.get(email="alice@test.com")
        """
        db = cls._get_db()
        dialect = getattr(db, "dialect", "sqlite")

        if pk is not None:
            pk_field = cls._fields.get(cls._pk_attr)
            db_pk = pk_field.to_db(pk, dialect=dialect) if pk_field is not None else pk
            sql = f'SELECT * FROM "{cls._table_name}" WHERE "{cls._pk_name}" = ?'
            row = await db.fetch_one(sql, [db_pk])
        elif filters:
            # Validate filter keys to prevent identifier injection
            import re

            _SAFE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
            for k in filters:
                if not _SAFE.match(k):
                    from ..faults.domains import QueryFault

                    raise QueryFault(
                        model=cls.__name__,
                        operation="get",
                        reason=f"Invalid field name: {k!r}. "
                        "Field names must contain only letters, digits, and underscores.",
                    )
            wheres = [f'"{k}" = ?' for k in filters]
            db_values = []
            for k, v in filters.items():
                field = cls._fields.get(k)
                db_values.append(field.to_db(v, dialect=dialect) if field is not None else v)
            sql = f'SELECT * FROM "{cls._table_name}" WHERE ' + " AND ".join(wheres)
            row = await db.fetch_one(sql, db_values)
        else:
            from ..faults.domains import QueryFault

            raise QueryFault(
                model=cls.__name__,
                operation="get",
                reason="Must provide pk or filters",
            )

        if row is None:
            from ..faults.domains import ModelNotFoundFault

            raise ModelNotFoundFault(model_name=cls.__name__)
        return cls.from_row(row)

    @classmethod
    async def get_or_none(cls, pk: Any = None, **filters: Any) -> Self | None:
        """
        Get a single record, returning ``None`` if not found.

        Unlike ``get()``, this never raises ``ModelNotFoundFault``.

        Usage:
            user = await User.get_or_none(pk=1)
            if user is None:
                ...
        """
        try:
            return await cls.get(pk=pk, **filters)
        except Exception:
            # Catch ModelNotFoundFault (which is an AquiliaFault)
            return None

    @classmethod
    async def get_or_create(cls, defaults: dict[str, Any] | None = None, **lookup: Any) -> tuple[Self, bool]:
        """
        Get existing or create new record.

        Returns (instance, created) tuple.
        """
        instance = await cls.get_or_none(**lookup)
        if instance is not None:
            return instance, False

        create_data = {**lookup, **(defaults or {})}
        instance = await cls.create(**create_data)
        return instance, True

    @classmethod
    async def update_or_create(cls, defaults: dict[str, Any] | None = None, **lookup: Any) -> tuple[Self, bool]:
        """
        Update existing or create new record.

        Returns (instance, created) tuple.
        """
        instance = await cls.get_or_none(**lookup)
        if instance is not None:
            # Update
            update_data = defaults or {}
            if update_data:
                await cls.query().filter(**lookup).update(update_data)
                for k, v in update_data.items():
                    setattr(instance, k, v)
            return instance, False

        create_data = {**lookup, **(defaults or {})}
        instance = await cls.create(**create_data)
        return instance, True

    @classmethod
    async def find_or_create(
        cls,
        defaults: dict[str, Any] | None = None,
        create_defaults: dict[str, Any] | None = None,
        **lookup: Any,
    ) -> tuple[Self, bool]:
        """
        Atomically find an existing record or create a new one.

        Unlike ``get_or_create()``, this method is truly atomic at the database
        level using ``INSERT ... ON CONFLICT DO NOTHING``, avoiding TOCTOU race
        conditions under concurrent access.

        Parameters
        ----------
        defaults : dict[str, Any] | None
            Extra fields to set only when creating a new record. These are
            merged with ``lookup`` fields for the INSERT.
        create_defaults : dict[str, Any] | None
            Override values for creation that take precedence over both
            ``lookup`` and ``defaults``. Use when the lookup value differs from
            the desired create value.
        **lookup : Any
            Field=value pairs to match. At least one lookup field MUST have
            a unique constraint (single-column or composite) for atomicity.

        Returns
        -------
        tuple[Model, bool]
            A 2-tuple of (instance, was_created):
            - instance: The found or newly created model instance
            - was_created: True if a new record was created, False if existing

        Raises
        ------
        QueryFault
            If lookup fields are invalid, empty, or lack a unique constraint.

        Concurrency Notes
        -----------------
        This method is safe for concurrent execution. The database-level upsert
        ensures that:

        1. If the record exists, no INSERT is attempted (conflict detected)
        2. If INSERT succeeds, the record was created atomically
        3. If INSERT is skipped due to conflict, a SELECT fetches the existing

        The method uses ``INSERT ... ON CONFLICT DO NOTHING`` (PostgreSQL/SQLite)
        or ``INSERT IGNORE`` (MySQL) to achieve atomicity without exceptions
        for control flow.

        Examples
        --------
        Basic usage::

            user, created = await User.find_or_create(
                email="alice@example.com",
                defaults={"name": "Alice"}
            )
            if created:
                print("New user created")

        With create_defaults to override lookup value::

            user, created = await User.find_or_create(
                email=email.lower(),
                create_defaults={"email": original_email, "name": "User"}
            )

        Multiple lookup fields (composite unique)::

            membership, created = await Membership.find_or_create(
                user_id=user.id,
                team_id=team.id,
                defaults={"role": "member"}
            )
        """
        import re

        from ..faults.domains import QueryFault

        # ── Validate lookup fields ────────────────────────────────────────
        if not lookup:
            raise QueryFault(
                model=cls.__name__,
                operation="find_or_create",
                reason="At least one lookup field is required",
            )

        # Validate field names (prevent SQL injection)
        _SAFE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
        for key in lookup:
            if not _SAFE.match(key):
                raise QueryFault(
                    model=cls.__name__,
                    operation="find_or_create",
                    reason=f"Invalid field name: {key!r}. "
                    "Field names must contain only letters, digits, and underscores.",
                )
            if key not in cls._fields:
                raise QueryFault(
                    model=cls.__name__,
                    operation="find_or_create",
                    reason=f"Unknown field: {key!r}. Valid fields: {list(cls._fields.keys())}",
                )

        # ── Validate unique constraint exists on lookup fields ────────────
        lookup_fields = set(lookup.keys())
        has_unique = cls._validate_unique_constraint(lookup_fields)
        if not has_unique:
            raise QueryFault(
                model=cls.__name__,
                operation="find_or_create",
                reason=f"Lookup fields {list(lookup_fields)} must have a unique constraint "
                "for atomic find_or_create. Add unique=True to the field or "
                "define a UniqueConstraint in Meta.constraints.",
            )

        # ── Prepare create data ───────────────────────────────────────────
        db = cls._get_db()
        dialect = getattr(db, "dialect", "sqlite")

        # Merge: lookup < defaults < create_defaults
        create_data = {**lookup}
        if defaults:
            create_data.update(defaults)
        if create_defaults:
            create_data.update(create_defaults)

        # Build instance for field processing (defaults, pre_save hooks)
        instance = cls(**create_data)

        # Process fields: apply defaults, pre_save hooks, convert to DB format
        final_data: dict[str, Any] = {}
        for attr_name, field in cls._non_m2m_fields:
            value = getattr(instance, attr_name, None)

            # Skip auto-PKs
            if field.primary_key and isinstance(field, (AutoField, BigAutoField)) and value is None:
                continue

            # pre_save hook (auto_now_add, etc.)
            if hasattr(field, "pre_save"):
                value = field.pre_save(instance, is_create=True)
                if value is not None:
                    setattr(instance, attr_name, value)

            # Apply default if still None
            if value is None and field.has_default():
                value = field.get_default()
                setattr(instance, attr_name, value)

            if value is not None:
                db_value = field.to_db(value, dialect=dialect)
                final_data[field.column_name] = db_value
            elif not field.null and not field.primary_key:
                if not field.has_default():
                    final_data[field.column_name] = None

        if not final_data:
            raise QueryFault(
                model=cls.__name__,
                operation="find_or_create",
                reason="Cannot create record with empty data",
            )

        # ── Build conflict target (unique constraint columns) ─────────────
        conflict_columns = cls._get_conflict_columns(lookup_fields, dialect)

        # ── Execute atomic INSERT ... ON CONFLICT DO NOTHING ──────────────
        from .sql_builder import UpsertIgnoreBuilder

        builder = UpsertIgnoreBuilder(cls._table_name, dialect=dialect)
        builder.from_dict(final_data)
        builder.conflict_target(*conflict_columns)
        sql, params = builder.build()

        cursor = await db.execute(sql, params)

        # ── Determine if insert succeeded ─────────────────────────────────
        # For INSERT ON CONFLICT DO NOTHING / INSERT IGNORE:
        # - lastrowid > 0 means insert succeeded (SQLite, MySQL)
        # - lastrowid == 0 or rowcount == 0 means conflict (no insert)
        was_created = bool(cursor.lastrowid)

        if was_created:
            pk_field = cls._fields[cls._pk_attr]
            if isinstance(pk_field, (AutoField, BigAutoField)):
                setattr(instance, cls._pk_attr, cursor.lastrowid)
            return instance, True

        # ── If not created, SELECT the existing record ────────────────────
        where_parts = []
        where_values = []
        for key, value in lookup.items():
            field = cls._fields[key]
            where_parts.append(f'"{field.column_name}" = ?')
            where_values.append(field.to_db(value, dialect=dialect))

        select_sql = f'SELECT * FROM "{cls._table_name}" WHERE ' + " AND ".join(where_parts)
        row = await db.fetch_one(select_sql, where_values)

        if row is None:
            # Extremely rare: record existed during INSERT but gone now
            raise QueryFault(
                model=cls.__name__,
                operation="find_or_create",
                reason="Record vanished between INSERT and SELECT. This may indicate concurrent DELETE operations.",
            )

        return cls.from_row(row), False

    @classmethod
    def _validate_unique_constraint(cls, lookup_fields: set[str]) -> bool:
        """
        Check if lookup fields are covered by a unique constraint.

        Returns True if:
        - Any single lookup field has unique=True
        - The primary key field is in lookup_fields
        - All lookup fields together form a composite unique constraint
          (via Meta.unique_together or Meta.constraints with UniqueConstraint)
        """
        # Check single-field unique constraints
        for field_name in lookup_fields:
            field = cls._fields.get(field_name)
            if field and (field.unique or field.primary_key):
                return True

        # Check unique_together (legacy)
        if hasattr(cls._meta, "unique_together"):
            for unique_fields in cls._meta.unique_together:
                unique_set = set(unique_fields)
                if unique_set.issubset(lookup_fields) or lookup_fields == unique_set:
                    return True

        # Check Meta.constraints for UniqueConstraint
        if hasattr(cls._meta, "constraints"):
            from .fields_module import UniqueConstraint

            for constraint in cls._meta.constraints:
                if isinstance(constraint, UniqueConstraint):
                    constraint_fields = set(constraint.fields)
                    if constraint_fields.issubset(lookup_fields) or lookup_fields == constraint_fields:
                        return True

        return False

    @classmethod
    def _get_conflict_columns(cls, lookup_fields: set[str], dialect: str) -> list[str]:
        """
        Determine the database column names for conflict detection.

        For single unique field: returns that field's column name.
        For composite unique: returns all columns in the unique constraint.
        """
        # Prefer single unique field if available
        for field_name in lookup_fields:
            field = cls._fields.get(field_name)
            if field and (field.unique or field.primary_key):
                return [field.column_name]

        # Check unique_together
        if hasattr(cls._meta, "unique_together"):
            for unique_fields in cls._meta.unique_together:
                unique_set = set(unique_fields)
                if unique_set.issubset(lookup_fields):
                    return [cls._fields[f].column_name for f in unique_fields]

        # Check Meta.constraints for UniqueConstraint
        if hasattr(cls._meta, "constraints"):
            from .fields_module import UniqueConstraint

            for constraint in cls._meta.constraints:
                if isinstance(constraint, UniqueConstraint):
                    constraint_fields = set(constraint.fields)
                    if constraint_fields.issubset(lookup_fields):
                        return [cls._fields[f].column_name for f in constraint.fields]

        # Fallback: use all lookup fields as conflict target
        return [cls._fields[f].column_name for f in lookup_fields]

    @classmethod
    async def bulk_create(
        cls,
        instances: list[dict[str, Any]],
        *,
        batch_size: int | None = None,
        ignore_conflicts: bool = False,
    ) -> list[Self]:
        """
        Create multiple records efficiently using batched inserts.

        Faster than individual create() calls.

        Note: Signals (pre_save/post_save) are NOT fired for bulk_create.
        Use individual create() if you need signals.

        Usage:
            users = await User.bulk_create([
                {"name": "Alice", "email": "alice@test.com"},
                {"name": "Bob", "email": "bob@test.com"},
            ], batch_size=100)

        Args:
            instances: List of dicts with field data
            batch_size: Number of records per INSERT batch (None = all at once)
            ignore_conflicts: If True, use INSERT OR IGNORE (SQLite)
        """
        if not instances:
            return []

        db = cls._get_db()
        dialect = getattr(db, "dialect", "sqlite")
        results: list[Self] = []

        # Process in batches
        effective_batch = batch_size or len(instances)
        for i in range(0, len(instances), effective_batch):
            batch = instances[i : i + effective_batch]
            for data in batch:
                obj = cls(**data)

                # Process fields
                final_data: dict[str, Any] = {}
                for attr_name, field in cls._non_m2m_fields:
                    value = getattr(obj, attr_name, None)
                    if field.primary_key and isinstance(field, (AutoField, BigAutoField)) and value is None:
                        continue
                    if hasattr(field, "pre_save"):
                        value = field.pre_save(obj, is_create=True)
                        if value is not None:
                            setattr(obj, attr_name, value)
                    if value is None and field.has_default():
                        value = field.get_default()
                        setattr(obj, attr_name, value)
                    if value is not None:
                        final_data[field.column_name] = field.to_db(value, dialect=dialect)

                if final_data:
                    builder = InsertBuilder(cls._table_name).from_dict(final_data)
                    sql, values = builder.build()
                    if ignore_conflicts:
                        sql = sql.replace("INSERT INTO", "INSERT OR IGNORE INTO", 1)
                    cursor = await db.execute(sql, values)
                    pk_field = cls._fields[cls._pk_attr]
                    if isinstance(pk_field, (AutoField, BigAutoField)) and cursor.lastrowid:
                        setattr(obj, cls._pk_attr, cursor.lastrowid)
                results.append(obj)

        return results

    @classmethod
    async def bulk_update(
        cls,
        instances: list[Self],
        fields: list[str],
        *,
        batch_size: int | None = None,
    ) -> int:
        """
        Update specific fields on multiple model instances efficiently.

        Updates only specified fields.

        Note: Signals are NOT fired. Auto-now fields
        are NOT updated automatically.

        Usage:
            for user in users:
                user.name = user.name.upper()
            await User.bulk_update(users, fields=["name"])

        Args:
            instances: List of Model instances with updated attributes
            fields: List of field names to update
            batch_size: Records per batch (None = all)

        Returns:
            Total number of rows updated
        """
        if not instances or not fields:
            return 0

        db = cls._get_db()
        dialect = getattr(db, "dialect", "sqlite")
        total_updated = 0
        effective_batch = batch_size or len(instances)

        for i in range(0, len(instances), effective_batch):
            batch = instances[i : i + effective_batch]
            for obj in batch:
                pk_val = getattr(obj, cls._pk_attr)
                if pk_val is None:
                    continue
                data: dict[str, Any] = {}
                for fname in fields:
                    field = cls._fields.get(fname)
                    if field is None or isinstance(field, ManyToManyField):
                        continue
                    value = getattr(obj, fname, None)
                    if value is not None:
                        data[field.column_name] = field.to_db(value, dialect=dialect)
                    else:
                        data[field.column_name] = None
                if data:
                    builder = UpdateBuilder(cls._table_name).set_dict(data)
                    pk_field = cls._fields[cls._pk_attr]
                    db_pk_val = pk_field.to_db(pk_val, dialect=dialect)
                    builder.where(f'"{cls._pk_name}" = ?', db_pk_val)
                    sql, params = builder.build()
                    cursor = await db.execute(sql, params)
                    total_updated += cursor.rowcount

        return total_updated

    @classmethod
    def query(cls) -> Q[Self]:
        """
        Start a query chain.

        Usage:
            users = await User.query().filter(active=True).all()
        """
        return Q(cls._table_name, cls, cls._get_db())

    @classmethod
    async def all(cls) -> list[Self]:
        """Shortcut: get all records."""
        return await cls.query().all()

    @classmethod
    async def count(cls) -> int:
        """Shortcut: count all records."""
        return await cls.query().count()

    @classmethod
    async def latest(cls, field_name: str | None = None) -> Self:
        """
        Return the latest record by date field.

        Uses Meta.get_latest_by if field_name is not provided.

        Usage:
            latest_user = await User.latest()           # uses Meta.get_latest_by
            latest_user = await User.latest("created_at")
        """
        field = field_name or getattr(cls._meta, "get_latest_by", None)
        if not field:
            from ..faults.domains import QueryFault

            raise QueryFault(
                model=cls.__name__,
                operation="latest",
                reason=f"{cls.__name__}.latest() requires 'field_name' argument or Meta.get_latest_by to be set",
            )
        result = await cls.query().order(f"-{field}").first()
        if result is None:
            from ..faults.domains import ModelNotFoundFault

            raise ModelNotFoundFault(model_name=cls.__name__)
        return result

    @classmethod
    async def earliest(cls, field_name: str | None = None) -> Self:
        """
        Return the earliest record by date field.

        Uses Meta.get_latest_by if field_name is not provided.

        Usage:
            first_user = await User.earliest()
            first_user = await User.earliest("created_at")
        """
        field = field_name or getattr(cls._meta, "get_latest_by", None)
        if not field:
            from ..faults.domains import QueryFault

            raise QueryFault(
                model=cls.__name__,
                operation="earliest",
                reason=f"{cls.__name__}.earliest() requires 'field_name' argument or Meta.get_latest_by to be set",
            )
        result = await cls.query().order(field).first()
        if result is None:
            from ..faults.domains import ModelNotFoundFault

            raise ModelNotFoundFault(model_name=cls.__name__)
        return result

    @classmethod
    async def raw(cls, sql: str, params: list[Any] | None = None) -> list[Self]:
        """
        Execute raw SQL and return model instances.

        The SQL must return columns matching the model's fields.

        .. warning::
            ``raw()`` executes arbitrary SQL. Always use parameterized
            queries (``?`` placeholders) for user-supplied values. DDL
            statements (DROP, ALTER, TRUNCATE) are rejected by default.

        Usage:
            users = await User.raw(
                "SELECT * FROM users WHERE age > ? ORDER BY name",
                [18]
            )

        Use parameterized queries to prevent SQL injection.
        """
        import re

        _DDL_RE = re.compile(r"\b(DROP|ALTER|TRUNCATE|GRANT|REVOKE)\b", re.IGNORECASE)
        if _DDL_RE.search(sql):
            from ..faults.domains import QueryFault

            raise QueryFault(
                model=cls.__name__,
                operation="raw",
                reason="DDL/DCL statements are not allowed in raw(). "
                "Use the database engine directly for schema operations.",
            )
        db = cls._get_db()
        rows = await db.fetch_all(sql, params or [])
        return [cls.from_row(row) for row in rows]

    @classmethod
    def using(cls, db_alias: str) -> Q[Self]:
        """
        Target a specific database for this query.

        Usage:
            users = await User.using("replica").filter(active=True).all()
        """
        return cls.query().using(db_alias)

    # ── Instance methods ─────────────────────────────────────────────

    async def save(
        self,
        *,
        update_fields: list[str] | None = None,
        force_insert: bool = False,
        force_update: bool = False,
        validate: bool = False,
    ) -> Self:
        """
        Save instance (insert or update).

        If PK is set, updates. Otherwise, inserts.

        Args:
            update_fields: Only update these specific fields.
                          More efficient -- generates SET for only these columns.
            force_insert: Force INSERT even if PK is set.
            force_update: Force UPDATE even if PK is None (raises if no PK).
            validate: Run full_clean() before saving (default False for perf).

        Usage:
            user.name = "Updated"
            await user.save(update_fields=["name"])  # only updates name column
            await user.save(validate=True)            # validates before saving
        """
        if force_insert and force_update:
            from ..faults.domains import QueryFault

            raise QueryFault(
                model=self.__class__.__name__,
                operation="save",
                reason="Cannot use force_insert and force_update together",
            )

        pk_val = getattr(self, self._pk_attr, None)

        if force_update and pk_val is None:
            from ..faults.domains import QueryFault

            raise QueryFault(
                model=self.__class__.__name__,
                operation="save",
                reason="Cannot force_update on unsaved instance (no primary key)",
            )

        db = self._get_db()
        dialect = getattr(db, "dialect", "sqlite")
        is_create = (
            pk_val is None or getattr(self, "_original_values", None) is None or force_insert
        ) and not force_update

        # Optional validation
        if validate:
            self.full_clean()

        # Signal: pre_save
        await pre_save.send(sender=self.__class__, instance=self, created=is_create)

        if not is_create:
            # Update -- use dirty tracking if update_fields not explicit
            data: dict[str, Any] = {}
            if update_fields:
                target_fields = update_fields
            else:
                dirty = self.get_dirty_fields()
                target_fields = (
                    list(dirty.keys())
                    if dirty
                    else [attr for attr in self._attr_names if not self._fields[attr].primary_key]
                )

            for attr_name in target_fields:
                upd_field = self._fields.get(attr_name)
                if upd_field is None or isinstance(upd_field, ManyToManyField):
                    continue
                if upd_field.primary_key:
                    continue
                value = getattr(self, attr_name, None)
                if hasattr(upd_field, "pre_save"):
                    value = upd_field.pre_save(self, is_create=False)
                    setattr(self, attr_name, value)
                if value is not None:
                    data[upd_field.column_name] = upd_field.to_db(value, dialect=dialect)
                else:
                    data[upd_field.column_name] = None

            if data:
                update_builder = UpdateBuilder(self._table_name).set_dict(data)
                pk_field = self._fields[self._pk_attr]
                db_pk_val = pk_field.to_db(pk_val, dialect=dialect)
                update_builder.where(f'"{self._pk_name}" = ?', db_pk_val)
                sql, params = update_builder.build()
                await db.execute(sql, params)

            # select_on_save: re-read from DB to get computed columns
            if self._meta.select_on_save:
                await self.refresh()
        else:
            # Insert -- build and execute directly to avoid
            # double signal firing from cls.create()
            final_data: dict[str, Any] = {}
            for attr_name, create_field in self._non_m2m_fields:
                value = getattr(self, attr_name, None)

                # Skip auto-PKs unless force_insert with explicit PK
                if create_field.primary_key and isinstance(create_field, (AutoField, BigAutoField)):
                    if force_insert and pk_val is not None:
                        final_data[create_field.column_name] = pk_val
                    continue

                # pre_save hook
                if hasattr(create_field, "pre_save"):
                    value = create_field.pre_save(self, is_create=True)
                    if value is not None:
                        setattr(self, attr_name, value)

                # Apply default if still None
                if value is None and create_field.has_default():
                    value = create_field.get_default()
                    setattr(self, attr_name, value)

                # Always include NOT NULL fields so to_db() can coerce
                # (e.g. CharField with null=False converts None → "").
                # Nullable fields with None are omitted to let the DB use its DEFAULT.
                if value is not None or not create_field.null:
                    final_data[create_field.column_name] = create_field.to_db(value, dialect=dialect)

            if final_data:
                insert_builder = InsertBuilder(self._table_name).from_dict(final_data)
                sql, params = insert_builder.build()
                cursor = await db.execute(sql, params)
                pk_field = self._fields[self._pk_attr]
                if isinstance(pk_field, (AutoField, BigAutoField)) and cursor.lastrowid:
                    setattr(self, self._pk_attr, cursor.lastrowid)

        # Signal: post_save
        await post_save.send(sender=self.__class__, instance=self, created=is_create)

        # Reset dirty tracking after successful save
        self._snapshot_original()

        return self

    @classmethod
    def _get_reverse_fk_refs(cls) -> list[tuple[type[Model], str, str]]:
        """
        Get all (model_cls, column_name, on_delete) tuples where other models
        have ForeignKey pointing to this model. Cached per class.
        """
        if cls._reverse_fk_cache is not None:
            return cls._reverse_fk_cache

        refs: list[tuple[type[Model], str, str]] = []
        for model_cls in ModelRegistry.all_models().values():
            for _fname, field in model_cls._fields.items():
                if isinstance(field, ForeignKey):
                    target_name = field.to if isinstance(field.to, str) else field.to.__name__
                    if target_name == cls.__name__:
                        refs.append((model_cls, field.column_name, field.on_delete))

        cls._reverse_fk_cache = refs
        return refs

    @classmethod
    def _reverse_relation_map(cls) -> dict[str, tuple[type[Model], str, str, bool]]:
        """
        Map of reverse-relation accessor name -> (referencing_model,
        fk_column_name, fk_attr_name, is_one_to_one) for every
        ForeignKey/OneToOneField in the registry that points at this model.
        Cached per class using the same lazy-on-first-use pattern as
        ``_get_reverse_fk_refs()`` (and for the same reason: this must run
        after every model is registered, which is only guaranteed once real
        use begins -- e.g. the first ``related()``/``related_manager()``
        call -- not at class-creation time, since import order across
        modules isn't guaranteed).

        Accessor name defaults to ``related_name`` when set on the FK,
        otherwise ``f"{referencing_model.__name__.lower()}_set"``.

        ``is_one_to_one`` lets ``related()`` return a single instance (or
        None) instead of a list for OneToOneField's reverse side, matching
        its actual 1:1 cardinality.

        Raises RelatedNameConflictFault if two different FKs targeting this
        model would resolve to the same accessor name.
        """
        if cls._reverse_relation_cache is not None:
            return cls._reverse_relation_cache

        mapping: dict[str, tuple[type[Model], str, str, bool]] = {}
        conflicts: dict[str, list[type[Model]]] = {}
        for model_cls in ModelRegistry.all_models().values():
            for fname, field in model_cls._fields.items():
                if not isinstance(field, ForeignKey):
                    continue
                target_name = field.to if isinstance(field.to, str) else field.to.__name__
                if target_name != cls.__name__:
                    continue
                accessor_name = field.related_name or f"{model_cls.__name__.lower()}_set"
                existing = mapping.get(accessor_name)
                if existing is not None and existing[0] is not model_cls:
                    conflicts.setdefault(accessor_name, [existing[0]]).append(model_cls)
                    continue
                mapping[accessor_name] = (model_cls, field.column_name, fname, isinstance(field, OneToOneField))

        if conflicts:
            name, conflicting_models = next(iter(conflicts.items()))
            from ..faults.domains import RelatedNameConflictFault

            raise RelatedNameConflictFault(
                model_name=cls.__name__,
                related_name=name,
                conflicting_models=[m.__name__ for m in conflicting_models],
            )

        cls._reverse_relation_cache = mapping
        return mapping

    async def delete_instance(self) -> int:
        """
        Delete this instance from database.

        Handles on_delete cascading via OnDeleteHandler from deletion.py:
        - CASCADE: delete related records
        - SET_NULL: set FK to NULL
        - PROTECT: raise ProtectedError if references exist
        - RESTRICT: raise RestrictedError if references exist
        """
        pk_val = getattr(self, self._pk_attr)
        if pk_val is None:
            from ..faults.domains import QueryFault

            raise QueryFault(
                model=self.__class__.__name__,
                operation="delete",
                reason="Cannot delete unsaved instance (no primary key)",
            )

        # Signal: pre_delete
        await pre_delete.send(sender=self.__class__, instance=self)

        db = self._get_db()
        dialect = getattr(db, "dialect", "sqlite")
        pk_field = self._fields[self._pk_attr]
        db_pk_val = pk_field.to_db(pk_val, dialect=dialect)

        # Cascade handling (potentially several statements across related
        # tables) plus the final delete must be one atomic unit -- otherwise
        # a failure partway through (e.g. a PROTECT check on a later table)
        # leaves the database in a partially-cascaded, inconsistent state.
        real_db = getattr(db, "_wrapped_db", db)
        async with real_db.transaction():
            # Handle on_delete for models that FK to us (cached lookup)
            for model_cls, col_name, on_delete_action in self._get_reverse_fk_refs():
                handler = OnDeleteHandler(on_delete_action)
                await handler.handle(db, model_cls, col_name, db_pk_val)

            # Delete this instance using DeleteBuilder
            builder = DeleteBuilder(self._table_name)
            builder.where(f'"{self._pk_name}" = ?', db_pk_val)
            sql, params = builder.build()
            cursor = await db.execute(sql, params)
            row_count = int(cursor.rowcount or 0)

        # Signal: post_delete
        await post_delete.send(sender=self.__class__, instance=self)

        return row_count

    def full_clean(self, exclude: list[str] | None = None) -> None:
        """
        Validate instance completely.

        Calls:
        1. clean_fields() -- per-field validation (type, null, choices, validators)
        2. clean() -- model-level cross-field validation (override in subclass)

        Raises:
            FieldValidationError: If any field fails validation
        """
        self.clean_fields(exclude=exclude)
        self.clean()

    def clean_fields(self, exclude: list[str] | None = None) -> None:
        """
        Validate all fields on this instance.

        Runs field.validate() for each field, collecting errors.

        Raises:
            FieldValidationError: On first validation failure
        """
        exclude_set = set(exclude or [])
        errors: dict[str, str] = {}
        for attr_name, field in self._fields.items():
            if isinstance(field, ManyToManyField):
                continue
            if attr_name in exclude_set:
                continue
            value = getattr(self, attr_name, None)
            try:
                field.validate(value)
            except FieldValidationError as e:
                errors[attr_name] = str(e)
        if errors:
            first_field = next(iter(errors))
            raise FieldValidationError(first_field, errors[first_field])

    def clean(self) -> None:
        """
        Model-level validation hook -- override in subclasses.

        Called by full_clean() after clean_fields(). Use for cross-field
        validation logic.

        Usage:
            class Event(Model):
                start = DateTimeField()
                end = DateTimeField()

                def clean(self):
                    if self.start and self.end and self.start > self.end:
                        raise FieldValidationError("end", "End must be after start")
        """
        pass

    async def refresh(self, fields: list[str] | None = None) -> Self:
        """Reload instance from database.

        Args:
            fields: Optional list of field names to refresh. If None,
                    refreshes all fields.

        Raises:
            QueryFault: If the instance has no PK (unsaved) or field is unknown.
            ModelNotFoundFault: If the record no longer exists in the database.
        """
        pk_val = getattr(self, self._pk_attr)
        if pk_val is None:
            from ..faults.domains import QueryFault

            raise QueryFault(
                model=self.__class__.__name__,
                operation="refresh",
                reason="Cannot refresh unsaved instance (no primary key)",
            )

        if fields is not None:
            # Partial refresh -- SELECT only requested columns
            cols = []
            for attr_name in fields:
                field = self._fields.get(attr_name)
                if field is None:
                    from ..faults.domains import QueryFault

                    raise QueryFault(
                        model=self.__class__.__name__,
                        operation="refresh",
                        reason=f"Unknown field: {attr_name}",
                    )
                cols.append(field.column_name)
            col_sql = ", ".join(f'"{c}"' for c in cols)
            sql = f'SELECT {col_sql} FROM "{self._table_name}" WHERE "{self._pk_name}" = ?'
            db = self._get_db()
            dialect = getattr(db, "dialect", "sqlite")
            pk_field = self._fields[self._pk_attr]
            db_pk_val = pk_field.to_db(pk_val, dialect=dialect)
            rows = await db.fetch_all(sql, [db_pk_val])
            if not rows:
                from ..faults.domains import ModelNotFoundFault

                raise ModelNotFoundFault(model_name=self.__class__.__name__)
            row = rows[0]
            for attr_name in fields:
                field = self._fields[attr_name]
                raw = row.get(field.column_name)
                setattr(self, attr_name, field.to_python(raw) if raw is not None else None)
            # These fields are now loaded -- no longer deferred.
            deferred = self.__dict__.get("_deferred_fields")
            if deferred:
                deferred.difference_update(fields)
                if not deferred:
                    base_cls = getattr(type(self), "__deferred_guard_base__", None)
                    if base_cls is not None:
                        self.__class__ = base_cls
        else:
            # Full refresh
            fresh = await self.__class__.get_or_none(pk=pk_val)
            if fresh is None:
                from ..faults.domains import ModelNotFoundFault

                raise ModelNotFoundFault(model_name=self.__class__.__name__)
            for attr in self._attr_names:
                setattr(self, attr, getattr(fresh, attr))
            # Fully reloaded -- no fields remain deferred.
            self.__dict__.pop("_deferred_fields", None)
            base_cls = getattr(type(self), "__deferred_guard_base__", None)
            if base_cls is not None:
                self.__class__ = base_cls

        # Reset dirty tracking snapshot
        self._snapshot_original()
        return self

    # Alias
    refresh_from_db = refresh

    def _snapshot_original(self) -> None:
        """Capture current field values for dirty-field tracking."""
        self._original_values = {attr: getattr(self, attr, None) for attr in self._attr_names}

    def get_dirty_fields(self) -> dict[str, Any]:
        """Return dict of fields whose values differ from the DB snapshot.

        Returns:
            Dict mapping field name -> current value for changed fields.
        """
        original = getattr(self, "_original_values", None)
        if original is None:
            # No snapshot -- treat all non-PK fields as dirty
            return {attr: getattr(self, attr, None) for attr in self._attr_names if not self._fields[attr].primary_key}
        dirty: dict[str, Any] = {}
        for attr in self._attr_names:
            if self._fields[attr].primary_key:
                continue
            current = getattr(self, attr, None)
            if current != original.get(attr):
                dirty[attr] = current
        return dirty

    # ── Relationships ────────────────────────────────────────────────

    async def related(self, name: str) -> Any:
        """
        Access a related model via FK, reverse FK, or M2M -- awaited,
        one-shot, always returns real hydrated data (never a
        RelatedNotLoaded sentinel or a lazy manager).

        Usage:
            author = await post.related("author")     # FK forward
            posts = await user.related("posts")        # FK reverse (related_name or default `_set` name)
            tags = await post.related("tags")           # M2M

        Forward FK: if the attribute already holds a hydrated instance
        (via select_related()/prefetch_related()/a prior related() call),
        returns it immediately with zero query. Otherwise resolves it and
        caches the hydrated instance in place, so subsequent bare
        attribute access (not just future related() calls) is instant and
        correctly typed from then on.

        Reverse FK: O(1) lookup into _reverse_relation_map() (see
        related_manager() for a lazy, chainable alternative that doesn't
        eagerly materialize the full list).
        """
        # Forward FK
        field = self._fields.get(name)
        if isinstance(field, ForeignKey):
            current = getattr(self, name, None)
            if current is None:
                return None
            if isinstance(current, Model):
                return current  # already hydrated -- zero-query fast path

            fk_value = current.pk if isinstance(current, RelatedNotLoaded) else current
            if fk_value is None:
                # Defensive fallback for the pre-1.3 _id-column convention.
                fk_value = getattr(self, field.column_name, None)
            if fk_value is None:
                return None

            target = field.related_model
            if target is None:
                target = ModelRegistry.get(field.to if isinstance(field.to, str) else field.to.__name__)
            if target is None:
                return None

            resolved = await target.get(pk=fk_value)
            setattr(self, name, resolved)  # cache -- future bare access just works
            return resolved

        # M2M
        if name in self._m2m_fields:
            m2m = self._m2m_fields[name]
            target = m2m.related_model or ModelRegistry.get(m2m.to if isinstance(m2m.to, str) else m2m.to.__name__)
            if target is None:
                return []

            jt = m2m.junction_table_name(self.__class__)
            src_col, tgt_col = m2m.junction_columns(self.__class__)
            pk_val = getattr(self, self._pk_attr)
            target_pk = getattr(target, "_pk_name", "id")

            db = self._get_db()
            dialect = getattr(db, "dialect", "sqlite")
            pk_field = self._fields[self._pk_attr]
            db_pk_val = pk_field.to_db(pk_val, dialect=dialect)
            sql = (
                f'SELECT t.* FROM "{target._table_name}" t '
                f'INNER JOIN "{jt}" j ON t."{target_pk}" = j."{tgt_col}" '
                f'WHERE j."{src_col}" = ?'
            )
            rows = await db.fetch_all(sql, [db_pk_val])
            return [target.from_row(r) for r in rows]

        # Reverse FK -- delegate to the lazy related_manager(). A
        # OneToOneField's reverse side is genuinely 1:1, so return a single
        # instance (or None) instead of a list, matching its actual
        # cardinality; a plain ForeignKey's reverse side stays a list.
        reverse_entry = self._reverse_relation_map().get(name)
        if reverse_entry is not None:
            is_one_to_one = reverse_entry[3]
            manager = self.related_manager(name)
            return await manager.first() if is_one_to_one else await manager.all()

        from ..faults.domains import QueryFault

        raise QueryFault(
            model=self.__class__.__name__,
            operation="related",
            reason=f"No relation '{name}' on {self.__class__.__name__}",
        )

    def related_manager(self, name: str) -> RelatedManager[Any]:
        """
        Return a lazy, chainable manager over the reverse relation `name`
        (rows in another table whose FK points back at this instance).

        Unlike related() (which awaits and returns a fully materialized
        list), this constructs a pre-filtered, async-terminal manager with
        zero I/O -- nothing executes until a terminal method is awaited:

            recent = await user.related_manager("verifications").filter(
                expires_at__gt=now,
            ).order("-created_at").first()

            count = await user.related_manager("verifications").count()
        """
        entry = self._reverse_relation_map().get(name)
        if entry is None:
            from ..faults.domains import QueryFault

            raise QueryFault(
                model=self.__class__.__name__,
                operation="related_manager",
                reason=f"No reverse relation '{name}' on {self.__class__.__name__}",
            )
        referencing_model, fk_column_name, _fk_attr_name, _is_one_to_one = entry

        db = self._get_db()
        dialect = getattr(db, "dialect", "sqlite")
        pk_field = self._fields[self._pk_attr]
        db_pk_val = pk_field.to_db(getattr(self, self._pk_attr), dialect=dialect)

        from .manager import RelatedManager

        return RelatedManager(referencing_model, fk_column_name, db_pk_val)

    async def attach(self, name: str, *targets: Any) -> None:
        """
        Attach records to a M2M relationship.

        Usage:
            await post.attach("tags", tag1.id, tag2.id)
        """
        m2m = self._m2m_fields.get(name)
        if m2m is None:
            from ..faults.domains import QueryFault

            raise QueryFault(
                model=self.__class__.__name__,
                operation="attach",
                reason=f"No M2M relation '{name}' on {self.__class__.__name__}",
            )

        jt = m2m.junction_table_name(self.__class__)
        src_col, tgt_col = m2m.junction_columns(self.__class__)
        pk_val = getattr(self, self._pk_attr)
        db = self._get_db()
        dialect = getattr(db, "dialect", "sqlite")
        pk_field = self._fields[self._pk_attr]
        db_pk_val = pk_field.to_db(pk_val, dialect=dialect)

        target_model = m2m.related_model or ModelRegistry.get(m2m.to if isinstance(m2m.to, str) else m2m.to.__name__)
        target_pk_field = target_model._fields[target_model._pk_attr]

        for target in targets:
            target_pk = target if isinstance(target, (int, str)) else getattr(target, target._pk_attr)
            db_target_pk = target_pk_field.to_db(target_pk, dialect=dialect)
            await db.execute(
                f'INSERT OR IGNORE INTO "{jt}" ("{src_col}", "{tgt_col}") VALUES (?, ?)',
                [db_pk_val, db_target_pk],
            )

        # Signal: m2m_changed
        await m2m_changed.send(
            sender=self.__class__,
            instance=self,
            action="attach",
            model=name,
            pk_set=[t if isinstance(t, (int, str)) else getattr(t, t._pk_attr) for t in targets],
        )

    async def detach(self, name: str, *targets: Any) -> None:
        """
        Detach records from a M2M relationship.

        Usage:
            await post.detach("tags", tag1.id)
        """
        m2m = self._m2m_fields.get(name)
        if m2m is None:
            from ..faults.domains import QueryFault

            raise QueryFault(
                model=self.__class__.__name__,
                operation="detach",
                reason=f"No M2M relation '{name}' on {self.__class__.__name__}",
            )

        jt = m2m.junction_table_name(self.__class__)
        src_col, tgt_col = m2m.junction_columns(self.__class__)
        pk_val = getattr(self, self._pk_attr)
        db = self._get_db()
        dialect = getattr(db, "dialect", "sqlite")
        pk_field = self._fields[self._pk_attr]
        db_pk_val = pk_field.to_db(pk_val, dialect=dialect)

        target_model = m2m.related_model or ModelRegistry.get(m2m.to if isinstance(m2m.to, str) else m2m.to.__name__)
        target_pk_field = target_model._fields[target_model._pk_attr]

        for target in targets:
            target_pk = target if isinstance(target, (int, str)) else getattr(target, target._pk_attr)
            db_target_pk = target_pk_field.to_db(target_pk, dialect=dialect)
            await db.execute(
                f'DELETE FROM "{jt}" WHERE "{src_col}" = ? AND "{tgt_col}" = ?',
                [db_pk_val, db_target_pk],
            )

        # Signal: m2m_changed
        await m2m_changed.send(
            sender=self.__class__,
            instance=self,
            action="detach",
            model=name,
            pk_set=[t if isinstance(t, (int, str)) else getattr(t, t._pk_attr) for t in targets],
        )

    # ── Serialization ────────────────────────────────────────────────

    def to_dict(
        self,
        *,
        fields: list[str] | None = None,
        exclude: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Serialize model instance to dict.

        Args:
            fields: Whitelist of field names to include (all if None).
            exclude: Blacklist of field names to exclude.

        Usage:
            user.to_dict()                         # all fields
            user.to_dict(fields=["id", "name"])    # only id & name
            user.to_dict(exclude=["password"])      # everything except password
        """
        include = set(fields) if fields else None
        skip = set(exclude or [])
        result: dict[str, Any] = {}

        for attr_name, field in self._fields.items():
            if isinstance(field, ManyToManyField):
                continue
            if include is not None and attr_name not in include:
                continue
            if attr_name in skip:
                continue

            value = getattr(self, attr_name, None)
            value = self._serialize_value(value)
            result[attr_name] = value
        return result

    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """Convert a Python value to a JSON-safe representation."""
        if value is None:
            return None
        if isinstance(value, datetime.datetime):
            return value.isoformat()
        if isinstance(value, datetime.date):
            return value.isoformat()
        if isinstance(value, datetime.time):
            return value.isoformat()
        if isinstance(value, datetime.timedelta):
            return value.total_seconds()
        if isinstance(value, uuid.UUID):
            return str(value)
        if isinstance(value, bytes):
            return value.hex()
        if isinstance(value, decimal.Decimal):
            return str(value)
        # Enum support (TextChoices, IntegerChoices, etc.)
        import enum

        if isinstance(value, enum.Enum):
            return value.value
        return value

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> Self:
        """Create model instance from database row dict.

        Performance: Uses _col_to_attr mapping cached at class creation
        to avoid per-field isinstance checks and double-lookups.

        Also snapshots original values for dirty-field tracking so that
        ``save()`` can generate minimal UPDATE statements.
        """
        instance = cls.__new__(cls)
        col_to_attr = cls._col_to_attr
        original: dict[str, Any] = {}
        seen: set[str] = set()

        # Iterate row keys and map to attrs via cached dict
        for key, raw in row.items():
            mapping = col_to_attr.get(key)
            if mapping is not None:
                attr_name, field = mapping
                converted = field.to_python(raw)
                if isinstance(field, ForeignKey) and converted is not None:
                    # A raw FK id read straight off a row is NOT a related
                    # model instance -- wrap it so accessing it as one
                    # raises a clear, actionable fault instead of a
                    # confusing AttributeError on the wrong type. Real
                    # hydration (select_related()/prefetch_related()/
                    # related()) always overwrites this with the actual
                    # instance afterward.
                    converted = RelatedNotLoaded(converted, field_name=attr_name, owner_model_name=cls.__name__)
                setattr(instance, attr_name, converted)
                original[attr_name] = converted
                seen.add(attr_name)

        # Fields not present in the row were excluded via only()/defer().
        # Do NOT default them to None -- that would be indistinguishable
        # from a real database NULL (worse: without this guard the raw
        # class-level Field object leaks through instead, since fields are
        # plain attributes with no descriptor to intercept the miss -- see
        # hasattr() being unreliable here for the same reason). Mark them
        # deferred and swap this instance's class to a guarded variant that
        # raises DeferredFieldAccessFault on access; every other (fully
        # loaded) instance pays zero extra cost.
        deferred = {attr_name for attr_name, _field in cls._non_m2m_fields if attr_name not in seen}

        if deferred:
            instance._deferred_fields = deferred
            instance.__class__ = _deferred_guard_class(cls)

        # Snapshot for dirty tracking (used by save())
        instance._original_values = original
        return instance

    # ── SQL Generation ───────────────────────────────────────────────

    @classmethod
    def generate_create_table_sql(cls, dialect: str = "sqlite") -> str:
        """Generate CREATE TABLE SQL using CreateTableBuilder."""
        builder = CreateTableBuilder(cls._table_name)

        for _attr_name, field in cls._non_m2m_fields:
            col_def = field.sql_column_def(dialect)
            if col_def:
                builder.column(col_def)

        # unique_together constraints
        for ut in cls._meta.unique_together:
            col_list = ", ".join(f'"{f}"' for f in ut)
            builder.constraint(f"UNIQUE ({col_list})")

        # Meta.constraints -- CheckConstraint, UniqueConstraint, etc.
        for constraint in cls._meta.constraints:
            if hasattr(constraint, "sql"):
                builder.constraint(constraint.sql(cls._table_name, dialect))
            elif hasattr(constraint, "fields"):
                from .schema_snapshot import _compile_schema_expression

                # Check if this unique constraint contains expressions.
                # If so, do NOT generate it as a table constraint (it will fail on CREATE TABLE).
                # Instead, it will be generated as a unique index in generate_index_sql.
                has_expression = any(
                    not isinstance(f, str) or "(" in str(f) or '"' in str(f) for f in constraint.fields
                )
                if has_expression:
                    continue

                cols = []
                for f in constraint.fields:
                    if isinstance(f, str) and not ("(" in f or '"' in f):
                        cols.append(f'"{f}"')
                    else:
                        cols.append(_compile_schema_expression(f, cls, dialect))
                col_list = ", ".join(cols)
                if getattr(constraint, "name", None):
                    builder.constraint(f'CONSTRAINT "{constraint.name}" UNIQUE ({col_list})')
                else:
                    builder.constraint(f"UNIQUE ({col_list})")

        return builder.build()

    @classmethod
    def generate_index_sql(cls, dialect: str = "sqlite") -> list[str]:
        """Generate CREATE INDEX statements from Meta.indexes."""
        stmts: list[str] = []
        for idx in cls._meta.indexes:
            stmts.append(idx.sql(cls._table_name, dialect=dialect))

        # Also generate unique indexes for UniqueConstraints that contain expressions
        for constraint in cls._meta.constraints:
            if not hasattr(constraint, "sql") and hasattr(constraint, "fields"):
                has_expression = any(
                    not isinstance(f, str) or "(" in str(f) or '"' in str(f) for f in constraint.fields
                )
                if has_expression:
                    import re

                    from .schema_snapshot import _compile_schema_expression

                    cols = []
                    for f in constraint.fields:
                        if isinstance(f, str) and not ("(" in f or '"' in f):
                            cols.append(f'"{f}"')
                        else:
                            cols.append(_compile_schema_expression(f, cls, dialect))
                    col_list = ", ".join(cols)

                    if getattr(constraint, "name", None):
                        idx_name = constraint.name
                    else:
                        # Fallback unique index name
                        clean_exprs = "_".join(
                            re.sub(r"[^a-zA-Z0-9_]", "_", str(f)).strip("_") for f in constraint.fields
                        )
                        idx_name = f"uidx_{cls._table_name}_{clean_exprs}"

                    ine = "" if dialect in ("mysql", "oracle") else " IF NOT EXISTS"
                    stmts.append(f'CREATE UNIQUE INDEX{ine} "{idx_name}" ON "{cls._table_name}" ({col_list});')

        # db_index on individual fields
        ine = "" if dialect == "mysql" else " IF NOT EXISTS"
        for _attr_name, field in cls._fields.items():
            if field.db_index and not field.primary_key and not field.unique:
                idx_name = f"idx_{cls._table_name}_{field.column_name}"
                stmts.append(f'CREATE INDEX{ine} "{idx_name}" ON "{cls._table_name}" ("{field.column_name}");')

        return stmts

    @classmethod
    def generate_m2m_sql(cls, dialect: str = "sqlite") -> list[str]:
        """Generate junction table SQL for M2M fields."""
        stmts: list[str] = []
        for _attr_name, m2m in cls._m2m_fields.items():
            if m2m.through:
                continue  # User-defined through table

            jt = m2m.junction_table_name(cls)
            src_col, tgt_col = m2m.junction_columns(cls)

            # Dialect-aware primary key definition
            if dialect == "postgresql":
                pk_def = '"id" SERIAL PRIMARY KEY'
            elif dialect == "mysql":
                pk_def = '"id" INTEGER PRIMARY KEY AUTO_INCREMENT'
            elif dialect == "oracle":
                pk_def = '"id" NUMBER(10) GENERATED ALWAYS AS IDENTITY PRIMARY KEY'
            else:
                pk_def = '"id" INTEGER PRIMARY KEY AUTOINCREMENT'

            sql = (
                f'CREATE TABLE IF NOT EXISTS "{jt}" (\n'
                f"  {pk_def},\n"
                f'  "{src_col}" INTEGER NOT NULL,\n'
                f'  "{tgt_col}" INTEGER NOT NULL,\n'
                f'  UNIQUE ("{src_col}", "{tgt_col}")\n'
                f");"
            )
            stmts.append(sql)
        return stmts

    @classmethod
    def fingerprint(cls) -> str:
        """Compute deterministic hash for migration diffing."""
        data = {
            "name": cls.__name__,
            "table": cls._table_name,
            "fields": {
                name: field.deconstruct()
                for name, field in cls._fields.items()
                if not isinstance(field, ManyToManyField)
            },
        }
        raw = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

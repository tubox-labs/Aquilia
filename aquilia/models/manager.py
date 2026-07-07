"""
Aquilia Model Manager -- descriptor-based QuerySet access.

Manager with async-first design.

Every Model gets a default ``objects`` Manager, which proxies all
query methods to the Q (QuerySet) class. Custom managers can override
``get_queryset()`` for pre-filtered defaults.

Usage:
    class User(Model):
        table = "users"
        name = CharField(max_length=150)
        objects = Manager()  # auto-attached even if omitted

    # QuerySet access via manager
    users = await User.objects.filter(active=True).all()
    users = await User.objects.all()

    # Custom manager with pre-filtered queryset
    class PublishedManager(Manager):
        def get_queryset(self):
            return super().get_queryset().filter(status="published")

    class Article(Model):
        objects = Manager()
        published = PublishedManager()

    # Custom QuerySet methods composed into manager
    class UserQuerySet(QuerySet):
        def active(self):
            return self.get_queryset().filter(active=True)

    UserManager = Manager.from_queryset(UserQuerySet)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, TypeVar, cast

if TYPE_CHECKING:
    from .base import Model
    from .query import Q


__all__ = ["Manager", "BaseManager", "QuerySet", "RelatedManager"]

M = TypeVar("M", bound="BaseManager")

#: Bound to Model -- parametrizes QuerySet/BaseManager/Manager so
#: `UserModel.objects.filter(...)` keeps resolving to `UserModel` (not the
#: bare Model base) through every chained/terminal call, restoring IDE and
#: mypy field-name autocomplete on the result.
TModel = TypeVar("TModel", bound="Model")


def _manager_attr_name(manager: BaseManager, owner: type) -> str:
    """Return the attribute name under which *manager* is stored on *owner*.

    Walks the MRO so inherited managers (e.g. ``objects`` defined on a base
    model) are still resolved correctly. Falls back to ``"objects"`` if the
    manager instance cannot be found -- this should never happen in practice
    since ``__set_name__`` runs before ``__get__``.
    """
    for cls in owner.__mro__:
        for name, val in vars(cls).items():
            if val is manager:
                return name
    return "objects"


class QuerySet(Generic[TModel]):
    """
    Reusable query method set -- compose into Manager via from_queryset().

    Define custom chainable query shortcuts here:

        class UserQuerySet(QuerySet):
            def active(self):
                return self.get_queryset().filter(active=True)

            def adults(self):
                return self.get_queryset().filter(age__gte=18)

        UserManager = Manager.from_queryset(UserQuerySet)

        class User(Model):
            objects = UserManager()

        # Chain custom + built-in methods:
        users = await User.objects.active().adults().order("-name").all()
    """

    _model_cls: type[TModel] | None = None

    def _get_queryset(self) -> Q[TModel]:
        """Return a fresh ``Q`` bound to ``self._model_cls``.

        Raises ``ModelRegistrationFault`` if this ``QuerySet`` hasn't been
        composed into a ``Manager`` yet (i.e. ``_model_cls`` is still
        ``None``) -- happens if a ``QuerySet`` subclass is used standalone
        instead of via ``Manager.from_queryset()``.
        """
        if self._model_cls is None:
            from aquilia.faults.domains import ModelRegistrationFault

            raise ModelRegistrationFault(
                model_name="<unknown>",
                reason="QuerySet is not bound to a model",
            )
        return self._model_cls.query()

    def get_queryset(self) -> Q[TModel]:
        """Public entry point for custom query methods -- delegates to ``_get_queryset()``.

        Override this (not ``_get_queryset()``) in a ``QuerySet`` subclass if
        you need pre-filtering, mirroring ``Manager.get_queryset()``.
        """
        return self._get_queryset()


class BaseManager(Generic[TModel]):
    """
    Base manager with Python descriptor protocol.

    Accessible only from the model CLASS, not from instances:
        User.objects.filter(...)    #
        user.objects                # AttributeError
    """

    _model_cls: type[TModel] | None = None

    def __set_name__(self, owner: type, name: str) -> None:
        """Bind this manager to its owning model at class-body definition time.

        Called automatically by Python when the manager is assigned as a
        class attribute (e.g. ``objects = Manager()`` inside ``class User(Model)``),
        letting ``self._model_cls`` be resolved before ``__get__`` ever runs.
        """
        self._model_cls = cast("type[TModel]", owner)

    def __get__(self: M, instance: Any, owner: type) -> M:
        """Descriptor accessor -- returns the (class-bound) manager itself.

        Re-binds ``_model_cls`` to *owner* on every access so subclassing
        works correctly (e.g. a manager defined on a base model resolves to
        the concrete subclass when accessed as ``SubModel.objects``).

        Raises ``AttributeError`` if accessed from an instance rather than
        the class (``user.objects`` fails; only ``User.objects`` works),
        since a single ``Manager()`` is shared across every row and isn't
        parametrized per-instance -- see ``RelatedManager`` for the
        per-instance equivalent.
        """
        # Bind to current class (supports inheritance)
        self._model_cls = cast("type[TModel]", owner)
        if instance is not None:
            from aquilia.faults.domains import ManagerInstanceAccessFault

            model_name = owner.__name__ if owner is not None else "<unknown>"
            raise ManagerInstanceAccessFault(
                model_name=model_name,
                manager_name=_manager_attr_name(self, owner),
            )
        return self

    # ── QuerySet factory ─────────────────────────────────────────────

    def _get_queryset(self) -> Q[TModel]:
        """Return a fresh Q (QuerySet) for the model."""
        if self._model_cls is None:
            from aquilia.faults.domains import ModelRegistrationFault

            raise ModelRegistrationFault(
                model_name="<unknown>",
                reason="Manager is not bound to a model",
            )
        return self._model_cls.query()

    def get_queryset(self) -> Q[TModel]:
        """
        Override point for custom managers.

        Return a pre-filtered queryset for all queries through this manager:

            class ActiveManager(Manager):
                def get_queryset(self):
                    return super().get_queryset().filter(active=True)
        """
        return self._get_queryset()

    # ── Forwarded chain methods (return Q) ───────────────────────────

    def filter(self, *q_nodes: Any, **kwargs: Any) -> Q[TModel]:
        """Field filtering. See Q.filter() for details."""
        return self.get_queryset().filter(*q_nodes, **kwargs)

    def exclude(self, **kwargs: Any) -> Q[TModel]:
        """Negated filter. See Q.exclude() for details."""
        return self.get_queryset().exclude(**kwargs)

    def where(self, clause: str, *args: Any, **kwargs: Any) -> Q[TModel]:
        """Raw WHERE clause (Aquilia-only). See Q.where() for details."""
        return self.get_queryset().where(clause, *args, **kwargs)

    def order(self, *fields: Any) -> Q[TModel]:
        """ORDER BY. See Q.order() for details -- supports str, F().desc(), OrderBy."""
        return self.get_queryset().order(*fields)

    # Alias
    order_by = order

    def limit(self, n: int) -> Q[TModel]:
        """Cap the number of rows returned (SQL ``LIMIT``). See Q.limit()."""
        return self.get_queryset().limit(n)

    def offset(self, n: int) -> Q[TModel]:
        """Skip the first *n* rows before returning results (SQL ``OFFSET``). See Q.offset()."""
        return self.get_queryset().offset(n)

    def distinct(self) -> Q[TModel]:
        """Deduplicate rows via ``SELECT DISTINCT``. See Q.distinct()."""
        return self.get_queryset().distinct()

    def only(self, *fields: str) -> Q[TModel]:
        """Load only specified fields."""
        return self.get_queryset().only(*fields)

    def defer(self, *fields: str) -> Q[TModel]:
        """Defer loading of specified fields."""
        return self.get_queryset().defer(*fields)

    def annotate(self, **expressions: Any) -> Q[TModel]:
        """Add annotations. See Q.annotate() for details."""
        return self.get_queryset().annotate(**expressions)

    def group_by(self, *fields: str) -> Q[TModel]:
        """Add a SQL ``GROUP BY`` over *fields* (paired with ``aggregate()``/``having()``). See Q.group_by()."""
        return self.get_queryset().group_by(*fields)

    def having(self, clause: str, *args: Any) -> Q[TModel]:
        """HAVING clause (use after group_by)."""
        return self.get_queryset().having(clause, *args)

    def union(self, *querysets: Any, all: bool = False) -> Q[TModel]:
        """Combine with other querysets via SQL ``UNION`` (dedupes unless ``all=True``). See Q.union()."""
        return self.get_queryset().union(*querysets, all=all)

    def intersection(self, *querysets: Any) -> Q[TModel]:
        """Combine with other querysets via SQL ``INTERSECT`` (rows present in all sets). See Q.intersection()."""
        return self.get_queryset().intersection(*querysets)

    def difference(self, *querysets: Any) -> Q[TModel]:
        """Combine with other querysets via SQL ``EXCEPT`` (rows in this set but not the others). See Q.difference()."""
        return self.get_queryset().difference(*querysets)

    def select_related(self, *fields: str) -> Q[TModel]:
        """JOIN-based eager loading."""
        return self.get_queryset().select_related(*fields)

    def prefetch_related(self, *lookups: Any) -> Q[TModel]:
        """Separate-query prefetching. Accepts strings or Prefetch objects."""
        return self.get_queryset().prefetch_related(*lookups)

    def select_for_update(self, **kwargs: Any) -> Q[TModel]:
        """SELECT ... FOR UPDATE (locking)."""
        return self.get_queryset().select_for_update(**kwargs)

    def iterator(self, chunk_size: int = 2000) -> Q[TModel]:
        """Memory-efficient chunked iteration. See Q.iterator() for details."""
        return self.get_queryset().iterator(chunk_size=chunk_size)

    def using(self, db_alias: str) -> Q[TModel]:
        """Target a specific database."""
        return self.get_queryset().using(db_alias)

    def none(self) -> Q[TModel]:
        """Return an empty queryset -- ``all()`` yields ``[]``, ``count()`` yields ``0``, no SQL is run.

        Useful as a no-op branch in conditional query-building code, e.g.
        returning ``self.get_queryset().none()`` when a precondition for a
        custom manager method isn't met, instead of special-casing the caller.
        """
        return self.get_queryset().none()

    def apply_q(self, q_node: Any) -> Q[TModel]:
        """Apply a composable ``QNode`` filter (supports AND/OR/NOT via ``&``, ``|``, ``~``). See Q.apply_q()."""
        return self.get_queryset().apply_q(q_node)

    # ── Forwarded terminal methods (async) ───────────────────────────

    async def all(self) -> list[TModel]:
        """Execute the query and return every matching row as a model instance. See Q.all()."""
        return await self.get_queryset().all()

    async def first(self) -> TModel | None:
        """Return the first matching row, or ``None`` if there are no matches. See Q.first()."""
        return await self.get_queryset().first()

    async def last(self) -> TModel | None:
        """Return the last matching row (reverses ordering), or ``None`` if empty. See Q.last()."""
        return await self.get_queryset().last()

    async def one(self) -> TModel:
        """Return exactly one row. Raises if 0 or >1 (Aquilia-only)."""
        return await self.get_queryset().one()

    async def latest(self, field_name: str | None = None) -> TModel:
        """Return latest record by date field."""
        return await self.get_queryset().latest(field_name)

    async def earliest(self, field_name: str | None = None) -> TModel:
        """Return earliest record by date field."""
        return await self.get_queryset().earliest(field_name)

    async def count(self) -> int:
        """Return the number of matching rows via ``SELECT COUNT(*)``. See Q.count()."""
        return await self.get_queryset().count()

    async def exists(self) -> bool:
        """Return whether any matching row exists, using a short-circuiting ``EXISTS`` query. See Q.exists()."""
        return await self.get_queryset().exists()

    async def values(self, *fields: str) -> list[dict[str, Any]]:
        """Return matching rows as plain dicts restricted to *fields* (all fields if omitted). See Q.values()."""
        return await self.get_queryset().values(*fields)

    async def values_list(self, *fields: str, flat: bool = False) -> list[Any]:
        """Return matching rows as tuples of *fields*; if ``flat=True`` and one field, returns a flat list. See Q.values_list()."""
        return await self.get_queryset().values_list(*fields, flat=flat)

    async def update(self, values: dict[str, Any] | None = None, **kwargs: Any) -> int:
        """Update matching rows in bulk and return the affected row count. Does not fire save signals. See Q.update()."""
        return await self.get_queryset().update(values or {}, **kwargs)

    async def delete(self) -> int:
        """Delete matching rows in bulk and return the deleted row count. Does not fire delete signals. See Q.delete()."""
        return await self.get_queryset().delete()

    async def aggregate(self, **expressions: Any) -> dict[str, Any]:
        """Compute aggregates. See Q.aggregate() for details."""
        return await self.get_queryset().aggregate(**expressions)

    async def in_bulk(self, id_list: list[Any]) -> dict[Any, TModel]:
        """Return dict mapping PKs to instances."""
        return await self.get_queryset().in_bulk(id_list)

    async def explain(self, **kwargs: Any) -> str:
        """Return query execution plan."""
        return await self.get_queryset().explain(**kwargs)

    # ── Convenience shortcuts (delegate to Model class methods) ──────

    async def get(self, pk: Any = None, **filters: Any) -> TModel | None:
        """
        Get a single instance by PK or filter kwargs.

        Usage:
            user = await User.objects.get(pk=1)
            user = await User.objects.get(email="alice@example.com")
        """
        if self._model_cls is None:
            from aquilia.faults.domains import ModelRegistrationFault

            raise ModelRegistrationFault(
                model_name="<unknown>",
                reason="Manager is not bound to a model",
            )
        return await self._model_cls.get(pk=pk, **filters)

    async def get_or_create(self, defaults: dict[str, Any] | None = None, **lookup: Any) -> tuple[TModel, bool]:
        """
        Get existing instance or create a new one.

        Returns (instance, created) tuple.

        Usage:
            user, created = await User.objects.get_or_create(
                email="alice@example.com",
                defaults={"name": "Alice"}
            )
        """
        if self._model_cls is None:
            from aquilia.faults.domains import ModelRegistrationFault

            raise ModelRegistrationFault(
                model_name="<unknown>",
                reason="Manager is not bound to a model",
            )
        return await self._model_cls.get_or_create(defaults=defaults, **lookup)

    async def update_or_create(self, defaults: dict[str, Any] | None = None, **lookup: Any) -> tuple[TModel, bool]:
        """
        Update existing instance or create a new one.

        Returns (instance, created) tuple.

        Usage:
            user, created = await User.objects.update_or_create(
                email="alice@example.com",
                defaults={"name": "Alice Updated", "active": True}
            )
        """
        if self._model_cls is None:
            from aquilia.faults.domains import ModelRegistrationFault

            raise ModelRegistrationFault(
                model_name="<unknown>",
                reason="Manager is not bound to a model",
            )
        return await self._model_cls.update_or_create(defaults=defaults, **lookup)

    async def create(self, **data: Any) -> TModel:
        """
        Create and save a new instance.

        Usage:
            user = await User.objects.create(name="Alice", email="a@b.com")
        """
        if self._model_cls is None:
            from aquilia.faults.domains import ModelRegistrationFault

            raise ModelRegistrationFault(
                model_name="<unknown>",
                reason="Manager is not bound to a model",
            )
        return await self._model_cls.create(**data)

    async def bulk_create(
        self,
        instances: list[Any],
        *,
        batch_size: int | None = None,
        ignore_conflicts: bool = False,
    ) -> list[TModel]:
        """
        Create multiple instances efficiently.

        Usage:
            users = await User.objects.bulk_create([
                {"name": "Alice"}, {"name": "Bob"}
            ], batch_size=100)
        """
        if self._model_cls is None:
            from aquilia.faults.domains import ModelRegistrationFault

            raise ModelRegistrationFault(
                model_name="<unknown>",
                reason="Manager is not bound to a model",
            )
        return await self._model_cls.bulk_create(instances, batch_size=batch_size, ignore_conflicts=ignore_conflicts)

    async def bulk_update(
        self,
        instances: list[TModel],
        fields: list[str],
        *,
        batch_size: int | None = None,
    ) -> int:
        """
        Update specific fields on multiple instances.

        Usage:
            users = await User.objects.filter(active=True).all()
            for u in users:
                u.score += 10
            await User.objects.bulk_update(users, ["score"], batch_size=50)
        """
        if self._model_cls is None:
            from aquilia.faults.domains import ModelRegistrationFault

            raise ModelRegistrationFault(
                model_name="<unknown>",
                reason="Manager is not bound to a model",
            )
        return await self._model_cls.bulk_update(instances, fields, batch_size=batch_size)

    async def raw(self, sql: str, params: list[Any] | None = None) -> list[TModel]:
        """
        Execute raw SQL and return model instances.

        Usage:
            users = await User.objects.raw(
                "SELECT * FROM users WHERE score > ? ORDER BY score DESC", [100]
            )
        """
        if self._model_cls is None:
            from aquilia.faults.domains import ModelRegistrationFault

            raise ModelRegistrationFault(
                model_name="<unknown>",
                reason="Manager is not bound to a model",
            )
        return await self._model_cls.raw(sql, params)

    # ── Slicing support ──────────────────────────────────────────────

    def __getitem__(self, key: Any) -> Q[TModel]:
        """
        Slice support: User.objects[:5], User.objects[10:20]
        """
        return self.get_queryset()[key]

    # ── Async iteration ──────────────────────────────────────────────

    def __aiter__(self):
        """
        Async iteration: async for user in User.objects: ...
        """
        return self.get_queryset().__aiter__()

    def __repr__(self) -> str:
        """Debug string naming the manager class and its bound model (or ``<unbound>``)."""
        model_name = self._model_cls.__name__ if self._model_cls else "<unbound>"
        return f"<{self.__class__.__name__} for {model_name}>"


class Manager(BaseManager[TModel]):
    """
    Default manager -- auto-attached as ``objects`` on every Model.

    Override ``get_queryset()`` for custom pre-filtered managers:

        class PublishedManager(Manager):
            def get_queryset(self):
                return super().get_queryset().filter(status="published")

        class Article(Model):
            table = "articles"
            title = CharField(max_length=200)
            status = CharField(max_length=20, default="draft")

            objects = Manager()             # default (all articles)
            published = PublishedManager()  # pre-filtered

        # Usage:
        all_articles = await Article.objects.all()
        pub_articles = await Article.published.filter(author="Alice").all()

    Or use from_queryset() to compose reusable query methods:

        class ArticleQuerySet(QuerySet):
            def published(self):
                return self.get_queryset().filter(status="published")

            def by_author(self, author_id):
                return self.get_queryset().filter(author_id=author_id)

        ArticleManager = Manager.from_queryset(ArticleQuerySet)
    """

    @classmethod
    def from_queryset(cls, queryset_class: type, class_name: str | None = None) -> type:
        """
        Create a Manager subclass that includes methods from a QuerySet.

        Allows defining reusable query shortcuts on a QuerySet class
        and making them available directly on the Manager:

            class CustomQuerySet(QuerySet):
                def active(self):
                    return self.get_queryset().filter(active=True)

            CustomManager = Manager.from_queryset(CustomQuerySet)

            class MyModel(Model):
                objects = CustomManager()

            # Now available: MyModel.objects.active().order("-name").all()
        """
        if class_name is None:
            class_name = f"{cls.__name__}From{queryset_class.__name__}"

        # Copy non-private QuerySet methods to a new Manager subclass
        attrs: dict[str, Any] = {}
        for attr_name in dir(queryset_class):
            if attr_name.startswith("_"):
                continue
            attr = getattr(queryset_class, attr_name)
            if callable(attr) and attr_name not in dir(cls):

                def _make_proxy(method_name: str):
                    def _proxy(self_mgr, *args, **kwargs):
                        # Get the base queryset through get_queryset() to preserve
                        # any manager-level filtering (e.g., PublishedManager)
                        qs = self_mgr.get_queryset()
                        return getattr(qs, method_name)(*args, **kwargs)

                    _proxy.__name__ = method_name
                    _proxy.__qualname__ = f"{class_name}.{method_name}"
                    return _proxy

                attrs[attr_name] = _make_proxy(attr_name)

        new_cls = type(class_name, (cls,), attrs)
        return new_cls


class RelatedManager(Manager[TModel]):
    """
    Instance-bound reverse-relation manager -- returned by
    ``Model.related_manager(name)``, not attached as a class attribute.

    ``BaseManager`` (and therefore ``Manager``) is deliberately class-only:
    its ``__get__`` raises ``AttributeError`` if accessed from an instance
    (``user.objects`` fails; only ``User.objects`` works), because a single
    ``Manager()`` object is shared across every instance of a model and
    isn't parametrized per-row. A reverse relation needs the opposite --
    one manager bound to *this* row's primary key -- so ``RelatedManager``
    is constructed directly (by ``related_manager()``) instead of through
    the descriptor protocol, and pre-filters every query through the
    owning instance's pk via ``get_queryset()``, following the exact same
    override shape as the ``PublishedManager`` example in this module's
    docstring -- just parametrized per-instance instead of per-class:

        class PublishedManager(Manager):
            def get_queryset(self):
                return super().get_queryset().filter(status="published")

    Fully lazy like every other manager/queryset in this ORM -- nothing
    executes until a terminal method (``.all()``, ``.count()``, etc.) is
    awaited, so it composes with the rest of the chainable query API:

        await user.related_manager("verifications").filter(
            expires_at__gt=now,
        ).order("-created_at").first()
    """

    # Narrows BaseManager's `type[TModel] | None` -- a RelatedManager is
    # always constructed with a concrete model class, never left unbound.
    _model_cls: type[TModel]

    def __init__(self, model_cls: type[TModel], fk_column_name: str, owner_pk: Any) -> None:
        """Bind this manager to one owning row.

        Args:
            model_cls: The related model being queried (the "many" side).
            fk_column_name: Column on *model_cls*'s table holding the foreign key
                back to the owning instance.
            owner_pk: The owning instance's primary key value to filter by.
        """
        self._model_cls = model_cls
        self._fk_column_name = fk_column_name
        self._owner_pk = owner_pk

    def get_queryset(self) -> Q[TModel]:
        """Return a queryset pre-filtered to rows whose FK column matches the owning instance's pk."""
        return self._model_cls.query().where(f'"{self._fk_column_name}" = ?', self._owner_pk)

    def __repr__(self) -> str:
        """Debug string showing the target model and the FK = owner_pk filter applied."""
        return f'<RelatedManager for {self._model_cls.__name__} where "{self._fk_column_name}" = {self._owner_pk!r}>'

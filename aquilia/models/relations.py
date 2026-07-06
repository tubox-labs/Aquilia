"""
Aquilia relation-access primitives.

Aquilia's DB layer (``aquilia/db/engine.py``) is 100% ``async def`` with no
synchronous fallback, and Python's descriptor protocol requires ``__get__``
to be synchronous -- so a ForeignKey/OneToOneField attribute can never
transparently run a hidden query on first access the way Django's
``ForwardManyToOneDescriptor`` does. There is no legal way to ``await``
inside ``__get__``. Hydration in Aquilia is therefore always explicit:

    await instance.related("user")                       # one-shot fetch + cache
    await Model.objects.select_related("user").first()    # eager JOIN
    await Model.objects.prefetch_related("user").all()    # eager batch
    await instance.related_manager("posts").filter(...)   # lazy reverse relation

Reading a ForeignKey/OneToOneField attribute that hasn't been hydrated by
one of the above returns a ``RelatedNotLoaded`` sentinel instead of the raw
stored id, so code that forgets to hydrate gets a clear, actionable error
the moment it tries to use the value as a model instance (e.g.
``instance.user.name``), rather than a confusing ``AttributeError`` from
treating a raw scalar as if it were the related object.
"""

from __future__ import annotations

from typing import Any

__all__ = ["RelatedNotLoaded"]


class RelatedNotLoaded:
    """
    Placeholder for a ForeignKey/OneToOneField attribute that holds a real,
    non-null foreign key value but hasn't been resolved to a related model
    instance yet.

    Cheap, no-query operations work directly on the sentinel:

        if instance.user:               # bool() -- True (pk is set)
        instance.user.pk                # raw stored id, no query
        instance.user == other_user     # compares by pk, no query

    Anything else raises ``RelatedNotLoadedFault`` with guidance on how to
    hydrate the relation:

        instance.user.name              # raises RelatedNotLoadedFault

    Once hydrated -- via ``select_related()``, ``prefetch_related()``, or
    ``await instance.related(field_name)`` -- the attribute holds the real
    model instance instead of this sentinel, permanently, for that instance.
    """

    __slots__ = ("_pk", "_field_name", "_owner_model_name")

    def __init__(self, pk: Any, *, field_name: str, owner_model_name: str) -> None:
        self._pk = pk
        self._field_name = field_name
        self._owner_model_name = owner_model_name

    @property
    def pk(self) -> Any:
        """The raw stored foreign key value -- no query, always available."""
        return self._pk

    # Alias -- mirrors the Model.pk / <field>_id convention used elsewhere
    # in the ORM (e.g. a hydrated instance's own .pk property).
    id = pk

    def __bool__(self) -> bool:
        return self._pk is not None

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, RelatedNotLoaded):
            return bool(self._pk == other._pk)
        if hasattr(other, "pk") and hasattr(other, "_fields"):
            # Duck-typed as a hydrated Model instance of some kind.
            return bool(self._pk == other.pk)
        return bool(self._pk == other)

    def __hash__(self) -> int:
        return hash(self._pk)

    def __repr__(self) -> str:
        return (
            f"<RelatedNotLoaded: {self._owner_model_name}.{self._field_name} "
            f"(pk={self._pk!r}) -- call `await instance.related({self._field_name!r})` "
            f"or use `.select_related({self._field_name!r})` on the query to load it>"
        )

    __str__ = __repr__

    def __getattr__(self, name: str) -> Any:
        # __slots__ entries and the pk/id property above are resolved by
        # normal attribute lookup and never reach here. Anything else means
        # calling code is trying to use this sentinel as if it already were
        # the hydrated related instance.
        from ..faults.domains import RelatedNotLoadedFault

        raise RelatedNotLoadedFault(
            model_name=self._owner_model_name,
            field_name=self._field_name,
            pk=self._pk,
        )

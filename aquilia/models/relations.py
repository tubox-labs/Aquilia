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

from typing import TYPE_CHECKING, Any, Generic, TypeAlias, TypeVar

if TYPE_CHECKING:
    from .base import Model

__all__ = ["RelatedNotLoaded", "Related"]

#: Bound to Model -- parametrizes RelatedNotLoaded so a checker can see
#: *which* model a given unhydrated relation would resolve to (e.g.
#: `RelatedNotLoaded[UserModel]`), matching the TModel convention already
#: used by Manager/QuerySet/Q (aquilia/models/manager.py).
TModel = TypeVar("TModel", bound="Model")


class RelatedNotLoaded(Generic[TModel]):
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

    Generic over the target model (``RelatedNotLoaded[UserModel]``) purely
    for static type-checking -- see ``Related[TModel]`` below, which is what
    a ``ForeignKey``/``OneToOneField`` attribute is actually typed as.
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


#: What a ForeignKey/OneToOneField attribute actually resolves to at
#: runtime: a hydrated instance of the target model, the RelatedNotLoaded
#: sentinel wrapping its raw stored id, or None (nullable FK with no value /
#: LEFT JOIN miss). ForeignKey/OneToOneField are real generic descriptors
#: (see ``aquilia.models.fields_module.ForeignKey.__get__``), so a plain,
#: unannotated field declaration already resolves to this union on instance
#: access with no extra work:
#:
#:     class Post(Model):
#:         author = ForeignKey(User, related_name="posts")
#:
#:     reveal_type(Post().author)  # User | RelatedNotLoaded[User] | None
#:
#: ``Related[TModel]`` itself is exported for the cases *outside* a field
#: declaration where you need to name the union explicitly -- a function
#: parameter/return type, a local variable, etc. Don't use it as the class
#: body's own annotation (``author: Related[User] = ForeignKey(...)``): a
#: type checker checks that assignment against ``ForeignKey[User]`` (the
#: descriptor's own type), not the instance-access union, so an explicit
#: annotation there produces a false-positive mismatch -- the same
#: descriptor-typing limitation Django-stubs/SQLAlchemy2-stubs work around
#: with a checker plugin. Leaving the field unannotated gets full,
#: correct typing for free without one.
#:
#: Narrowing (``isinstance(post.author, User)``) is required before using
#: it as the hydrated instance -- exactly the same discipline
#: RelatedNotLoadedFault already enforces at runtime, now visible statically.
Related: TypeAlias = TModel | RelatedNotLoaded[TModel] | None

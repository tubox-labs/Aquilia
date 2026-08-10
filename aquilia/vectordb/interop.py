"""
AquilaVectorDB — Interop with ``aquilia.models``.

Three mechanisms, because "interop" covers three genuinely different needs:

:class:`Link`
    A vector record carrying the primary key of a SQL row. Not a foreign key —
    elips enforces nothing and there is no join. Resolution is always explicit.

:func:`mirror`
    Keeps a vector collection in sync with a SQL table via ``post_save`` /
    ``post_delete``. One-way: the mirror never writes back into SQL.

:func:`as_models`
    Runs a vector search, then hydrates the matching ORM rows in *relevance*
    order with a single SQL round trip.

The dependency arrow points one way
------------------------------------

This module imports ``aquilia.models``; nothing in ``aquilia.models`` imports
``aquilia.vectordb``. That is what keeps ``elips`` genuinely optional — an app
using only the SQL ORM never loads any of this. The
:mod:`aquilia.vectordb.__init__` module defers importing it for the same reason.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, TypeVar

from aquilia.vectordb.faults import VectorRegistryFault, VectorSchemaFault

if TYPE_CHECKING:
    from aquilia.models.base import Model
    from aquilia.vectordb.base import VectorModel
    from aquilia.vectordb.query import Hit

logger = logging.getLogger("aquilia.vectordb.interop")

TModel = TypeVar("TModel", bound="Model")

#: SQLite caps a statement at 999 bound parameters, which ``models/query.py``
#: already respects via ``in_bulk(batch_size=999)``. ``as_models`` chunks
#: ``pk__in`` to match rather than discovering the ceiling on a large result set.
PK_CHUNK_SIZE = 999

OnDelete = Literal["detach", "purge"]
SyncMode = Literal["task", "inline"]


@dataclass(frozen=True)
class Link:
    """
    Marks a payload attribute holding the primary key of a SQL row.

    Compiles to an ordinary :class:`~aquilia.vectordb.annotations.Payload` entry
    plus registry metadata naming the target model. It is deliberately *not* a
    foreign key: elips has no referential integrity, no cascade, and no join.

    Example::

        class Document(VectorModel):
            key:     Annotated[str, Key()]
            body:    Annotated[str, Text()]
            user_id: Annotated[int, Link(User)]

        hit = (await Document.vectors.search("alpha"))[0]
        user = await resolve(hit, "user_id")     # one SELECT, explicit

    Args:
        model: The target ``Model`` class, or a dotted ``"module:Class"`` path
            for a forward reference.
        on_delete: What happens to vector records when the SQL row is deleted.
            Honoured only when the SQL model is mirrored (:func:`mirror`).

            * ``"detach"`` (default) — leave the vector record. It is still
              searchable; its link simply points at nothing.
            * ``"purge"`` — delete vector records whose link matches.

            There is no ``"cascade"`` spelling on purpose: it would imply a
            database-level guarantee that does not exist here.
    """

    model: Any
    on_delete: OnDelete = "detach"

    def resolve_model(self) -> type[Model]:
        """
        Resolve the target model class, importing a dotted reference if needed.

        Raises:
            VectorSchemaFault: When the reference cannot be resolved.
        """
        if isinstance(self.model, type):
            return self.model

        ref = str(self.model)
        if ":" in ref:
            module_path, _, class_name = ref.partition(":")
        else:
            module_path, _, class_name = ref.rpartition(".")

        if not module_path:
            from aquilia.models.registry import ModelRegistry

            resolved = ModelRegistry.get(ref)
            if resolved is None:
                raise VectorSchemaFault(
                    model="<link>",
                    reason=f"Link target {ref!r} is not a registered model",
                )
            return resolved

        import importlib

        try:
            module = importlib.import_module(module_path)
        except ImportError as exc:
            raise VectorSchemaFault(
                model="<link>",
                reason=f"cannot import Link target module {module_path!r}: {exc}",
            ) from exc

        target = getattr(module, class_name, None)
        if not isinstance(target, type):
            raise VectorSchemaFault(
                model="<link>",
                reason=f"Link target {ref!r} did not resolve to a class",
            )
        return target


# ============================================================================
# Link resolution
# ============================================================================


async def resolve(hit: Hit[Any] | VectorModel, attr: str) -> Model | None:
    """
    Resolve a :class:`Link` attribute to its SQL row.

    Explicit by design, following the ``RelatedNotLoaded`` precedent in
    ``aquilia/models/relations.py``: a descriptor that silently issued a SELECT
    on attribute access turns one loop into N queries with nothing at the call
    site to suggest it.

    Args:
        hit: A :class:`~aquilia.vectordb.query.Hit` or a vector model instance.
        attr: The linked attribute name.

    Returns:
        The SQL row, or ``None`` when the link is unset or the row is gone.

    Raises:
        VectorSchemaFault: When ``attr`` is not a declared link.
    """
    record = getattr(hit, "record", hit)
    model_cls = type(record)
    links = getattr(model_cls, "_vlinks", {})

    link = links.get(attr)
    if link is None:
        declared = ", ".join(sorted(links)) or "(none)"
        raise VectorSchemaFault(
            model=model_cls.__name__,
            reason=f"{attr!r} is not a Link attribute. Declared links: {declared}",
        )

    value = getattr(record, attr, None)
    if value is None:
        return None

    target = link.resolve_model()
    # `pk` is a property on Model instances, not a filter alias, so the query
    # has to name the actual primary-key attribute.
    return await target.query().filter(**{target._pk_attr: value}).first()


# ============================================================================
# Mirroring
# ============================================================================


@dataclass(frozen=True)
class MirrorSpec:
    """
    Compiled ``@mirror`` configuration.

    Attributes:
        source: The SQL model being mirrored.
        target: The vector model receiving records.
        text: Builds the text to embed from a SQL instance.
        meta: ``{payload attr: value or callable}``.
        key: Builds the vector record key. Deterministic, so a re-save
            overwrites rather than duplicating.
        when: Predicate deciding whether an instance should be mirrored.
        on_delete: Whether deleting the SQL row deletes the vector record.
        sync: ``"task"`` queues the write; ``"inline"`` awaits it.
        vector: Optionally builds the vector directly, bypassing embedding.
    """

    source: type[Model]
    target: type[VectorModel]
    text: Callable[[Any], str] | None = None
    meta: dict[str, Any] | None = None
    key: Callable[[Any], str] | None = None
    when: Callable[[Any], bool] | None = None
    on_delete: OnDelete = "purge"
    sync: SyncMode = "task"
    vector: Callable[[Any], list[float]] | None = None

    def build_key(self, instance: Any) -> str:
        """
        Return the vector record key for a SQL instance.

        Defaults to ``"<collection>:<record key>"``, where the collection name is
        taken from the *target vector model* rather than from the source SQL
        table. The vector side owns the key space it writes into, and naming it
        after the target keeps mirrored keys stable when the SQL table is
        renamed.

        Determinism is the whole point: the manager folds a non-UUID key into a
        stable UUIDv5, so re-saving the same row overwrites its vector record
        instead of accumulating duplicates.
        """
        if self.key is not None:
            return str(self.key(instance))
        collection = self.target.collection_name() or type(instance).__name__.lower()
        return f"{collection}:{instance.pk}"

    def build_payload(self, instance: Any) -> dict[str, Any]:
        """Return ``{attr: value}`` for the target model's payload attributes."""
        payload: dict[str, Any] = {}
        for attr, source in (self.meta or {}).items():
            payload[attr] = source(instance) if callable(source) else source
        return payload

    def should_mirror(self, instance: Any) -> bool:
        """Return whether ``instance`` currently qualifies for mirroring."""
        return True if self.when is None else bool(self.when(instance))


#: Every registered mirror, keyed by source model. Consulted by
#: ``aq vectordb reindex`` and by the signal handlers.
_MIRRORS: dict[type, MirrorSpec] = {}


def mirror(
    *,
    into: type[VectorModel],
    text: Callable[[Any], str] | None = None,
    meta: dict[str, Any] | None = None,
    key: Callable[[Any], str] | None = None,
    when: Callable[[Any], bool] | None = None,
    vector: Callable[[Any], list[float]] | None = None,
    on_delete: OnDelete = "purge",
    sync: SyncMode = "task",
) -> Callable[[type[TModel]], type[TModel]]:
    """
    Keep a vector collection in sync with a SQL model.

    Registers ``post_save`` / ``post_delete`` handlers on the existing
    ``aquilia.models.signals`` bus.

    Example::

        @mirror(
            into=Document,
            text=lambda p: f"{p.title}\\n\\n{p.body}",
            meta={"kind": "post", "author_id": lambda p: p.author_id},
            when=lambda p: p.published,
        )
        class Post(Model):
            ...

    Args:
        into: The vector model receiving mirrored records.
        text: Builds the text to embed. Required unless ``vector`` is given.
        meta: ``{payload attr: value or callable}`` written alongside.
        key: Builds the record key. Defaults to ``"<table>:<pk>"``.
        when: Predicate; instances failing it are skipped, and any existing
            vector record for them is removed — so un-publishing a post takes it
            out of the index rather than leaving a stale copy.
        vector: Builds the vector directly, bypassing server-side embedding.
        on_delete: ``"purge"`` (default) removes the vector record when the SQL
            row is deleted; ``"detach"`` leaves it.
        sync: ``"task"`` (default) enqueues the write through ``aquilia.tasks``;
            ``"inline"`` awaits it inside the signal.

    Returns:
        The decorated class, unchanged.

    Notes:
        **Queued by default, and that matters.** A vector write inside a
        request's transaction adds embedding latency to the response and cannot
        be rolled back with the SQL transaction — so a rolled-back save would
        leave an orphaned vector record. ``sync="inline"`` is available and is
        documented as best-effort.

        **Bulk writes bypass the mirror.** ``bulk_create`` / ``bulk_update``
        fire no signals, so records written that way are not mirrored.
        ``aq vectordb reindex <Model>`` is the sanctioned repair.
    """
    if text is None and vector is None:
        raise VectorSchemaFault(
            model=getattr(into, "__name__", "<target>"),
            reason="mirror() needs text= (to embed) or vector= (to store directly)",
        )

    def decorator(model_cls: type[TModel]) -> type[TModel]:
        spec = MirrorSpec(
            source=model_cls,
            target=into,
            text=text,
            meta=meta,
            key=key,
            when=when,
            vector=vector,
            on_delete=on_delete,
            sync=sync,
        )
        register_mirror(spec)
        return model_cls

    return decorator


def register_mirror(spec: MirrorSpec) -> None:
    """
    Register a mirror and connect its signal handlers.

    Args:
        spec: The compiled mirror configuration.
    """
    from aquilia.models.signals import post_delete, post_save

    _MIRRORS[spec.source] = spec

    async def _on_save(sender: type, instance: Any, **kwargs: Any) -> None:
        await _handle_save(spec, instance)

    async def _on_delete(sender: type, instance: Any, **kwargs: Any) -> None:
        await _handle_delete(spec, instance)

    # Strong references: these closures have no other owner, and a weak
    # connection would let them be collected the moment the decorator returns.
    post_save.connect(_on_save, sender=spec.source, weak=False)
    post_delete.connect(_on_delete, sender=spec.source, weak=False)


def get_mirror(model_cls: type) -> MirrorSpec | None:
    """Return the mirror registered for ``model_cls``, or ``None``."""
    return _MIRRORS.get(model_cls)


def all_mirrors() -> dict[type, MirrorSpec]:
    """Return a copy of every registered mirror."""
    return dict(_MIRRORS)


async def _handle_save(spec: MirrorSpec, instance: Any) -> None:
    """Mirror one saved SQL row into its vector collection."""
    if not spec.should_mirror(instance):
        # The row no longer qualifies (e.g. unpublished). Remove any record
        # written when it did, so the index does not serve stale content.
        await _safe(_delete_record(spec, instance), spec, "delete")
        return

    if spec.sync == "inline":
        await _safe(_write_record(spec, instance), spec, "write")
        return

    key = spec.build_key(instance)
    payload = spec.build_payload(instance)
    text = spec.text(instance) if spec.text else None
    vector = spec.vector(instance) if spec.vector else None

    if not await _enqueue(spec, "write", key=key, payload=payload, text=text, vector=vector):
        await _safe(_write_record(spec, instance), spec, "write")


async def _handle_delete(spec: MirrorSpec, instance: Any) -> None:
    """Remove a vector record when its SQL row is deleted."""
    if spec.on_delete == "detach":
        return

    if spec.sync == "inline":
        await _safe(_delete_record(spec, instance), spec, "delete")
        return

    key = spec.build_key(instance)
    if not await _enqueue(spec, "delete", key=key):
        await _safe(_delete_record(spec, instance), spec, "delete")


async def _write_record(spec: MirrorSpec, instance: Any) -> None:
    """Build and save the vector record for a SQL instance."""
    fields = spec.build_payload(instance)
    record = spec.target(**fields)

    schema = spec.target._vfields
    if schema.key_attr:
        setattr(record, schema.key_attr, spec.build_key(instance))
    if spec.text is not None and schema.text_attr:
        setattr(record, schema.text_attr, spec.text(instance))
    if spec.vector is not None and schema.vector_attr:
        setattr(record, schema.vector_attr, spec.vector(instance))

    await record.save()


async def _delete_record(spec: MirrorSpec, instance: Any) -> None:
    """Remove the vector record corresponding to a SQL instance."""
    await spec.target.vectors.remove(spec.build_key(instance))


async def _enqueue(spec: MirrorSpec, op: str, **payload: Any) -> bool:
    """
    Queue a mirror operation through ``aquilia.tasks``.

    Returns:
        ``True`` when the job was enqueued, ``False`` when no task manager is
        running — the caller then falls back to an inline write, so a mirror
        still works in a project that has not configured tasks.

    Notes:
        The fallback is logged rather than silent. This function previously
        imported a name that did not exist, so ``ImportError`` was caught on
        every call and *every* mirror ran inline — the documented
        ``sync="task"`` default never took effect and nothing said so.
    """
    from aquilia.tasks import get_task_manager

    manager = get_task_manager()
    if manager is None:
        logger.debug(
            "Mirror %s for %s running inline: no task manager is started. "
            "Configure Integration.tasks() to queue mirror writes.",
            op,
            spec.source.__name__,
        )
        return False

    try:
        await manager.enqueue(
            _run_mirror_job,
            spec.source.__name__,
            op,
            payload,
        )
        return True
    except Exception as exc:
        logger.warning(
            "Mirror enqueue failed for %s, falling back inline: %s",
            spec.source.__name__,
            exc,
        )
        return False


async def _run_mirror_job(source_name: str, op: str, payload: dict[str, Any]) -> None:
    """
    Task entry point applying a queued mirror operation.

    Looked up by source-model *name* rather than carrying the spec: a task
    payload has to survive serialization to a worker process, and callables
    cannot.
    """
    spec = next((s for s in _MIRRORS.values() if s.source.__name__ == source_name), None)
    if spec is None:
        logger.warning("Mirror job for unknown model %r — skipping", source_name)
        return

    key = payload.get("key")
    if op == "delete":
        await spec.target.vectors.remove(str(key))
        return

    schema = spec.target._vfields
    record = spec.target(**(payload.get("payload") or {}))
    if schema.key_attr:
        setattr(record, schema.key_attr, key)
    if payload.get("text") is not None and schema.text_attr:
        setattr(record, schema.text_attr, payload["text"])
    if payload.get("vector") is not None and schema.vector_attr:
        setattr(record, schema.vector_attr, payload["vector"])
    await record.save()


async def _safe(coro: Any, spec: MirrorSpec, op: str) -> None:
    """
    Await a mirror operation, logging rather than propagating failures.

    A mirror is a derived index. Letting its failure escape would turn a search
    problem into a failed ``save()``, rolling back a write the user asked for
    because a secondary index could not be updated. ``aq vectordb reindex``
    repairs the drift.
    """
    try:
        await coro
    except Exception as exc:
        logger.error(
            "Mirror %s failed for %s -> %s: %s",
            op,
            spec.source.__name__,
            spec.target.__name__,
            exc,
            exc_info=True,
        )


async def reindex(model_cls: type[Model], *, batch_size: int = 500) -> int:
    """
    Rebuild a mirrored collection from its SQL table.

    The repair for the ``bulk_create`` / ``bulk_update`` blind spot: those fire
    no signals, so records written that way never reach the mirror.

    Args:
        model_cls: The mirrored SQL model.
        batch_size: Rows per vector write batch.

    Returns:
        The number of records written.

    Raises:
        VectorRegistryFault: When ``model_cls`` has no registered mirror.
    """
    spec = _MIRRORS.get(model_cls)
    if spec is None:
        raise VectorRegistryFault(
            reason=f"{model_cls.__name__} has no registered mirror — nothing to reindex",
            model=model_cls.__name__,
        )

    rows = await model_cls.query().all()
    schema = spec.target._vfields

    pending: list[Any] = []
    written = 0

    for row in rows:
        if not spec.should_mirror(row):
            continue

        record = spec.target(**spec.build_payload(row))
        if schema.key_attr:
            setattr(record, schema.key_attr, spec.build_key(row))
        if spec.text is not None and schema.text_attr:
            setattr(record, schema.text_attr, spec.text(row))
        if spec.vector is not None and schema.vector_attr:
            setattr(record, schema.vector_attr, spec.vector(row))

        pending.append(record)

        if len(pending) >= batch_size:
            await spec.target.vectors.add_many(pending, batch_size=batch_size)
            written += len(pending)
            pending.clear()

    if pending:
        await spec.target.vectors.add_many(pending, batch_size=batch_size)
        written += len(pending)

    return written


# ============================================================================
# Hybrid retrieval
# ============================================================================


async def as_models(
    hits: list[Hit[Any]],
    model_cls: type[TModel],
    *,
    via: str,
    queryset: Any | None = None,
    with_hits: bool = False,
) -> list[TModel] | list[tuple[TModel, Hit[Any]]]:
    """
    Hydrate ORM rows for a list of hits, preserving relevance order.

    The common hybrid-retrieval shape: search vectors, return fully-loaded SQL
    rows ranked by similarity.

    Example::

        hits = await Document.vectors.search("alpha design", limit=20)
        posts = await as_models(
            hits, Post, via="post_id",
            queryset=Post.query().select_related("author"),
        )

    Args:
        hits: Hits from a vector search, in relevance order.
        model_cls: The SQL model to hydrate.
        via: The link attribute on the vector model holding the SQL primary key.
        queryset: Base queryset, for eager loading. Defaults to
            ``model_cls.query()``.
        with_hits: Return ``(row, hit)`` pairs instead of bare rows.

    Returns:
        Rows in hit order. Rows the SQL side no longer has are dropped.

    Notes:
        One round trip, not N+1: primary keys are collected from the hits and
        fetched with a single ``pk__in``, chunked at :data:`PK_CHUNK_SIZE` to
        respect the SQLite parameter ceiling.

        The re-sort afterwards is not optional. SQL ``IN`` does not preserve
        argument order, and relevance ordering is the entire point of the query.
    """
    if not hits:
        return []

    # Deduplicate while preserving first position — several chunks of one
    # document can legitimately point at the same SQL row.
    ordered_pks: list[Any] = []
    seen: set[Any] = set()
    pk_to_hit: dict[Any, Hit[Any]] = {}

    for hit in hits:
        record = getattr(hit, "record", hit)
        pk = getattr(record, via, None)
        if pk is None or pk in seen:
            continue
        seen.add(pk)
        ordered_pks.append(pk)
        pk_to_hit[pk] = hit

    if not ordered_pks:
        return []

    base = queryset if queryset is not None else model_cls.query()
    pk_attr = model_cls._pk_attr

    rows: list[Any] = []
    for start in range(0, len(ordered_pks), PK_CHUNK_SIZE):
        chunk = ordered_pks[start : start + PK_CHUNK_SIZE]
        rows.extend(await base.filter(**{f"{pk_attr}__in": chunk}).all())

    by_pk = {row.pk: row for row in rows}

    if with_hits:
        return [(by_pk[pk], pk_to_hit[pk]) for pk in ordered_pks if pk in by_pk]
    return [by_pk[pk] for pk in ordered_pks if pk in by_pk]


__all__ = [
    "PK_CHUNK_SIZE",
    "Link",
    "MirrorSpec",
    "all_mirrors",
    "as_models",
    "get_mirror",
    "mirror",
    "register_mirror",
    "reindex",
    "resolve",
]

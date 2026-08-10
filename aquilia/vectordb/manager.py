"""
AquilaVectorDB — Manager descriptor.

``Model.vectors`` is the entry point for every read and write. The descriptor
mirrors ``aquilia.models.manager.Manager``: class-only access, a fresh query per
chain, and an ``__set_name__`` hook so the manager knows its owner.

Instance access raises rather than returning a bound manager. ``doc.vectors``
almost always means the caller meant ``type(doc).vectors``, and silently
returning a class-level manager from an instance hides the mistake until it
produces a query over the wrong scope.
"""

from __future__ import annotations

import sys
import uuid
from typing import TYPE_CHECKING, Any, Generic, TypeVar

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from aquilia.vectordb.faults import (
    VectorEmbedderFault,
    VectorQueryFault,
    VectorSchemaFault,
)

if TYPE_CHECKING:
    from aquilia.vectordb.base import VectorModel
    from aquilia.vectordb.engine import VectorEngine
    from aquilia.vectordb.query import Hit, VectorQuery

TModel = TypeVar("TModel", bound="VectorModel")

#: Batch size for ``add_many``. elips holds the prior state of every touched
#: record in memory for the duration of a commit, so an unbounded batch turns a
#: large ingest into an OOM. 500 keeps the undo log small while still amortizing
#: the per-call overhead.
DEFAULT_BATCH_SIZE = 500


class BaseVectorManager(Generic[TModel]):
    """
    Base class for vector managers.

    Subclass to add domain-specific query shortcuts::

        class PublishedDocs(BaseVectorManager):
            def query(self):
                return super().query().filter(published=True)

        class Document(VectorModel):
            published_docs = PublishedDocs()
    """

    def __init__(self) -> None:
        self._model: type[TModel] | None = None
        self._name = "vectors"

    def __set_name__(self, owner: type, name: str) -> None:
        """Bind this manager to its owning model class and attribute name."""
        self._model = owner  # type: ignore[assignment]
        self._name = name

    def __get__(self, instance: Any, owner: type) -> Self:
        """
        Return the class-bound manager.

        Raises:
            VectorQueryFault: When accessed through an instance.
        """
        if instance is not None:
            raise VectorQueryFault(
                reason=(
                    f"{owner.__name__}.{self._name} is a class-level manager and cannot be "
                    f"accessed through an instance. Use {owner.__name__}.{self._name} instead."
                )
            )

        if self._model is None or self._model is not owner:
            # Subclass access: return a copy bound to the subclass so two models
            # sharing an inherited manager do not write into each other's
            # collection.
            clone = type(self)()
            clone._model = owner  # type: ignore[assignment]
            clone._name = self._name
            return clone

        return self

    @property
    def model(self) -> type[TModel]:
        """
        The bound model class.

        Raises:
            VectorSchemaFault: When the manager was never bound to a model.
        """
        if self._model is None:
            raise VectorSchemaFault(
                model="<unbound>",
                reason="manager is not bound to a model class",
            )
        return self._model

    # ── Engine access ────────────────────────────────────────────────────

    async def engine(self) -> VectorEngine:
        """Return the engine backing this model's store."""
        from aquilia.vectordb.registry import VectorRegistry

        return await VectorRegistry.engine_for(self.model)

    async def collection(self) -> Any:
        """Return the native elips collection this model reads and writes."""
        engine = await self.engine()
        return await engine.collection(self.model.collection_name())

    # ── Queries ──────────────────────────────────────────────────────────

    def query(self) -> VectorQuery[TModel]:
        """
        Return a fresh query over this model.

        Every chainable method clones, so a query returned here can be reused as
        a base without a later ``.filter()`` mutating it.
        """
        from aquilia.vectordb.query import VectorQuery

        return VectorQuery(self.model)

    def filter(self, *nodes: Any, **lookups: Any) -> VectorQuery[TModel]:
        """Shorthand for ``query().filter(...)``."""
        return self.query().filter(*nodes, **lookups)

    def exclude(self, *nodes: Any, **lookups: Any) -> VectorQuery[TModel]:
        """Shorthand for ``query().exclude(...)``."""
        return self.query().exclude(*nodes, **lookups)

    async def search(
        self,
        text: str | None = None,
        *,
        vector: list[float] | None = None,
        limit: int = 10,
        **lookups: Any,
    ) -> list[Hit[TModel]]:
        """
        Run a similarity search.

        Args:
            text: Query text. Requires a store embedder.
            vector: Query vector. Mutually exclusive with ``text``.
            limit: Maximum hits.
            **lookups: Metadata filters, AND-ed with the search.

        Returns:
            Hits ordered by descending similarity.
        """
        query = self.query()
        if lookups:
            query = query.filter(**lookups)
        return await query.search(text=text, vector=vector, limit=limit)

    async def all(self, *, limit: int | None = None) -> list[TModel]:
        """Return every record, up to ``limit``."""
        return await self.query().limit(limit).all() if limit else await self.query().all()

    async def count(self) -> int:
        """Return the number of records in this collection."""
        return await self.query().count()

    # ── Reads by key ─────────────────────────────────────────────────────

    async def get(self, key: str) -> TModel | None:
        """
        Fetch one record by key.

        Args:
            key: Record key. A natural key is folded to the same deterministic
                UUID the write path used, so ``get("post:42")`` finds the record
                ``save()`` stored under that key.

        Returns:
            The record, or ``None`` when absent.
        """
        engine = await self.engine()
        collection = await self.collection()
        found = await engine.read(collection.pull, [_normalize_key(key)], include_vectors=True)
        if not found:
            return None
        return self._hydrate_record(found[0])

    async def get_many(self, keys: list[str]) -> list[TModel]:
        """
        Fetch several records by key.

        Args:
            keys: Record keys; natural keys are normalized as in :meth:`get`.

        Returns:
            The records that exist, in storage order. Missing keys are omitted
            rather than yielding ``None`` placeholders.
        """
        if not keys:
            return []
        engine = await self.engine()
        collection = await self.collection()
        found = await engine.read(collection.pull, [_normalize_key(k) for k in keys], include_vectors=True)
        return [self._hydrate_record(entry) for entry in found]

    # ── Writes ───────────────────────────────────────────────────────────

    async def add(self, instance: TModel, *, embed: bool | None = None) -> TModel:
        """
        Write one record, embedding its text when needed.

        Args:
            instance: The record to write.
            embed: Force embedding on or off. ``None`` embeds when the model has
                text, no vector, and an embedder is reachable.

        Returns:
            The instance, with ``key`` assigned when it was newly created.

        Raises:
            VectorEmbedderFault: When embedding is required but unavailable.
            VectorValidationFault: When the record fails validation.
        """
        instance.validate()

        engine = await self.engine()
        collection = await self.collection()

        records = await self._prepare_writes([instance], embed, engine)
        assigned = await engine.write(collection.write, **records[0])

        key_attr = self.model._vfields.key_attr
        if key_attr and assigned:
            instance.__dict__[key_attr] = str(assigned)

        # Chunked models fan one logical document out into child records; the
        # parent is written above, the chunks follow under derived keys.
        await self._write_chunks(instance, engine, collection)
        return instance

    async def add_many(
        self,
        instances: list[TModel],
        *,
        embed: bool | None = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> list[TModel]:
        """
        Write many records, in batches.

        Args:
            instances: Records to write.
            embed: Force embedding on or off.
            batch_size: Records per native call. See :data:`DEFAULT_BATCH_SIZE`
                for why this is bounded.

        Returns:
            The instances, with keys assigned.

        Notes:
            Save signals do **not** fire for bulk writes — per-record dispatch
            would dominate the cost of a batched ingest. This mirrors
            ``bulk_create`` in the SQL ORM, and is what ``aq vectordb reindex``
            exists to repair for mirrored models.

            Embedding is batched within each write batch, so an ingest of 5,000
            documents makes ceil(5000/batch_size) embed calls rather than 5,000.
        """
        if not instances:
            return []

        for instance in instances:
            instance.validate()

        engine = await self.engine()
        collection = await self.collection()
        key_attr = self.model._vfields.key_attr

        for start in range(0, len(instances), batch_size):
            chunk = instances[start : start + batch_size]
            records = await self._prepare_writes(chunk, embed, engine)

            assigned = await engine.write(collection.write_many, records)

            if key_attr and assigned:
                for instance, key in zip(chunk, assigned, strict=False):
                    instance.__dict__[key_attr] = str(key)

            for instance in chunk:
                await self._write_chunks(instance, engine, collection)

        return instances

    async def remove(self, key: str) -> bool:
        """
        Delete one record by key.

        Args:
            key: Record key; natural keys are normalized as in :meth:`get`, so a
                mirror can delete by the same natural key it wrote under.

        Returns:
            ``True`` when a record was removed.
        """
        engine = await self.engine()
        collection = await self.collection()
        removed = await engine.write(collection.discard, [_normalize_key(key)])
        return bool(removed)

    async def remove_many(self, keys: list[str]) -> int:
        """
        Delete several records by key.

        Args:
            keys: Record keys; normalized as in :meth:`get`.

        Returns:
            The number of records removed.
        """
        if not keys:
            return 0
        engine = await self.engine()
        collection = await self.collection()
        return int(await engine.write(collection.discard, [_normalize_key(k) for k in keys]))

    # ── Maintenance ──────────────────────────────────────────────────────

    async def health(self) -> dict[str, Any]:
        """Return this collection's health snapshot."""
        engine = await self.engine()
        collection = await self.collection()
        native = await engine.read(collection.health)
        return {
            "collection": self.model.collection_name(),
            "store": self.model._voptions.store,
            "model": self.model.__name__,
            "count": getattr(native, "live", None),
            "dimension": getattr(native, "dimension", None),
            "metric": getattr(native, "metric", None),
            "codec": getattr(native, "codec", None),
            "read_only": getattr(native, "read_only", None),
            "sealed": getattr(native, "sealed", None),
        }

    async def quantize(self, *, codec: str | None = None) -> dict[str, Any]:
        """
        Train a codebook over this collection and compress it in place.

        Args:
            codec: Codec to apply. Defaults to the store's configured one; a
                different value is rejected, since elips fixes the codec when
                the database is opened.

        Returns:
            ``{"collection", "codec", "compressed", "reason"}``.

        Raises:
            VectorConfigFault: When the store configures no codec.

        Notes:
            Irreversible in place: the full-precision vectors are freed once the
            codebook is trained. Every hit from a compressed collection reports
            ``approximate=True`` and its codec, so a caller applying a score
            threshold can see what it is thresholding on.
        """
        engine = await self.engine()
        return await engine.quantize(self.model.collection_name(), codec=codec)

    async def rebuild(self) -> None:
        """
        Rebuild this collection's index from the record store.

        Worth doing after a bulk ingest: inserting in arrival order yields a
        lower-quality graph than rebuilding once the full set is known.
        """
        engine = await self.engine()
        collection = await self.collection()
        await engine.write(collection.rebuild)

    async def pending_writes(self) -> int:
        """Return the number of un-checkpointed WAL records on this store."""
        engine = await self.engine()
        return await engine.pending_writes()

    # ── Internals ────────────────────────────────────────────────────────

    def _should_embed(self, instance: TModel, embed: bool | None, engine: VectorEngine) -> bool:
        """
        Decide whether this write needs an embedding step.

        Raises:
            VectorEmbedderFault: When embedding was explicitly requested but the
                store has no embedder, or when the record has neither a vector
                nor embeddable text.
        """
        schema = self.model._vfields
        has_embedder = engine.can_embed
        text = instance.text_value()
        vector = instance.vector_value()

        if embed is True:
            if not has_embedder:
                raise VectorEmbedderFault(
                    reason=(
                        f"embed=True requires an embedder on store "
                        f"{engine.config.alias!r}; configure one with "
                        f"EmbedderOptions(provider='uri', uri='sentence-transformers/all-MiniLM-L6-v2')"
                    ),
                    model=schema.model_name,
                )
            if text is None:
                raise VectorEmbedderFault(
                    reason=f"embed=True but {schema.model_name} has no text value to embed",
                    model=schema.model_name,
                )
            return True

        if embed is False:
            return False

        # Auto: embed only when there is no vector to use.
        if vector is None and text is not None:
            if not has_embedder:
                raise VectorEmbedderFault(
                    reason=(
                        f"{schema.model_name} has text but no vector, and store "
                        f"{engine.config.alias!r} has no embedder configured. Supply a "
                        f"vector, or configure an embedder."
                    ),
                    model=schema.model_name,
                )
            return schema.embed_text

        return False

    async def _resolve_embedder(self, engine: VectorEngine) -> Any | None:
        """
        Return the embedder that should vectorize this model's text.

        Precedence, narrowest wins: the text field's own ``embedder=``, then
        ``Meta.embedder``, then the store's. A model overriding the store gets
        its own adapter; without an override it shares the store's, which is
        what keeps one loaded transformer serving every model on that store.
        """
        schema = self.model._vfields
        options = self.model._voptions

        text_field = schema.text_field
        override = getattr(text_field, "embedder", None) if text_field is not None else None
        override = override or options.embedder

        if override:
            return _model_embedder(self.model, override)

        return engine.text_embedder

    async def _prepare_writes(
        self,
        instances: list[TModel],
        embed: bool | None,
        engine: VectorEngine,
    ) -> list[dict[str, Any]]:
        """
        Encode instances into native record mappings, embedding where needed.

        Embedding is batched across the whole call rather than done per record:
        a transformer processes 32 texts in roughly the time it takes to process
        two, so a per-record loop would dominate the cost of any bulk ingest.

        Text whose vectors the *engine* computes (``provider="local"``) is passed
        through as text — elips embeds it outside the vault lock, which is
        strictly better than round-tripping it through Python.
        """
        records: list[dict[str, Any]] = []
        pending_text: list[str] = []
        pending_slots: list[int] = []

        server_side = engine.embeds_server_side

        for instance in instances:
            payload = self._encode(instance)
            record: dict[str, Any] = {"meta": payload["meta"]}
            if payload["key"] is not None:
                record["key"] = payload["key"]
            if payload["text"] is not None:
                record["text"] = payload["text"]

            if self._should_embed(instance, embed, engine):
                if server_side:
                    # elips embeds this one itself; nothing more to attach.
                    records.append(record)
                    continue
                pending_text.append(payload["text"] or "")
                pending_slots.append(len(records))
            else:
                record["vector"] = payload["vector"]

            records.append(record)

        if pending_text:
            embedder = await self._resolve_embedder(engine)
            if embedder is None:
                raise VectorEmbedderFault(
                    reason=(
                        f"{self.model.__name__} needs an embedder to vectorize text, but store "
                        f"{engine.config.alias!r} has none configured."
                    ),
                    model=self.model.__name__,
                )

            vectors = await embedder.embed(pending_text)
            lineage = _native_lineage(embedder)

            for slot, vector in zip(pending_slots, vectors, strict=True):
                records[slot]["vector"] = vector
                if lineage is not None:
                    records[slot]["lineage"] = lineage

        return records

    def _encode(self, instance: TModel) -> dict[str, Any]:
        """Encode an instance into the raw parts of an elips write."""
        from aquilia.vectordb.faults import VectorEncodingFault

        schema = self.model._vfields
        meta: dict[str, Any] = {}

        for spec in schema.written_payloads:
            value = getattr(instance, spec.attribute, None)
            if value is None:
                # elips has no null: an absent key is the absence. Writing a
                # sentinel would make `field=None` match records that never set
                # the field at all.
                continue
            try:
                meta[spec.key] = spec.codec.encode(value)
            except Exception as exc:
                raise VectorEncodingFault(
                    model=schema.model_name,
                    attr=spec.attribute,
                    reason=f"{type(exc).__name__}: {exc}",
                ) from exc

        key = instance.key
        return {
            "key": _normalize_key(key) if key is not None else None,
            "vector": instance.vector_value(),
            "text": instance.text_value(),
            "meta": meta,
        }

    def _hydrate_record(self, raw: Any) -> TModel:
        """
        Build a model instance from a native elips record.

        Accepts anything carrying ``key`` / ``meta`` / ``vector`` — the native
        scan and fetch types both qualify — so one hydration path serves search,
        scan, and key lookup.
        """
        return self.model._from_hit(
            key=str(raw.key),
            meta=dict(raw.meta or {}),
            vector=list(raw.vector) if getattr(raw, "vector", None) else None,
            lineage=getattr(raw, "lineage", None),
            chunk=getattr(raw, "chunk", None),
        )

    # ── Chunking ─────────────────────────────────────────────────────────

    async def _write_chunks(self, instance: TModel, engine: VectorEngine, collection: Any) -> int:
        """
        Split a chunked model's text into child records and write them.

        Returns:
            The number of chunk records written; ``0`` when the model declares
            no chunker or the text fits in one chunk.

        Notes:
            Chunks are written *after* the parent, and the parent keeps its own
            whole-document vector. That costs one extra record per document and
            buys two retrieval modes from one write: a document-level match for
            "what is this about", and passage-level matches for "where does it
            say that".

            Stale chunks from a previous save are removed first. Without that, a
            document edited from 10 chunks down to 6 would leave 4 orphans that
            still match searches and still point at text the document no longer
            contains.
        """
        chunker, text = self._chunking_inputs(instance)
        if chunker is None or not text:
            return 0

        chunks = chunker.split(text)
        if len(chunks) <= 1:
            return 0

        parent_key = instance.key
        if parent_key is None:
            return 0

        await self._discard_stale_chunks(str(parent_key), engine, collection, keep=len(chunks))

        embedder = await self._resolve_embedder(engine)
        if embedder is None and not engine.embeds_server_side:
            raise VectorEmbedderFault(
                reason=(
                    f"{self.model.__name__} declares a chunker but store "
                    f"{engine.config.alias!r} has no embedder to vectorize the chunks with."
                ),
                model=self.model.__name__,
            )

        base_meta = self._encode(instance)["meta"]
        records: list[dict[str, Any]] = []

        vectors: list[list[float]] = []
        if embedder is not None:
            vectors = await embedder.embed([c.text for c in chunks])
        lineage = _native_lineage(embedder) if embedder is not None else None

        for index, chunk in enumerate(chunks):
            record: dict[str, Any] = {
                "key": _normalize_key(chunk.key_for(str(parent_key))),
                "meta": dict(base_meta),
                "text": chunk.text,
                "chunk": chunk.to_native(str(parent_key)),
            }
            if vectors:
                record["vector"] = vectors[index]
            if lineage is not None:
                record["lineage"] = lineage
            records.append(record)

        await engine.write(collection.write_many, records)
        return len(records)

    def _chunking_inputs(self, instance: TModel) -> tuple[Any, str | None]:
        """Return ``(chunker, text)`` for a model, or ``(None, None)``."""
        text_field = self.model._vfields.text_field
        if text_field is None:
            return None, None

        resolve = getattr(text_field, "resolve_chunker", None)
        if resolve is None:
            return None, None

        return resolve(), instance.text_value()

    async def _discard_stale_chunks(
        self,
        parent_key: str,
        engine: VectorEngine,
        collection: Any,
        *,
        keep: int,
    ) -> None:
        """
        Remove chunk records left over from a previous, longer version.

        Deletes by derived key rather than by scanning: chunk keys are
        deterministic, so the ordinals beyond the new count can be named
        directly. The probe window stops after a run of misses, since chunk
        ordinals are contiguous and a gap means the tail is already gone.
        """
        from aquilia.vectordb.chunking import CHUNK_KEY_SEPARATOR

        stale: list[str] = []
        misses = 0
        ordinal = keep

        while misses < _STALE_CHUNK_PROBE:
            stale.append(_normalize_key(f"{parent_key}{CHUNK_KEY_SEPARATOR}{ordinal}"))
            ordinal += 1
            misses += 1

        if stale:
            # discard() ignores keys that are not present, so probing costs one
            # call rather than a read followed by a write.
            await engine.write(collection.discard, stale)


class VectorManager(BaseVectorManager[TModel]):
    """
    The default manager, auto-attached as ``vectors`` by the metaclass.

    Declaring a manager explicitly in the class body suppresses the automatic
    one, which is how a model swaps in a :class:`BaseVectorManager` subclass.
    """


#: How many ordinals past the current chunk count to probe when clearing stale
#: chunks. A document shrinking by more than this in one save leaves orphans
#: that ``aq vectordb reindex`` clears; the alternative is scanning the whole
#: collection on every chunked write.
_STALE_CHUNK_PROBE = 32

#: Per-model embedder cache, keyed by ``(model, uri)``.
#:
#: Without it, a model declaring ``Meta.embedder`` would construct — and for a
#: local transformer, *load* — a fresh model object on every single save.
_MODEL_EMBEDDERS: dict[tuple[type, str], Any] = {}


def _model_embedder(model_cls: type, uri: str) -> Any:
    """Return the cached embedder for a model's declared override."""
    cache_key = (model_cls, uri)
    embedder = _MODEL_EMBEDDERS.get(cache_key)
    if embedder is None:
        from aquilia.vectordb.embedders import resolve_embedder

        embedder = resolve_embedder(uri)
        _MODEL_EMBEDDERS[cache_key] = embedder
    return embedder


def _native_lineage(embedder: Any) -> Any:
    """
    Build an ``elips.EmbeddingLineage`` describing ``embedder``.

    Returns ``None`` when elips is unavailable or the build predates lineage —
    provenance is valuable but never worth failing a write over.
    """
    try:
        from aquilia.vectordb._compat import require_elips

        elips = require_elips()
        lineage_cls = getattr(elips, "EmbeddingLineage", None)
        if lineage_cls is None:
            return None

        source = embedder.lineage()
        native = lineage_cls()
        native.provider = source.provider
        native.model = source.model
        native.revision = source.revision
        native.attributes = dict(source.attributes)
        return native
    except Exception:
        return None


def _normalize_key(key: Any) -> str:
    """
    Coerce a caller-supplied key into a form elips accepts.

    elips parses record keys as UUIDs. A caller using a natural key
    (``"post:42"``) would otherwise get an opaque parse error from the storage
    layer, so a non-UUID string is folded into a deterministic UUIDv5 instead.

    Determinism is the point: the same logical key always maps to the same
    record, so re-saving overwrites rather than duplicating. That is what makes
    mirroring idempotent.
    """
    text = str(key)
    try:
        return str(uuid.UUID(text))
    except (ValueError, AttributeError, TypeError):
        return str(uuid.uuid5(uuid.NAMESPACE_URL, text))


__all__ = ["DEFAULT_BATCH_SIZE", "BaseVectorManager", "VectorManager"]

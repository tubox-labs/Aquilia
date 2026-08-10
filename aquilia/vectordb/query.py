"""
AquilaVectorDB — Query builder.

:class:`VectorQuery` mirrors ``aquilia.models.query.Q``: chainable methods clone,
``async`` terminals execute, and the query itself is never awaitable. Two query
*modes* exist, and the difference is load-bearing:

**Search mode** — ``search(text=...)`` or ``search(vector=...)``. Results come
back ordered by similarity, and ``limit`` is the ``top-k`` handed to the index.

**Scan mode** — ``all()`` / ``count()`` with only metadata filters. Results come
back in *insertion* order, because with no query vector there is nothing to rank
by. ``order_by`` is not offered rather than silently ignored.

Truthiness guards
-----------------

``__bool__`` and ``__len__`` raise. ``if query:`` would test object identity
(always true) rather than "are there matching records", and ``len(query)`` cannot
run a coroutine. Both faults name the async call to use instead. This is the same
guard ``Q`` already installs, for the same reason.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, Self, TypeVar

from aquilia.vectordb.expressions import FieldExpression, to_vf
from aquilia.vectordb.faults import (
    VectorEmbedderFault,
    VectorMultipleFoundFault,
    VectorNotFoundFault,
    VectorQueryFault,
)
from aquilia.vectordb.filters import VF, FilterCompiler, apply_residuals

if TYPE_CHECKING:
    from aquilia.vectordb.base import VectorModel

TModel = TypeVar("TModel", bound="VectorModel")

#: Native page size for scan-mode reads. elips returns whole result sets, so
#: this bounds how much a bare ``.all()`` on a large collection materializes.
DEFAULT_SCAN_LIMIT = 1000

#: Planner strategies that examined every record. Reported by ``.explain()`` and
#: warned about when :data:`WARN_ON_FULL_SCAN` is on.
FULL_SCAN_STRATEGIES = frozenset({"full_scan", "QueryStrategy.full_scan"})

#: Log a warning when a search plans a full scan. On by default: a silent full
#: scan is the failure mode that surfaces months later as a latency cliff.
WARN_ON_FULL_SCAN = True

_log = logging.getLogger("aquilia.vectordb.query")

#: Query knobs already warned about, so a hot loop logs once rather than per call.
_WARNED_KNOBS: set[str] = set()


def _warn_query_knob(name: str, detail: str) -> None:
    """Warn once per process that a per-query knob is advisory only."""
    if name in _WARNED_KNOBS:
        return
    _WARNED_KNOBS.add(name)
    _log.warning("VectorQuery.%s() is advisory: %s", name, detail)


@dataclass(frozen=True, slots=True)
class Hit(Generic[TModel]):
    """
    One similarity-search result.

    Attributes:
        record: The hydrated model instance.
        score: Similarity score. Higher is more similar — elips reports
            *distance* (lower is closer), which is converted once here so that
            ranking reads the same way regardless of metric.
        distance: The raw distance elips returned, unconverted.
        approximate: ``True`` when the vector was reconstructed from a compressed
            form, making the distance an estimate. Surfaced rather than hidden
            because a caller applying a score threshold deserves to know what it
            is thresholding on.
        codec: Compression codec the record is stored under.
    """

    record: TModel
    score: float
    distance: float
    approximate: bool = False
    codec: str = "none"

    def __getattr__(self, name: str) -> Any:
        """Proxy attribute access to the underlying record.

        Lets ``hit.title`` work without ``hit.record.title``, while ``record``
        stays available for callers that want to be explicit.
        """
        try:
            return getattr(object.__getattribute__(self, "record"), name)
        except AttributeError:
            raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}") from None

    def __repr__(self) -> str:
        approx = " ~" if self.approximate else " "
        return f"<Hit score={self.score:.4f}{approx}{self.record!r}>"


class VectorQuery(Generic[TModel]):
    """
    Chainable, lazily-executed query over a vector collection.

    Args:
        model: The model class being queried.

    Example::

        query = Document.vectors.filter(source="docs").limit(20)
        hits = await query.search("release notes")
        rows = await query.all()
    """

    __slots__ = (
        "_model",
        "_nodes",
        "_lookups",
        "_excludes",
        "_limit",
        "_offset",
        "_min_score",
        "_with_vectors",
        "_ef_search",
        "_gpu",
        "_prompt",
    )

    def __init__(self, model: type[TModel]) -> None:
        self._model = model
        self._nodes: tuple[VF, ...] = ()
        self._lookups: dict[str, Any] = {}
        self._excludes: tuple[VF, ...] = ()
        self._limit: int | None = None
        self._offset: int = 0
        self._min_score: float | None = None
        self._with_vectors: bool = False
        self._ef_search: int | None = None
        self._gpu: bool | None = None
        self._prompt: str | None = None

    # ── Chainables ───────────────────────────────────────────────────────

    def _clone(self) -> Self:
        """Return a copy carrying the accumulated chain state."""
        clone = type(self)(self._model)
        clone._nodes = self._nodes
        clone._lookups = dict(self._lookups)
        clone._excludes = self._excludes
        clone._limit = self._limit
        clone._offset = self._offset
        clone._min_score = self._min_score
        clone._with_vectors = self._with_vectors
        clone._ef_search = self._ef_search
        clone._gpu = self._gpu
        clone._prompt = self._prompt
        return clone

    def filter(self, *nodes: VF | FieldExpression, **lookups: Any) -> Self:
        """
        Narrow the query. Every call AND-s with what came before.

        Accepts both filter syntaxes interchangeably (§4.2.3) — they compile
        through one path, so neither can drift from the other::

            .filter(source="docs", views__gte=10)              # keyword lookups
            .filter(Doc.source == "docs", Doc.views >= 10)     # expressions
            .filter((Doc.a == 1) | (Doc.b == 2))               # expression tree

        Args:
            *nodes: :class:`VF` trees or
                :class:`~aquilia.vectordb.expressions.FieldExpression` objects.
            **lookups: ``field__lookup=value`` pairs.

        Returns:
            A new query; ``self`` is unchanged.
        """
        clone = self._clone()
        clone._nodes = self._nodes + tuple(to_vf(node) for node in nodes)
        clone._lookups.update(lookups)
        return clone

    def where(self, *nodes: VF | FieldExpression, **lookups: Any) -> Self:
        """
        Alias of :meth:`filter`, matching the plan's ``.where(...)`` spelling.

        Both names are supported deliberately: ``filter`` mirrors the SQL ORM's
        ``Q.filter`` so the two model worlds read alike, and ``where`` is what
        the vector-native examples use.
        """
        return self.filter(*nodes, **lookups)

    def exclude(self, *nodes: VF | FieldExpression, **lookups: Any) -> Self:
        """
        Exclude matching records — the negation of :meth:`filter`.

        Args:
            *nodes: :class:`VF` trees or expressions to negate.
            **lookups: ``field__lookup=value`` pairs to negate.

        Returns:
            A new query; ``self`` is unchanged.
        """
        clone = self._clone()
        negated = [~to_vf(node) for node in nodes]
        if lookups:
            negated.append(~VF(**lookups))
        clone._excludes = self._excludes + tuple(negated)
        return clone

    def limit(self, count: int | None) -> Self:
        """Cap the number of results. ``None`` clears a previously set cap."""
        if count is not None and count < 0:
            raise VectorQueryFault(reason=f"limit must be non-negative, got {count}")
        clone = self._clone()
        clone._limit = count
        return clone

    def offset(self, count: int) -> Self:
        """
        Skip ``count`` records.

        Notes:
            Scan mode only. Similarity search has no stable offset — the index
            returns top-k, so paging through it by offset would re-rank between
            pages. :meth:`search` raises when an offset is set.
        """
        if count < 0:
            raise VectorQueryFault(reason=f"offset must be non-negative, got {count}")
        clone = self._clone()
        clone._offset = count
        return clone

    def min_score(self, score: float) -> Self:
        """
        Drop hits scoring below ``score``.

        Search mode only; ignored by scan-mode terminals, which have no score.
        """
        clone = self._clone()
        clone._min_score = score
        return clone

    def top(self, count: int) -> Self:
        """
        Alias of :meth:`limit`, spelled for search mode.

        ``top(10)`` and ``limit(10)`` are the same cap; ``top`` reads better next
        to a similarity search, where the number *is* the index's top-k.
        """
        return self.limit(count)

    def with_vectors(self) -> Self:
        """
        Include raw vectors on returned records.

        Off by default: hydrating a 1536-float list per record is a real cost
        that most callers never use.
        """
        clone = self._clone()
        clone._with_vectors = True
        return clone

    def ef_search(self, value: int) -> Self:
        """
        Record a preferred HNSW search beam width for this query.

        Advisory, and deliberately so. elips fixes ``ef_search`` on
        ``Config.graph_params`` when the database is *opened* — the search entry
        points take no per-call override — so a value set here cannot reach the
        index. It is kept on the query and reported by :meth:`explain` so the
        intent stays visible, and a one-time warning names the store-level knob
        that does take effect.

        To actually change the beam width, set it on the store::

            Workspace.vectordb(stores={"default": {
                "dimension": 384,
                "index": "hnsw",
                "index_options": {"ef_search": 128},
            }})

        Args:
            value: Beam width. Must be positive.

        Raises:
            VectorQueryFault: If ``value`` is not positive.
        """
        if value <= 0:
            raise VectorQueryFault(reason=f"ef_search must be positive, got {value}")
        _warn_query_knob(
            "ef_search",
            "elips fixes ef_search at open time via Config.graph_params. Set it on the store "
            "with index_options={'ef_search': N}; the per-query value is recorded for explain() "
            "but does not reach the index.",
        )
        clone = self._clone()
        clone._ef_search = value
        return clone

    def gpu(self, enabled: bool = True) -> Self:
        """
        Record a GPU preference for this query.

        Advisory, and deliberately so. GPU selection is bound to the database at
        open through ``Config.gpu``, not per search, so this cannot switch an
        individual query onto or off a device. Whether the GPU index actually
        served a query is reported by :meth:`explain` under ``gpu_index``.

        To change GPU policy, set it on the store::

            Workspace.vectordb(..., gpu=GpuOptions(policy="prefer_gpu"))
        """
        _warn_query_knob(
            "gpu",
            "elips binds GPU policy at open time via Config.gpu. Set it on the store with "
            "GpuOptions(policy=...); the per-query flag is recorded for explain() but does not "
            "change device selection.",
        )
        clone = self._clone()
        clone._gpu = enabled
        return clone

    def prompt(self, template: str) -> Self:
        """
        Apply an embedder prompt template to the query text (§5.4).

        Asymmetric models want the query side wrapped — ``"query: {text}"`` for
        E5, an instruction prefix for BGE. The template is applied to
        :meth:`search`'s ``text`` only, never to stored documents, which is the
        whole point of the asymmetry.

        Args:
            template: A format string containing ``{text}``.

        Raises:
            VectorQueryFault: If the template lacks a ``{text}`` placeholder.
        """
        if "{text}" not in template:
            raise VectorQueryFault(reason=f"prompt template must contain '{{text}}', got {template!r}")
        clone = self._clone()
        clone._prompt = template
        return clone

    # ── Terminals ────────────────────────────────────────────────────────

    async def search(
        self,
        text: str | None = None,
        *,
        vector: list[float] | None = None,
        limit: int | None = None,
        prompt_template: str | None = None,
    ) -> list[Hit[TModel]]:
        """
        Run a similarity search.

        Args:
            text: Query text. Requires an embedder on the store.
            vector: Query vector. Mutually exclusive with ``text``.
            limit: Maximum hits; falls back to the chained ``.limit()``, then 10.
            prompt_template: Task-specific template wrapping the query text, for
                asymmetric models (``"query: {text}"`` for E5). Equivalent to
                :meth:`prompt`; this form is convenient for a one-off call.

        Returns:
            Hits ordered by descending score.

        Raises:
            VectorQueryFault: When neither or both of ``text``/``vector`` are
                given, or when an offset is set.
            VectorEmbedderFault: When ``text`` is used without an embedder.
        """
        if (text is None) == (vector is None):
            raise VectorQueryFault(
                reason="search() takes exactly one of text= or vector=",
            )

        if prompt_template is not None:
            return await self.prompt(prompt_template).search(text, vector=vector, limit=limit)

        if self._offset:
            raise VectorQueryFault(
                reason=(
                    "offset() cannot be combined with search(): a similarity index returns "
                    "top-k, so offsetting would re-rank between pages. Raise the limit and "
                    "slice the results instead."
                )
            )

        top = limit if limit is not None else (self._limit if self._limit is not None else 10)
        if top <= 0:
            return []

        manager = self._model.vectors
        engine = await manager.engine()
        collection = await manager.collection()
        compiled = self._compile()

        native_top = top if not compiled.residuals else max(top * 4, top + 50)

        kwargs: dict[str, Any] = {"top": native_top, "include_vectors": self._with_vectors}
        if compiled.native is not None:
            kwargs["where"] = compiled.native
        # `ef_search` and `gpu` are deliberately *not* forwarded: elips binds both
        # at open time and `Collection.probe`/`probe_text` reject them. They stay
        # on the query for explain() to report. See :meth:`ef_search`.

        if vector is not None:
            self._check_dimension(vector, engine)
            raw = await engine.read(collection.probe, list(vector), **kwargs)
        else:
            query_text = self._apply_prompt(str(text))
            embedder = await manager._resolve_embedder(engine)

            if embedder is not None:
                # Embed in Python, then probe by vector. The query text goes
                # through the same embedder the documents did, which is the only
                # way the resulting distances mean anything.
                query_vector = await embedder.embed_one(query_text)
                self._check_dimension(query_vector, engine)
                raw = await engine.read(collection.probe, query_vector, **kwargs)
            elif engine.embeds_server_side:
                raw = await engine.read(collection.probe_text, query_text, **kwargs)
            else:
                raise VectorEmbedderFault(
                    reason=(
                        f"search(text=...) needs an embedder on store "
                        f"{engine.config.alias!r}. Configure one, or pass vector= instead."
                    ),
                    model=self._model.__name__,
                )

        hits = [self._to_hit(item) for item in raw]

        if compiled.residuals:
            records = apply_residuals([h.record for h in hits], compiled.residuals)
            keep = {id(r) for r in records}
            hits = [h for h in hits if id(h.record) in keep]

        if self._min_score is not None:
            hits = [h for h in hits if h.score >= self._min_score]

        return hits[:top]

    async def all(self) -> list[TModel]:
        """
        Return matching records in insertion order.

        Notes:
            Scan mode: there is no query vector, so there is nothing to rank by.
            Use :meth:`search` when relevance ordering matters.
        """
        manager = self._model.vectors
        engine = await manager.engine()
        collection = await manager.collection()
        compiled = self._compile()

        kwargs: dict[str, Any] = {
            "offset": self._offset,
            "include_vectors": self._with_vectors,
        }
        if compiled.native is not None:
            kwargs["where"] = compiled.native

        # Over-fetch when residuals will discard some rows, so a `.limit(10)`
        # with a residual predicate still returns 10 where 10 exist.
        if self._limit is not None:
            kwargs["limit"] = self._limit * 4 if compiled.residuals else self._limit
        elif compiled.residuals:
            kwargs["limit"] = DEFAULT_SCAN_LIMIT

        raw = await engine.read(collection.sweep, **kwargs)
        records = [manager._hydrate_record(row) for row in raw]
        records = apply_residuals(records, compiled.residuals)

        if self._limit is not None:
            records = records[: self._limit]
        return records

    async def records(self) -> list[TModel]:
        """
        Return matching records in insertion order.

        The vector-native spelling of :meth:`all`. A vector store holds
        semi-structured records — a vector, a document attachment, and a flat
        metadata payload — not tabular rows, so ``records()`` is the name the
        rest of this subsystem uses.
        """
        return await self.all()

    async def rows(self) -> list[TModel]:
        """
        Deprecated alias of :meth:`records`.

        Kept for one release so existing call sites keep working; ``row`` is
        relational vocabulary that does not describe what elips stores.
        """
        import warnings

        warnings.warn(
            "VectorQuery.rows() is deprecated; use VectorQuery.records() instead. "
            "A vector store holds records, not relational rows.",
            DeprecationWarning,
            stacklevel=2,
        )
        return await self.records()

    async def first(self) -> TModel | None:
        """Return the first matching record, or ``None``."""
        records = await self.limit(1).all()
        return records[0] if records else None

    async def one(self) -> TModel:
        """
        Return exactly one matching record.

        Raises:
            VectorNotFoundFault: When nothing matched.
            VectorMultipleFoundFault: When more than one matched.
        """
        records = await self.limit(2).all()
        if not records:
            raise VectorNotFoundFault(model=self._model.__name__)
        if len(records) > 1:
            raise VectorMultipleFoundFault(model=self._model.__name__, count=len(records))
        return records[0]

    async def count(self) -> int:
        """
        Return the number of matching records.

        Notes:
            An unfiltered count is a native counter. A filtered count scans,
            because elips has no filtered-count primitive — so a count over a
            large filtered set costs the same as fetching it.
        """
        manager = self._model.vectors
        engine = await manager.engine()
        collection = await manager.collection()
        compiled = self._compile()

        if compiled.is_empty() and not self._offset and self._limit is None:
            return int(await engine.read(collection.count))

        kwargs: dict[str, Any] = {"offset": self._offset, "include_vectors": False}
        if compiled.native is not None:
            kwargs["where"] = compiled.native
        if self._limit is not None and not compiled.residuals:
            kwargs["limit"] = self._limit

        rows = await engine.read(collection.sweep, **kwargs)

        if compiled.residuals:
            records = apply_residuals([manager._hydrate_record(r) for r in rows], compiled.residuals)
            total = len(records)
        else:
            total = len(rows)

        return min(total, self._limit) if self._limit is not None else total

    async def exists(self) -> bool:
        """Return whether any record matches."""
        return await self.first() is not None

    async def delete(self) -> int:
        """
        Delete every matching record.

        Returns:
            The number of records removed.

        Raises:
            VectorQueryFault: When the query has no filters. An unfiltered
                ``delete()`` would empty the collection, which is almost never
                what a chained call means; use
                ``Model.vectors.filter(...)`` explicitly, or the CLI to drop a
                collection.
        """
        compiled = self._compile()
        if compiled.is_empty():
            raise VectorQueryFault(
                reason=(
                    f"refusing to delete every {self._model.__name__} record from an unfiltered "
                    f"query. Add a filter, or use 'aq vectordb drop' to remove the collection."
                )
            )

        manager = self._model.vectors
        engine = await manager.engine()
        collection = await manager.collection()

        if compiled.residuals:
            # Residual predicates cannot be pushed down, so resolve the matching
            # keys first and delete by key. Correct, at the cost of a read.
            records = await self.all()
            keys = [str(r.key) for r in records if r.key is not None]
            return await manager.remove_many(keys) if keys else 0

        return int(await engine.write(collection.discard, where=compiled.native))

    async def explain(self, *, vector: list[float] | None = None) -> dict[str, Any]:
        """
        Return the planner's decision for this query.

        Args:
            vector: Probe vector to plan against. Defaults to a zero vector,
                which exercises the same index path without needing real input.

        Returns:
            The plan strategy, index type, candidate count, whether the metadata
            index was used, and whether the GPU index served it.
        """
        manager = self._model.vectors
        engine = await manager.engine()
        collection = await manager.collection()
        compiled = self._compile()

        probe = vector if vector is not None else [0.0] * (engine.config.dimension or 1)
        kwargs: dict[str, Any] = {"top": self._limit or 10}
        if compiled.native is not None:
            kwargs["where"] = compiled.native

        plan = await engine.read(collection.explain, probe, **kwargs)
        strategy = str(getattr(plan, "strategy", "unknown"))
        full_scan = strategy in FULL_SCAN_STRATEGIES

        if full_scan and WARN_ON_FULL_SCAN:
            _log.warning(
                "vector query on %s planned a full scan (%s candidates) — index a filtered field, or narrow the filter",
                self._model.__name__,
                getattr(plan, "candidate_count", "?"),
            )

        return {
            "strategy": strategy,
            "index_type": str(getattr(plan, "index_type", "unknown")),
            "candidate_count": getattr(plan, "candidate_count", None),
            "metadata_accelerated": getattr(plan, "metadata_accelerated", None),
            "gpu_index": getattr(plan, "gpu_index", None),
            "full_scan": full_scan,
            "residuals": [r.description for r in compiled.residuals],
            "ef_search": self._ef_search,
        }

    # ── Internals ────────────────────────────────────────────────────────

    def _apply_prompt(self, text: str) -> str:
        """Wrap query text in the chained prompt template, if any."""
        return self._prompt.format(text=text) if self._prompt else text

    # ── Iteration ────────────────────────────────────────────────────────

    def __aiter__(self) -> _VectorQueryIterator[TModel]:
        """
        Iterate matching records.

        Sync, returning an object with an ``async __anext__`` — so nothing runs
        until the first iteration, matching ``Q.__aiter__``.
        """
        return _VectorQueryIterator(self)

    # ── Guards ───────────────────────────────────────────────────────────

    def __bool__(self) -> bool:
        """Always raises — a lazy query has no truthiness until executed."""
        raise VectorQueryFault(
            reason=(
                "VectorQuery has no boolean value — 'if query:' would test the object, not "
                "the results. Use 'await query.exists()' instead."
            )
        )

    def __len__(self) -> int:
        """Always raises — counting requires an await."""
        raise VectorQueryFault(reason="VectorQuery does not support len(). Use 'await query.count()' instead.")

    def __repr__(self) -> str:
        parts = [self._model.__name__]
        if self._lookups:
            parts.append(f"filter={self._lookups}")
        if self._nodes:
            parts.append(f"nodes={len(self._nodes)}")
        if self._excludes:
            parts.append(f"excludes={len(self._excludes)}")
        if self._limit is not None:
            parts.append(f"limit={self._limit}")
        if self._offset:
            parts.append(f"offset={self._offset}")
        return f"<VectorQuery {' '.join(parts)}>"

    # ── Internals ────────────────────────────────────────────────────────

    def _compile(self) -> Any:
        """Compile the accumulated chain state into a native filter."""
        compiler = FilterCompiler(self._model._vfields)
        return compiler.compile(self._nodes + self._excludes, self._lookups)

    def _check_dimension(self, vector: list[float], engine: Any) -> None:
        """Reject a query vector whose length does not match the store."""
        from aquilia.vectordb.faults import VectorDimensionFault

        expected = engine.config.dimension
        if expected and len(vector) != expected:
            raise VectorDimensionFault(
                expected=expected,
                actual=len(vector),
                context=f"{self._model.__name__} search query",
            )

    def _to_hit(self, raw: Any) -> Hit[TModel]:
        """Convert a native elips hit into a typed :class:`Hit`."""
        record = self._model._from_hit(
            key=str(raw.key),
            meta=dict(raw.meta or {}),
            score=_to_score(raw.distance),
            vector=list(raw.vector) if getattr(raw, "vector", None) else None,
            lineage=getattr(raw, "lineage", None),
            chunk=getattr(raw, "chunk", None),
        )
        return Hit(
            record=record,
            score=_to_score(raw.distance),
            distance=float(raw.distance),
            approximate=bool(getattr(raw, "approximate", False)),
            codec=str(getattr(raw, "codec", "none")),
        )


class _VectorQueryIterator(Generic[TModel]):
    """Async iterator over a query's results, fetched on first ``__anext__``."""

    __slots__ = ("_query", "_records", "_index")

    def __init__(self, query: VectorQuery[TModel]) -> None:
        self._query = query
        self._records: list[TModel] | None = None
        self._index = 0

    async def __anext__(self) -> TModel:
        """Return the next record, executing the query lazily on first call."""
        if self._records is None:
            self._records = await self._query.all()
        if self._index >= len(self._records):
            raise StopAsyncIteration
        record = self._records[self._index]
        self._index += 1
        return record


def _to_score(distance: float) -> float:
    """
    Convert an elips distance into a similarity score where higher is better.

    elips normalizes every metric so that smaller means closer, with cosine and
    euclidean distances starting at ``0.0`` for an exact match. Mapping through
    ``1 / (1 + d)`` gives a bounded ``(0, 1]`` score that is monotonic in
    distance for all three metrics, so ranking and thresholds behave the same way
    regardless of which metric a store was configured with. The raw distance
    stays on :attr:`Hit.distance` for callers that need it.
    """
    return 1.0 / (1.0 + max(0.0, float(distance)))


__all__ = ["DEFAULT_SCAN_LIMIT", "Hit", "VectorQuery"]

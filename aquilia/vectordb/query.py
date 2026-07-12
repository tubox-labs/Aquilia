"""
Aquilia VectorDB query -- VF filter nodes, VQ chainable queryset, VectorHit.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .faults import VectorQueryFault

if TYPE_CHECKING:
    from elips import Filter

    from .base import VectorModel
    from .engine import ElipsEngine

__all__ = ["VF", "VQ", "VectorHit"]


def _build_leaf_filter(kwargs: dict[str, Any], meta_fields: dict) -> Filter:
    """Convert a flat ``{field_lookup: value}`` dict into an ``elips.Filter``, AND-ed together."""
    from elips import Filter

    lookup_map = {
        "exact": lambda f, v: f.equals(v),
        "ne": lambda f, v: f.not_equals(v),
        "gt": lambda f, v: f.gt(v),
        "gte": lambda f, v: f.gte(v),
        "lt": lambda f, v: f.lt(v),
        "lte": lambda f, v: f.le(v),
        "in": lambda f, v: f.one_of(v),
        "contains": lambda f, v: f.contains(v),
    }

    result: Filter | None = None

    for lookup_key, value in kwargs.items():
        parts = lookup_key.split("__", 1)
        field_name = parts[0]
        op = parts[1] if len(parts) == 2 else "exact"

        if op not in lookup_map:
            raise VectorQueryFault(operation="filter", reason=f"Unknown lookup: __{op}")

        meta_key = field_name
        field = meta_fields.get(field_name)
        if field is not None:
            meta_key = field.meta_key
            value = [field.to_meta(v) for v in value] if op == "in" else field.to_meta(value)

        predicate = lookup_map[op](Filter().field(meta_key), value)

        result = predicate if result is None else result.and_(predicate)

    return result if result is not None else Filter()


class VF:
    """
    Composable metadata filter node. Mirrors Aquilia's ``QNode``.

    Usage:
        VF(author="Alice")
        VF(year__gte=2024)
        VF(author="Alice") & VF(active=True)    # AND
        VF(author="Alice") | VF(author="Bob")   # OR
        ~VF(kind="doc")                          # NOT
    """

    AND = "AND"
    OR = "OR"

    def __init__(self, **kwargs: Any) -> None:
        self._kwargs = kwargs
        self._connector = VF.AND
        self._children: list[VF] = []
        self._negated = False

    def __and__(self, other: VF) -> VF:
        node = VF.__new__(VF)
        node._kwargs = {}
        node._connector = VF.AND
        node._children = [self, other]
        node._negated = False
        return node

    def __or__(self, other: VF) -> VF:
        node = VF.__new__(VF)
        node._kwargs = {}
        node._connector = VF.OR
        node._children = [self, other]
        node._negated = False
        return node

    def __invert__(self) -> VF:
        node = VF.__new__(VF)
        node._kwargs = self._kwargs.copy()
        node._connector = self._connector
        node._children = list(self._children)
        node._negated = not self._negated
        return node

    def _build_filter(self, meta_fields: dict) -> Filter:
        """Convert this ``VF`` tree into an ``elips.Filter``."""
        from elips import Filter

        if self._children:
            parts = [child._build_filter(meta_fields) for child in self._children]
            result = parts[0]
            for part in parts[1:]:
                result = result.and_(part) if self._connector == VF.AND else result.or_(part)
        else:
            result = _build_leaf_filter(self._kwargs, meta_fields)

        if self._negated:
            result = Filter.not_(result)
        return result

    def __repr__(self) -> str:
        if self._children:
            return f"VF({self._connector}, children={len(self._children)}, negated={self._negated})"
        return f"VF({self._kwargs}, negated={self._negated})"


class VectorHit:
    """
    A search result: a ``VectorModel`` instance with an attached ``.distance``.

    Attribute access is proxied to the underlying instance, so ``hit.title``,
    ``hit.author``, ``hit.key`` all work naturally.
    """

    __slots__ = ("_instance", "distance")

    def __init__(self, instance: VectorModel, distance: float) -> None:
        object.__setattr__(self, "_instance", instance)
        object.__setattr__(self, "distance", distance)

    def __getattr__(self, name: str) -> Any:
        return getattr(object.__getattribute__(self, "_instance"), name)

    def __repr__(self) -> str:
        inst = object.__getattribute__(self, "_instance")
        dist = object.__getattribute__(self, "distance")
        return f"<VectorHit distance={dist:.4f} {inst!r}>"


class _VQAsyncIterator:
    """Async iterator over a ``VQ``'s results -- executes and caches on first ``__anext__``."""

    def __init__(self, vq: VQ) -> None:
        self._vq = vq
        self._results: list | None = None
        self._idx = 0

    def __aiter__(self) -> _VQAsyncIterator:
        return self

    async def __anext__(self) -> Any:
        if self._results is None:
            self._results = await self._vq.all()
        if self._idx >= len(self._results):
            raise StopAsyncIteration
        item = self._results[self._idx]
        self._idx += 1
        return item


class VQ:
    """
    Chainable, immutable queryset for ``VectorModel``.

    Every chain method returns a new ``VQ`` (never mutates ``self``); every
    terminal method is async.

    Two modes:
      - Scan mode (default): ``arena.sweep()`` with a metadata filter,
        returns ``list[VectorModel]``.
      - Search mode: activated by ``.near()``/``.near_text()``/``.hybrid()``,
        uses ``arena.probe*()``, returns ``list[VectorHit]``.
    """

    __slots__ = (
        "_model_cls",
        "_engine",
        "_meta_filters",
        "_exclude_filters",
        "_near_vector",
        "_near_text",
        "_lexical_weight",
        "_max_distance",
        "_top",
        "_limit_val",
        "_offset_val",
        "_include_vectors",
        "_is_none",
        "_is_search_mode",
        "_result_cache",
    )

    def __init__(self, *, model_cls: type[VectorModel], engine: ElipsEngine) -> None:
        self._model_cls = model_cls
        self._engine = engine
        self._meta_filters: list[VF] = []
        self._exclude_filters: list[VF] = []
        self._near_vector: list[float] | None = None
        self._near_text: str | None = None
        self._lexical_weight: float = 0.5
        self._max_distance: float | None = None
        self._top: int = 10
        self._limit_val: int | None = None
        self._offset_val: int = 0
        self._include_vectors: bool = False
        self._is_none: bool = False
        self._is_search_mode: bool = False
        self._result_cache: list | None = None

    def _clone(self) -> VQ:
        c = VQ.__new__(VQ)
        c._model_cls = self._model_cls
        c._engine = self._engine
        c._meta_filters = list(self._meta_filters)
        c._exclude_filters = list(self._exclude_filters)
        c._near_vector = self._near_vector
        c._near_text = self._near_text
        c._lexical_weight = self._lexical_weight
        c._max_distance = self._max_distance
        c._top = self._top
        c._limit_val = self._limit_val
        c._offset_val = self._offset_val
        c._include_vectors = self._include_vectors
        c._is_none = self._is_none
        c._is_search_mode = self._is_search_mode
        c._result_cache = None
        return c

    # ── Chain methods ────────────────────────────────────────────────

    def filter(self, *vf_nodes: VF, **kwargs: Any) -> VQ:
        c = self._clone()
        c._meta_filters.extend(vf_nodes)
        if kwargs:
            c._meta_filters.append(VF(**kwargs))
        return c

    def exclude(self, *vf_nodes: VF, **kwargs: Any) -> VQ:
        c = self._clone()
        c._exclude_filters.extend(vf_nodes)
        if kwargs:
            c._exclude_filters.append(VF(**kwargs))
        return c

    def near(self, vector: list[float], *, top: int = 10, max_distance: float | None = None) -> VQ:
        c = self._clone()
        c._near_vector = list(vector)
        c._top = top
        c._max_distance = max_distance
        c._is_search_mode = True
        return c

    def near_text(self, text: str, *, top: int = 10, max_distance: float | None = None) -> VQ:
        c = self._clone()
        c._near_text = text
        c._top = top
        c._max_distance = max_distance
        c._is_search_mode = True
        return c

    def hybrid(
        self,
        vector: list[float],
        text: str,
        *,
        top: int = 10,
        lexical_weight: float = 0.5,
        max_distance: float | None = None,
    ) -> VQ:
        c = self._clone()
        c._near_vector = list(vector)
        c._near_text = text
        c._lexical_weight = lexical_weight
        c._top = top
        c._max_distance = max_distance
        c._is_search_mode = True
        return c

    def limit(self, n: int) -> VQ:
        if self._is_search_mode:
            raise VectorQueryFault(
                operation="limit",
                reason="limit() is not valid in search mode; use top= on near()/near_text()/hybrid()",
            )
        c = self._clone()
        c._limit_val = n
        return c

    def offset(self, n: int) -> VQ:
        if self._is_search_mode:
            raise VectorQueryFault(operation="offset", reason="offset() is not valid in search mode")
        c = self._clone()
        c._offset_val = n
        return c

    def include_vectors(self, value: bool = True) -> VQ:
        c = self._clone()
        c._include_vectors = value
        return c

    def none(self) -> VQ:
        c = self._clone()
        c._is_none = True
        return c

    # ── Filter compilation ──────────────────────────────────────────

    def _build_elips_filter(self) -> Filter | None:
        """Combine all accumulated ``VF`` nodes into a single ``elips.Filter``, or ``None`` if empty."""
        from elips import Filter

        meta_fields = self._model_cls._meta_fields
        combined: Filter | None = None

        for vf in self._meta_filters:
            f = vf._build_filter(meta_fields)
            combined = f if combined is None else combined.and_(f)

        for vf in self._exclude_filters:
            f = Filter.not_(vf._build_filter(meta_fields))
            combined = f if combined is None else combined.and_(f)

        return combined

    # ── Terminal methods ────────────────────────────────────────────

    async def all(self) -> list:
        """Execute the query. Scan mode returns ``list[VectorModel]``; search mode returns ``list[VectorHit]``."""
        if self._is_none:
            return []

        if self._result_cache is not None:
            return list(self._result_cache)

        arena = await self._engine.arena(self._model_cls._vault_name)
        where = self._build_elips_filter()

        results = (
            await self._execute_search(arena, where) if self._is_search_mode else await self._execute_scan(arena, where)
        )

        self._result_cache = results
        return results

    async def _execute_scan(self, arena: Any, where: Any) -> list:
        rows = await self._engine.run_sync(
            arena.sweep,
            where=where,
            offset=self._offset_val,
            limit=self._limit_val,
            include_vectors=self._include_vectors,
        )
        return [self._model_cls._from_row(row) for row in rows]

    async def _execute_search(self, arena: Any, where: Any) -> list:
        has_vector = self._near_vector is not None
        has_text = self._near_text is not None

        if has_vector and has_text:
            hits = await self._engine.run_sync(
                arena.probe_hybrid,
                self._near_vector,
                self._near_text,
                top=self._top,
                where=where,
                max_distance=self._max_distance,
                lexical_weight=self._lexical_weight,
                include_vectors=self._include_vectors,
            )
        elif has_vector:
            hits = await self._engine.run_sync(
                arena.probe,
                self._near_vector,
                top=self._top,
                where=where,
                max_distance=self._max_distance,
                include_vectors=self._include_vectors,
            )
        else:
            hits = await self._engine.run_sync(
                arena.probe_text,
                self._near_text,
                top=self._top,
                where=where,
                max_distance=self._max_distance,
                include_vectors=self._include_vectors,
            )

        return [VectorHit(self._model_cls._from_row_like(hit), hit.distance) for hit in hits]

    async def first(self):
        results = await self.all()
        return results[0] if results else None

    async def one(self):
        results = await self.all()
        if len(results) == 0:
            raise VectorQueryFault(
                model=self._model_cls.__name__,
                operation="one",
                reason="Expected exactly one result, got 0",
            )
        if len(results) > 1:
            raise VectorQueryFault(
                model=self._model_cls.__name__,
                operation="one",
                reason=f"Expected exactly one result, got {len(results)}",
            )
        return results[0]

    async def count(self) -> int:
        if self._is_none:
            return 0
        if not self._is_search_mode and not self._meta_filters and not self._exclude_filters:
            arena = await self._engine.arena(self._model_cls._vault_name)
            return await self._engine.run_sync(arena.count)
        return len(await self.all())

    async def delete(self) -> int:
        if self._is_search_mode:
            raise VectorQueryFault(
                model=self._model_cls.__name__,
                operation="delete",
                reason="delete() is not valid in search mode",
            )
        if self._is_none:
            return 0
        where = self._build_elips_filter()
        arena = await self._engine.arena(self._model_cls._vault_name)
        if where is None:
            rows = await self._engine.run_sync(arena.sweep, where=None, limit=None)
            keys = [row.key for row in rows]
            if not keys:
                return 0
            return await self._engine.run_sync(arena.discard, keys)
        return await self._engine.run_sync(arena.discard, where=where)

    async def explain(self) -> str:
        if not self._is_search_mode or self._near_vector is None:
            raise VectorQueryFault(
                operation="explain",
                reason="explain() requires a near() or hybrid() query with an explicit vector",
            )
        arena = await self._engine.arena(self._model_cls._vault_name)
        where = self._build_elips_filter()
        plan = await self._engine.run_sync(
            arena.explain,
            self._near_vector,
            top=self._top,
            where=where,
            max_distance=self._max_distance,
            has_text_component=self._near_text is not None,
        )
        return str(plan)

    def __aiter__(self) -> _VQAsyncIterator:
        return _VQAsyncIterator(self)

    def __repr__(self) -> str:
        return f"<VQ: {self._model_cls.__name__} search_mode={self._is_search_mode}>"

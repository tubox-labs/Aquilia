"""
AquilaVectorDB — Compiled schema types.

The immutable output of :mod:`aquilia.vectordb.metaclass`. Split into its own
module so :mod:`aquilia.vectordb.base`, :mod:`~aquilia.vectordb.manager`, and
:mod:`~aquilia.vectordb.filters` can read schema types without importing the
metaclass and creating an import cycle.

Everything here is built once, at class creation, and never mutated. The hot
paths — hydration, encoding, filter compilation — read precomputed mappings
rather than re-deriving anything from annotations, mirroring the
``_non_m2m_fields`` / ``_col_to_attr`` precomputation in ``aquilia/models``.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from aquilia.vectordb.codecs import Codec

if TYPE_CHECKING:
    from aquilia.vectordb.fields import BaseVectorField


@dataclass(frozen=True)
class PayloadSpec:
    """
    Compiled definition of one payload attribute.

    Attributes:
        attribute: Python attribute name.
        key: On-disk metadata key — ``Field(alias=...)``, ``Payload(name=...)``,
            or the attribute name.
        codec: Encoder/decoder pair for this attribute's type.
        python_type: The unwrapped, non-optional annotation type. Hydration
            needs it to pick the decode target.
        validators: Built validator callables from the field's constraints or
            ``Annotated`` metadata.
        optional: Whether ``None`` is allowed.
        indexed: Whether an index hint was declared.
        written: Whether the attribute is persisted (a score is not).
        field: The declaring :class:`~aquilia.vectordb.fields.BaseVectorField`,
            or ``None`` for a legacy ``Annotated`` declaration. Carries defaults
            and normalization rules the write path applies.
    """

    attribute: str
    key: str
    codec: Codec
    python_type: Any
    validators: tuple[Callable[[Any], None], ...] = ()
    optional: bool = False
    indexed: bool = False
    written: bool = True
    field: BaseVectorField | None = None


@dataclass(frozen=True)
class VectorOptions:
    """
    Resolved ``class Meta`` for a vector model.

    Attributes:
        collection: elips vault name; defaults to the lowercased class name.
        store: Which configured store alias this model binds to.
        dimension: Vector length declared via ``Meta``; ``0`` when only a
            ``Dimension()`` marker carries it.
        metric: Similarity metric — ``cosine``, ``l2``, or ``dot``.
        index: Index kind — ``flat``, ``hnsw``, or ``ivf``.
        index_options: Index tuning forwarded to elips.
        abstract: Base class for others; never registered or bound.
        read_only: Reject writes to this collection.
        embedder: Per-model embedder override, as a URI
            (``"sentence-transformers/all-MiniLM-L6-v2"``).
        ef_search: Default HNSW beam width for searches on this collection.
            Overridable per query with ``VectorQuery.ef_search()``.
        max_connections: HNSW ``M`` — edges retained per graph node.
        ef_construction: HNSW build-time beam width.
        compaction_ratio: Tombstone fraction at which the index self-rebuilds.
        prompt_template: Applied to query text before embedding, for models that
            expect one (``"query: {}"`` for E5).
    """

    collection: str = ""
    store: str = "default"
    dimension: int = 0
    metric: str = "cosine"
    index: str = "flat"
    index_options: dict[str, Any] = field(default_factory=dict)
    abstract: bool = False
    read_only: bool = False
    embedder: str | None = None
    ef_search: int | None = None
    max_connections: int | None = None
    ef_construction: int | None = None
    compaction_ratio: float | None = None
    prompt_template: str | None = None


@dataclass(frozen=True)
class VectorSchema:
    """
    Compiled, immutable description of a vector model.

    Attributes:
        model: The model class.
        model_name: Class name, used in fault messages.
        key_attr: Attribute carrying ``Key()``.
        text_attr: Attribute carrying ``Text()``, or ``None``.
        vector_attr: Attribute holding the vector, or ``None``.
        dimension: Resolved vector length; ``0`` when unknown until bind time.
        payloads: ``{attribute: PayloadSpec}``, declaration-ordered.
        payload_keys: ``{storage key: PayloadSpec}`` — the read-path index.
        link_attrs: Attributes carrying an interop ``Link`` or a ``LinkField``.
        score_attr: Attribute receiving search scores, or ``None``.
        embed_text: Whether the text slot asked for automatic embedding.
        fields: ``{attribute: BaseVectorField}`` for every unified field
            declaration. Empty for a purely legacy ``Annotated`` model.
    """

    model: type
    model_name: str
    key_attr: str | None
    text_attr: str | None
    vector_attr: str | None
    dimension: int
    payloads: dict[str, PayloadSpec] = field(default_factory=dict)
    payload_keys: dict[str, PayloadSpec] = field(default_factory=dict)
    link_attrs: frozenset[str] = frozenset()
    score_attr: str | None = None
    embed_text: bool = True
    fields: dict[str, BaseVectorField] = field(default_factory=dict)

    # ── Derived caches, computed once in __post_init__ ───────────────────

    attribute_names: frozenset[str] = field(default=frozenset(), repr=False)
    validators: dict[str, tuple[Callable[[Any], None], ...]] = field(default_factory=dict, repr=False)
    written_payloads: tuple[PayloadSpec, ...] = field(default=(), repr=False)

    def __post_init__(self) -> None:
        """Precompute the mappings the hot paths read on every record."""
        names: set[str] = set(self.payloads)
        for attr in (self.key_attr, self.text_attr, self.vector_attr, self.score_attr):
            if attr:
                names.add(attr)

        object.__setattr__(self, "attribute_names", frozenset(names))
        object.__setattr__(
            self,
            "validators",
            {spec.attribute: spec.validators for spec in self.payloads.values() if spec.validators},
        )
        object.__setattr__(
            self,
            "written_payloads",
            tuple(spec for spec in self.payloads.values() if spec.written),
        )

    def resolve_payload(self, name: str) -> PayloadSpec | None:
        """Resolve a payload by Python attribute name, falling back to storage key."""
        return self.payloads.get(name) or self.payload_keys.get(name)

    @property
    def payload_by_attr(self) -> dict[str, PayloadSpec]:
        """Alias of :attr:`payloads`, for filter-compiler readability."""
        return self.payloads

    @property
    def key_field(self) -> BaseVectorField | None:
        """The declaring field for the key slot, when declared as a field."""
        return self.fields.get(self.key_attr) if self.key_attr else None

    @property
    def text_field(self) -> BaseVectorField | None:
        """The declaring field for the text slot, when declared as a field."""
        return self.fields.get(self.text_attr) if self.text_attr else None

    @property
    def vector_field(self) -> BaseVectorField | None:
        """The declaring field for the vector slot, when declared as a field."""
        return self.fields.get(self.vector_attr) if self.vector_attr else None


__all__ = ["PayloadSpec", "VectorOptions", "VectorSchema"]

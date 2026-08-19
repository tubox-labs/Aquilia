"""
AquilaVectorDB — VectorModel metaclass and schema.

:class:`VectorModelMeta` turns a typed class body into a :class:`VectorSchema`:

* modern ``BaseVectorField`` assignments (``KeyField()``, ``TextField()``,
  ``VectorField()``, ``Field()``) are resolved first;
* ``Annotated`` field objects and the older slot markers remain supported;
* attributes with no declaration are inferred by type (§2.4 of the
  implementation plan), with anything unroutable rejected at class creation;
* validators from field options or ``Annotated`` metadata are built and cached;
* the class is registered in :class:`VectorRegistry` and a
  ``vector_class_prepared`` signal is fired.

The processing sequence mirrors ``aquilia/models/metaclass.py`` step for step,
minus SQL concerns: early return for the base class, pop ``Meta``, inherit the
parent schema, resolve annotations with ``include_extras=True``, route fields,
precompute caches, bind the manager, register, signal.

Why ``include_extras=True`` matters
-----------------------------------

PEP 563 (``from __future__ import annotations``) is in force across this repo:
annotations are strings, evaluated lazily by :func:`typing.get_type_hints`.
Without ``include_extras=True`` the ``Annotated`` metadata wrapper is *stripped*
and every marker vanishes, silently turning a ``Key()`` field into an inferred
payload. This is the single most important line in the metaclass.

Field descriptors and instance storage
---------------------------------------

Modern field assignments install descriptors on the model class. Class access
returns the field object, so ``Document.views >= 10`` builds a filter expression;
instance access reads the typed value from ``instance.__dict__``. Pure marker
models retain the older no-descriptor behavior and use keyword filters. Both
styles compile to the same schema, but direct field assignment is the preferred
declaration for new code.
"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Any, get_type_hints

from aquilia.vectordb.annotations import (
    Constraint,
    Dimension,
    Key,
    Payload,
    Score,
    Text,
    build_validators,
)
from aquilia.vectordb.codecs import resolve_codec
from aquilia.vectordb.faults import VectorSchemaFault
from aquilia.vectordb.fields import (
    BaseVectorField,
    KeyField,
    LinkField,
    ScoreField,
    TextField,
    VectorField,
)
from aquilia.vectordb.schema import PayloadSpec, VectorOptions, VectorSchema

if TYPE_CHECKING:
    pass

#: Elips metadata primitives — anything outside this set needs a codec.
_META_TYPES: tuple[type, ...] = (bool, int, float, str)

#: Payload attributes whose values are never written (score slot).
_NON_WRITABLE = frozenset({"score"})


class VectorModelMeta(type):
    """
    Metaclass for vector models.

    Handles annotation resolution, slot routing, cardinality checks,
    ``Meta`` → :class:`VectorOptions`, precomputed caches, manager binding,
    registry registration, and the ``vector_class_prepared`` signal.
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> type:
        parents = [b for b in bases if isinstance(b, VectorModelMeta)]
        if not parents:
            # This is VectorModel itself.
            return super().__new__(mcs, name, bases, namespace)

        # Inherit the parent schema, if any.
        inherited: VectorSchema | None = None
        for base in bases:
            candidate = base.__dict__.get("_vfields")
            if isinstance(candidate, VectorSchema):
                inherited = candidate
                break

        meta_class = namespace.pop("Meta", None)

        cls = super().__new__(mcs, name, bases, namespace)
        model_cls = cls

        options = _options_from_meta(name, meta_class, inherited)

        try:
            schema = _build_schema(model_cls, inherited, options)
        except VectorSchemaFault:
            raise
        except Exception as exc:
            raise VectorSchemaFault(
                model=name,
                reason=f"failed to build schema: {exc}",
            ) from exc

        model_cls._vfields = schema
        model_cls._meta = schema
        model_cls._voptions = options

        # Bind the manager, unless the body declared its own.
        from aquilia.vectordb.manager import BaseVectorManager, VectorManager

        if not any(isinstance(v, BaseVectorManager) for v in namespace.values()):
            mgr = VectorManager()
            mgr.__set_name__(model_cls, "vectors")
            model_cls.vectors = mgr

        # Register and signal — mirroring ModelMeta's late registration so
        # listeners see a fully-built class. Abstract bases are skipped: they
        # exist to be inherited, not bound to a collection.
        if not model_cls._voptions.abstract:
            from aquilia.vectordb.registry import VectorRegistry

            VectorRegistry.register(model_cls)

        from aquilia.vectordb.signals import vector_class_prepared

        vector_class_prepared.send_sync(sender=model_cls)

        return cls

    # ── Base-class convenience: Meta lives on the metaclass for
    #    `class Meta:` in subclasses; VectorModel's own options are in base.py.


def _build_schema(
    model_cls: type,
    inherited: VectorSchema | None,
    options: VectorOptions,
) -> VectorSchema:
    """
    Compile the schema for one concrete model class.

    Steps, mirroring ``ModelMeta.__new__``:

    1. Resolve direct field assignments and annotations, including
       ``Annotated`` metadata.
    2. Merge inherited payloads and field descriptors; this class's declarations
       override them.
    3. Route each attribute to a slot through the unified priority chain
       (§2.5): a directly-assigned field, then ``Annotated`` field metadata,
       then a compatibility marker, then type inference.
    4. Enforce cardinality: ≤1 ``Key``, ≤1 ``Text``, ≤1 ``Score``, ≤1 vector
       attribute; at least one of vector/text so the model can be written.
    5. Precompute the caches the hot paths read.
    """
    hints = _resolve_hints(model_cls)

    key_attr: str | None = None
    text_attr: str | None = None
    vector_attr: str | None = None
    score_attr: str | None = None
    dimension_from_marker: int | None = None
    embed_text = True

    payloads: dict[str, PayloadSpec] = {}
    fields: dict[str, BaseVectorField] = {}

    if inherited is not None:
        for attr, spec in inherited.payloads.items():
            payloads[attr] = spec
        for attr, field_obj in getattr(inherited, "fields", {}).items():
            # Clone: two model classes must never share one field object, or
            # __set_name__ on the subclass would rewrite the parent's owner.
            fields[attr] = field_obj.clone()

    # Skip descriptors declared in *this* class body (a model's own property or
    # method is not a record field) — but never skip a BaseVectorField, which is
    # a descriptor precisely so expressions and value access can coexist.
    # Inherited descriptors are deliberately not skipped: ``VectorModel``
    # defines a ``key`` property, and a model annotating ``key: Annotated[str,
    # Key()]`` must still route it.
    declared = [
        attr
        for attr in hints
        if not attr.startswith("_")
        and attr != "Meta"
        and (
            isinstance(model_cls.__dict__.get(attr), BaseVectorField)
            or not isinstance(
                model_cls.__dict__.get(attr),
                (classmethod, staticmethod, property),
            )
        )
    ]

    # A field may be assigned without an annotation (`views = Field(default=0)`).
    # Those are real declarations and must route, so they join the walk after the
    # annotated ones, preserving declaration order.
    for attr, value in model_cls.__dict__.items():
        if isinstance(value, BaseVectorField) and attr not in declared and not attr.startswith("_"):
            declared.append(attr)

    for attr in declared:
        annotation = hints.get(attr)
        metadata = _annotated_metadata(annotation)
        base_type = _annotation_base_type(annotation) if annotation is not None else None

        field_obj = _resolve_field(model_cls, attr, metadata)
        if field_obj is not None:
            field_obj.__set_name__(model_cls, attr)
            fields[attr] = field_obj
            setattr(model_cls, attr, field_obj)

            slot = field_obj.slot
            if base_type is None:
                base_type = _infer_type_from_field(field_obj)

            if slot == "key":
                _ensure_none(key_attr, model_cls.__name__, "Key", attr)
                key_attr = attr
                continue

            if slot == "score":
                _ensure_none(score_attr, model_cls.__name__, "Score", attr)
                score_attr = attr
                continue

            if slot == "vector":
                _ensure_none(vector_attr, model_cls.__name__, "vector", attr)
                vector_attr = attr
                declared_dim = getattr(field_obj, "dimension", None)
                if declared_dim is not None:
                    if dimension_from_marker is not None and dimension_from_marker != declared_dim:
                        raise VectorSchemaFault(
                            model=model_cls.__name__,
                            reason=(
                                f"conflicting vector dimensions: {attr} declares {declared_dim} "
                                f"but another attribute declares {dimension_from_marker}"
                            ),
                        )
                    dimension_from_marker = declared_dim
                continue

            if slot == "text":
                _ensure_none(text_attr, model_cls.__name__, "Text", attr)
                text_attr = attr
                embed_text = bool(getattr(field_obj, "embed", True))
                payloads[attr] = _payload_spec_from_field(
                    model_cls.__name__, attr, field_obj, base_type or str, metadata
                )
                continue

            payloads[attr] = _payload_spec_from_field(model_cls.__name__, attr, field_obj, base_type or str, metadata)
            continue

        # ── Compatibility slot markers, checked before inference ───────
        if isinstance(metadata.get("key"), Key):
            _ensure_none(key_attr, model_cls.__name__, "Key", attr)
            key_attr = attr
            continue

        if isinstance(metadata.get("score"), Score):
            _ensure_none(score_attr, model_cls.__name__, "Score", attr)
            score_attr = attr
            continue

        dim_marker = metadata.get("dimension")
        if isinstance(dim_marker, Dimension):
            _ensure_none(vector_attr, model_cls.__name__, "vector", attr)
            vector_attr = attr
            if dimension_from_marker is not None and dimension_from_marker != dim_marker.size:
                raise VectorSchemaFault(
                    model=model_cls.__name__,
                    reason=(
                        f"conflicting Dimension markers: {attr} declares {dim_marker.size} "
                        f"but another attribute declares {dimension_from_marker}"
                    ),
                )
            dimension_from_marker = dim_marker.size
            continue

        # Text is both a slot and a retrievable payload: the text is stored on
        # the document attachment, and also mirrored into metadata so filters
        # and hydration can reach it without a second fetch.
        text_marker = metadata.get("text")
        if isinstance(text_marker, Text):
            _ensure_none(text_attr, model_cls.__name__, "Text", attr)
            text_attr = attr
            embed_text = bool(text_marker.embed)
            payloads[attr] = _payload_spec(model_cls.__name__, attr, None, base_type, metadata)
            continue

        if isinstance(metadata.get("payload"), Payload):
            payloads[attr] = _payload_spec(
                model_cls.__name__,
                attr,
                metadata["payload"],
                base_type,
                metadata,
            )
            continue

        # ── Inference (§2.5 step 3), strictly ordered ───────────────────
        if _is_vector_type(base_type):
            _ensure_none(vector_attr, model_cls.__name__, "vector", attr)
            vector_attr = attr
            continue

        if base_type is str and attr in ("key", "id"):
            _ensure_none(key_attr, model_cls.__name__, "Key", attr)
            key_attr = attr
            continue

        if base_type in _META_TYPES or resolve_codec(base_type) is not None:
            payloads[attr] = _payload_spec(model_cls.__name__, attr, None, base_type, metadata)
            continue

        raise VectorSchemaFault(
            model=model_cls.__name__,
            reason=(
                f"attribute {attr!r} has type {_display_type(base_type)} with no slot marker "
                f"and no payload codec. Annotate it with Key(), Text(), Payload(), "
                f"Dimension(), or Score() — or assign a KeyField()/TextField()/"
                f"VectorField()/Field() descriptor."
            ),
        )

    # ── Cardinality ─────────────────────────────────────────────────────
    vector_present = vector_attr is not None or dimension_from_marker is not None
    if key_attr is None and not options.abstract:
        raise VectorSchemaFault(
            model=model_cls.__name__,
            reason=(
                "no key attribute declared — every vector record needs a key. "
                "Assign one attribute a KeyField(), or annotate it with Key()."
            ),
        )
    if not vector_present and text_attr is None:
        raise VectorSchemaFault(
            model=model_cls.__name__,
            reason=(
                "model has neither a vector attribute nor a text attribute — it can "
                "never be written. Assign a VectorField()/TextField(), or annotate "
                "one with Dimension()/Text()."
            ),
        )

    dimension = _resolve_dimension(model_cls.__name__, options, dimension_from_marker)

    # ── Caches ──────────────────────────────────────────────────────────
    payload_keys = {spec.key: spec for spec in payloads.values()}

    schema = VectorSchema(
        model=model_cls,
        model_name=model_cls.__name__,
        key_attr=key_attr,
        text_attr=text_attr,
        vector_attr=vector_attr,
        dimension=dimension,
        payloads=payloads,
        payload_keys=payload_keys,
        link_attrs=frozenset(),
        score_attr=score_attr,
        embed_text=embed_text,
        fields=fields,
    )

    # Link attrs are filled by interop when the (optional) Link marker is
    # present; interop hooks into the metaclass via the model class itself.
    _attach_links(model_cls, hints, schema)

    return schema


def _resolve_field(model_cls: type, attr: str, metadata: dict[str, Any]) -> BaseVectorField | None:
    """
    Find the field object declaring ``attr``, following the §2.5 priority chain.

    1. Direct class-attribute assignment — ``views: int = Field(ge=0)``.
    2. ``Annotated`` metadata — ``views: Annotated[int, Field(ge=0)]``.

    Returns:
        The declaring field, or ``None`` when the attribute uses compatibility
        markers or bare type inference. A field found in *both* places is a
        contradiction and is rejected rather than resolved by precedence.
    """
    assigned = model_cls.__dict__.get(attr)
    direct = assigned if isinstance(assigned, BaseVectorField) else None
    annotated = metadata.get("field")

    if direct is not None and annotated is not None and direct is not annotated:
        raise VectorSchemaFault(
            model=model_cls.__name__,
            reason=(
                f"attribute {attr!r} declares a field twice — once as an assigned value "
                f"({type(direct).__name__}) and once inside Annotated[...] "
                f"({type(annotated).__name__}). Keep one."
            ),
        )

    field_obj = direct if direct is not None else annotated
    if field_obj is None:
        return None

    # An Annotated field may carry a plain assignment as its default:
    #   source: Annotated[str, Field(indexed=True)] = "web"
    if direct is None and not field_obj.has_default:
        fallback = model_cls.__dict__.get(attr, UNSET_SENTINEL)
        if fallback is not UNSET_SENTINEL and not isinstance(fallback, BaseVectorField):
            field_obj.default = fallback

    # Compatibility constraints may sit beside a field in the same Annotated tuple;
    # fold them in so the two metadata vocabularies compose rather than one
    # silently winning.
    compatibility_constraints = metadata.get("constraints") or []
    if compatibility_constraints:
        field_obj.extra_validators = tuple(field_obj.extra_validators) + tuple(
            constraint.build() for constraint in compatibility_constraints
        )

    return field_obj


#: Distinguishes "attribute absent from __dict__" from a real ``None`` default.
UNSET_SENTINEL = object()


def _infer_type_from_field(field_obj: BaseVectorField) -> Any:
    """
    Guess a payload type for an unannotated field assignment.

    Only reached when a field was assigned without an annotation
    (``views = Field(default=0)``). The declared default is the best available
    evidence; a field with no default falls back to ``str``, which every codec
    table entry accepts.
    """
    if isinstance(field_obj, (KeyField, TextField)):
        return str
    if isinstance(field_obj, VectorField):
        return list
    if isinstance(field_obj, ScoreField):
        return float

    default = field_obj.get_default()
    return type(default) if default is not None else str


def _payload_spec_from_field(
    model_name: str,
    attr: str,
    field_obj: BaseVectorField,
    base_type: Any,
    metadata: dict[str, Any],
) -> PayloadSpec:
    """Compile a payload spec from a unified field declaration."""
    codec = resolve_codec(base_type)
    if codec is None:
        raise VectorSchemaFault(
            model=model_name,
            reason=(
                f"payload attribute {attr!r} has type {_display_type(base_type)}, which elips "
                f"metadata cannot store and no codec covers. Allowed: bool, int, float, str, "
                f"datetime, date, time, Decimal, UUID, bytes, Enum."
            ),
        )

    optional = _is_optional_type(metadata.get("raw_annotation", base_type)) or field_obj.get_default() is None

    return PayloadSpec(
        attribute=attr,
        key=field_obj.storage_key,
        codec=codec,
        python_type=base_type,
        validators=field_obj.build_validators(model_name, attr, optional=optional),
        optional=optional,
        indexed=field_obj.indexed,
        written=not isinstance(field_obj, ScoreField),
        field=field_obj,
    )


def _attach_links(model_cls: type, hints: dict[str, Any], schema: VectorSchema) -> None:
    """
    Record link declarations on the model class.

    Two spellings are recognised and normalised to one registry: the
    compatibility ``Link`` marker inside ``Annotated`` (matched by class name in
    :func:`_slot_name`, so the metaclass never imports ``aquilia.models``), and
    an assigned :class:`~aquilia.vectordb.fields.LinkField`.

    A linked attribute is also an ordinary payload (that is how the primary key
    reaches storage and becomes filterable); the routing loop in
    :func:`_build_schema` has already given it a :class:`PayloadSpec`, since a
    link's type is always an ``int`` or ``str`` primary key. This pass only
    records which attributes carry links, and their markers.
    """
    links: dict[str, Any] = {}

    for attr, field_obj in schema.fields.items():
        if isinstance(field_obj, LinkField):
            if attr not in schema.payloads:
                raise VectorSchemaFault(
                    model=model_cls.__name__,
                    reason=(
                        f"LinkField attribute {attr!r} is not storable — a link holds the "
                        f"target's primary key, so annotate it as int or str."
                    ),
                )
            links[attr] = field_obj

    for attr, annotation in hints.items():
        if attr.startswith("_"):
            continue
        marker = _annotated_metadata(annotation).get("link")
        if marker is None:
            continue
        if attr not in schema.payloads:
            raise VectorSchemaFault(
                model=model_cls.__name__,
                reason=(
                    f"Link attribute {attr!r} is not storable — a link holds the target's "
                    f"primary key, so annotate it as int or str."
                ),
            )
        links[attr] = marker

    # Inherited links stay in effect unless the subclass redeclares them.
    inherited = getattr(model_cls, "_vlinks", None)
    if inherited:
        links = {**inherited, **links}

    model_cls._vlinks = links
    if links:
        object.__setattr__(schema, "link_attrs", frozenset(links))


def _payload_spec(
    model_name: str,
    attr: str,
    marker: Payload | None,
    base_type: Any,
    metadata: dict[str, Any],
) -> PayloadSpec:
    """Compile one payload attribute's spec, resolving its codec and validators."""
    codec = resolve_codec(base_type)
    if codec is None:
        raise VectorSchemaFault(
            model=model_name,
            reason=(
                f"payload attribute {attr!r} has type {_display_type(base_type)}, which elips "
                f"metadata cannot store and no codec covers. Allowed: bool, int, float, str, "
                f"datetime, date, time, Decimal, UUID, bytes, Enum."
            ),
        )

    key = marker.name if marker is not None and marker.name else attr
    optional = _is_optional_type(metadata.get("raw_annotation", base_type))
    constraints: list[Constraint] = list(metadata.get("constraints", ()))

    return PayloadSpec(
        attribute=attr,
        key=key,
        codec=codec,
        python_type=base_type,
        validators=build_validators(model_name, attr, constraints, optional=optional),
        optional=optional,
        indexed=bool(marker.indexed) if marker is not None else False,
        written=attr not in _NON_WRITABLE,
    )


def _options_from_meta(
    model_name: str,
    meta_class: type | None,
    inherited: VectorSchema | None,
) -> VectorOptions:
    """Resolve ``class Meta`` into a :class:`VectorOptions`."""
    values: dict[str, Any] = {}
    if inherited is not None:
        # Inherited options merge underneath, so a subclass overrides only what
        # it declares. Two keys are deliberately never inherited:
        #   * `abstract` — an abstract base's whole purpose is concrete
        #     subclasses; inheriting it would make every one of them abstract too.
        #   * `collection` — inheriting it would silently point two models at one
        #     vault, where each would see the other's records as its own.
        prev = getattr(inherited.model, "_voptions", None)
        if prev is not None:
            values.update({k: v for k, v in dataclasses.asdict(prev).items() if k not in ("abstract", "collection")})

    if meta_class is not None:
        for key in vars(meta_class):
            if key.startswith("_"):
                continue
            val = getattr(meta_class, key)
            if callable(val) and not isinstance(val, type):
                continue
            values[key] = val

    collection = values.get("collection") or ""
    if not collection:
        collection = model_name.lower()

    def _opt_int(name: str) -> int | None:
        raw = values.get(name)
        return int(raw) if raw is not None else None

    return VectorOptions(
        collection=collection,
        store=str(values.get("store", "default")),
        dimension=int(values.get("dimension", 0) or 0),
        metric=str(values.get("metric", "cosine")),
        index=str(values.get("index", "flat")),
        index_options=dict(values.get("index_options") or {}),
        abstract=bool(values.get("abstract", False)),
        read_only=bool(values.get("read_only", False)),
        embedder=str(values["embedder"]) if values.get("embedder") else None,
        ef_search=_opt_int("ef_search"),
        max_connections=_opt_int("max_connections"),
        ef_construction=_opt_int("ef_construction"),
        compaction_ratio=(float(values["compaction_ratio"]) if values.get("compaction_ratio") is not None else None),
        prompt_template=str(values["prompt_template"]) if values.get("prompt_template") else None,
    )


def _resolve_dimension(
    model_name: str,
    options: VectorOptions,
    marker_dimension: int | None,
) -> int:
    """Resolve the declared dimension from marker and Meta, rejecting conflicts."""
    if marker_dimension is not None and options.dimension:
        if marker_dimension != options.dimension:
            raise VectorSchemaFault(
                model=model_name,
                reason=(
                    f"Dimension() marker declares {marker_dimension} but Meta.dimension "
                    f"declares {options.dimension}; they must agree."
                ),
            )
        return marker_dimension

    if marker_dimension is not None:
        return marker_dimension

    if options.dimension:
        return options.dimension

    # No dimension anywhere. Permitted only when an embedder can supply one,
    # which is checked at bind time; the schema records 0 to mean "unknown".
    return 0


def _resolve_hints(model_cls: type) -> dict[str, Any]:
    """
    Resolve the class's annotations, preserving ``Annotated`` metadata.

    This is where PEP 563 is undone. ``get_type_hints`` evaluates string
    annotations; ``include_extras=True`` keeps the ``Annotated`` wrapper
    instead of stripping it. Without the flag every marker vanishes.

    ``ClassVar`` annotations are dropped: they declare framework plumbing
    (``_vfields``, ``vectors``), not record fields, and some reference names
    that only exist under ``TYPE_CHECKING``.
    """
    from typing import ClassVar, get_origin

    hints = get_type_hints(model_cls, include_extras=True, localns=_HINT_NAMESPACE)
    return {
        attr: annotation
        for attr, annotation in hints.items()
        if get_origin(annotation) is not ClassVar and not _is_classvar_str(annotation)
    }


def _is_classvar_str(annotation: Any) -> bool:
    """Detect a ``ClassVar`` that survived as an unevaluated string."""
    return isinstance(annotation, str) and annotation.startswith("ClassVar")


#: Names injected when resolving model annotations.
#:
#: ``VectorModel`` declares ``ClassVar`` attributes typed with names imported
#: only under ``TYPE_CHECKING`` (``VectorManager``, ``VectorSchema``, ...).
#: ``get_type_hints`` evaluates every annotation on every base in the MRO, so
#: those names must resolve to *something* or resolution fails before the
#: ``ClassVar`` filter above ever runs. The bound values are irrelevant.
_HINT_NAMESPACE: dict[str, Any] = {
    "VectorSchema": VectorSchema,
    "VectorOptions": VectorOptions,
    "PayloadSpec": PayloadSpec,
    "VectorManager": Any,
    "BaseVectorManager": Any,
    "VectorState": Any,
    "VectorQuery": Any,
    "Hit": Any,
}


#: Marker class → slot name used as the key in the extracted metadata dict.
_SLOT_NAMES: dict[type, str] = {}


def _slot_name(marker: Any) -> str | None:
    """Map a marker instance to its slot name, memoizing the class lookup."""
    cls = type(marker)
    cached = _SLOT_NAMES.get(cls)
    if cached is not None:
        return cached

    from aquilia.vectordb.annotations import Dimension, Key, Payload, Score, Text

    mapping: dict[type, str] = {
        Key: "key",
        Text: "text",
        Payload: "payload",
        Dimension: "dimension",
        Score: "score",
    }
    for base, slot in mapping.items():
        if isinstance(marker, base):
            _SLOT_NAMES[cls] = slot
            return slot

    # Interop's Link marker, when present.
    if cls.__name__ == "Link":
        _SLOT_NAMES[cls] = "link"
        return "link"

    return None


def _annotated_metadata(annotation: Any) -> dict[str, Any]:
    """
    Extract slot markers, fields, and constraints from an ``Annotated[...]``.

    Returns a dict with compatibility slot names (``"key"``, ``"text"``, ``"payload"``,
    ``"dimension"``, ``"score"``, ``"link"``) mapped to marker instances, plus
    ``"field"`` (a :class:`BaseVectorField`, when one is present),
    ``"constraints"`` (every :class:`Constraint`), and ``"raw_annotation"``.

    Uses ``__metadata__`` rather than ``__args__[1:]``: it is the canonical
    extras tuple, and ``Annotated.__origin__`` is the *wrapped type*, not
    ``Annotated`` — reading the origin to detect an annotated type silently
    fails for every annotation.
    """
    result: dict[str, Any] = {"constraints": [], "raw_annotation": annotation}

    extras = getattr(annotation, "__metadata__", None)
    if not extras:
        return result

    for meta in extras:
        if isinstance(meta, BaseVectorField):
            if result.get("field") is not None:
                raise VectorSchemaFault(
                    model="<annotation>",
                    reason=(
                        f"Annotated[...] carries two field declarations "
                        f"({type(result['field']).__name__} and {type(meta).__name__}); keep one"
                    ),
                )
            result["field"] = meta
            continue
        if isinstance(meta, Constraint):
            result["constraints"].append(meta)
            continue
        slot = _slot_name(meta)
        if slot is not None:
            result[slot] = meta
    return result


def _annotation_base_type(annotation: Any) -> Any:
    """
    Unwrap an annotation to its payload type.

    Handles ``Annotated[T, ...]``, ``Optional[T]`` / ``T | None``, and
    ``list[T]`` / ``Sequence[T]`` (vector attribute). Anything else returns the
    annotation unchanged, letting the caller raise the unroutable-type fault.
    """
    from collections.abc import Sequence
    from typing import Annotated, Union, get_args, get_origin

    origin = get_origin(annotation)

    if origin is Annotated:
        args = get_args(annotation)
        return _annotation_base_type(args[0]) if args else annotation

    if origin is Union or origin is types_UnionType():
        args = [a for a in get_args(annotation) if a is not type(None)]
        if len(args) == 1:
            return _annotation_base_type(args[0])
        return annotation

    if origin is list or origin is tuple:
        return list

    if origin is not None and isinstance(origin, type) and issubclass(origin, Sequence) and origin is not str:
        return list

    return annotation


def _is_optional_type(annotation: Any) -> bool:
    """True when the annotation allows ``None``."""
    from typing import Annotated, Union, get_args, get_origin

    if annotation is None:
        return True

    origin = get_origin(annotation)
    if origin is Union or origin is types_UnionType():
        return any(a is type(None) for a in get_args(annotation))
    if origin is Annotated:
        args = get_args(annotation)
        return bool(args) and _is_optional_type(args[0])
    return False


def _is_vector_type(base_type: Any) -> bool:
    """True for ``list[float]`` / ``Sequence[float]`` — the vector slot."""
    return base_type is list


def _ensure_none(existing: str | None, model: str, slot: str, attr: str) -> None:
    """Enforce single-cardinality slots."""
    if existing is not None:
        raise VectorSchemaFault(
            model=model,
            reason=f"duplicate {slot} slot: {existing!r} and {attr!r} both claim it",
        )


def _display_type(base_type: Any) -> str:
    name = getattr(base_type, "__name__", None)
    if name:
        return name
    return str(base_type).replace("typing.", "").replace("types.", "")


# ── Internal helper: resolved lazily so a circular import cannot be created
#    by touching typing internals at module-import time.


def types_UnionType() -> Any:
    """The ``types.UnionType`` (``X | None``) form object."""
    import types

    return types.UnionType


__all__ = [
    "PayloadSpec",
    "VectorModelMeta",
    "VectorOptions",
    "VectorSchema",
]

"""
AquilaVectorDB — Unified field architecture.

The Pydantic-inspired declaration surface (§2.2 of the implementation plan).
One field object carries slot routing, defaults, storage aliasing, and every
validation constraint, replacing the stack of separate ``Annotated`` markers the
legacy syntax needed::

    # Legacy — three markers, one attribute
    source: Annotated[str, Payload(indexed=True), MinLength(1), MaxLength(256)]

    # Unified
    source: str = Field(default="web", indexed=True, min_length=1, max_length=256)

Hierarchy::

                            BaseVectorField
                                   │
           ┌───────────────┬───────┴───────┬───────────────┐
       KeyField       VectorField      TextField      PayloadField (Field)
           │                                               │
       ScoreField                                      LinkField

Both declaration styles are supported and interchangeable — a field instance is
equally valid as a class-attribute default or as ``Annotated`` metadata, because
:class:`~aquilia.vectordb.metaclass.VectorModelMeta` looks in both places.

Fields are descriptors, and that is load-bearing
------------------------------------------------

``__set_name__`` records the attribute name so ``Document.views >= 10`` can name
the attribute it filters on. ``__get__`` returns the *field* on class access (so
expressions work) and the *value* on instance access (so ``doc.views`` is an
``int``). Instance values live in ``instance.__dict__`` and are read directly,
which keeps attribute reads at dict-lookup cost.

Mutability
----------

Unlike the frozen legacy markers, a field is mutable: the metaclass fills in
``name``, and a subclass may inherit and re-route one. Fields are therefore
never shared between attributes — :meth:`BaseVectorField.clone` exists for the
inheritance path, which copies rather than aliasing.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal

from aquilia.vectordb.expressions import FieldExpression


#: Sentinel distinguishing "no default given" from ``default=None``.
#:
#: A required payload and an optional one that defaults to ``None`` are
#: different declarations, and ``None`` cannot tell them apart.
class _Unset:
    """Type of :data:`UNSET`."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "UNSET"

    def __bool__(self) -> bool:
        return False


UNSET = _Unset()

OnDeleteAction = Literal["detach", "purge"]


# ============================================================================
# Constraint containers
# ============================================================================


class StringConstraints:
    """
    Reusable bundle of string validation rules (§2.3).

    Pass to any field accepting string constraints, instead of repeating the
    same four keywords across a dozen attributes::

        SLUG = StringConstraints(min_length=1, max_length=64, pattern=r"^[a-z0-9-]+$")

        class Doc(VectorModel):
            slug: str = Field(constraints=SLUG)

    Args:
        min_length: Inclusive minimum length.
        max_length: Inclusive maximum length.
        pattern: Regular expression the value must match.
        choices: Explicit set of permitted values.
        strip_whitespace: Strip surrounding whitespace before validating and
            before storing. Applied on assignment during encode, so the stored
            value matches what was validated.
    """

    __slots__ = ("min_length", "max_length", "pattern", "choices", "strip_whitespace")

    def __init__(
        self,
        *,
        min_length: int | None = None,
        max_length: int | None = None,
        pattern: str | None = None,
        choices: tuple[Any, ...] | list[Any] | None = None,
        strip_whitespace: bool = False,
    ) -> None:
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = pattern
        self.choices = tuple(choices) if choices is not None else None
        self.strip_whitespace = strip_whitespace

    def to_dict(self) -> dict[str, Any]:
        """Return the non-default rules as keyword arguments."""
        out: dict[str, Any] = {}
        for name in ("min_length", "max_length", "pattern", "choices"):
            value = getattr(self, name)
            if value is not None:
                out[name] = value
        if self.strip_whitespace:
            out["strip_whitespace"] = True
        return out

    def __repr__(self) -> str:
        return f"StringConstraints({self.to_dict()})"


class NumericConstraints:
    """
    Reusable bundle of numeric validation rules (§2.3).

    Args:
        ge: Inclusive lower bound (``>=``).
        gt: Exclusive lower bound (``>``).
        le: Inclusive upper bound (``<=``).
        lt: Exclusive upper bound (``<``).
        multiple_of: Value must be an exact multiple of this.

    Example::

        age: int = Field(constraints=NumericConstraints(ge=0, le=150))
    """

    __slots__ = ("ge", "gt", "le", "lt", "multiple_of")

    def __init__(
        self,
        *,
        ge: Any = None,
        gt: Any = None,
        le: Any = None,
        lt: Any = None,
        multiple_of: Any = None,
    ) -> None:
        self.ge = ge
        self.gt = gt
        self.le = le
        self.lt = lt
        self.multiple_of = multiple_of

    def to_dict(self) -> dict[str, Any]:
        """Return the non-default rules as keyword arguments."""
        return {
            name: getattr(self, name)
            for name in ("ge", "gt", "le", "lt", "multiple_of")
            if getattr(self, name) is not None
        }

    def __repr__(self) -> str:
        return f"NumericConstraints({self.to_dict()})"


# ============================================================================
# Base field
# ============================================================================


class BaseVectorField:
    """
    Base class for every vector field.

    Carries the shared declaration state — name, default, storage alias,
    constraints — and the operator overloads that make a field usable as the
    left-hand side of a filter expression.

    Args:
        default: Constant default. Mutually exclusive with ``default_factory``.
        default_factory: Zero-argument callable producing the default. Use for
            mutable or time-dependent values (``datetime.utcnow``), where a
            constant would be evaluated once at class-creation time and shared
            by every instance.
        alias: Storage key override. Defaults to the attribute name. Set it when
            the on-disk key must differ from the Python name — renaming an
            attribute without it orphans existing data.
        indexed: Metadata index hint for accelerated filtering.
        description: Human-readable documentation, surfaced by
            ``aq vectordb models``.
        constraints: A :class:`StringConstraints` or :class:`NumericConstraints`
            bundle, merged with any keyword constraints.
        validators: Extra validator instances or callables, applied after the
            declarative constraints.
        min_length, max_length, pattern, choices, strip_whitespace: String
            constraints, equivalent to a :class:`StringConstraints` bundle.
        ge, gt, le, lt, multiple_of: Numeric constraints, equivalent to a
            :class:`NumericConstraints` bundle.

    Raises:
        ValueError: When both ``default`` and ``default_factory`` are given.
            Raised at class-body evaluation, so a contradictory declaration
            fails at import rather than producing an arbitrary winner.
    """

    #: Slot this field routes its attribute to. Subclasses override.
    slot: str = "payload"

    __slots__ = (
        "name",
        "alias",
        "default",
        "default_factory",
        "indexed",
        "description",
        "string_constraints",
        "numeric_constraints",
        "extra_validators",
        "owner",
    )

    def __init__(
        self,
        *,
        default: Any = UNSET,
        default_factory: Callable[[], Any] | None = None,
        alias: str | None = None,
        indexed: bool = False,
        description: str = "",
        constraints: StringConstraints | NumericConstraints | None = None,
        validators: list[Any] | tuple[Any, ...] | None = None,
        # String constraints
        min_length: int | None = None,
        max_length: int | None = None,
        pattern: str | None = None,
        choices: tuple[Any, ...] | list[Any] | None = None,
        strip_whitespace: bool = False,
        # Numeric constraints
        ge: Any = None,
        gt: Any = None,
        le: Any = None,
        lt: Any = None,
        multiple_of: Any = None,
    ) -> None:
        if default is not UNSET and default_factory is not None:
            raise ValueError(
                f"{type(self).__name__}(default=..., default_factory=...) — give one or the other, not both"
            )

        self.name: str = ""
        self.owner: type | None = None
        self.alias = alias
        self.default = default
        self.default_factory = default_factory
        self.indexed = bool(indexed)
        self.description = description

        merged_string = StringConstraints(
            min_length=min_length,
            max_length=max_length,
            pattern=pattern,
            choices=choices,
            strip_whitespace=strip_whitespace,
        )
        merged_numeric = NumericConstraints(ge=ge, gt=gt, le=le, lt=lt, multiple_of=multiple_of)

        # An explicit bundle fills only the rules the keywords left unset, so
        # `Field(constraints=SLUG, max_length=32)` narrows the shared bundle
        # rather than being silently overridden by it.
        if isinstance(constraints, StringConstraints):
            for attr in ("min_length", "max_length", "pattern", "choices"):
                if getattr(merged_string, attr) is None:
                    setattr(merged_string, attr, getattr(constraints, attr))
            merged_string.strip_whitespace = merged_string.strip_whitespace or constraints.strip_whitespace
        elif isinstance(constraints, NumericConstraints):
            for attr in ("ge", "gt", "le", "lt", "multiple_of"):
                if getattr(merged_numeric, attr) is None:
                    setattr(merged_numeric, attr, getattr(constraints, attr))
        elif constraints is not None:
            raise ValueError(
                f"{type(self).__name__}(constraints=...) expects StringConstraints or "
                f"NumericConstraints, got {type(constraints).__name__}"
            )

        self.string_constraints = merged_string
        self.numeric_constraints = merged_numeric
        self.extra_validators = tuple(validators or ())

    # ── Descriptor protocol ──────────────────────────────────────────────

    def __set_name__(self, owner: type, name: str) -> None:
        """Record the attribute name and owner at class creation."""
        self.name = name
        self.owner = owner
        if self.alias is None:
            self.alias = name

    def __get__(self, instance: Any, owner: type | None = None) -> Any:
        """
        Return the field on class access, the value on instance access.

        Class access is what makes ``Document.views >= 10`` build an expression;
        instance access must return the stored value or a model would be unusable
        as a plain object.
        """
        if instance is None:
            return self
        try:
            return instance.__dict__[self.name]
        except KeyError:
            return self.get_default()

    def __set__(self, instance: Any, value: Any) -> None:
        """Store the value and mark the attribute dirty."""
        instance.__dict__[self.name] = value
        state = instance.__dict__.get("_vstate")
        if state is not None:
            state.mark_dirty(self.name)

    def __delete__(self, instance: Any) -> None:
        """Clear the stored value, reverting to the declared default."""
        instance.__dict__.pop(self.name, None)

    # ── Declaration helpers ──────────────────────────────────────────────

    @property
    def storage_key(self) -> str:
        """The metadata key this field is stored under."""
        return self.alias or self.name

    @property
    def has_default(self) -> bool:
        """Whether a default value or factory was declared."""
        return self.default is not UNSET or self.default_factory is not None

    def get_default(self) -> Any:
        """
        Return a fresh default value.

        Calls ``default_factory`` per invocation, so two records never share one
        mutable default.
        """
        if self.default_factory is not None:
            return self.default_factory()
        if self.default is not UNSET:
            return self.default
        return None

    def clone(self) -> BaseVectorField:
        """
        Return an unbound copy of this field.

        Used when a subclass inherits a parent's field: two model classes must
        not share one field object, or ``__set_name__`` on the second would
        rewrite the first's owner.
        """
        copy = object.__new__(type(self))
        for slot in _all_slots(type(self)):
            try:
                object.__setattr__(copy, slot, getattr(self, slot))
            except AttributeError:
                continue
        copy.name = self.name
        copy.owner = None
        return copy

    def constraint_kwargs(self) -> dict[str, Any]:
        """Return every declared constraint as a flat keyword mapping."""
        return {**self.string_constraints.to_dict(), **self.numeric_constraints.to_dict()}

    def build_validators(self, model_name: str, attribute: str, *, optional: bool) -> tuple[Callable[[Any], None], ...]:
        """
        Compile this field's constraints into validator callables.

        Delegates to the shared constraint wrappers in
        :mod:`aquilia.vectordb.annotations`, so a rule declared through a field
        and the same rule declared through ``Annotated`` metadata are validated
        by identical code.

        Args:
            model_name: Owning model, for fault messages.
            attribute: Attribute name, for fault messages.
            optional: Whether ``None`` is a permitted value.

        Returns:
            Validator callables in declaration order.
        """
        from aquilia.vectordb.annotations import (
            Choices,
            Constraint,
            MaxLength,
            MaxValue,
            MinLength,
            MinValue,
            Pattern,
            Validate,
            build_validators,
        )

        constraints: list[Constraint] = []
        sc = self.string_constraints
        nc = self.numeric_constraints

        if sc.min_length is not None:
            constraints.append(MinLength(sc.min_length))
        if sc.max_length is not None:
            constraints.append(MaxLength(sc.max_length))
        if sc.pattern is not None:
            constraints.append(Pattern(sc.pattern))
        if sc.choices is not None:
            constraints.append(Choices(*sc.choices))

        # `gt`/`lt` are exclusive and the shared validators only offer inclusive
        # bounds, so those two go through a dedicated exclusive validator rather
        # than being approximated by MinValue/MaxValue.
        if nc.ge is not None:
            constraints.append(MinValue(nc.ge))
        if nc.le is not None:
            constraints.append(MaxValue(nc.le))
        if nc.gt is not None:
            constraints.append(Validate(_ExclusiveMin(nc.gt)))
        if nc.lt is not None:
            constraints.append(Validate(_ExclusiveMax(nc.lt)))
        if nc.multiple_of is not None:
            constraints.append(Validate(_MultipleOf(nc.multiple_of)))

        for validator in self.extra_validators:
            constraints.append(Validate(validator))

        return build_validators(model_name, attribute, constraints, optional=optional)

    def prepare_value(self, value: Any) -> Any:
        """
        Normalize a value before validation and storage.

        Only ``strip_whitespace`` acts here today. Normalizing before validation
        is deliberate: a value that passes ``min_length`` only because of
        trailing spaces should not pass at all.
        """
        if value is not None and self.string_constraints.strip_whitespace and isinstance(value, str):
            return value.strip()
        return value

    # ── Expression operators (§4.2) ──────────────────────────────────────

    def __eq__(self, other: Any) -> Any:  # type: ignore[override]
        """``Document.kind == "design"`` → an equality expression."""
        return FieldExpression(self.name, "eq", other)

    def __ne__(self, other: Any) -> Any:  # type: ignore[override]
        """``Document.kind != "draft"`` → an inequality expression."""
        return FieldExpression(self.name, "ne", other)

    def __ge__(self, other: Any) -> FieldExpression:
        """``Document.views >= 10``."""
        return FieldExpression(self.name, "gte", other)

    def __gt__(self, other: Any) -> FieldExpression:
        """``Document.views > 0``."""
        return FieldExpression(self.name, "gt", other)

    def __le__(self, other: Any) -> FieldExpression:
        """``Document.score <= 0.95``."""
        return FieldExpression(self.name, "lte", other)

    def __lt__(self, other: Any) -> FieldExpression:
        """``Document.score < 1.0``."""
        return FieldExpression(self.name, "lt", other)

    def __hash__(self) -> int:
        """Hash by identity — ``__eq__`` builds expressions, so it cannot hash."""
        return object.__hash__(self)

    def in_(self, values: Any) -> FieldExpression:
        """
        Set membership.

        Args:
            values: Permitted values.

        Example::

            Document.source.in_(["web", "api"])
        """
        return FieldExpression(self.name, "in", list(values))

    def contains(self, needle: str) -> FieldExpression:
        """Substring containment, pushed down to the engine."""
        return FieldExpression(self.name, "contains", needle)

    def icontains(self, needle: str) -> FieldExpression:
        """Case-insensitive containment, applied as a residual predicate."""
        return FieldExpression(self.name, "icontains", needle)

    def startswith(self, prefix: str) -> FieldExpression:
        """Prefix match — containment push-down plus an exact residual."""
        return FieldExpression(self.name, "startswith", prefix)

    def endswith(self, suffix: str) -> FieldExpression:
        """Suffix match — containment push-down plus an exact residual."""
        return FieldExpression(self.name, "endswith", suffix)

    def between(self, low: Any, high: Any) -> FieldExpression:
        """
        Inclusive range.

        Example::

            Document.views.between(10, 1000)
        """
        return FieldExpression(self.name, "range", (low, high))

    def asc(self) -> str:
        """Return this field's name, for callers sorting hydrated records."""
        return self.name

    def __repr__(self) -> str:
        bits = [f"name={self.name!r}"] if self.name else []
        if self.alias and self.alias != self.name:
            bits.append(f"alias={self.alias!r}")
        if self.has_default:
            bits.append(f"default={self.get_default()!r}")
        constraints = self.constraint_kwargs()
        if constraints:
            bits.append(f"constraints={constraints}")
        return f"{type(self).__name__}({', '.join(bits)})"


def _all_slots(cls: type) -> tuple[str, ...]:
    """Collect ``__slots__`` across an MRO, for :meth:`BaseVectorField.clone`."""
    names: list[str] = []
    for klass in cls.__mro__:
        for slot in getattr(klass, "__slots__", ()):
            if slot not in names:
                names.append(slot)
    return tuple(names)


# ============================================================================
# Validators backing the constraints the shared module has no wrapper for
# ============================================================================


class _ExclusiveMin:
    """Validator for ``gt`` — strictly greater than a bound."""

    code = "min_value_exclusive"

    def __init__(self, bound: Any) -> None:
        self.bound = bound

    def __call__(self, value: Any) -> None:
        from aquilia.models.fields.validators import ValidationError

        if value is None:
            return
        if not value > self.bound:
            raise ValidationError(f"Value must be greater than {self.bound}", code=self.code)


class _ExclusiveMax:
    """Validator for ``lt`` — strictly less than a bound."""

    code = "max_value_exclusive"

    def __init__(self, bound: Any) -> None:
        self.bound = bound

    def __call__(self, value: Any) -> None:
        from aquilia.models.fields.validators import ValidationError

        if value is None:
            return
        if not value < self.bound:
            raise ValidationError(f"Value must be less than {self.bound}", code=self.code)


class _MultipleOf:
    """Validator for ``multiple_of`` — exact divisibility."""

    code = "not_multiple_of"

    def __init__(self, step: Any) -> None:
        self.step = step

    def __call__(self, value: Any) -> None:
        from decimal import Decimal

        from aquilia.models.fields.validators import ValidationError

        if value is None:
            return
        # Decimal keeps 0.3 % 0.1 from failing on binary float error, which
        # would otherwise reject legitimately-multiple decimal values.
        try:
            remainder = Decimal(str(value)) % Decimal(str(self.step))
        except (ArithmeticError, ValueError) as exc:
            raise ValidationError(f"Value {value!r} is not comparable to step {self.step!r}", code=self.code) from exc
        if remainder != 0:
            raise ValidationError(f"Value must be a multiple of {self.step}", code=self.code)


# ============================================================================
# Concrete fields
# ============================================================================


class PayloadField(BaseVectorField):
    """
    Metadata payload attribute — the default field, aliased as :func:`Field`.

    Stores a scalar alongside the vector, filterable through both syntaxes.
    Values are encoded by the codec table in :mod:`aquilia.vectordb.codecs`;
    a type no codec covers is rejected at class-creation time.

    Example::

        source: str = Field(default="web", indexed=True, max_length=256)
        views: int = Field(default=0, ge=0)
        created_at: datetime = Field(default_factory=datetime.utcnow)
    """

    slot = "payload"
    __slots__ = ()


#: Canonical spelling of :class:`PayloadField`, matching the plan's ``Field(...)``.
Field = PayloadField


class KeyField(BaseVectorField):
    """
    The record's unique document key.

    Exactly one per model — elips addresses every record by key, so a model
    without one cannot be written and a model with two has no single identity.

    Args:
        prefix: Prepended to generated keys, e.g. ``"doc_"``. Purely cosmetic
            for humans reading the store: elips folds a non-UUID key into a
            deterministic UUIDv5, so the prefix survives as part of the logical
            key, not the stored one.
        autogenerate: Generate a key on save when none was set. Turn this off to
            require an explicit key, making an unkeyed save a validation error
            rather than a record under a random identifier.

    Example::

        key: str = KeyField(prefix="doc_")
    """

    slot = "key"
    __slots__ = ("prefix", "autogenerate")

    def __init__(self, *, prefix: str | None = None, autogenerate: bool = True, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.prefix = prefix
        self.autogenerate = bool(autogenerate)

    def generate(self) -> str:
        """Return a fresh record key, honouring :attr:`prefix`."""
        import uuid

        raw = str(uuid.uuid4())
        return f"{self.prefix}{raw}" if self.prefix else raw


class VectorField(BaseVectorField):
    """
    The raw floating-point embedding.

    Args:
        dimension: Vector length. Must agree with the store's configured
            dimension — elips holds it database-global, so a mismatch is a bind
            time fault rather than something a collection can reconcile.
        metric: Similarity metric for this model. Must agree with the store.
        index: ``"graph"`` (HNSW) or ``"exact"`` (brute force).

    Example::

        vector: list[float] = VectorField(dimension=384)
    """

    slot = "vector"
    __slots__ = ("dimension", "metric", "index")

    def __init__(
        self,
        dimension: int | None = None,
        *,
        metric: str | None = None,
        index: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        if dimension is not None and (not isinstance(dimension, int) or dimension <= 0):
            raise ValueError(f"VectorField(dimension=...) must be a positive int, got {dimension!r}")
        self.dimension = dimension
        self.metric = metric
        self.index = index


class TextField(BaseVectorField):
    """
    Source text for semantic embedding and hybrid text search.

    A model with a text field may be written without a vector: the ingest
    pipeline embeds the text (§3.4) and records the resulting
    :class:`~aquilia.vectordb.embedders.EmbeddingLineage` on the record.

    Args:
        embed: Compute an embedding from this text on write. Set ``False`` to
            store the text as a retrievable, filterable field only.
        embedder: Per-field embedder URI override, e.g.
            ``"openai/text-embedding-3-small"``. Falls back to the model's
            ``Meta.embedder``, then the store's.
        chunk_size: Split text longer than this into child chunk records. Sugar
            for ``chunker=RecursiveCharacterChunker(chunk_size=...)``.
        chunk_overlap: Characters shared between adjacent chunks.
        chunker: An explicit :class:`~aquilia.vectordb.chunking.Chunker`.
            Mutually exclusive with ``chunk_size``.
        prompt_template: Applied to the text before embedding, for models that
            expect one (``"passage: {}"`` for E5). The query-side counterpart is
            ``VectorQuery.search(prompt_template=...)``.

    Example::

        body: str = TextField(embed=True, min_length=1, max_length=8192)
    """

    slot = "text"
    __slots__ = ("embed", "embedder", "chunk_size", "chunk_overlap", "chunker", "prompt_template")

    def __init__(
        self,
        *,
        embed: bool = True,
        embedder: str | None = None,
        chunk_size: int | None = None,
        chunk_overlap: int = 0,
        chunker: Any = None,
        prompt_template: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        if chunk_size is not None and chunker is not None:
            raise ValueError(
                "TextField(chunk_size=..., chunker=...) — give one or the other. "
                "chunk_size is shorthand for RecursiveCharacterChunker(chunk_size=...)."
            )
        self.embed = bool(embed)
        self.embedder = embedder
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunker = chunker
        self.prompt_template = prompt_template

    def resolve_chunker(self) -> Any:
        """
        Return the chunker for this field, or ``None`` when chunking is off.

        Built lazily so declaring ``chunk_size`` does not import the chunking
        module at class-creation time.
        """
        if self.chunker is not None:
            return self.chunker
        if self.chunk_size is None:
            return None

        from aquilia.vectordb.chunking import RecursiveCharacterChunker

        self.chunker = RecursiveCharacterChunker(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        return self.chunker


class ScoreField(BaseVectorField):
    """
    Read-only similarity score, populated on search results.

    Never written to storage. On a record fetched by key or constructed
    locally it stays ``None`` — there is no score outside a query's context.

    Example::

        score: float | None = ScoreField()
    """

    slot = "score"
    __slots__ = ()

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("default", None)
        super().__init__(**kwargs)


class LinkField(PayloadField):
    """
    A reference to a row in the SQL ORM, by primary key.

    Stored as an ordinary payload — that is how the key reaches storage and
    becomes filterable — plus registry metadata naming the target. Deliberately
    not a foreign key: elips enforces no referential integrity, runs no cascade,
    and performs no join, so resolution is always explicit through
    :func:`aquilia.vectordb.interop.resolve`.

    Args:
        target_model: The target ``Model`` class, or a ``"module:Class"`` path
            for a forward reference.
        on_delete: What happens to vector records when the SQL row is deleted,
            honoured only for mirrored models. ``"detach"`` leaves the record
            searchable with a dangling link; ``"purge"`` deletes it. There is no
            ``"cascade"`` spelling on purpose — it would imply a database-level
            guarantee that does not exist here.

    Example::

        author_id: int = LinkField(User, on_delete="detach")
    """

    slot = "payload"
    __slots__ = ("target_model", "on_delete")

    def __init__(self, target_model: Any, *, on_delete: OnDeleteAction = "detach", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.target_model = target_model
        self.on_delete = on_delete

    def resolve_model(self) -> type:
        """
        Resolve the target model class, importing a dotted reference if needed.

        Raises:
            VectorSchemaFault: When the reference cannot be resolved.
        """
        from aquilia.vectordb.interop import Link

        return Link(self.target_model, self.on_delete).resolve_model()


__all__ = [
    "UNSET",
    "BaseVectorField",
    "Field",
    "KeyField",
    "LinkField",
    "NumericConstraints",
    "OnDeleteAction",
    "PayloadField",
    "ScoreField",
    "StringConstraints",
    "TextField",
    "VectorField",
]

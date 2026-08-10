"""
AquilaVectorDB — Annotation markers and constraints.

Vector models declare their shape through :data:`typing.Annotated` metadata
rather than field-descriptor assignment::

    class Doc(VectorModel):
        key:    Annotated[str, Key()]
        vector: Annotated[list[float], Dimension(768)]
        text:   Annotated[str, Text(), MinLength(1)]
        views:  Annotated[int, Payload(), MinValue(0)]

Two kinds of metadata live in those annotations:

**Slot markers** (:class:`Key`, :class:`Dimension`, :class:`Text`,
:class:`Payload`, :class:`Score`) route an attribute to one of elips'
five record positions.  Exactly one ``Key`` and at most one each of
``Dimension`` / ``Text`` / ``Score`` per model.

**Constraints** (:class:`MinLength`, :class:`MaxValue`, ...) are thin,
declarative wrappers that build validator instances from
``aquilia.models.fields.validators``.  Reusing those validators — rather than
reimplementing bounds checks here — is what keeps a constraint's meaning
identical whichever model world declares it, and means a fix to
``MinLengthValidator`` reaches both.

Notes:
    Markers are frozen dataclasses so they are hashable and safe to share
    across annotations; ``Annotated`` metadata is class-level state that any
    number of models may reference.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from aquilia.models.fields import validators as _v

# ============================================================================
# Slot markers
# ============================================================================


@dataclass(frozen=True)
class Key:
    """
    Marks the attribute holding the record's unique key.

    Maps to the elips record key (``str``).  Exactly one per model — elips
    addresses every record by key, so a model without one cannot be written,
    and a model with two has no single identity.

    Example::

        key: Annotated[str, Key()]
    """

    __slots__ = ()


@dataclass(frozen=True)
class Dimension:
    """
    Marks the attribute holding the raw vector, and declares its length.

    Args:
        size: Vector length. Must match the store's ``Config.dimension``;
            elips holds dimension database-global, so every model sharing a
            store must agree. Checked at model-creation time against
            ``Meta.dimension`` and again at bind time against the engine.

    Example::

        vector: Annotated[list[float], Dimension(768)]
    """

    size: int

    def __post_init__(self) -> None:
        if not isinstance(self.size, int) or self.size <= 0:
            # A non-positive dimension is a declaration error, not a runtime
            # one; raising here surfaces it at import rather than at open().
            raise ValueError(f"Dimension(size=...) must be a positive int, got {self.size!r}")


@dataclass(frozen=True)
class Text:
    """
    Marks the attribute holding source text for server-side embedding.

    A model with a ``Text`` slot may be written without supplying a vector:
    the engine routes those writes through ``place_document``, which embeds on
    the elips side. At most one per model.

    Args:
        embed: When ``True`` (default), writes without an explicit vector are
            embedded from this attribute. Set ``False`` to store the text as a
            retrievable field only, leaving vectors always caller-supplied.

    Example::

        text: Annotated[str, Text()]
    """

    embed: bool = True


@dataclass(frozen=True)
class Payload:
    """
    Marks an attribute stored as elips record metadata.

    elips ``MetaValue`` is flat ``bool | int | float | str``. Types outside
    that set are encoded by the codec table in :mod:`aquilia.vectordb.codecs`
    (``datetime`` → epoch float, ``Decimal`` → string, ``Enum`` → value, ...).
    Nested ``dict``/``list`` payloads have no faithful encoding and are
    rejected at model-creation time.

    Args:
        name: Metadata key to store under. Defaults to the attribute name.
            Use it when the on-disk key must differ from the Python name —
            renaming an attribute without setting this orphans existing data.
        indexed: Reserved for future metadata-index hints. elips filters scan
            metadata linearly today, so this is recorded but not yet acted on.

    Example::

        views: Annotated[int, Payload(), MinValue(0)]
        slug:  Annotated[str, Payload(name="url_slug")]
    """

    name: str | None = None
    indexed: bool = False


@dataclass(frozen=True)
class Score:
    """
    Marks a read-only attribute receiving the similarity score of a search hit.

    Populated only by ``search()`` results. On a record fetched by key, or one
    the caller constructed, it stays ``None`` — there is no score outside the
    context of a query. Never written to the store. At most one per model.

    Example::

        score: Annotated[float | None, Score()] = None
    """

    __slots__ = ()


# ============================================================================
# Constraints
# ============================================================================


@dataclass(frozen=True)
class Constraint:
    """
    Base class for declarative validation metadata.

    Subclasses implement :meth:`build` to return a validator instance from
    ``aquilia.models.fields.validators``. The metaclass collects them per
    attribute at class creation and stores the built validators on the model,
    so per-write validation costs a list walk and no reflection.
    """

    def build(self) -> Any:
        """Return the validator instance this constraint declares."""
        raise NotImplementedError


@dataclass(frozen=True)
class MinLength(Constraint):
    """
    Require a minimum length.

    Args:
        value: Inclusive minimum length.

    Example::

        title: Annotated[str, Payload(), MinLength(1)]
    """

    value: int

    def build(self) -> Any:
        return _v.MinLengthValidator(self.value)


@dataclass(frozen=True)
class MaxLength(Constraint):
    """
    Require a maximum length.

    Args:
        value: Inclusive maximum length.

    Example::

        title: Annotated[str, Payload(), MaxLength(256)]
    """

    value: int

    def build(self) -> Any:
        return _v.MaxLengthValidator(self.value)


@dataclass(frozen=True)
class MinValue(Constraint):
    """
    Require a minimum numeric value.

    Args:
        value: Inclusive lower bound.

    Example::

        views: Annotated[int, Payload(), MinValue(0)]
    """

    value: Any

    def build(self) -> Any:
        return _v.MinValueValidator(self.value)


@dataclass(frozen=True)
class MaxValue(Constraint):
    """
    Require a maximum numeric value.

    Args:
        value: Inclusive upper bound.

    Example::

        rating: Annotated[float, Payload(), MaxValue(5.0)]
    """

    value: Any

    def build(self) -> Any:
        return _v.MaxValueValidator(self.value)


@dataclass(frozen=True)
class Range(Constraint):
    """
    Require a value within an inclusive range.

    Args:
        min_value: Inclusive lower bound.
        max_value: Inclusive upper bound.

    Example::

        rating: Annotated[float, Payload(), Range(0.0, 5.0)]
    """

    min_value: Any
    max_value: Any

    def build(self) -> Any:
        return _v.RangeValidator(self.min_value, self.max_value)


@dataclass(frozen=True)
class Pattern(Constraint):
    """
    Require a value matching a regular expression.

    Args:
        regex: Pattern the value must match.
        message: Optional custom error message.

    Example::

        code: Annotated[str, Payload(), Pattern(r"^[A-Z]{3}-\\d{4}$")]
    """

    regex: str
    message: str | None = None

    def build(self) -> Any:
        return _v.RegexValidator(self.regex, message=self.message)


@dataclass(frozen=True)
class Email(Constraint):
    """
    Require a valid email address.

    Example::

        author: Annotated[str, Payload(), Email()]
    """

    def build(self) -> Any:
        return _v.EmailValidator()


@dataclass(frozen=True)
class URL(Constraint):
    """
    Require a valid URL.

    Example::

        source: Annotated[str, Payload(), URL()]
    """

    def build(self) -> Any:
        return _v.URLValidator()


@dataclass(frozen=True)
class Slug(Constraint):
    """
    Require a slug (letters, numbers, hyphens, underscores).

    Example::

        slug: Annotated[str, Payload(), Slug()]
    """

    def build(self) -> Any:
        return _v.SlugValidator()


@dataclass(frozen=True)
class Choices(Constraint):
    """
    Restrict a value to an explicit set.

    Args:
        values: Allowed values.

    Example::

        status: Annotated[str, Payload(), Choices("draft", "live")]
    """

    values: tuple[Any, ...]

    def __init__(self, *values: Any) -> None:
        object.__setattr__(self, "values", tuple(values))

    def build(self) -> Any:
        return _ChoicesValidator(self.values)


class _ChoicesValidator(_v.BaseValidator):
    """Validator backing :class:`Choices` — membership in a fixed set.

    Lives here rather than in the shared validators module because it is
    specific to how vector payloads declare enumerations; the shared module has
    no equivalent, and adding one there would change ``aquilia.models``.
    """

    code = "invalid_choice"

    def __init__(self, values: tuple[Any, ...]):
        self.values = tuple(values)

    def is_valid(self, value: Any) -> bool:
        """Return True if ``value`` is ``None`` or a member of the allowed set."""
        if value is None:
            return True
        return value in self.values

    def get_message(self, value: Any) -> str:
        """Return a message naming the allowed values."""
        allowed = ", ".join(repr(v) for v in self.values)
        return f"Value {value!r} is not one of: {allowed}"

    def __repr__(self) -> str:
        return f"_ChoicesValidator({self.values!r})"


@dataclass(frozen=True)
class Validate(Constraint):
    """
    Attach an arbitrary validator instance or callable.

    Escape hatch for project-specific rules, and the way to reuse a validator
    from ``aquilia.models.fields.validators`` that has no wrapper here.

    Args:
        validator: A ``BaseValidator`` instance, or any callable raising
            ``ValidationError`` on invalid input.

    Example::

        from aquilia.models.fields.validators import DecimalValidator

        amount: Annotated[str, Payload(), Validate(DecimalValidator(10, 2))]
    """

    validator: Any = field(compare=False)

    def build(self) -> Any:
        return self.validator


def build_validators(
    model: str,
    attribute: str,
    constraints: list[Constraint],
    *,
    optional: bool = False,
) -> tuple[Callable[[Any], None], ...]:
    """
    Build runtime validator callables from declared constraints.

    Each returned callable takes a value and raises
    :class:`~aquilia.vectordb.faults.VectorValidationFault` when it is invalid.
    The shared validators raise ``ValidationError`` (a ``ValueError`` subclass
    from ``aquilia.models``); translating here means callers only ever catch
    vectordb faults, and no ORM exception type crosses the subsystem boundary.

    Args:
        model: Model class name, for the fault message.
        attribute: Attribute name, for the fault message.
        constraints: Declared :class:`Constraint` metadata.
        optional: When ``True``, ``None`` short-circuits as valid. The shared
            validators already treat ``None`` as valid, so this is belt-and-braces
            for any custom validator supplied via :class:`Validate`.

    Returns:
        A tuple of validator callables, in declaration order.
    """
    from aquilia.vectordb.faults import VectorValidationFault

    built: list[Callable[[Any], None]] = []

    for constraint in constraints:
        validator = constraint.build()
        if validator is None:
            continue

        def check(value: Any, _validator: Any = validator) -> None:
            if value is None and optional:
                return
            try:
                _validator(value)
            except _v.ValidationError as exc:
                raise VectorValidationFault(
                    model=model,
                    attr=attribute,
                    reason=str(exc),
                    validator_code=getattr(exc, "code", "") or getattr(_validator, "code", ""),
                ) from exc

        built.append(check)

    return tuple(built)


__all__ = [
    "Choices",
    "Constraint",
    "Dimension",
    "Email",
    "Key",
    "MaxLength",
    "MaxValue",
    "MinLength",
    "MinValue",
    "Pattern",
    "Payload",
    "Range",
    "Score",
    "Slug",
    "Text",
    "URL",
    "Validate",
    "build_validators",
]

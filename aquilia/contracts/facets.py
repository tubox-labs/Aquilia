"""
Aquilia Contract Facets -- the field-level primitives of a Contract.

A Facet is a single aspect of a model exposed through a Contract.
Facets auto-derive from Model fields but can be overridden, composed,
or created standalone.

Naming:
    - "Facet" because each one represents a *facet* of the model
      visible to the outside world.
    - Replaces the "SerializerField" abstraction with Contract-native
      semantics: cast (inbound), mold (outbound), seal (validate).
"""

from __future__ import annotations

import re
import uuid
from collections.abc import Callable, Sequence
from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from typing import (
    TYPE_CHECKING,
    Any,
)

from .exceptions import CastFault, SealFault

if TYPE_CHECKING:
    from .core import Contract


__all__ = [
    "Facet",
    "TextFacet",
    "IntFacet",
    "FloatFacet",
    "DecimalFacet",
    "BoolFacet",
    "DateFacet",
    "TimeFacet",
    "DateTimeFacet",
    "DurationFacet",
    "UUIDFacet",
    "EmailFacet",
    "URLFacet",
    "SlugFacet",
    "IPFacet",
    "ListFacet",
    "DictFacet",
    "JSONFacet",
    "FileFacet",
    "ChoiceFacet",
    "LiteralFacet",
    "EnumFacet",
    "UploadFileFacet",
    "FormDataFacet",
    "Computed",
    "Constant",
    "WriteOnly",
    "ReadOnly",
    "Hidden",
    "Inject",
    "UNSET",
]


# ── Sentinel ─────────────────────────────────────────────────────────────


class _Unset:
    """Sentinel for 'no value provided'."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "<UNSET>"

    def __bool__(self) -> bool:
        return False


UNSET = _Unset()


# ── Facet Factory Metaclass ──────────────────────────────────────────────


class FacetMeta(type):
    """Metaclass on Facet to support class property factory proxies."""

    @property
    def text(cls) -> _FactoryProxy:
        return _FactoryProxy(TextFacet)

    @property
    def int(cls) -> _FactoryProxy:
        return _FactoryProxy(IntFacet)

    @property
    def float(cls) -> _FactoryProxy:
        return _FactoryProxy(FloatFacet)

    @property
    def bool(cls) -> _FactoryProxy:
        return _FactoryProxy(BoolFacet)

    @property
    def list(cls) -> _FactoryProxy:
        return _FactoryProxy(ListFacet)

    @property
    def dict(cls) -> _FactoryProxy:
        return _FactoryProxy(DictFacet)

    def pattern(cls, regex: str, **kwargs: Any) -> TextFacet:
        """Create a TextFacet constrained by a regex pattern."""
        return TextFacet(pattern=regex, **kwargs)

    def email(cls, **kwargs: Any) -> EmailFacet:
        """Create an EmailFacet."""
        return EmailFacet(**kwargs)

    def url(cls, **kwargs: Any) -> URLFacet:
        """Create a URLFacet."""
        return URLFacet(**kwargs)

    def uuid(cls, **kwargs: Any) -> UUIDFacet:
        """Create a UUIDFacet."""
        return UUIDFacet(**kwargs)

    def choice(cls, choices: Any, **kwargs: Any) -> ChoiceFacet:
        """Create a ChoiceFacet."""
        return ChoiceFacet(choices=choices, **kwargs)

    def date(cls, **kwargs: Any) -> DateFacet:
        """Create a DateFacet."""
        return DateFacet(**kwargs)

    def datetime(cls, **kwargs: Any) -> DateTimeFacet:
        """Create a DateTimeFacet."""
        return DateTimeFacet(**kwargs)

    def decimal(cls, **kwargs: Any) -> DecimalFacet:
        """Create a DecimalFacet."""
        return DecimalFacet(**kwargs)

    def ip(cls, **kwargs: Any) -> IPFacet:
        """Create an IPFacet."""
        return IPFacet(**kwargs)

    def slug(cls, **kwargs: Any) -> SlugFacet:
        """Create a SlugFacet."""
        return SlugFacet(**kwargs)

    def time(cls, **kwargs: Any) -> TimeFacet:
        """Create a TimeFacet."""
        return TimeFacet(**kwargs)

    def json(cls, **kwargs: Any) -> JSONFacet:
        """Create a JSONFacet."""
        return JSONFacet(**kwargs)

    def file(cls, **kwargs: Any) -> FileFacet:
        """Create a FileFacet."""
        return FileFacet(**kwargs)

    def duration(cls, **kwargs: Any) -> DurationFacet:
        """Create a DurationFacet."""
        return DurationFacet(**kwargs)


class _FactoryProxy:
    """Proxy descriptor to support slice-subscript bounds on Facet factory."""

    __slots__ = ("facet_class",)

    def __init__(self, facet_class: type[Facet]):
        self.facet_class = facet_class

    def __call__(self, *args: Any, **kwargs: Any) -> Facet:
        return self.facet_class(*args, **kwargs)

    def __getitem__(self, val: Any) -> Facet:
        if self.facet_class is ListFacet:
            if isinstance(val, tuple):
                child_facet = val[0]
                sl = val[1]
                if not isinstance(sl, slice):
                    raise TypeError("Expected a slice for list bounds")
                return ListFacet(child=child_facet, min_items=sl.start, max_items=sl.stop)
            elif isinstance(val, slice):
                return ListFacet(min_items=val.start, max_items=val.stop)
            else:
                return ListFacet(child=val)

        if not isinstance(val, slice):
            raise TypeError("Expected a slice")

        if self.facet_class is TextFacet:
            return TextFacet(min_length=val.start, max_length=val.stop)

        if self.facet_class is IntFacet:
            # multiple_of is step
            return IntFacet(min_value=val.start, max_value=val.stop, multiple_of=val.step)

        if self.facet_class is FloatFacet:
            kwargs = {}
            if val.start is not None:
                kwargs["min_value"] = float(val.start)
            if val.stop is not None:
                kwargs["max_value"] = float(val.stop)
            if val.step is not None:
                kwargs["multiple_of"] = float(val.step)
            return FloatFacet(**kwargs)

        raise TypeError(f"Subscripting not supported on {self.facet_class.__name__}")


# ── Facet Base ───────────────────────────────────────────────────────────


class Facet(metaclass=FacetMeta):
    """
    Base facet -- a single data point in a Contract.

    Lifecycle::

        inbound:   raw_value → cast() → seal() → validated_value
        outbound:  model_attr → mold() → output_value

    Attributes:
        source:       Model attribute name (defaults to facet name)
        required:     Must be present in input (default True)
        read_only:    Only appears in output, never accepted as input
        write_only:   Only accepted as input, never in output
        default:      Default value if not provided
        allow_null:   Accept None as a valid value
        allow_blank:  Accept empty string (text facets)
        label:        Human-readable label
        help_text:    Documentation string
        validators:   Extra validator callables
    """

    # Class-level ordering counter for stable field ordering
    _creation_order: int = 0

    # Override in subclasses for schema generation
    _type_name: str = "any"

    def __init__(
        self,
        *,
        source: str | None = None,
        required: bool | None = None,
        read_only: bool = False,
        write_only: bool = False,
        default: Any = UNSET,
        allow_null: bool = False,
        allow_blank: bool = False,
        label: str | None = None,
        help_text: str | None = None,
        validators: Sequence[Callable] | None = None,
    ):
        self.source = source
        self._required = required  # None = auto-detect from model field
        self.read_only = read_only
        self.write_only = write_only
        self.default = default
        self.allow_null = allow_null
        self.allow_blank = allow_blank
        self.label = label
        self.help_text = help_text
        self.validators: list[Callable] = list(validators) if validators else []

        # Set during bind()
        self.name: str | None = None
        self.contract: Contract | None = None
        self._bound = False

        # Auto-increment creation order for stable ordering
        Facet._creation_order += 1
        self._order = Facet._creation_order

    @property
    def required(self) -> bool:
        if self._required is not None:
            return self._required
        if self.read_only:
            return False
        if self.default is not UNSET:
            return False
        return not self.allow_null

    @required.setter
    def required(self, value: bool) -> None:
        self._required = value

    def bind(self, name: str, contract: Contract) -> None:
        """Attach this facet to a Contract with a field name."""
        self.name = name
        self.contract = contract
        if self.source is None:
            self.source = name
        self._bound = True

    def clone(self) -> Facet:
        """Create a shallow copy for Contract inheritance."""
        import copy

        new = copy.copy(self)
        new.validators = list(self.validators)
        new._bound = False
        new.name = None
        new.contract = None
        return new

    # ── Inbound: Cast ────────────────────────────────────────────────

    def cast(self, value: Any) -> Any:
        """
        Cast an incoming value to the internal Python type.

        Override in subclasses for type-specific coercion.
        Raise ``CastFault`` on failure.
        """
        return value

    # ── Outbound: Mold ───────────────────────────────────────────────

    def mold(self, value: Any) -> Any:
        """
        Shape an outgoing value for the response.

        Override in subclasses for type-specific formatting.
        """
        return value

    # ── Validation: Seal ─────────────────────────────────────────────

    def seal(self, value: Any) -> Any:
        """
        Run all field-level validators on a cast value.

        Returns the (possibly transformed) value.
        """
        for validator in self.validators:
            try:
                validator(value)
            except (ValueError, TypeError) as exc:
                raise CastFault(
                    self.name or "<unbound>",
                    str(exc),
                ) from exc
        return value

    # ── Attribute Access ─────────────────────────────────────────────

    def extract(self, instance: Any) -> Any:
        """
        Extract this facet's value from a model instance.

        Handles dotted sources like "category.name".
        """
        if self.source == "*":
            return instance

        parts = getattr(self, "_source_parts", None)
        if parts is None or getattr(self, "_source_cached", None) != self.source:
            parts = self.source.split(".") if self.source else []
            self._source_parts = parts
            self._source_cached = self.source

        obj = instance
        for part in parts:
            if obj is None:
                return None
            from .core import Contract

            if isinstance(obj, Contract):
                if obj._validated_data is not None and part in obj._validated_data:
                    obj = obj._validated_data[part]
                else:
                    obj = getattr(obj, part, None)
            else:
                obj = obj.get(part) if isinstance(obj, dict) else getattr(obj, part, None)
        return obj

    # ── Schema ───────────────────────────────────────────────────────

    def to_schema(self) -> dict[str, Any]:
        """Generate JSON Schema for this facet."""
        schema: dict[str, Any] = {"type": self._type_name}
        if self.label:
            schema["title"] = self.label
        if self.help_text:
            schema["description"] = self.help_text
        if self.default is not UNSET:
            schema["default"] = self.default
        if self.read_only:
            schema["readOnly"] = True
        if self.write_only:
            schema["writeOnly"] = True
        return schema

    # ── Factories ────────────────------------------------------------

    @classmethod
    def write_only(cls, **kwargs) -> Facet:
        """Factory: create a write-only facet."""
        kwargs["write_only"] = True
        return cls(**kwargs)

    @classmethod
    def read_only(cls, **kwargs) -> Facet:
        """Factory: create a read-only facet."""
        kwargs["read_only"] = True
        return cls(**kwargs)

    def __getitem__(self, val: Any) -> Facet:
        """Subscript slice constraint convenience."""
        if not isinstance(val, slice):
            raise TypeError("Expected a slice")
        new_facet = self.clone()
        if isinstance(new_facet, TextFacet):
            if val.start is not None:
                new_facet.min_length = val.start
            if val.stop is not None:
                new_facet.max_length = val.stop
        elif isinstance(new_facet, (IntFacet, FloatFacet)):
            if val.start is not None:
                new_facet.min_value = val.start
            if val.stop is not None:
                new_facet.max_value = val.stop
            if val.step is not None:
                new_facet.multiple_of = val.step
        elif isinstance(new_facet, ListFacet):
            if val.start is not None:
                new_facet.min_items = val.start
            if val.stop is not None:
                new_facet.max_items = val.stop
        return new_facet

    def __rshift__(self, other: Any) -> Any:
        """Pipeline operator: compose transforms left-to-right."""
        from .pipeline import Pipeline, _as_rune

        return Pipeline([_as_rune(self), _as_rune(other)])

    def __repr__(self) -> str:
        name = self.name or "<unbound>"
        return f"<{type(self).__name__} '{name}'>"


# ── Text Facets ──────────────────────────────────────────────────────────


class TextFacet(Facet):
    """Text/string facet with length constraints."""

    _type_name = "string"

    # Maximum allowed length for regex patterns to prevent ReDoS
    MAX_PATTERN_LENGTH = 500

    def __init__(
        self,
        *,
        min_length: int | None = None,
        max_length: int | None = None,
        trim: bool = True,
        pattern: str | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.min_length = min_length
        self.max_length = max_length
        self.trim = trim
        if pattern:
            if len(pattern) > self.MAX_PATTERN_LENGTH:
                raise CastFault(
                    "<pattern>",
                    f"Regex pattern too long ({len(pattern)} chars). Maximum allowed: {self.MAX_PATTERN_LENGTH}",
                )
            # Check for dangerous nested quantifiers (basic ReDoS detection)
            import re as _re

            _nested_quantifier = _re.compile(
                r"(\([^)]*[+*]\)[+*?]|\([^)]*\)\{[0-9,]+\}[+*?]|"
                r"[+*]\{[0-9,]+\}|[+*][+*])"
            )
            if _nested_quantifier.search(pattern):
                raise CastFault(
                    "<pattern>",
                    "Regex pattern contains potentially dangerous nested quantifiers "
                    "(ReDoS risk). Simplify the pattern or use a non-backtracking engine.",
                )
            self.pattern = re.compile(pattern)
        else:
            self.pattern = None

    def cast(self, value: Any) -> str:
        if isinstance(value, str):
            if self.trim:
                value = value.strip()
            return value
        # Only coerce safe primitive types to string
        if isinstance(value, (int, float, bool)):
            value = str(value)
        else:
            raise CastFault(self.name or "<unbound>", f"Expected string, got {type(value).__name__}")
        if self.trim:
            value = value.strip()
        return value

    def seal(self, value: Any) -> str:
        if not self.allow_blank and isinstance(value, str) and value == "":
            raise CastFault(self.name or "<unbound>", "This field may not be blank")
        if self.min_length is not None and len(value) < self.min_length:
            raise CastFault(self.name or "<unbound>", f"Must be at least {self.min_length} characters")
        if self.max_length is not None and len(value) > self.max_length:
            raise CastFault(self.name or "<unbound>", f"Must be at most {self.max_length} characters")
        if self.pattern and not self.pattern.search(value):
            raise CastFault(self.name or "<unbound>", "Does not match required pattern")
        return super().seal(value)

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        if self.min_length is not None:
            schema["minLength"] = self.min_length
        if self.max_length is not None:
            schema["maxLength"] = self.max_length
        if self.pattern:
            schema["pattern"] = self.pattern.pattern
        return schema


class EmailFacet(TextFacet):
    """Email address facet with format validation."""

    _EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    def cast(self, value: Any) -> str:
        value = super().cast(value)
        return value.lower()

    def seal(self, value: Any) -> str:
        if not self._EMAIL_RE.match(value):
            raise CastFault(self.name or "<unbound>", "Invalid email address")
        return super().seal(value)

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        schema["format"] = "email"
        return schema


class URLFacet(TextFacet):
    """URL facet with format validation."""

    _URL_RE = re.compile(
        r"^https?://"
        r"(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*"
        r"[a-zA-Z]{2,}"
        r"(?::\d+)?"
        r"(?:/[^\s]*)?$"
    )

    def seal(self, value: Any) -> str:
        if not self._URL_RE.match(value):
            raise CastFault(self.name or "<unbound>", "Invalid URL")
        return super().seal(value)

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        schema["format"] = "uri"
        return schema


class SlugFacet(TextFacet):
    """URL slug facet (lowercase alphanumeric + hyphens)."""

    _SLUG_RE = re.compile(r"^[-a-zA-Z0-9_]+$")

    def cast(self, value: Any) -> str:
        value = super().cast(value)
        return value.lower()

    def seal(self, value: Any) -> str:
        if not self._SLUG_RE.match(value):
            raise CastFault(self.name or "<unbound>", "Invalid slug (use letters, numbers, hyphens, underscores)")
        return super().seal(value)

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        schema["pattern"] = self._SLUG_RE.pattern
        return schema


class IPFacet(TextFacet):
    """IP address facet (v4 or v6)."""

    def seal(self, value: Any) -> str:
        import ipaddress

        try:
            ipaddress.ip_address(value)
        except ValueError:
            raise CastFault(self.name or "<unbound>", "Invalid IP address")
        return super().seal(value)

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        schema["format"] = "ip-address"
        return schema


# ── Numeric Facets ───────────────────────────────────────────────────────


class IntFacet(Facet):
    """Integer facet with range constraints."""

    _type_name = "integer"

    def __init__(
        self,
        *,
        min_value: int | None = None,
        max_value: int | None = None,
        multiple_of: int | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value
        self.multiple_of = multiple_of

    def cast(self, value: Any) -> int:
        if isinstance(value, bool):
            raise CastFault(self.name or "<unbound>", "Boolean is not a valid integer")
        try:
            return int(value)
        except (ValueError, TypeError, OverflowError) as exc:
            raise CastFault(self.name or "<unbound>", f"Expected integer, got {type(value).__name__}") from exc

    def seal(self, value: Any) -> int:
        if self.min_value is not None and value < self.min_value:
            raise CastFault(self.name or "<unbound>", f"Must be at least {self.min_value}")
        if self.max_value is not None and value > self.max_value:
            raise CastFault(self.name or "<unbound>", f"Must be at most {self.max_value}")
        if self.multiple_of is not None:
            if value % self.multiple_of != 0:
                raise CastFault(self.name or "<unbound>", f"Must be a multiple of {self.multiple_of}")
        return super().seal(value)

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        if self.min_value is not None:
            schema["minimum"] = self.min_value
        if self.max_value is not None:
            schema["maximum"] = self.max_value
        if self.multiple_of is not None:
            schema["multipleOf"] = self.multiple_of
        return schema


class FloatFacet(Facet):
    """Floating-point facet."""

    _type_name = "number"

    def __init__(
        self,
        *,
        min_value: float | None = None,
        max_value: float | None = None,
        allow_nan: bool = False,
        allow_infinity: bool = False,
        multiple_of: float | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value
        self.allow_nan = allow_nan
        self.allow_infinity = allow_infinity
        self.multiple_of = multiple_of

    def cast(self, value: Any) -> float:
        import math

        try:
            result = float(value)
        except (ValueError, TypeError, OverflowError) as exc:
            raise CastFault(self.name or "<unbound>", f"Expected number, got {type(value).__name__}") from exc
        if not self.allow_nan and math.isnan(result):
            raise CastFault(self.name or "<unbound>", "NaN is not allowed")
        if not self.allow_infinity and math.isinf(result):
            raise CastFault(self.name or "<unbound>", "Infinity is not allowed")
        return result

    def seal(self, value: Any) -> float:
        if self.min_value is not None and value < self.min_value:
            raise CastFault(self.name or "<unbound>", f"Must be at least {self.min_value}")
        if self.max_value is not None and value > self.max_value:
            raise CastFault(self.name or "<unbound>", f"Must be at most {self.max_value}")
        if self.multiple_of is not None:
            if abs(value / self.multiple_of - round(value / self.multiple_of)) > 1e-9:
                raise CastFault(self.name or "<unbound>", f"Must be a multiple of {self.multiple_of}")
        return super().seal(value)

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        if self.min_value is not None:
            schema["minimum"] = self.min_value
        if self.max_value is not None:
            schema["maximum"] = self.max_value
        if self.multiple_of is not None:
            schema["multipleOf"] = self.multiple_of
        return schema


class DecimalFacet(Facet):
    """Decimal facet with precision constraints."""

    _type_name = "string"  # JSON doesn't have decimal, use string

    def __init__(
        self,
        *,
        max_digits: int | None = None,
        decimal_places: int | None = None,
        min_value: Decimal | float | None = None,
        max_value: Decimal | float | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.max_digits = max_digits
        self.decimal_places = decimal_places
        self.min_value = Decimal(str(min_value)) if min_value is not None else None
        self.max_value = Decimal(str(max_value)) if max_value is not None else None

    def cast(self, value: Any) -> Decimal:
        if isinstance(value, float):
            value = str(value)
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise CastFault(self.name or "<unbound>", "Invalid decimal value") from exc

    def seal(self, value: Decimal) -> Decimal:
        if self.min_value is not None and value < self.min_value:
            raise CastFault(self.name or "<unbound>", f"Must be at least {self.min_value}")
        if self.max_value is not None and value > self.max_value:
            raise CastFault(self.name or "<unbound>", f"Must be at most {self.max_value}")
        if self.max_digits is not None:
            sign, digits, exp = value.as_tuple()
            total_digits = len(digits)
            if total_digits > self.max_digits:
                raise CastFault(self.name or "<unbound>", f"Must have at most {self.max_digits} digits")
        if self.decimal_places is not None:
            sign, digits, exp = value.as_tuple()
            actual_places = -exp if exp < 0 else 0
            if actual_places > self.decimal_places:
                raise CastFault(self.name or "<unbound>", f"Must have at most {self.decimal_places} decimal places")
        return super().seal(value)

    def mold(self, value: Any) -> str:
        """Decimals are molded to strings for JSON precision."""
        if value is None:
            return None
        return str(value)

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        schema["format"] = "decimal"
        return schema


# ── Boolean Facet ────────────────────────────────────────────────────────


class BoolFacet(Facet):
    """Boolean facet with truthy/falsy coercion."""

    _type_name = "boolean"

    _TRUE_VALUES = {"true", "1", "yes", "on", "t", "y"}
    _FALSE_VALUES = {"false", "0", "no", "off", "f", "n"}

    def cast(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lower = value.lower().strip()
            if lower in self._TRUE_VALUES:
                return True
            if lower in self._FALSE_VALUES:
                return False
        if isinstance(value, (int, float)):
            if value == 1:
                return True
            if value == 0:
                return False
        raise CastFault(self.name or "<unbound>", f"Expected boolean, got {value!r}")


# ── Date/Time Facets ─────────────────────────────────────────────────────


class DateFacet(Facet):
    """Date facet (ISO 8601)."""

    _type_name = "string"

    def cast(self, value: Any) -> date:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError:
                pass
        raise CastFault(self.name or "<unbound>", "Expected ISO 8601 date (YYYY-MM-DD)")

    def mold(self, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        return str(value)

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        schema["format"] = "date"
        return schema


class TimeFacet(Facet):
    """Time facet (ISO 8601)."""

    _type_name = "string"

    def cast(self, value: Any) -> time:
        if isinstance(value, time):
            return value
        if isinstance(value, str):
            try:
                return time.fromisoformat(value)
            except ValueError:
                pass
        raise CastFault(self.name or "<unbound>", "Expected ISO 8601 time (HH:MM:SS)")

    def mold(self, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, time):
            return value.isoformat()
        return str(value)

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        schema["format"] = "time"
        return schema


class DateTimeFacet(Facet):
    """DateTime facet (ISO 8601)."""

    _type_name = "string"

    def cast(self, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            val_str = value.strip()
            if val_str.endswith("Z"):
                val_str = val_str[:-1] + "+00:00"
            try:
                return datetime.fromisoformat(val_str)
            except ValueError:
                pass
        raise CastFault(self.name or "<unbound>", "Expected ISO 8601 datetime")

    def mold(self, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        schema["format"] = "date-time"
        return schema


class DurationFacet(Facet):
    """Duration/timedelta facet."""

    _type_name = "string"

    def cast(self, value: Any) -> timedelta:
        if isinstance(value, timedelta):
            return value
        if isinstance(value, (int, float)):
            return timedelta(seconds=value)
        if isinstance(value, str):
            val_str = value.strip()
            sign = 1
            if val_str.startswith("-"):
                sign = -1
                val_str = val_str[1:]
            elif val_str.startswith("+"):
                val_str = val_str[1:]
            try:
                return timedelta(seconds=sign * float(val_str))
            except ValueError:
                pass
            parts = val_str.split(":")
            if len(parts) == 3:
                try:
                    h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
                    return timedelta(hours=sign * h, minutes=sign * m, seconds=sign * s)
                except (ValueError, TypeError):
                    pass
        raise CastFault(self.name or "<unbound>", "Expected duration (seconds or HH:MM:SS)")

    def mold(self, value: Any) -> float | None:
        if value is None:
            return None
        if isinstance(value, timedelta):
            return value.total_seconds()
        return value

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        schema["format"] = "duration"
        return schema


class UUIDFacet(Facet):
    """UUID facet."""

    _type_name = "string"

    def cast(self, value: Any) -> uuid.UUID:
        if isinstance(value, uuid.UUID):
            return value
        try:
            return uuid.UUID(str(value))
        except (ValueError, AttributeError) as exc:
            raise CastFault(self.name or "<unbound>", "Invalid UUID") from exc

    def mold(self, value: Any) -> str | None:
        if value is None:
            return None
        return str(value)

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        schema["format"] = "uuid"
        return schema


# ── Structured Facets ────────────────────────────────────────────────────


class ListFacet(Facet):
    """List/array facet with optional child facet."""

    _type_name = "array"

    def __init__(
        self,
        *,
        child: Facet | None = None,
        min_items: int | None = None,
        max_items: int | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.child = child
        self.min_items = min_items
        self.max_items = max_items

    def cast(self, value: Any) -> list:
        if not isinstance(value, (list, tuple)):
            raise CastFault(self.name or "<unbound>", f"Expected list, got {type(value).__name__}")
        result = list(value)
        if self.child is not None:
            cast_items = []
            for i, item in enumerate(result):
                try:
                    cast_items.append(self.child.cast(item))
                except CastFault as exc:
                    raise CastFault(
                        f"{self.name or '<unbound>'}[{i}]",
                        str(exc),
                    ) from exc
            result = cast_items
        return result

    def seal(self, value: list) -> list:
        if self.min_items is not None and len(value) < self.min_items:
            raise CastFault(self.name or "<unbound>", f"Must have at least {self.min_items} items")
        if self.max_items is not None and len(value) > self.max_items:
            raise CastFault(self.name or "<unbound>", f"Must have at most {self.max_items} items")
        if self.child is not None:
            for i, item in enumerate(value):
                try:
                    self.child.seal(item)
                except CastFault as exc:
                    raise CastFault(f"{self.name or '<unbound>'}[{i}]", str(exc)) from exc
        return super().seal(value)

    def mold(self, value: Any) -> list | None:
        if value is None:
            return None
        if self.child is not None:
            return [self.child.mold(item) for item in value]
        return list(value)

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        if self.child is not None:
            schema["items"] = self.child.to_schema()
        if self.min_items is not None:
            schema["minItems"] = self.min_items
        if self.max_items is not None:
            schema["maxItems"] = self.max_items
        return schema


class SetFacet(Facet):
    """Set/unique array facet with optional child facet."""

    _type_name = "array"

    def __init__(
        self,
        *,
        child: Facet | None = None,
        min_items: int | None = None,
        max_items: int | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.child = child
        self.min_items = min_items
        self.max_items = max_items

    def cast(self, value: Any) -> set:
        if not isinstance(value, (list, tuple, set)):
            raise CastFault(self.name or "<unbound>", f"Expected collection, got {type(value).__name__}")
        result = set(value)
        if self.child is not None:
            cast_items = set()
            for item in result:
                try:
                    cast_items.add(self.child.cast(item))
                except CastFault as exc:
                    raise CastFault(
                        f"{self.name or '<unbound>'}[*]",
                        str(exc),
                    ) from exc
            result = cast_items
        return result

    def seal(self, value: set) -> set:
        if self.min_items is not None and len(value) < self.min_items:
            raise CastFault(self.name or "<unbound>", f"Must have at least {self.min_items} items")
        if self.max_items is not None and len(value) > self.max_items:
            raise CastFault(self.name or "<unbound>", f"Must have at most {self.max_items} items")
        if self.child is not None:
            for item in value:
                try:
                    self.child.seal(item)
                except CastFault as exc:
                    raise CastFault(f"{self.name or '<unbound>'}[*]", str(exc)) from exc
        return super().seal(value)

    def mold(self, value: Any) -> list | None:
        if value is None:
            return None
        if self.child is not None:
            return [self.child.mold(item) for item in value]
        return list(value)

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        schema["uniqueItems"] = True
        if self.child is not None:
            schema["items"] = self.child.to_schema()
        if self.min_items is not None:
            schema["minItems"] = self.min_items
        if self.max_items is not None:
            schema["maxItems"] = self.max_items
        return schema


class TupleFacet(Facet):
    """Tuple array facet with optional child facet."""

    _type_name = "array"

    def __init__(
        self,
        *,
        child: Facet | None = None,
        min_items: int | None = None,
        max_items: int | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.child = child
        self.min_items = min_items
        self.max_items = max_items

    def cast(self, value: Any) -> tuple:
        if not isinstance(value, (list, tuple, set)):
            raise CastFault(self.name or "<unbound>", f"Expected collection, got {type(value).__name__}")
        result = tuple(value)
        if self.child is not None:
            cast_items = []
            for i, item in enumerate(result):
                try:
                    cast_items.append(self.child.cast(item))
                except CastFault as exc:
                    raise CastFault(
                        f"{self.name or '<unbound>'}[{i}]",
                        str(exc),
                    ) from exc
            result = tuple(cast_items)
        return result

    def seal(self, value: tuple) -> tuple:
        if self.min_items is not None and len(value) < self.min_items:
            raise CastFault(self.name or "<unbound>", f"Must have at least {self.min_items} items")
        if self.max_items is not None and len(value) > self.max_items:
            raise CastFault(self.name or "<unbound>", f"Must have at most {self.max_items} items")
        if self.child is not None:
            for i, item in enumerate(value):
                try:
                    self.child.seal(item)
                except CastFault as exc:
                    raise CastFault(f"{self.name or '<unbound>'}[{i}]", str(exc)) from exc
        return super().seal(value)

    def mold(self, value: Any) -> list | None:
        if value is None:
            return None
        if self.child is not None:
            return [self.child.mold(item) for item in value]
        return list(value)

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        if self.child is not None:
            schema["items"] = self.child.to_schema()
        if self.min_items is not None:
            schema["minItems"] = self.min_items
        if self.max_items is not None:
            schema["maxItems"] = self.max_items
        return schema


class DictFacet(Facet):
    """Dictionary/object facet, optionally validating all values against a specific facet."""

    _type_name = "object"

    # Default maximum number of keys to prevent hash-collision DoS
    DEFAULT_MAX_KEYS = 1000

    def __init__(self, *, value_facet: Facet | None = None, max_keys: int | None = None, **kwargs):
        super().__init__(**kwargs)
        self.value_facet = value_facet
        self.max_keys = max_keys if max_keys is not None else self.DEFAULT_MAX_KEYS

    def cast(self, value: Any) -> dict:
        if isinstance(value, str):
            value = value.strip()
            if value.startswith("{") and value.endswith("}"):
                import json

                try:
                    value = json.loads(value)
                except Exception as exc:
                    raise CastFault(self.name or "<unbound>", "Invalid JSON object string") from exc

        if not isinstance(value, dict):
            raise CastFault(self.name or "<unbound>", f"Expected object, got {type(value).__name__}")

        if self.max_keys is not None and len(value) > self.max_keys:
            raise CastFault(
                self.name or "<unbound>",
                f"Too many keys: {len(value)} exceeds maximum of {self.max_keys}",
            )

        result = {}
        for k, v in value.items():
            if not isinstance(k, str):
                raise CastFault(self.name or "<unbound>", f"Dictionary keys must be strings, got {type(k).__name__}")
            if self.value_facet:
                # Thread-safe: use local variable for name instead of mutating shared facet
                child_name = f"{self.name or '<unbound>'}[{k}]"
                try:
                    result[k] = self.value_facet.cast(v)
                except CastFault:
                    raise CastFault(child_name, f"Invalid value for key '{k}'")
            else:
                result[k] = v
        return result

    def seal(self, value: dict) -> dict:
        if not self.value_facet:
            return value

        result = {}
        for k, v in value.items():
            child_name = f"{self.name or '<unbound>'}[{k}]"
            try:
                result[k] = self.value_facet.seal(v)
            except CastFault:
                raise CastFault(child_name, f"Validation failed for key '{k}'")
        return result

    def mold(self, value: Any) -> dict | None:
        if value is None:
            return None
        if not isinstance(value, dict):
            try:
                value = dict(value)
            except (TypeError, ValueError):
                return value

        if not self.value_facet:
            return value

        result = {}
        for k, v in value.items():
            result[k] = self.value_facet.mold(v)
        return result

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        if self.value_facet:
            schema["additionalProperties"] = self.value_facet.to_schema()
        return schema


class JSONFacet(Facet):
    """Arbitrary JSON facet with configurable depth and type restrictions."""

    _type_name = "object"

    # Default maximum nesting depth for JSON structures
    DEFAULT_MAX_DEPTH = 32

    # Safe JSON-primitive types (default allowlist)
    JSON_SAFE_TYPES = (str, int, float, bool, type(None), list, dict)

    def __init__(
        self,
        *,
        max_depth: int | None = None,
        allowed_types: tuple | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.max_depth = max_depth if max_depth is not None else self.DEFAULT_MAX_DEPTH
        self.allowed_types = allowed_types if allowed_types is not None else self.JSON_SAFE_TYPES

    def _check_depth(self, value: Any, current_depth: int = 0) -> None:
        """Recursively check nesting depth and type safety."""
        if current_depth > self.max_depth:
            raise CastFault(
                self.name or "<unbound>",
                f"JSON nesting depth exceeds maximum of {self.max_depth}",
            )
        if not isinstance(value, self.allowed_types):
            raise CastFault(
                self.name or "<unbound>",
                f"Type {type(value).__name__} is not allowed in JSON field",
            )
        if isinstance(value, dict):
            for v in value.values():
                self._check_depth(v, current_depth + 1)
        elif isinstance(value, list):
            for item in value:
                self._check_depth(item, current_depth + 1)

    def cast(self, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if (value.startswith("{") and value.endswith("}")) or (value.startswith("[") and value.endswith("]")):
                import json

                try:
                    value = json.loads(value)
                except Exception:
                    pass
        self._check_depth(value)
        return value


# ── File Facet ───────────────────────────────────────────────────────────


class FileFacet(Facet):
    """File reference facet -- stores path/URL string."""

    _type_name = "string"

    def __init__(self, *, allowed_types: list[str] | None = None, **kwargs):
        super().__init__(**kwargs)
        self.allowed_types = allowed_types

    def mold(self, value: Any) -> str | None:
        if value is None:
            return None
        return str(value)

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        schema["format"] = "binary"
        return schema


# ── Choice Facet ─────────────────────────────────────────────────────────


class ChoiceFacet(Facet):
    """Facet with a fixed set of allowed values."""

    _type_name = "string"

    def __init__(self, *, choices: Sequence, **kwargs):
        super().__init__(**kwargs)
        if isinstance(choices, dict):
            self.choices = choices
            self._valid_values = set(choices.keys())
        elif choices and isinstance(choices[0], (list, tuple)):
            self.choices = {k: v for k, v in choices}
            self._valid_values = {k for k, v in choices}
        else:
            self.choices = {c: c for c in choices}
            self._valid_values = set(choices)

    @property
    def allowed_values(self) -> tuple:
        """Alias for _valid_values, matching schema needs."""
        return tuple(self.choices.keys())

    def cast(self, value: Any) -> Any:
        return value

    def seal(self, value: Any) -> Any:
        if value not in self._valid_values:
            raise CastFault(
                self.name or "<unbound>",
                f"Invalid choice '{value}'. Valid: {sorted(str(v) for v in self._valid_values)}",
            )
        return super().seal(value)

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        schema["enum"] = sorted(str(v) for v in self._valid_values)
        return schema


class LiteralFacet(ChoiceFacet):
    """Facet representing a single fixed literal value."""

    def __init__(self, value: Any, **kwargs: Any):
        super().__init__(choices=[value], **kwargs)
        self.value = value


class EnumFacet(Facet):
    """Facet representing a Python Enum type."""

    def __init__(self, enum_class: type, **kwargs: Any):
        super().__init__(**kwargs)
        self.enum_class = enum_class
        self._valid_members = set(enum_class)
        self._valid_values = {m.value for m in enum_class}

    @property
    def allowed_values(self) -> tuple:
        return tuple(m.value for m in self.enum_class)

    def cast(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, self.enum_class):
            return value

        coerced_value = value
        if issubclass(self.enum_class, int):
            try:
                coerced_value = int(value)
            except (ValueError, TypeError):
                pass
        elif issubclass(self.enum_class, str):
            try:
                coerced_value = str(value)
            except (ValueError, TypeError):
                pass

        try:
            return self.enum_class(coerced_value)
        except ValueError:
            pass
        if isinstance(value, str) and value in self.enum_class.__members__:
            return self.enum_class[value]
        raise CastFault(
            self.name or "<unbound>",
            f"Invalid choice '{value}'. Valid: {list(self._valid_values)}",
        )

    def seal(self, value: Any) -> Any:
        if value not in self._valid_members:
            value = self.cast(value)
        return super().seal(value)

    def mold(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, self.enum_class):
            return value.value
        return value

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        first_val = next(iter(self._valid_values)) if self._valid_values else None
        if isinstance(first_val, int):
            schema["type"] = "integer"
        elif isinstance(first_val, float):
            schema["type"] = "number"
        elif isinstance(first_val, bool):
            schema["type"] = "boolean"
        else:
            schema["type"] = "string"
        schema["enum"] = list(self._valid_values)
        return schema


# ── PolymorphicFacet ───────────────────────────────────────────────────


class PolymorphicFacet(Facet):
    """
    A Facet that attempts to cast and seal through multiple candidate Facets.
    Useful for Union types like `Union[CatContract, DogContract]`.
    """

    _type_name = "object"

    def __init__(self, choices: list[Facet], **kwargs):
        super().__init__(**kwargs)
        self.choices = choices

    def cast(self, value: Any) -> Any:
        errors = []
        for choice in self.choices:
            choice.name = self.name
            try:
                return choice.cast(value)
            except CastFault as e:
                errors.append(str(e))

        raise CastFault(
            self.name or "<unbound>", f"Value did not match any polymorphic schema. Errors: {'; '.join(errors)}"
        )

    def seal(self, value: Any) -> Any:
        errors = []
        for choice in self.choices:
            choice.name = self.name
            try:
                return choice.seal(value)
            except (CastFault, SealFault) as e:
                errors.append(str(e))

        raise SealFault(
            self.name or "<unbound>",
            f"Value did not match any polymorphic schema during seal. Errors: {'; '.join(errors)}",
        )

    def mold(self, value: Any) -> Any:
        for choice in self.choices:
            choice.name = self.name
            try:
                molded = choice.mold(value)
                # If molding didn't crash, we assume success.
                # For dictionaries, we might want to ensure it's not None if value wasn't None.
                if molded is not None or value is None:
                    return molded
            except Exception:
                pass
        return value

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        schema["anyOf"] = [choice.to_schema() for choice in self.choices]
        return schema


# ── Special Facets ───────────────────────────────────────────────────────


class Computed(Facet):
    """
    A facet whose value is computed at output time -- never accepted as input.

    Usage::

        full_name = Computed(lambda user: f"{user.first_name} {user.last_name}")
        item_count = Computed("get_item_count")  # calls method on model/contract
    """

    def __init__(self, compute: Callable | str, **kwargs):
        kwargs["read_only"] = True
        super().__init__(**kwargs)
        self._compute = compute

    def extract(self, instance: Any) -> Any:
        """Compute the value from the instance."""
        if isinstance(self._compute, str):
            # Method name on the contract
            if self.contract is not None:
                method = getattr(self.contract, self._compute, None)
                if method is not None:
                    return method(instance)
            # Method name on the instance
            method = getattr(instance, self._compute, None)
            if method is not None:
                result = method()
                return result
            return None
        # Callable -- may be a lambda(instance) or an unbound method(self, instance)
        # from @computed decorator. Detect by inspecting parameter count.
        import inspect

        try:
            sig = inspect.signature(self._compute)
            if len(sig.parameters) >= 2:
                # Unbound method: needs (contract_self, instance)
                bp = self.contract
                if bp is None:
                    # Facets are class-level shared; contract is not bound per-instance.
                    # Create a minimal owning Contract instance for method binding.
                    qualname = getattr(self._compute, "__qualname__", "")
                    if "." in qualname:
                        cls_name = qualname.rsplit(".", 1)[0]
                        # Walk the declaring module to find the class
                        mod = inspect.getmodule(self._compute)
                        if mod is not None:
                            bp_cls = getattr(mod, cls_name, None)
                            if bp_cls is not None:
                                bp = bp_cls.__new__(bp_cls)
                if bp is not None:
                    return self._compute(bp, instance)
        except (ValueError, TypeError):
            pass
        return self._compute(instance)

    def mold(self, value: Any) -> Any:
        return value


class Constant(Facet):
    """
    A facet that always returns a fixed value -- useful for type
    discriminators, API versioning, etc.

    Usage::

        api_version = Constant("v2")
        type = Constant("user")
    """

    def __init__(self, value: Any, **kwargs):
        kwargs["read_only"] = True
        super().__init__(**kwargs)
        self._constant = value

    def extract(self, instance: Any) -> Any:
        return self._constant

    def mold(self, value: Any) -> Any:
        return self._constant

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        schema["const"] = self._constant
        return schema


class WriteOnly(TextFacet):
    """
    Convenience: a text facet that is write-only (e.g., passwords).

    Usage::

        password = WriteOnly(min_length=8)
    """

    def __init__(self, **kwargs):
        kwargs["write_only"] = True
        super().__init__(**kwargs)


class ReadOnly(Facet):
    """
    A pass-through read-only facet.

    Usage::

        created_at = ReadOnly()
    """

    def __init__(self, **kwargs):
        kwargs["read_only"] = True
        super().__init__(**kwargs)

    def mold(self, value: Any) -> Any:
        # Auto-serialize common types
        if isinstance(value, (datetime, date, time)):
            return value.isoformat()
        if isinstance(value, uuid.UUID):
            return str(value)
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, timedelta):
            return value.total_seconds()
        return value


class Hidden(Facet):
    """
    A hidden facet -- populated from default/DI, never in input or output.

    Usage::

        class AuditContract(Contract):
            created_by = Hidden(default=CurrentUserDefault())
    """

    def __init__(self, **kwargs):
        kwargs["write_only"] = True
        super().__init__(**kwargs)


# ── DI Injection Facet ───────────────────────────────────────────────────


class Inject(Facet):
    """
    A facet that resolves its value from the DI container at validation time.

    This is Aquilia's native approach to computed defaults -- the value
    comes from a registered service rather than from user input.

    Usage::

        class OrderContract(Contract):
            total = Inject(PricingService, via="calculate")
            audit_user = Inject("identity", attr="id")

    Args:
        token: DI token (type or string) to resolve.
        via: Method to call on the resolved service (result becomes the value).
        attr: Attribute to read from the resolved service.
    """

    def __init__(
        self,
        token: Any,
        *,
        via: str | None = None,
        attr: str | None = None,
        **kwargs,
    ):
        kwargs.setdefault("read_only", True)
        super().__init__(**kwargs)
        self.token = token
        self.via = via
        self.attr = attr

    def resolve_from_context(self, context: dict[str, Any]) -> Any:
        """Resolve value from DI container or context in Contract context.

        Resolution order:
        1. DI container (container.resolve(token))
        2. Direct context key (context[token]) -- handles "identity",
           "request", and other context-injected objects without a
           full DI container.
        """
        # Try DI container first
        container = context.get("container")
        if container is not None:
            try:
                service = container.resolve(self.token, optional=True)
            except Exception:
                service = None

            if service is not None:
                if self.via:
                    method = getattr(service, self.via, None)
                    if method and callable(method):
                        return method()
                    return UNSET
                if self.attr:
                    return getattr(service, self.attr, UNSET)
                return service

        # Fallback: resolve token directly from context dict
        # (handles "identity", "request" etc. injected by the engine)
        if isinstance(self.token, str):
            obj = context.get(self.token)
            if obj is not None:
                if self.via:
                    method = getattr(obj, self.via, None)
                    if method and callable(method):
                        return method()
                    return UNSET
                if self.attr:
                    return getattr(obj, self.attr, UNSET)
                return obj

        return UNSET


class UploadFileFacet(FileFacet):
    """Facet representing an uploaded file."""

    _type_name = "object"

    def __init__(
        self,
        *,
        max_size: int | None = None,
        allowed_types: list[str] | None = None,
        **kwargs: Any,
    ):
        super().__init__(allowed_types=allowed_types, **kwargs)
        self.max_size = max_size

    def cast(self, value: Any) -> Any:
        if value is None:
            return None

        from .._uploads import UploadFile

        if not isinstance(value, UploadFile):
            raise CastFault(
                self.name or "<unbound>",
                f"Expected UploadFile, got {type(value).__name__}",
            )

        if self.max_size is not None and value.size is not None:
            if value.size > self.max_size:
                raise CastFault(
                    self.name or "<unbound>",
                    f"File size {value.size} exceeds maximum limit of {self.max_size} bytes",
                )

        if self.allowed_types is not None and value.content_type:
            mime = value.content_type.lower()
            matched = False
            for allowed in self.allowed_types:
                allowed_lower = allowed.lower()
                if allowed_lower == mime:
                    matched = True
                    break
                if allowed_lower.endswith("/*"):
                    prefix = allowed_lower[:-2]
                    if mime.startswith(prefix):
                        matched = True
                        break
            if not matched:
                raise CastFault(
                    self.name or "<unbound>",
                    f"Content type '{value.content_type}' is not allowed. Allowed: {self.allowed_types}",
                )

        return value

    def mold(self, value: Any) -> Any:
        if value is None:
            return None
        from .._uploads import UploadFile

        if isinstance(value, UploadFile):
            return {
                "filename": value.filename,
                "content_type": value.content_type,
                "size": value.size,
            }
        return super().mold(value)

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        schema["type"] = "string"
        schema["format"] = "binary"
        return schema


class FormDataFacet(Facet):
    """Facet representing form data input (from urlencoded or multipart fields)."""

    def __init__(
        self,
        *,
        type: Any = str,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.type_annotation = type
        self.child_facet = None

        from .annotations import UNSET, _build_facet_from_annotation

        self.child_facet = _build_facet_from_annotation(
            name=self.name or "",
            annotation=type,
            field_spec=None,
            class_default=UNSET,
        )

    def cast(self, value: Any) -> Any:
        if value is None:
            return None

        if self.child_facet is not None:
            self.child_facet.name = self.name
            return self.child_facet.cast(value)

        return str(value)

    def seal(self, value: Any) -> Any:
        if self.child_facet is not None:
            self.child_facet.name = self.name
            return self.child_facet.seal(value)
        return super().seal(value)

    def mold(self, value: Any) -> Any:
        if self.child_facet is not None:
            return self.child_facet.mold(value)
        return value

    def to_schema(self) -> dict[str, Any]:
        if self.child_facet is not None:
            return self.child_facet.to_schema()
        return super().to_schema()


# ── Model Field → Facet Mapping ──────────────────────────────────────────

# Maps model field class names to facet classes for auto-derivation
MODEL_FIELD_TO_FACET: dict[str, type[Facet]] = {
    # Text
    "CharField": TextFacet,
    "TextField": TextFacet,
    "SlugField": SlugFacet,
    "EmailField": EmailFacet,
    "URLField": URLFacet,
    "UUIDField": UUIDFacet,
    "FilePathField": TextFacet,
    # Numeric
    "IntegerField": IntFacet,
    "BigIntegerField": IntFacet,
    "SmallIntegerField": IntFacet,
    "PositiveIntegerField": IntFacet,
    "PositiveSmallIntegerField": IntFacet,
    "FloatField": FloatFacet,
    "DecimalField": DecimalFacet,
    "AutoField": IntFacet,
    "BigAutoField": IntFacet,
    # Boolean
    "BooleanField": BoolFacet,
    # Date/Time
    "DateField": DateFacet,
    "TimeField": TimeFacet,
    "DateTimeField": DateTimeFacet,
    "DurationField": DurationFacet,
    # Structured
    "JSONField": JSONFacet,
    "ArrayField": ListFacet,
    "HStoreField": DictFacet,
    # IP
    "GenericIPAddressField": IPFacet,
    "InetAddressField": IPFacet,
    # Files
    "FileField": FileFacet,
    "ImageField": FileFacet,
    # Binary
    "BinaryField": TextFacet,
    # Generated
    "GeneratedField": ReadOnly,
    # Range (PostgreSQL)
    "RangeField": TextFacet,
}


def derive_facet(model_field: Any) -> Facet:
    """
    Derive a Facet instance from an Aquilia Model field.

    Reads the model field's type, constraints, and defaults to
    produce a correctly configured Facet.
    """
    field_cls_name = type(model_field).__name__
    facet_cls = MODEL_FIELD_TO_FACET.get(field_cls_name, Facet)

    kwargs: dict[str, Any] = {}

    # Null/blank
    if getattr(model_field, "null", False):
        kwargs["allow_null"] = True
    if getattr(model_field, "blank", False):
        kwargs["allow_blank"] = True

    # Help text
    if getattr(model_field, "help_text", ""):
        kwargs["help_text"] = model_field.help_text

    # Default value
    try:
        from ..models.fields_module import UNSET as MODEL_UNSET
    except ImportError:
        MODEL_UNSET = None

    field_default = getattr(model_field, "default", UNSET)
    if field_default is not MODEL_UNSET and field_default is not UNSET:
        kwargs["default"] = field_default

    # Read-only detection
    if getattr(model_field, "primary_key", False):
        kwargs["read_only"] = True
    if not getattr(model_field, "editable", True):
        kwargs["read_only"] = True
    if getattr(model_field, "auto_now", False) or getattr(model_field, "auto_now_add", False):
        kwargs["read_only"] = True

    # Required detection
    if not kwargs.get("read_only", False):
        has_default = getattr(model_field, "has_default", lambda: False)
        if callable(has_default):
            has_default = has_default()
        if getattr(model_field, "null", False) or getattr(model_field, "blank", False) or has_default:
            kwargs["required"] = False

    # Choices → ChoiceFacet
    if getattr(model_field, "choices", None):
        return ChoiceFacet(choices=model_field.choices, **kwargs)

    # Type-specific kwargs
    if facet_cls in (TextFacet, SlugFacet, EmailFacet, URLFacet):
        if hasattr(model_field, "max_length") and model_field.max_length:
            kwargs["max_length"] = model_field.max_length

    if facet_cls is DecimalFacet:
        if hasattr(model_field, "max_digits") and model_field.max_digits:
            kwargs["max_digits"] = model_field.max_digits
        if hasattr(model_field, "decimal_places") and model_field.decimal_places is not None:
            kwargs["decimal_places"] = model_field.decimal_places

    if facet_cls in (IntFacet, FloatFacet):
        if hasattr(model_field, "min_value") and model_field.min_value is not None:
            kwargs["min_value"] = model_field.min_value
        if hasattr(model_field, "max_value") and model_field.max_value is not None:
            kwargs["max_value"] = model_field.max_value

    return facet_cls(**kwargs)

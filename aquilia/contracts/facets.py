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
from pathlib import PurePath, PurePosixPath
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
)

from .exceptions import CastFault, SealFault
from .messages import contract_message

if TYPE_CHECKING:
    from .core import Contract


__all__ = [
    "Facet",
    "TextFacet",
    "IntFacet",
    "BytesFacet",
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
    "MACAddressFacet",
    "PathFacet",
    "SecretFacet",
    "Secret",
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


class Secret:
    """
    Sensitive string container hiding wrapped secret values from `repr`, `str`, and tracebacks.

    Purpose:
        Wraps passwords, API tokens, and secret keys to prevent accidental leakage in logging or string formatting.

    Lifecycle:
        1. **Instantiation**: Wraps raw sensitive string `value`.
        2. **Protection Phase**: Overrides `__str__` and `__repr__` to output masked string `**********`.
        3. **Access Phase**: Exposes raw secret only via explicit `.reveal()` call.

    Execution Order:
        1. Wrap string in `Secret` container.
        2. Mask output on `str()` or `repr()`.
        3. Evaluate constant-time comparison in `__eq__()`.

    Parameters:
        value (str): The sensitive secret string to wrap.

    Return Values:
        Secret: An initialized sensitive secret container instance.

    Exceptions:
        TypeError: Raised if non-string value is passed during initialization.

    Notes:
        - Security: Uses `hmac.compare_digest` for constant-time string comparison to prevent timing attacks.

    Internal Behaviour:
        Stores value in `__slots__ = ("_value",)` to minimize memory leaks.

    Edge Cases:
        - Comparing `Secret("a") == Secret("a")` evaluates using constant-time digest comparison.

    Examples:
        >>> token = Secret("sk-live-1234")
        >>> str(token)
        '**********'
        >>> token.reveal()
        'sk-live-1234'
    """

    __slots__ = ("_value",)

    _MASK = "**********"

    def __init__(self, value: str):
        self._value = value

    def reveal(self) -> str:
        """Return the underlying value. Call only at the point of use."""
        return self._value

    def __str__(self) -> str:
        return self._MASK

    def __repr__(self) -> str:
        return f"Secret({self._MASK!r})"

    def __eq__(self, other: object) -> bool:
        import hmac

        if isinstance(other, Secret):
            return hmac.compare_digest(self._value, other._value)
        if isinstance(other, str):
            return hmac.compare_digest(self._value, other)
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._value)

    def __len__(self) -> int:
        return len(self._value)

    def __bool__(self) -> bool:
        return bool(self._value)


# ── Facet Factory Metaclass ──────────────────────────────────────────────


class FacetMeta(type):
    """
    Metaclass on Facet enabling fluent property factory proxies (`Facet.text`, `Facet.int`, `Facet.email()`).

    Purpose:
        Provides class-level factory shortcuts on `Facet` for clean contract field declaration syntax.

    Lifecycle:
        1. **Class Creation**: Applied as metaclass for `Facet` base class.
        2. **Property Access**: Returns `_FactoryProxy` or instantiates specialized Facet instances.

    Execution Order:
        1. Intercept class attribute property lookups (`Facet.text`, `Facet.int`).
        2. Construct and return corresponding `_FactoryProxy` or Facet subclass instance.

    Parameters:
        *args: Standard Python metaclass creation parameters.

    Return Values:
        FacetMeta: The `FacetMeta` metaclass instance.

    Exceptions:
        AttributeError: Raised if requested factory property is invalid.

    Notes:
        - Supports subscript syntax like `Facet.text[3:50]`.

    Internal Behaviour:
        Instantiates `_FactoryProxy` wrapper around Facet subclasses.

    Edge Cases:
        - Accessing properties returns new proxy descriptors each time.

    Examples:
        >>> facet = Facet.text[3:50]
        >>> facet.min_length, facet.max_length
        (3, 50)
    """

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
    """
    Proxy descriptor supporting slice-subscript bounds on Facet factory properties.

    Purpose:
        Enables Python slice notation `Facet.text[3:50]` to configure Facet constraints concisely.

    Lifecycle:
        1. **Instantiation**: Wraps target `facet_class`.
        2. **Subscript Pass**: Intercepts `__getitem__()` slice calls to return configured Facet.

    Execution Order:
        1. Parse slice `start`, `stop`, and `step`.
        2. Map slice parameters to `min_length`, `max_length`, `min_value`, `max_value`.

    Parameters:
        facet_class (type[Facet]): Target Facet subclass to configure.

    Return Values:
        _FactoryProxy: An initialized factory proxy.

    Exceptions:
        TypeError: Raised if non-slice value is provided during subscripting.

    Notes:
        - `IntFacet[1:100:2]` maps `step=2` to `multiple_of=2`.

    Internal Behaviour:
        Calls target `facet_class` constructor with keyword arguments extracted from slice.

    Edge Cases:
        - Unsupported facet classes raise `TypeError`.

    Examples:
        >>> proxy = _FactoryProxy(TextFacet)
        >>> facet = proxy[5:10]
        >>> facet.min_length, facet.max_length
        (5, 10)
    """

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
    Base facet descriptor class representing a single field, attribute, or property in a Contract.

    Purpose:
        Defines field-level casting (type coercion), molding (outbound formatting), and validation constraints.
        Serves as the foundation for all Contract field primitives (e.g., `TextFacet`, `IntFacet`, `Lens`, `NestedContractFacet`).

    Lifecycle:
        1. **Instantiation / Decoration**: Declared as a class attribute or generated from type annotations via `introspect_annotations()`.
        2. **Binding Phase**: Bound to a host Contract class during `ContractMeta.__new__` via `bind(name, contract)`.
        3. **Inbound Validation**: Processes incoming raw input data via `cast()` (coercion) and `seal()` (validation rules).
        4. **Outbound Serialization**: Formats ORM model attributes into output values via `mold()`.

    Execution Order:
        - **Inbound Validation Pipeline**:
          1. Check for `UNSET` or `None` values against `required`, `allow_null`, and `default`.
          2. Coerce raw value to Python type via subclass `cast()`.
          3. Apply subclass `seal()` constraint checks (min/max length, bounds, patterns).
          4. Execute custom `self.validators` callables.
          5. Return post-cast validated value.
        - **Outbound Serialization Pipeline**:
          1. Extract raw model value via `source` attribute lookup.
          2. Coerce or format via subclass `mold()`.
          3. Return output payload value.

    Parameters:
        source (str | None, optional): Model attribute name override. Defaults to field name.
        required (bool | None, optional): Override auto-detected required status. If `None`, auto-detects from defaults/nullability.
        read_only (bool, optional): If `True`, field appears only in outbound output; ignored during inbound validation. Defaults to `False`.
        write_only (bool, optional): If `True`, field accepted as inbound input; omitted from outbound output. Defaults to `False`.
        default (Any, optional): Static default value or default factory function when value is unprovided. Defaults to `UNSET`.
        allow_null (bool, optional): Accept `None` as a valid value. Defaults to `False`.
        allow_blank (bool, optional): Accept empty strings for text facets. Defaults to `False`.
        label (str | None, optional): Human-readable label for UI rendering.
        help_text (str | None, optional): Documentation description string.
        validators (Sequence[Callable] | None, optional): Additional custom validator functions.

    Return Values:
        Facet: An initialized Facet descriptor instance.

    Exceptions:
        CastFault: Raised during `cast()` if value cannot be coerced to target type.
        SealFault: Raised during `seal()` if validation constraints are violated.

    Notes:
        - Fluent Builder API: Facets support factory shortcuts (`Facet.text()`, `Facet.email()`) and `>>` composition.

    Internal Behaviour:
        Tracks static `_creation_order` to preserve declaration order on host contracts.

    Edge Cases:
        - Accessing un-bound facets defaults `name` to `<unbound>`.

    Examples:
        >>> field = TextFacet(min_length=3, max_length=50)
        >>> field.cast("   alice   ")
        'alice'
    """

    # Class-level ordering counter for stable field ordering
    _creation_order: int = 0

    # Override in subclasses for schema generation
    _type_name: str = "any"

    #: Python type of the *validated* value this facet produces, as source text
    #: for a type annotation. Consumed by stub generation (``aq contracts
    #: stubs``) so a type checker sees the post-cast type rather than the wire
    #: type — ``IntFacet`` accepts ``"42"`` but yields ``int``. ``"Any"`` means
    #: no narrower type is guaranteed.
    _python_type: str = "Any"

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

    # ── Static typing ────────────────────────────────────────────────

    def python_type(self) -> str:
        """
        Source text for the type annotation of this facet's validated value.

        Consumed by stub generation (``aq contracts stubs``). The default
        returns :attr:`_python_type`; facets whose type depends on how they
        were constructed — a list's child, an enum's class, a nested
        Contract's target — override this.

        Return Values:
            An annotation expression. Names of user-defined types (enums,
            Contracts) are fully qualified, so the stub writer can derive the
            import from the name alone rather than re-walking the facet tree.
        """
        return self._python_type

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
    """
    Facet primitive representing text and string fields with length, trim, and pattern validation.

    Purpose:
        Coerces inbound primitive values to clean Python strings and enforces string character limits and regex constraints.

    Lifecycle:
        1. **Instantiation**: Configured with `min_length`, `max_length`, `trim`, and `pattern`.
        2. **Casting Phase**: Coerces input values to string and strips whitespace if `trim=True`.
        3. **Validation Pass**: Validates blank state, length boundaries, and regex match.

    Execution Order:
        1. Coerce input to `str` and strip whitespace if enabled in `cast()`.
        2. Check for blank string against `allow_blank` in `seal()`.
        3. Validate character count against `min_length` and `max_length`.
        4. Validate against compiled regex `pattern`.

    Parameters:
        min_length (int | None, optional): Inclusive minimum string character count.
        max_length (int | None, optional): Inclusive maximum string character count.
        trim (bool, optional): If `True`, strips leading and trailing whitespace. Defaults to `True`.
        pattern (str | None, optional): Regular expression pattern string. ReDoS-dangerous patterns are rejected.
        **kwargs: Base Facet parameters (`required`, `allow_null`, `default`, etc.).

    Return Values:
        TextFacet: An initialized text facet descriptor.

    Exceptions:
        CastFault: Raised if value cannot be coerced to string, violates length bounds, or fails regex match.

    Notes:
        - Security: Analyzes patterns to prevent Regular Expression Denial of Service (ReDoS) vulnerability.

    Internal Behaviour:
        Compiles and stores an internal `re.Pattern` object during initialization.

    Edge Cases:
        - Empty string `""` with `allow_blank=False` (default) raises `CastFault`.

    Examples:
        >>> facet = TextFacet(min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9_]+$")
        >>> facet.cast("   user_123   ")
        'user_123'
    """

    _type_name = "string"
    _python_type = "str"

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
            raise CastFault(self.name or "<unbound>", contract_message("blank"))
        if self.min_length is not None and len(value) < self.min_length:
            raise CastFault(self.name or "<unbound>", contract_message("min_length", min=self.min_length))
        if self.max_length is not None and len(value) > self.max_length:
            raise CastFault(self.name or "<unbound>", contract_message("max_length", max=self.max_length))
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
    """
    Specialized string facet for RFC-compliant email address validation and normalization.

    Purpose:
        Validates email formatting and automatically normalizes incoming email strings to lowercase.

    Lifecycle:
        1. **Casting Phase**: Coerces input string and applies `.lower()` normalization.
        2. **Validation Pass**: Validates format against RFC email regular expression.

    Execution Order:
        1. Cast and lowercase string value in `cast()`.
        2. Match value against internal email regex `_EMAIL_RE` in `seal()`.
        3. Execute parent `TextFacet.seal()` checks.

    Parameters:
        **kwargs: Inherited parameters from `TextFacet`.

    Return Values:
        EmailFacet: An initialized email facet.

    Exceptions:
        CastFault: Raised if email format is invalid.

    Notes:
        - Output format in OpenAPI schema is set to `"email"`.

    Internal Behaviour:
        Uses compiled `_EMAIL_RE` regex for RFC syntax checking.

    Edge Cases:
        - Mixed-case emails like `User@Domain.COM` are converted to `user@domain.com`.

    Examples:
        >>> facet = EmailFacet()
        >>> facet.cast("USER@EXAMPLE.COM")
        'user@example.com'
    """

    _EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    def cast(self, value: Any) -> str:
        value = super().cast(value)
        return value.lower()

    def seal(self, value: Any) -> str:
        if not self._EMAIL_RE.match(value):
            raise CastFault(self.name or "<unbound>", contract_message("invalid_email"))
        return super().seal(value)

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        schema["format"] = "email"
        return schema


class URLFacet(TextFacet):
    """
    Specialized string facet for HTTP/HTTPS web URL validation.

    Purpose:
        Ensures string values conform to valid absolute HTTP or HTTPS URL formats.

    Lifecycle:
        1. **Casting Phase**: Coerces and trims string value.
        2. **Validation Pass**: Enforces scheme (`http://` or `https://`), domain name, port, and path constraints.

    Execution Order:
        1. Cast string value via `TextFacet.cast()`.
        2. Match against `_URL_RE` regex during `seal()`.

    Parameters:
        **kwargs: Inherited `TextFacet` arguments.

    Return Values:
        URLFacet: An initialized URL facet descriptor.

    Exceptions:
        CastFault: Raised if string is not a valid HTTP/HTTPS URL.

    Notes:
        - Schema format is `"uri"`.

    Internal Behaviour:
        Uses regular expression matching for HTTP/HTTPS protocol scheme validation.

    Edge Cases:
        - Non-HTTP URLs (e.g. `ftp://`, `mailto:`) are rejected.

    Examples:
        >>> facet = URLFacet()
        >>> facet.cast("https://example.com/api")
        'https://example.com/api'
    """

    _URL_RE = re.compile(
        r"^https?://"
        r"(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*"
        r"[a-zA-Z]{2,}"
        r"(?::\d+)?"
        r"(?:/[^\s]*)?$"
    )

    def seal(self, value: Any) -> str:
        if not self._URL_RE.match(value):
            raise CastFault(self.name or "<unbound>", contract_message("invalid_url"))
        return super().seal(value)

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        schema["format"] = "uri"
        return schema


class SlugFacet(TextFacet):
    """
    Specialized string facet for URL slug validation (lowercase alphanumeric characters, underscores, and hyphens).

    Purpose:
        Validates and lowercases string identifiers suitable for clean URL paths.

    Lifecycle:
        1. **Casting Phase**: Coerces and lowercases input string.
        2. **Validation Pass**: Matches against `[-a-zA-Z0-9_]+`.

    Execution Order:
        1. Lowercase string in `cast()`.
        2. Validate format using `_SLUG_RE` in `seal()`.

    Parameters:
        **kwargs: Inherited `TextFacet` arguments.

    Return Values:
        SlugFacet: An initialized slug facet descriptor.

    Exceptions:
        CastFault: Raised if string contains invalid characters (spaces, punctuation).

    Notes:
        - Schema includes pattern matching string.

    Internal Behaviour:
        Applies `value.lower()` before pattern matching.

    Edge Cases:
        - Slugs with spaces (`"my post"`) are rejected.

    Examples:
        >>> facet = SlugFacet()
        >>> facet.cast("My-First-Post")
        'my-first-post'
    """

    _SLUG_RE = re.compile(r"^[-a-zA-Z0-9_]+$")

    def cast(self, value: Any) -> str:
        value = super().cast(value)
        return value.lower()

    def seal(self, value: Any) -> str:
        if not self._SLUG_RE.match(value):
            raise CastFault(self.name or "<unbound>", contract_message("invalid_slug"))
        return super().seal(value)

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        schema["pattern"] = self._SLUG_RE.pattern
        return schema


class IPFacet(TextFacet):
    """
    Specialized string facet for IPv4 and IPv6 address validation.

    Purpose:
        Validates string inputs using Python's stdlib `ipaddress` module to guarantee valid IP syntax.

    Lifecycle:
        1. **Casting Phase**: Coerces input string.
        2. **Validation Pass**: Parses using `ipaddress.ip_address()`.

    Execution Order:
        1. Cast to string in `cast()`.
        2. Pass to `ipaddress.ip_address()` in `seal()`.

    Parameters:
        **kwargs: Inherited `TextFacet` arguments.

    Return Values:
        IPFacet: An initialized IP facet descriptor.

    Exceptions:
        CastFault: Raised if string is not a valid IPv4 or IPv6 address.

    Notes:
        - Schema format is `"ip-address"`.

    Internal Behaviour:
        Delegates parsing directly to stdlib `ipaddress`.

    Edge Cases:
        - Invalid IP formats like `"256.256.256.256"` raise `CastFault`.

    Examples:
        >>> facet = IPFacet()
        >>> facet.cast("192.168.1.1")
        '192.168.1.1'
    """

    def seal(self, value: Any) -> str:
        import ipaddress

        try:
            ipaddress.ip_address(value)
        except ValueError:
            raise CastFault(self.name or "<unbound>", contract_message("invalid_ip"))
        return super().seal(value)

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        schema["format"] = "ip-address"
        return schema


class MACAddressFacet(TextFacet):
    """
    MAC address facet, normalized to lowercase colon-separated form.

    Purpose:
        Accepts any standard MAC address notation (`aa:bb:cc:dd:ee:ff`, `aa-bb-cc-dd-ee-ff`, `aabb.ccdd.eeff`)
        and normalizes input to lowercase colon-separated hex pairs.

    Lifecycle:
        1. **Casting Phase**: Strips separators (`:`, `-`, `.`), converts to lowercase hex digits, and formats with colons.
        2. **Validation Pass**: Validates digit count and hex character range.

    Execution Order:
        1. Normalize notation to `xx:xx:xx:xx:xx:xx` in `cast()`.
        2. Re-validate normalized string in `seal()`.

    Parameters:
        **kwargs: Inherited `TextFacet` arguments.

    Return Values:
        MACAddressFacet: An initialized MAC address facet.

    Exceptions:
        CastFault: Raised if string is not a valid 12-digit hex MAC address.

    Notes:
        - Normalizes all input formats to a single canonical standard.

    Internal Behaviour:
        Uses `str.maketrans` to strip common delimiters before formatting.

    Edge Cases:
        - Inputs with non-hex characters (`"zz:bb:cc:dd:ee:ff"`) raise `CastFault`.

    Examples:
        >>> facet = MACAddressFacet()
        >>> facet.cast("AA-BB-CC-DD-EE-FF")
        'aa:bb:cc:dd:ee:ff'
    """

    _MAC_SEPARATORS = str.maketrans("", "", ":-.")

    def cast(self, value: Any) -> str:
        """Normalize any accepted notation to lowercase colon-separated form."""
        if not isinstance(value, str):
            raise CastFault(self.name or "<unbound>", f"Expected a MAC address string, got {type(value).__name__}")

        digits = value.strip().translate(self._MAC_SEPARATORS).lower()
        if len(digits) != 12 or any(c not in "0123456789abcdef" for c in digits):
            raise CastFault(self.name or "<unbound>", contract_message("invalid_mac"))
        return ":".join(digits[i : i + 2] for i in range(0, 12, 2))

    def seal(self, value: Any) -> str:
        return super().seal(self.cast(value))

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        schema["format"] = "mac-address"
        schema["pattern"] = "^([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}$"
        return schema


class PathFacet(TextFacet):
    """
    Filesystem path facet, validating and casting string paths to :class:`pathlib.PurePosixPath`.

    Purpose:
        Safely processes client-supplied file paths while guarding against path traversal attacks (`..`)
        and absolute root escape attempts.

    Lifecycle:
        1. **Casting Phase**: Parses string into `PurePosixPath`, normalizing Windows backslashes to forward slashes.
        2. **Validation Pass**: Rejects null bytes, empty strings, absolute paths (if `must_be_relative=True`), and `..` segments.

    Execution Order:
        1. Check for null bytes and empty string in `cast()`.
        2. Convert to `PurePosixPath` and check relative/traversal flags.
        3. Enforce string length constraints in `seal()`.

    Parameters:
        must_be_relative (bool, optional): If `True`, rejects absolute paths. Defaults to `True`.
        allow_traversal (bool, optional): If `False`, rejects `..` path segments. Defaults to `False`.
        **kwargs: Inherited `TextFacet` arguments.

    Return Values:
        PathFacet: An initialized path facet descriptor.

    Exceptions:
        CastFault: Raised if path contains null bytes, absolute paths, or traversal segments.

    Notes:
        - Returns `PurePosixPath` objects for cross-platform consistency.

    Internal Behaviour:
        Normalizes `\\` to `/` before inspecting path parts.

    Edge Cases:
        - Path containing null byte `"\x00"` raises `CastFault` immediately.

    Examples:
        >>> facet = PathFacet()
        >>> facet.cast("docs/report.pdf")
        PurePosixPath('docs/report.pdf')
    """

    _type_name = "string"
    _python_type = "pathlib.PurePosixPath"

    def __init__(
        self,
        *,
        must_be_relative: bool = True,
        allow_traversal: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.must_be_relative = must_be_relative
        self.allow_traversal = allow_traversal

    def cast(self, value: Any) -> PurePosixPath:
        if isinstance(value, PurePath):
            text = str(value)
        elif isinstance(value, str):
            text = value
        else:
            raise CastFault(self.name or "<unbound>", f"Expected a path string, got {type(value).__name__}")

        if "\x00" in text:
            raise CastFault(self.name or "<unbound>", contract_message("path_null_byte"))
        if not text.strip():
            raise CastFault(self.name or "<unbound>", contract_message("path_empty"))

        path = PurePosixPath(text.replace("\\", "/"))

        if self.must_be_relative and path.is_absolute():
            raise CastFault(self.name or "<unbound>", contract_message("path_not_relative"))
        if not self.allow_traversal and ".." in path.parts:
            raise CastFault(self.name or "<unbound>", contract_message("path_traversal"))
        return path

    def seal(self, value: Any) -> PurePosixPath:
        path = self.cast(value)
        super().seal(str(path))
        return path

    def mold(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, PurePath):
            return str(value)
        return value

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        schema["format"] = "path"
        return schema


class SecretFacet(TextFacet):
    """
    Sensitive string facet whose value is wrapped in a `Secret` object to prevent accidental logging or leakage.

    Purpose:
        Protects passwords, secret keys, and API tokens from leaking into tracebacks, log lines, or JSON outputs.

    Lifecycle:
        1. **Casting Phase**: Coerces string and wraps value inside a `Secret` instance.
        2. **Validation Pass**: Applies string length constraints against the revealed secret value.
        3. **Molding Phase**: Renders masked string (`"**********"`) rather than raw value.

    Execution Order:
        1. Wrap string in `Secret` container in `cast()`.
        2. Unwrap value temporarily via `.reveal()` to validate length/pattern in `seal()`.
        3. Return masked string representation in `mold()`.

    Parameters:
        **kwargs: Inherited `TextFacet` arguments. Defaults `write_only=True`.

    Return Values:
        SecretFacet: An initialized secret facet.

    Exceptions:
        CastFault: Raised if value fails string validation constraints.

    Notes:
        - Marked `write_only=True` by default.

    Internal Behaviour:
        Uses `Secret` class wrapper to intercept `__repr__` and `__str__`.

    Edge Cases:
        - Calling `mold()` on a `SecretFacet` returns masked placeholder rather than real value.

    Examples:
        >>> facet = SecretFacet(min_length=8)
        >>> secret = facet.cast("my_password_123")
        >>> secret.reveal()
        'my_password_123'
    """

    _python_type = "aquilia.contracts.facets.Secret"

    def __init__(self, **kwargs):
        kwargs.setdefault("write_only", True)
        super().__init__(**kwargs)

    def cast(self, value: Any) -> Secret:
        if isinstance(value, Secret):
            return value
        return Secret(super().cast(value))

    def seal(self, value: Any) -> Secret:
        raw = value.reveal() if isinstance(value, Secret) else value
        return Secret(super().seal(raw))

    def mold(self, value: Any) -> Any:
        if value is None:
            return None
        return str(value)

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        schema["format"] = "password"
        schema["writeOnly"] = True
        return schema


# ── Numeric Facets ───────────────────────────────────────────────────────


class BytesFacet(Facet):
    """
    Binary data facet, transported as base64 or hex strings over wire formats (JSON).

    Purpose:
        Decodes incoming base64 or hex string payloads into Python `bytes` and re-encodes outbound `bytes` back to wire safe strings.

    Lifecycle:
        1. **Casting Phase**: Decodes base64/hex string to `bytes`. Passes raw `bytes`/`bytearray` through directly.
        2. **Validation Pass**: Enforces min and max byte size limits.

    Execution Order:
        1. Inspect input type in `cast()`, decoding string via base64 or hex.
        2. Validate size limits (`min_length`, `max_length`) in `seal()`.
        3. Re-encode bytes to string representation in `mold()`.

    Parameters:
        min_length (int | None, optional): Inclusive minimum decoded byte size.
        max_length (int | None, optional): Inclusive maximum decoded byte size.
        encoding (Literal["base64", "hex"], optional): Wire encoding format. Defaults to `"base64"`.
        **kwargs: Base Facet parameters.

    Return Values:
        BytesFacet: An initialized binary facet descriptor.

    Exceptions:
        CastFault: Raised if string decoding fails or size bounds are violated.

    Notes:
        - Security: Bounding `max_length` prevents base64 memory exhaustion attacks.

    Internal Behaviour:
        Uses stdlib `base64` or `binascii` for decoding and encoding.

    Edge Cases:
        - Accepts raw `bytes` or `bytearray` without decoding overhead.

    Examples:
        >>> facet = BytesFacet(encoding="base64")
        >>> facet.cast("aGVsbG8=")
        b'hello'
    """

    _type_name = "string"
    _python_type = "bytes"

    def __init__(
        self,
        *,
        min_length: int | None = None,
        max_length: int | None = None,
        encoding: Literal["base64", "hex"] = "base64",
        **kwargs,
    ):
        super().__init__(**kwargs)
        if encoding not in ("base64", "hex"):
            raise CastFault("<encoding>", f"Unsupported bytes encoding '{encoding}'. Use 'base64' or 'hex'.")
        self.min_length = min_length
        self.max_length = max_length
        self.encoding = encoding

    def cast(self, value: Any) -> bytes:
        """
        Decode ``value`` to ``bytes``.

        Raises:
            CastFault: If a string value is not valid for the configured
                encoding, or the value is neither string nor bytes-like.
        """
        if isinstance(value, bytes):
            return value
        if isinstance(value, bytearray | memoryview):
            return bytes(value)
        if isinstance(value, str):
            import base64
            import binascii

            try:
                if self.encoding == "hex":
                    return bytes.fromhex(value)
                return base64.b64decode(value, validate=True)
            except (binascii.Error, ValueError) as exc:
                raise CastFault(self.name or "<unbound>", f"Invalid {self.encoding}-encoded value") from exc
        raise CastFault(
            self.name or "<unbound>", f"Expected {self.encoding} string or bytes, got {type(value).__name__}"
        )

    def seal(self, value: Any) -> bytes:
        """
        Enforce size constraints on the decoded bytes.

        Raises:
            CastFault: If the decoded length falls outside
                ``min_length``/``max_length``.
        """
        if self.min_length is not None and len(value) < self.min_length:
            raise CastFault(self.name or "<unbound>", contract_message("min_bytes", min=self.min_length))
        if self.max_length is not None and len(value) > self.max_length:
            raise CastFault(self.name or "<unbound>", contract_message("max_bytes", max=self.max_length))
        return super().seal(value)

    def mold(self, value: Any) -> Any:
        """Encode ``bytes`` back to a wire-safe string."""
        if value is None:
            return None
        if isinstance(value, bytes | bytearray | memoryview):
            raw = bytes(value)
            if self.encoding == "hex":
                return raw.hex()
            import base64

            return base64.b64encode(raw).decode("ascii")
        return value

    def to_schema(self) -> dict[str, Any]:
        schema = super().to_schema()
        schema["format"] = "byte" if self.encoding == "base64" else "hex"
        if self.min_length is not None:
            schema["minLength"] = self.min_length
        if self.max_length is not None:
            schema["maxLength"] = self.max_length
        return schema


class IntFacet(Facet):
    """
    Integer numeric facet supporting range bounds and divisibility constraints.

    Purpose:
        Coerces numeric inputs to Python `int` while rejecting fractional floats and booleans.

    Lifecycle:
        1. **Casting Phase**: Coerces ints, integral floats (`3.0`), and numeric strings (`"42"`) to `int`.
        2. **Validation Pass**: Validates inclusive `min_value`, `max_value`, and `multiple_of` constraints.

    Execution Order:
        1. Reject booleans and non-integral numbers in `cast()`.
        2. Enforce `min_value` and `max_value` limits in `seal()`.
        3. Enforce `multiple_of` modulus check.

    Parameters:
        min_value (int | None, optional): Inclusive minimum integer bound.
        max_value (int | None, optional): Inclusive maximum integer bound.
        multiple_of (int | None, optional): Divisibility factor constraint.
        **kwargs: Base Facet parameters.

    Return Values:
        IntFacet: An initialized integer facet descriptor.

    Exceptions:
        CastFault: Raised if value is boolean, fractional float, NaN, or out of bounds.

    Notes:
        - Integer precision: Accepts string integers to avoid JavaScript float loss.

    Internal Behaviour:
        Uses `value.is_integer()` to reject fractional float coercion.

    Edge Cases:
        - Fractional float `3.9` raises `CastFault`; integral float `3.0` casts to `3`.

    Examples:
        >>> facet = IntFacet(min_value=1, max_value=100)
        >>> facet.cast("42")
        42
    """

    _type_name = "integer"
    _python_type = "int"

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
        """
        Coerce ``value`` to ``int``.

        Accepts ints, integral floats/Decimals (``3.0``), and integral numeric
        strings (``"3"``). Rejects booleans and anything with a fractional part.

        Raises:
            CastFault: If the value is a bool, is NaN/Infinity, has a fractional
                part, or is not numeric at all.

        Notes:
            ``3.9`` is rejected rather than truncated to ``3``. Truncation is
            silent data corruption — a client sending ``{"quantity": 3.9}``
            would otherwise get ``3`` persisted with no indication anything was
            dropped. ``3.0`` is accepted because no information is lost.
        """
        if isinstance(value, bool):
            raise CastFault(self.name or "<unbound>", "Boolean is not a valid integer")
        if isinstance(value, float):
            if value != value or value in (float("inf"), float("-inf")):
                raise CastFault(self.name or "<unbound>", "NaN and Infinity are not valid integers")
            if not value.is_integer():
                raise CastFault(self.name or "<unbound>", f"Expected integer, got non-integer number {value}")
            return int(value)
        if isinstance(value, Decimal):
            if not value.is_finite():
                raise CastFault(self.name or "<unbound>", "NaN and Infinity are not valid integers")
            if value != value.to_integral_value():
                raise CastFault(self.name or "<unbound>", f"Expected integer, got non-integer number {value}")
            return int(value)
        try:
            return int(value)
        except (ValueError, TypeError, OverflowError) as exc:
            raise CastFault(self.name or "<unbound>", f"Expected integer, got {type(value).__name__}") from exc

    def seal(self, value: Any) -> int:
        if self.min_value is not None and value < self.min_value:
            raise CastFault(self.name or "<unbound>", contract_message("min_value", min=self.min_value))
        if self.max_value is not None and value > self.max_value:
            raise CastFault(self.name or "<unbound>", contract_message("max_value", max=self.max_value))
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
    """
    Floating-point numeric facet supporting range bounds, divisibility, and NaN/Infinity guards.

    Purpose:
        Coerces numeric inputs to Python `float` and enforces strict numerical boundary rules.

    Lifecycle:
        1. **Casting Phase**: Coerces numeric/string inputs to float and applies NaN/Inf guards.
        2. **Validation Pass**: Validates `min_value`, `max_value`, and `multiple_of`.

    Execution Order:
        1. Parse float and check `math.isnan` / `math.isinf` in `cast()`.
        2. Check range bounds and divisibility in `seal()`.

    Parameters:
        min_value (float | None, optional): Inclusive minimum bound.
        max_value (float | None, optional): Inclusive maximum bound.
        allow_nan (bool, optional): If `True`, permits `NaN` values. Defaults to `False`.
        allow_infinity (bool, optional): If `True`, permits `inf` / `-inf`. Defaults to `False`.
        multiple_of (float | None, optional): Divisibility factor constraint.
        **kwargs: Base Facet parameters.

    Return Values:
        FloatFacet: An initialized float facet.

    Exceptions:
        CastFault: Raised if value cannot be parsed as float, is NaN/Inf when disallowed, or is out of bounds.

    Notes:
        - Uses epsilon tolerance (`1e-9`) for `multiple_of` float division checks.

    Internal Behaviour:
        Calls stdlib `float(value)` with math safety checks.

    Edge Cases:
        - `NaN` input with `allow_nan=False` raises `CastFault`.

    Examples:
        >>> facet = FloatFacet(min_value=0.0, max_value=1.0)
        >>> facet.cast("0.75")
        0.75
    """

    _type_name = "number"
    _python_type = "float"

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
            raise CastFault(self.name or "<unbound>", contract_message("min_value", min=self.min_value))
        if self.max_value is not None and value > self.max_value:
            raise CastFault(self.name or "<unbound>", contract_message("max_value", max=self.max_value))
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
    """
    Fixed-precision decimal numeric facet, preserving exact decimal representation using `decimal.Decimal`.

    Purpose:
        Prevents floating-point rounding errors on currency and precision metrics. Molded back to string for JSON safety.

    Lifecycle:
        1. **Casting Phase**: Coerces strings, ints, or floats to `Decimal`.
        2. **Validation Pass**: Enforces `max_digits`, `decimal_places`, `min_value`, and `max_value`.
        3. **Molding Phase**: Renders `Decimal` instance as string.

    Execution Order:
        1. Convert input to string and instantiate `Decimal` in `cast()`.
        2. Check digit counts and bounds in `seal()`.
        3. Format as `str(value)` in `mold()`.

    Parameters:
        max_digits (int | None, optional): Maximum permitted total digits.
        decimal_places (int | None, optional): Maximum permitted decimal places.
        min_value (Decimal | float | None, optional): Inclusive lower bound.
        max_value (Decimal | float | None, optional): Inclusive upper bound.
        **kwargs: Base Facet parameters.

    Return Values:
        DecimalFacet: An initialized decimal facet.

    Exceptions:
        CastFault: Raised if value cannot be parsed as a valid decimal or violates precision limits.

    Notes:
        - Output format in OpenAPI schema is `"decimal"`.

    Internal Behaviour:
        Uses `Decimal.as_tuple()` to inspect total digits and fractional decimal places.

    Edge Cases:
        - Molding converts `Decimal('19.99')` to string `'19.99'` for lossless JSON transport.

    Examples:
        >>> facet = DecimalFacet(max_digits=5, decimal_places=2)
        >>> facet.cast("19.99")
        Decimal('19.99')
    """

    _type_name = "string"  # JSON doesn't have decimal, use string
    _python_type = "decimal.Decimal"

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
            raise CastFault(self.name or "<unbound>", contract_message("min_value", min=self.min_value))
        if self.max_value is not None and value > self.max_value:
            raise CastFault(self.name or "<unbound>", contract_message("max_value", max=self.max_value))
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
    """
    Boolean facet supporting boolean primitives and truthy/falsy string/numeric coercion (`"true"`, `"false"`, `1`, `0`).

    Purpose:
        Coerces diverse client boolean inputs into strict Python `bool` values.

    Lifecycle:
        1. **Casting Phase**: Maps booleans, strings (`"true"`, `"false"`, `"yes"`, `"no"`), and ints (`1`, `0`) to `bool`.
        2. **Validation Pass**: Validates non-null boolean output.

    Execution Order:
        1. Match against `_TRUE_VALUES` and `_FALSE_VALUES` sets in `cast()`.
        2. Return boolean result.

    Parameters:
        **kwargs: Base Facet parameters.

    Return Values:
        BoolFacet: An initialized boolean facet.

    Exceptions:
        CastFault: Raised if value cannot be coerced to a boolean.

    Notes:
        - Accepts string forms: `"true"`, `"1"`, `"yes"`, `"on"`, `"t"`, `"y"` (case-insensitive).

    Internal Behaviour:
        Uses lookup sets `_TRUE_VALUES` and `_FALSE_VALUES`.

    Edge Cases:
        - Arbitrary strings like `"maybe"` raise `CastFault`.

    Examples:
        >>> facet = BoolFacet()
        >>> facet.cast("yes")
        True
    """

    _type_name = "boolean"
    _python_type = "bool"

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
    """
    Calendar date facet, parsing and validating ISO 8601 strings (`YYYY-MM-DD`) into `datetime.date`.

    Purpose:
        Ensures clean calendar date parsing and ISO string formatting.

    Lifecycle:
        1. **Casting Phase**: Coerces ISO string or `datetime` to `datetime.date`.
        2. **Molding Phase**: Formats `date` to ISO string (`"YYYY-MM-DD"`).

    Execution Order:
        1. Parse ISO string via `date.fromisoformat()` in `cast()`.
        2. Format using `.isoformat()` in `mold()`.

    Parameters:
        **kwargs: Base Facet parameters.

    Return Values:
        DateFacet: An initialized date facet descriptor.

    Exceptions:
        CastFault: Raised if string is not a valid ISO 8601 date.

    Notes:
        - OpenAPI format is `"date"`.

    Internal Behaviour:
        Delegates to stdlib `datetime.date.fromisoformat`.

    Edge Cases:
        - Invalid date strings like `"2026-02-30"` raise `CastFault`.

    Examples:
        >>> facet = DateFacet()
        >>> facet.cast("2026-07-30")
        datetime.date(2026, 7, 30)
    """

    _type_name = "string"
    _python_type = "datetime.date"

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
    """
    Time of day facet, parsing and validating ISO 8601 time strings (`HH:MM:SS`) into `datetime.time`.

    Purpose:
        Validates time component values independently of dates.

    Lifecycle:
        1. **Casting Phase**: Parses ISO time string into `datetime.time`.
        2. **Molding Phase**: Formats `time` back to ISO string (`"HH:MM:SS"`).

    Execution Order:
        1. Parse using `time.fromisoformat()` in `cast()`.
        2. Format using `.isoformat()` in `mold()`.

    Parameters:
        **kwargs: Base Facet parameters.

    Return Values:
        TimeFacet: An initialized time facet.

    Exceptions:
        CastFault: Raised if time string is invalid.

    Notes:
        - OpenAPI format is `"time"`.

    Internal Behaviour:
        Uses `datetime.time.fromisoformat()`.

    Edge Cases:
        - Accepts optional microsecond components (`"12:30:45.123456"`).

    Examples:
        >>> facet = TimeFacet()
        >>> facet.cast("14:30:00")
        datetime.time(14, 30)
    """

    _type_name = "string"
    _python_type = "datetime.time"

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
    """
    Timestamp facet, parsing ISO 8601 date-time strings into timezone-aware `datetime.datetime` instances.

    Purpose:
        Provides robust ISO 8601 timestamp parsing (including `Z` suffix normalization to `+00:00`).

    Lifecycle:
        1. **Casting Phase**: Normalizes `Z` suffix and parses string to `datetime.datetime`.
        2. **Molding Phase**: Formats `datetime` back to ISO string.

    Execution Order:
        1. Strip and convert `Z` to `+00:00` in `cast()`.
        2. Parse using `datetime.fromisoformat()`.
        3. Format output via `.isoformat()` in `mold()`.

    Parameters:
        **kwargs: Base Facet parameters.

    Return Values:
        DateTimeFacet: An initialized date-time facet.

    Exceptions:
        CastFault: Raised if timestamp string is invalid.

    Notes:
        - OpenAPI format is `"date-time"`.

    Internal Behaviour:
        Handles timezone offset strings and UTC `Z` suffixes seamlessly.

    Edge Cases:
        - `Z` suffix is converted to `+00:00` for standard library compatibility.

    Examples:
        >>> facet = DateTimeFacet()
        >>> facet.cast("2026-07-30T12:00:00Z")
        datetime.datetime(2026, 7, 30, 12, 0, tzinfo=datetime.timezone.utc)
    """

    _type_name = "string"
    _python_type = "datetime.datetime"

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
    """
    Duration facet, parsing seconds (numeric/string) or `HH:MM:SS` strings into `datetime.timedelta`.

    Purpose:
        Represents elapsed time durations and molds values back to total seconds.

    Lifecycle:
        1. **Casting Phase**: Parses numeric seconds or `HH:MM:SS` string to `timedelta`.
        2. **Molding Phase**: Converts `timedelta` to total seconds float.

    Execution Order:
        1. Inspect numeric or colon-separated duration string in `cast()`.
        2. Calculate seconds and return `timedelta`.
        3. Call `value.total_seconds()` in `mold()`.

    Parameters:
        **kwargs: Base Facet parameters.

    Return Values:
        DurationFacet: An initialized duration facet.

    Exceptions:
        CastFault: Raised if duration string format is unrecognized.

    Notes:
        - OpenAPI format is `"duration"`.

    Internal Behaviour:
        Splits colon notation into hours, minutes, seconds.

    Edge Cases:
        - Negative duration strings (e.g. `"-01:30:00"`) are supported.

    Examples:
        >>> facet = DurationFacet()
        >>> facet.cast("01:30:00")
        datetime.timedelta(seconds=5400)
    """

    _type_name = "string"
    _python_type = "datetime.timedelta"

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
    """
    UUID facet, parsing standard 36-character hexadecimal strings into `uuid.UUID` objects.

    Purpose:
        Validates Universally Unique Identifier strings and molds back to canonical string representations.

    Lifecycle:
        1. **Casting Phase**: Coerces string to `uuid.UUID`.
        2. **Molding Phase**: Renders `UUID` instance to standard string (`"str(value)"`).

    Execution Order:
        1. Parse string using `uuid.UUID()` in `cast()`.
        2. Format using `str()` in `mold()`.

    Parameters:
        **kwargs: Base Facet parameters.

    Return Values:
        UUIDFacet: An initialized UUID facet descriptor.

    Exceptions:
        CastFault: Raised if string is not a valid 128-bit UUID hex representation.

    Notes:
        - OpenAPI format is `"uuid"`.

    Internal Behaviour:
        Delegates validation to `uuid.UUID(str(value))`.

    Edge Cases:
        - Accepts UUIDs with or without hyphens.

    Examples:
        >>> facet = UUIDFacet()
        >>> facet.cast("123e4567-e89b-12d3-a456-426614174000")
        UUID('123e4567-e89b-12d3-a456-426614174000')
    """

    _type_name = "string"
    _python_type = "uuid.UUID"

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
    """
    List array facet primitive with optional element-level child facet validation and item count boundaries.

    Purpose:
        Validates, casts, and molds homogeneous or heterogeneous list collections of data.

    Lifecycle:
        1. **Instantiation**: Bound with optional `child` Facet and `min_items` / `max_items` constraints.
        2. **Casting Phase**: Coerces iterable input into a list and executes `child.cast()` on each element.
        3. **Validation Pass**: Validates length against `min_items` / `max_items` and calls `child.seal()` on each item.
        4. **Molding Phase**: Transforms elements back via `child.mold()`.

    Execution Order:
        1. Verify collection type (list/tuple) in `cast()`.
        2. Cast each element via `self.child.cast()` if child facet is present.
        3. Check item count bounds (`min_items`, `max_items`) in `seal()`.
        4. Seal each element via `self.child.seal()`.

    Parameters:
        child (Facet | None, optional): Backing Facet descriptor to validate each list element.
        min_items (int | None, optional): Inclusive minimum allowed list element count.
        max_items (int | None, optional): Inclusive maximum allowed list element count.
        **kwargs: Base Facet parameters.

    Return Values:
        ListFacet: An initialized list facet.

    Exceptions:
        CastFault: Raised if input is not a collection, element casting fails, or item limits are violated.

    Notes:
        - Subscript shortcut support: `Facet.list[TextFacet()]` or `list[str]` annotations.

    Internal Behaviour:
        Iterates over items using standard list comprehensions, embedding element indices into error path strings (`field[0]`).

    Edge Cases:
        - Empty list `[]` with `min_items > 0` raises `CastFault`.

    Examples:
        >>> facet = ListFacet(child=TextFacet(min_length=2), min_items=1)
        >>> facet.cast(["alpha", "beta"])
        ['alpha', 'beta']
    """

    _type_name = "array"
    _python_type = "list[Any]"

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

    def python_type(self) -> str:
        return f"list[{self.child.python_type() if self.child else 'Any'}]"

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
    """
    Set/unique collection facet primitive with optional element validation and item boundaries.

    Purpose:
        Coerces inputs to Python `set` collections, ensuring element uniqueness.

    Lifecycle:
        1. **Casting Phase**: Converts iterable input to Python `set` and casts items via `child.cast()`.
        2. **Validation Pass**: Validates unique item count boundaries.

    Execution Order:
        1. Convert iterable input to `set` in `cast()`.
        2. Enforce `min_items` and `max_items` boundaries in `seal()`.
        3. Mold output back to list for JSON serialization.

    Parameters:
        child (Facet | None, optional): Element validation facet descriptor.
        min_items (int | None, optional): Inclusive minimum unique item count.
        max_items (int | None, optional): Inclusive maximum unique item count.
        **kwargs: Base Facet parameters.

    Return Values:
        SetFacet: An initialized set facet.

    Exceptions:
        CastFault: Raised if input is unhashable or fails child item validation.

    Notes:
        - Schema generates `uniqueItems: true`.

    Internal Behaviour:
        Molds `set` to `list` for JSON serializability.

    Edge Cases:
        - Duplicate items in input list are deduplicated automatically into the set.

    Examples:
        >>> facet = SetFacet(child=IntFacet())
        >>> facet.cast([1, 2, 2, 3])
        {1, 2, 3}
    """

    _type_name = "array"
    _python_type = "set[Any]"

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

    def python_type(self) -> str:
        return f"set[{self.child.python_type() if self.child else 'Any'}]"

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
    """
    Tuple array facet primitive supporting element validation and fixed sequence representations.

    Purpose:
        Validates and coerces collection inputs to immutable Python tuples.

    Lifecycle:
        1. **Casting Phase**: Coerces collection into `tuple` and casts items via `child.cast()`.
        2. **Molding Phase**: Formats `tuple` into list for JSON output.

    Execution Order:
        1. Check collection type and cast to `tuple` in `cast()`.
        2. Validate item bounds and seal elements in `seal()`.

    Parameters:
        child (Facet | None, optional): Element validation facet descriptor.
        min_items (int | None, optional): Minimum item count.
        max_items (int | None, optional): Maximum item count.
        **kwargs: Base Facet parameters.

    Return Values:
        TupleFacet: An initialized tuple facet.

    Exceptions:
        CastFault: Raised if input is not a collection.

    Notes:
        - Python type annotation produces `tuple[T, ...]`.

    Internal Behaviour:
        Converts tuple to list during `mold()`.

    Edge Cases:
        - Accepts inputs as lists or sets and coerces to tuple.

    Examples:
        >>> facet = TupleFacet(child=IntFacet())
        >>> facet.cast([10, 20])
        (10, 20)
    """

    _type_name = "array"
    _python_type = "tuple[Any, ...]"

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

    def python_type(self) -> str:
        return f"tuple[{self.child.python_type() if self.child else 'Any'}, ...]"

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
    """
    Dictionary object facet primitive, optionally validating dictionary values against a value facet.

    Purpose:
        Validates key-value dictionary mappings and protects against hash-collision DoS attacks.

    Lifecycle:
        1. **Casting Phase**: Coerces dict or JSON object string into a dictionary, checking key limit `max_keys`.
        2. **Validation Pass**: Validates each key value against `value_facet`.

    Execution Order:
        1. Parse JSON string if needed and verify dict type in `cast()`.
        2. Enforce `max_keys` limit (default 1000).
        3. Validate key string types and cast values using `value_facet`.

    Parameters:
        value_facet (Facet | None, optional): Facet descriptor applied to every dictionary value.
        max_keys (int | None, optional): Maximum allowed key count (defaults to 1000).
        **kwargs: Base Facet parameters.

    Return Values:
        DictFacet: An initialized dictionary facet.

    Exceptions:
        CastFault: Raised if value is not a dictionary or key count exceeds limit.

    Notes:
        - Thread safety: Key validation creates local variable paths rather than mutating shared facets.

    Internal Behaviour:
        Iterates over `value.items()` validating each entry individually.

    Edge Cases:
        - Non-string dictionary keys raise `CastFault`.

    Examples:
        >>> facet = DictFacet(value_facet=IntFacet())
        >>> facet.cast({"a": "1", "b": "2"})
        {'a': 1, 'b': 2}
    """

    _type_name = "object"
    _python_type = "dict[str, Any]"

    # Default maximum number of keys to prevent hash-collision DoS
    DEFAULT_MAX_KEYS = 1000

    def __init__(self, *, value_facet: Facet | None = None, max_keys: int | None = None, **kwargs):
        super().__init__(**kwargs)
        self.value_facet = value_facet
        self.max_keys = max_keys if max_keys is not None else self.DEFAULT_MAX_KEYS

    def python_type(self) -> str:
        return f"dict[str, {self.value_facet.python_type() if self.value_facet else 'Any'}]"

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
    """
    Arbitrary JSON facet with configurable nesting depth and type allowlists.

    Purpose:
        Stores unstructured JSON structures while preventing infinite recursion and unsafe object injection.

    Lifecycle:
        1. **Casting Phase**: Parses JSON string if necessary and performs recursive depth and type safety checks.
        2. **Validation Pass**: Confirms structure safety.

    Execution Order:
        1. Parse JSON string in `cast()`.
        2. Execute `_check_depth()` recursively checking nesting levels and type allowlists.

    Parameters:
        max_depth (int | None, optional): Maximum allowed nesting depth (defaults to 32).
        allowed_types (tuple | None, optional): Tuple of allowed primitive types in JSON payload.
        **kwargs: Base Facet parameters.

    Return Values:
        JSONFacet: An initialized JSON facet.

    Exceptions:
        CastFault: Raised if nesting depth exceeds limit or un-serializable object types are present.

    Notes:
        - Default safe allowlist includes: `str`, `int`, `float`, `bool`, `None`, `list`, `dict`.

    Internal Behaviour:
        Traverses nested dicts and lists recursively in `_check_depth()`.

    Edge Cases:
        - Attempting to pass complex objects (e.g. custom class instances) raises `CastFault`.

    Examples:
        >>> facet = JSONFacet(max_depth=5)
        >>> facet.cast({"settings": {"theme": "dark"}})
        {'settings': {'theme': 'dark'}}
    """

    _type_name = "object"
    _python_type = "Any"

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


class FileFacet(Facet):
    """
    File reference facet storing string path or URL references.

    Purpose:
        Represents file path or URL strings pointing to stored assets.

    Lifecycle:
        1. **Molding Phase**: Renders string path/URL representation.

    Execution Order:
        1. Cast via default facet string handling.
        2. Mold value using `str(value)`.

    Parameters:
        allowed_types (list[str] | None, optional): Allowed file extensions or MIME types.
        **kwargs: Base Facet parameters.

    Return Values:
        FileFacet: An initialized file reference facet.

    Exceptions:
        CastFault: Raised if value fails standard facet casting.

    Notes:
        - OpenAPI schema format is `"binary"`.

    Internal Behaviour:
        Converts non-string file references using `str()`.

    Edge Cases:
        - `None` value molds to `None`.

    Examples:
        >>> facet = FileFacet()
        >>> facet.mold("/var/storage/invoice.pdf")
        '/var/storage/invoice.pdf'
    """

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


class ChoiceFacet(Facet):
    """
    Facet primitive restricting allowed field values to a fixed set of options.

    Purpose:
        Enforces choice validation against sets, lists, or dictionary keys.

    Lifecycle:
        1. **Instantiation**: Parses choices mapping/sequence into `_valid_values` set.
        2. **Validation Pass**: Validates that inbound value exists in `_valid_values`.

    Execution Order:
        1. Match input value against `_valid_values` in `seal()`.
        2. Return value on success, or raise `CastFault`.

    Parameters:
        choices (Sequence): Sequence or dict of allowed choices.
        **kwargs: Base Facet parameters.

    Return Values:
        ChoiceFacet: An initialized choice facet.

    Exceptions:
        CastFault: Raised if input value is not in `allowed_values`.

    Notes:
        - Generates OpenAPI `enum` schema array.

    Internal Behaviour:
        Stores valid choices inside internal set `_valid_values` for O(1) lookup.

    Edge Cases:
        - Supports tuple/list pairs `[("key", "label")]`.

    Examples:
        >>> facet = ChoiceFacet(choices=["active", "pending", "disabled"])
        >>> facet.seal("active")
        'active'
    """

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

    def python_type(self) -> str:
        values = self.allowed_values
        if not values or not all(v is None or isinstance(v, (str, int, bool)) for v in values):
            return "Any"
        return f"Literal[{', '.join(repr(v) for v in values)}]"

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
    """
    Facet primitive representing a single exact literal value (e.g. discriminator fields).

    Purpose:
        Restricts acceptable values to a single specific literal constant.

    Lifecycle:
        1. **Instantiation**: Wraps single literal value inside `ChoiceFacet(choices=[value])`.
        2. **Validation Pass**: Enforces strict equality match.

    Execution Order:
        1. Delegate matching to `ChoiceFacet.seal()`.

    Parameters:
        value (Any): The single literal constant value.
        **kwargs: Base Facet parameters.

    Return Values:
        LiteralFacet: An initialized literal facet.

    Exceptions:
        CastFault: Raised if value does not equal the target literal value.

    Notes:
        - Commonly used in discriminated union contracts.

    Internal Behaviour:
        Passes `[value]` list to parent `ChoiceFacet.__init__()`.

    Edge Cases:
        - Mismatched types (e.g., `"1"` vs `1`) raise `CastFault`.

    Examples:
        >>> facet = LiteralFacet("v1")
        >>> facet.seal("v1")
        'v1'
    """

    def __init__(self, value: Any, **kwargs: Any):
        super().__init__(choices=[value], **kwargs)
        self.value = value


class EnumFacet(Facet):
    """
    Facet primitive representing a Python `enum.Enum` type.

    Purpose:
        Validates, coerces, and molds values to and from Python Enum member instances.

    Lifecycle:
        1. **Casting Phase**: Coerces primitive values or string names to `enum_class` members.
        2. **Molding Phase**: Converts Enum member to underlying `.value` primitive.

    Execution Order:
        1. Match Enum instance or coerce primitive value in `cast()`.
        2. Enforce member membership in `seal()`.
        3. Extract `value.value` in `mold()`.

    Parameters:
        enum_class (type): The target Python `Enum` subclass.
        **kwargs: Base Facet parameters.

    Return Values:
        EnumFacet: An initialized Enum facet descriptor.

    Exceptions:
        CastFault: Raised if input value does not map to any valid Enum member or value.

    Notes:
        - Supports StringEnums, IntEnums, and standard Enums.

    Internal Behaviour:
        Inspects `enum_class.__members__` and member values during casting.

    Edge Cases:
        - Casting accepts either member name (`"ACTIVE"`) or raw enum value (`"active"`).

    Examples:
        >>> class Status(TextChoices):
        ...     ACTIVE = "active", "Active"
        >>> facet = EnumFacet(Status)
        >>> facet.cast("active")
        <Status.ACTIVE: 'active'>
    """

    def __init__(self, enum_class: type, **kwargs: Any):
        super().__init__(**kwargs)
        self.enum_class = enum_class
        self._valid_members = set(enum_class)
        self._valid_values = {m.value for m in enum_class}

    @property
    def allowed_values(self) -> tuple:
        return tuple(m.value for m in self.enum_class)

    def python_type(self) -> str:
        module = getattr(self.enum_class, "__module__", "")
        qualname = getattr(self.enum_class, "__qualname__", getattr(self.enum_class, "__name__", "Any"))
        if not module or module == "builtins" or "<locals>" in qualname:
            return "Any"
        return f"{module}.{qualname}"

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


class PolymorphicFacet(Facet):
    """
    Polymorphic facet attempting casting and sealing through multiple candidate Facet options.

    Purpose:
        Enables union type handling (e.g. `Union[CatContract, DogContract]`).

    Lifecycle:
        1. **Casting Phase**: Iterates through `choices` attempting `cast()` until one succeeds.
        2. **Validation Pass**: Validates matched choice via `seal()`.

    Execution Order:
        1. Try each `choice.cast(value)` sequentially.
        2. If all choices fail, collect error messages and raise `CastFault`.

    Parameters:
        choices (list[Facet]): List of candidate Facet descriptors.
        **kwargs: Base Facet parameters.

    Return Values:
        PolymorphicFacet: An initialized polymorphic facet.

    Exceptions:
        CastFault: Raised if value fails to match any of the candidate facet choices.

    Notes:
        - Generates OpenAPI `anyOf` schema.

    Internal Behaviour:
        Traverses candidate choices in order of declaration.

    Edge Cases:
        - If first matching choice succeeds, remaining choices are skipped.

    Examples:
        >>> facet = PolymorphicFacet(choices=[IntFacet(), TextFacet()])
        >>> facet.cast(42)
        42
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
    Computed value facet primitive whose value is calculated dynamically at serialization time.

    Purpose:
        Computes dynamic field values using callables or contract/model instance methods.

    Lifecycle:
        1. **Instantiation**: Bound with `compute` callable or method string name, setting `read_only=True`.
        2. **Extraction Pass**: Executes computation during `extract()`.
        3. **Molding Phase**: Passes computed value through directly.

    Execution Order:
        1. Resolve string method or callable in `extract()`.
        2. Supply live Contract instance `_owner` to `@computed` methods.
        3. Pass computed return value through `mold()`.

    Parameters:
        compute (Callable | str): Callable `(instance) -> value` or string method name on Contract/Model.
        **kwargs: Base Facet parameters (`read_only=True`).

    Return Values:
        Computed: An initialized computed facet.

    Exceptions:
        CastFault: Not raised directly as input is ignored (`read_only=True`).

    Notes:
        - Contract context `self.context` and validated data `self._validated_data` are accessible in computed methods.

    Internal Behaviour:
        Inspects signature of `self._compute` to detect unbound method signatures.

    Edge Cases:
        - If method target cannot be resolved on model or contract, returns `None`.

    Examples:
        >>> facet = Computed(lambda user: f"{user.first_name} {user.last_name}")
    """

    def __init__(self, compute: Callable | str, **kwargs):
        kwargs["read_only"] = True
        super().__init__(**kwargs)
        self._compute = compute

    def extract(self, instance: Any, _owner: Any = None) -> Any:
        if isinstance(self._compute, str):
            owner = _owner if _owner is not None else self.contract
            if owner is not None:
                method = getattr(owner, self._compute, None)
                if method is not None:
                    return method(instance)
            method = getattr(instance, self._compute, None)
            if method is not None:
                return method()
            return None

        import inspect

        try:
            sig = inspect.signature(self._compute)
            if len(sig.parameters) >= 2:
                bp = _owner if _owner is not None else self.contract
                if bp is None:
                    qualname = getattr(self._compute, "__qualname__", "")
                    if "." in qualname:
                        cls_name = qualname.rsplit(".", 1)[0]
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
    Fixed constant facet primitive returning a static value on serialization.

    Purpose:
        Emits hardcoded API versioning identifiers or type discriminators.

    Lifecycle:
        1. **Instantiation**: Bound with fixed constant value, setting `read_only=True`.
        2. **Extraction Pass**: Returns stored constant during `extract()`.

    Execution Order:
        1. Return stored `_constant` in `extract()`.
        2. Emit `const` property in OpenAPI schema.

    Parameters:
        value (Any): The fixed constant value.
        **kwargs: Base Facet parameters.

    Return Values:
        Constant: An initialized constant facet.

    Exceptions:
        CastFault: Not raised directly.

    Notes:
        - Output schema emits `"const": value`.

    Internal Behaviour:
        Overrides `extract()` and `mold()` to return `_constant`.

    Edge Cases:
        - User input during casting is ignored due to `read_only=True`.

    Examples:
        >>> facet = Constant("v2")
        >>> facet.extract(None)
        'v2'
    """

    def __init__(self, value: Any, **kwargs):
        kwargs["read_only"] = True
        super().__init__(**kwargs)
        self._constant = value

    def python_type(self) -> str:
        if self._constant is None or isinstance(self._constant, (str, int, bool)):
            return f"Literal[{self._constant!r}]"
        return "Any"

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
    Write-only text facet primitive (e.g. passwords).

    Purpose:
        Accepts inbound client inputs during request casting but hides values from output serialization.

    Lifecycle:
        1. **Instantiation**: Sets `write_only=True` on underlying `TextFacet`.
        2. **Casting Pass**: Validates incoming password string.
        3. **Molding Pass**: Omitted from output payload.

    Execution Order:
        1. Execute `TextFacet.cast()` and `TextFacet.seal()`.
        2. Exclude field from serialization output dictionary.

    Parameters:
        **kwargs: Arguments passed to `TextFacet`.

    Return Values:
        WriteOnly: An initialized write-only text facet.

    Exceptions:
        CastFault: Raised if password string fails length/pattern checks.

    Notes:
        - Schema generates `"writeOnly": true`.

    Internal Behaviour:
        Sets `write_only = True` flag in `__init__`.

    Edge Cases:
        - Field is completely omitted during `Contract.to_dict()`.

    Examples:
        >>> facet = WriteOnly(min_length=8)
    """

    def __init__(self, **kwargs):
        kwargs["write_only"] = True
        super().__init__(**kwargs)


class ReadOnly(Facet):
    """
    Pass-through read-only facet primitive.

    Purpose:
        Exposes model attributes on output payloads while ignoring incoming request body inputs.

    Lifecycle:
        1. **Instantiation**: Configured with `read_only=True`.
        2. **Molding Pass**: Automatically serializes dates, UUIDs, Decimals, and timedeltas.

    Execution Order:
        1. Ignore inbound request input in `cast()`.
        2. Format dates, UUIDs, Decimals in `mold()`.

    Parameters:
        **kwargs: Base Facet parameters (`read_only=True`).

    Return Values:
        ReadOnly: An initialized read-only facet.

    Exceptions:
        CastFault: Not raised directly as input is skipped.

    Notes:
        - Automatically converts `datetime`, `UUID`, `Decimal`, and `timedelta` to strings.

    Internal Behaviour:
        Checks `isinstance` in `mold()` for automatic scalar stringification.

    Edge Cases:
        - `None` passes through unchanged.

    Examples:
        >>> facet = ReadOnly()
        >>> facet.mold(datetime(2026, 7, 30))
        '2026-07-30T00:00:00'
    """

    def __init__(self, **kwargs):
        kwargs["read_only"] = True
        super().__init__(**kwargs)

    def mold(self, value: Any) -> Any:
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
    Hidden facet primitive, populated internally via DI or defaults, and excluded from inputs/outputs.

    Purpose:
        Manages internal audit or state fields hidden from public API schema.

    Lifecycle:
        1. **Instantiation**: Configured with `write_only=True`.
        2. **Execution**: Evaluates default or DI resolution internally.

    Execution Order:
        1. Populate from default or DI context.
        2. Omit from OpenAPI schema and serialization outputs.

    Parameters:
        **kwargs: Base Facet parameters.

    Return Values:
        Hidden: An initialized hidden facet.

    Exceptions:
        CastFault: Not exposed externally.

    Notes:
        - Excluded from client input and response schemas.

    Internal Behaviour:
        Sets `write_only=True`.

    Edge Cases:
        - Never rendered in OpenAPI documentation.

    Examples:
        >>> facet = Hidden(default="internal_system")
    """

    def __init__(self, **kwargs):
        kwargs["write_only"] = True
        super().__init__(**kwargs)


# ── DI Injection Facet ───────────────────────────────────────────────────


class Inject(Facet):
    """
    Dependency Injection facet primitive resolving values from the application DI container at runtime.

    Purpose:
        Resolves contextual dependencies (current user, services, request objects) into contract fields.

    Lifecycle:
        1. **Instantiation**: Configured with target DI token, `via` method name, or `attr` property.
        2. **Resolution Pass**: Queries DI container or context mapping in `resolve_from_context()`.

    Execution Order:
        1. Query `context["container"]` for registered token service.
        2. Fallback to direct key lookup in `context` dict.
        3. Invoke `via` method or read `attr` attribute on resolved service.

    Parameters:
        token (Any): Target DI service token (type or string name).
        via (str | None, optional): Service method to execute for value.
        attr (str | None, optional): Service property attribute to read.
        **kwargs: Base Facet parameters (`read_only=True`).

    Return Values:
        Inject: An initialized DI inject facet.

    Exceptions:
        CastFault: Not raised directly.

    Notes:
        - Solves dependency resolution without user input payload tampering.

    Internal Behaviour:
        Supports both full `container.resolve()` and lightweight `context[token]` lookups.

    Edge Cases:
        - If token is missing, returns `UNSET`.

    Examples:
        >>> facet = Inject("identity", attr="id")
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
    """
    Uploaded file facet primitive for multipart form file uploads.

    Purpose:
        Validates uploaded file instances (`UploadFile`), enforcing byte size limits and MIME content type allowlists.

    Lifecycle:
        1. **Casting Phase**: Asserts input is an `UploadFile` instance, checking `max_size` and `allowed_types`.
        2. **Molding Phase**: Serializes metadata dictionary (`filename`, `content_type`, `size`).

    Execution Order:
        1. Verify `UploadFile` type in `cast()`.
        2. Check byte size against `max_size`.
        3. Match `content_type` against `allowed_types` list or wildcard patterns (`"image/*"`).
        4. Return metadata dict in `mold()`.

    Parameters:
        max_size (int | None, optional): Maximum permitted file size in bytes.
        allowed_types (list[str] | None, optional): List of allowed MIME types or wildcards.
        **kwargs: Base Facet parameters.

    Return Values:
        UploadFileFacet: An initialized upload file facet descriptor.

    Exceptions:
        CastFault: Raised if value is not an `UploadFile`, exceeds `max_size`, or has disallowed MIME type.

    Notes:
        - Supports wildcard MIME matching like `"image/*"`.

    Internal Behaviour:
        Inspects `UploadFile.content_type` and `UploadFile.size`.

    Edge Cases:
        - Molds `UploadFile` to dictionary metadata instead of raw bytes.

    Examples:
        >>> facet = UploadFileFacet(max_size=5_000_000, allowed_types=["image/png", "image/jpeg"])
    """

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
    """
    Form data input facet primitive for urlencoded or multipart scalar fields.

    Purpose:
        Wraps and delegates validation to an inner child facet built from type annotations.

    Lifecycle:
        1. **Instantiation**: Builds inner `child_facet` from type annotation (`int`, `str`, etc.).
        2. **Delegation Pass**: Delegates `cast()`, `seal()`, and `mold()` to inner `child_facet`.

    Execution Order:
        1. Construct `child_facet` using `_build_facet_from_annotation()`.
        2. Delegate `cast()` and `seal()` execution to `child_facet`.

    Parameters:
        type (Any, optional): Type annotation for inner facet coercion. Defaults to `str`.
        **kwargs: Base Facet parameters.

    Return Values:
        FormDataFacet: An initialized form data facet.

    Exceptions:
        CastFault: Raised if inner child facet casting fails.

    Notes:
        - Bridges web HTML form inputs with typed contract facets.

    Internal Behaviour:
        Calls `_build_facet_from_annotation()` on initialization.

    Edge Cases:
        - Falls back to `str(value)` if child facet resolution is unavailable.

    Examples:
        >>> facet = FormDataFacet(type=int)
        >>> facet.cast("100")
        100
    """

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

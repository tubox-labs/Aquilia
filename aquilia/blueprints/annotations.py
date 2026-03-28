"""
Aquilia Blueprint Annotations -- type-annotation–driven schema declaration.

Enables Blueprints to be declared using Python type annotations instead of
(or alongside) explicit Facet instantiation.  This is a first-class,
Aquilia-native system -- no external libraries.

Usage::

    from aquilia.blueprints import Blueprint, Field, computed

    class UserBlueprint(Blueprint):
        name: str = Field(min_length=2, max_length=100)
        age: int = Field(ge=0, le=150)
        email: str = Field(pattern=r"^[\\w.+-]+@[\\w-]+\\.[\\w.]+$")
        role: str = Field(default="user", choices=["user", "admin", "mod"])
        tags: list[str] = Field(default_factory=list)
        bio: str | None = None

        @computed
        def full_name(self, instance) -> str:
            return f"{instance.first_name} {instance.last_name}"

    class OrderBlueprint(Blueprint):
        user: UserBlueprint            # nested Blueprint
        items: list[ItemBlueprint]     # list of nested Blueprints
        total: float
"""

from __future__ import annotations

import sys
import types
import uuid
from collections.abc import Callable, Sequence
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import (
    Any,
    Optional,
    Union,
    get_args,
    get_origin,
)

from .exceptions import CastFault
from .facets import (
    UNSET,
    BoolFacet,
    ChoiceFacet,
    Computed,
    DateFacet,
    DateTimeFacet,
    DecimalFacet,
    DictFacet,
    DurationFacet,
    EmailFacet,
    Facet,
    FloatFacet,
    IntFacet,
    ListFacet,
    PolymorphicFacet,
    TextFacet,
    TimeFacet,
    URLFacet,
    UUIDFacet,
)

__all__ = [
    "Field",
    "computed",
    "NestedBlueprintFacet",
    "LazyBlueprintFacet",
    "introspect_annotations",
    "ANNOTATION_TO_FACET",
]


# ── Type → Facet Mapping ────────────────────────────────────────────────

ANNOTATION_TO_FACET: dict[type, type[Facet]] = {
    str: TextFacet,
    int: IntFacet,
    float: FloatFacet,
    bool: BoolFacet,
    Decimal: DecimalFacet,
    datetime: DateTimeFacet,
    date: DateFacet,
    time: TimeFacet,
    timedelta: DurationFacet,
    uuid.UUID: UUIDFacet,
    dict: DictFacet,
    list: ListFacet,
    bytes: TextFacet,
}


# ── Field Descriptor ────────────────────────────────────────────────────


class Field:
    """
    Constraint descriptor for annotation-driven Blueprint fields.

    Provides the same power as explicit Facet kwargs, but in a concise
    form suitable for use as a default value alongside a type annotation.

    Args:
        default:         Static default value.
        default_factory: Zero-arg callable producing the default.
        required:        Override auto-detected required status.
        read_only:       If True, field only appears in output.
        write_only:      If True, field only accepted as input.
        allow_null:      Accept None as a valid value.
        allow_blank:     Accept empty string (text fields).
        source:          Model attribute name override.
        label:           Human-readable label.
        help_text:       Documentation string.
        validators:      Extra validator callables.

        # Numeric constraints
        ge:              Greater-than-or-equal (min_value).
        le:              Less-than-or-equal (max_value).
        gt:              Strictly greater-than.
        lt:              Strictly less-than.

        # Text constraints
        min_length:      Minimum string length.
        max_length:      Maximum string length.
        pattern:         Regex pattern the value must match.

        # Collection constraints
        min_items:       Minimum list length.
        max_items:       Maximum list length.

        # Choice constraint
        choices:         Allowed values.

        # Decimal
        max_digits:      Maximum total digits.
        decimal_places:  Maximum decimal places.

        # Alias
        alias:           Alternative input key name.
    """

    # Track creation order for stable field ordering.
    _creation_counter: int = 0

    __slots__ = (
        "default",
        "default_factory",
        "required",
        "read_only",
        "write_only",
        "allow_null",
        "allow_blank",
        "source",
        "label",
        "help_text",
        "validators",
        "ge",
        "le",
        "gt",
        "lt",
        "min_length",
        "max_length",
        "pattern",
        "min_items",
        "max_items",
        "choices",
        "max_digits",
        "decimal_places",
        "alias",
        "_order",
    )

    def __init__(
        self,
        *,
        default: Any = UNSET,
        default_factory: Callable | None = None,
        required: bool | None = None,
        read_only: bool = False,
        write_only: bool = False,
        allow_null: bool = False,
        allow_blank: bool = False,
        source: str | None = None,
        label: str | None = None,
        help_text: str | None = None,
        validators: Sequence[Callable] | None = None,
        ge: int | float | None = None,
        le: int | float | None = None,
        gt: int | float | None = None,
        lt: int | float | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        pattern: str | None = None,
        min_items: int | None = None,
        max_items: int | None = None,
        choices: Sequence | None = None,
        max_digits: int | None = None,
        decimal_places: int | None = None,
        alias: str | None = None,
    ):
        if default is not UNSET and default_factory is not None:
            from aquilia.faults.domains import ConfigInvalidFault

            raise ConfigInvalidFault(
                key="field.default",
                reason="Cannot specify both 'default' and 'default_factory'",
            )

        self.default = default
        self.default_factory = default_factory
        self.required = required
        self.read_only = read_only
        self.write_only = write_only
        self.allow_null = allow_null
        self.allow_blank = allow_blank
        self.source = source
        self.label = label
        self.help_text = help_text
        self.validators = list(validators) if validators else []
        self.ge = ge
        self.le = le
        self.gt = gt
        self.lt = lt
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = pattern
        self.min_items = min_items
        self.max_items = max_items
        self.choices = choices
        self.max_digits = max_digits
        self.decimal_places = decimal_places
        self.alias = alias

        Field._creation_counter += 1
        self._order = Field._creation_counter

    def __repr__(self) -> str:
        parts = []
        if self.default is not UNSET:
            parts.append(f"default={self.default!r}")
        if self.default_factory is not None:
            parts.append(f"default_factory={self.default_factory!r}")
        if self.required is not None:
            parts.append(f"required={self.required}")
        return f"Field({', '.join(parts)})"


# ── NestedBlueprintFacet ────────────────────────────────────────────────


class NestedBlueprintFacet(Facet):
    """
    A Facet that delegates validation to a nested Blueprint.

    Used when a type annotation references another Blueprint subclass.
    Handles both single-instance and list-of-instances nesting.

    The nested Blueprint is fully sealed during the parent's seal phase,
    producing structured, validated output.
    """

    _type_name = "object"

    # Maximum nesting depth to prevent stack overflow from recursive Blueprints
    MAX_NESTING_DEPTH = 32

    # Thread-local nesting depth counter
    _current_nesting_depth = 0

    def __init__(
        self,
        blueprint_cls: type,
        *,
        many: bool = False,
        max_nesting_depth: int | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._blueprint_cls = blueprint_cls
        self.many = many
        self._max_depth = max_nesting_depth or self.MAX_NESTING_DEPTH

    @property
    def target(self) -> type:
        return self._blueprint_cls

    def cast(self, value: Any) -> Any:
        """Cast input through the nested Blueprint's seal pipeline."""
        # Guard against recursive nesting depth
        NestedBlueprintFacet._current_nesting_depth += 1
        try:
            if NestedBlueprintFacet._current_nesting_depth > self._max_depth:
                raise CastFault(
                    self.name or "<unbound>",
                    f"Nested Blueprint depth exceeds maximum of {self._max_depth}",
                )
            if self.many:
                return self._cast_many(value)
            return self._cast_single(value)
        finally:
            NestedBlueprintFacet._current_nesting_depth -= 1

    def _cast_single(self, value: Any) -> dict:
        """Cast a single nested value."""
        if isinstance(value, dict):
            bp = self._blueprint_cls(data=value)
            if not bp.is_sealed():
                # Collect nested errors with field prefix
                raise CastFault(
                    self.name or "<unbound>",
                    f"Nested validation failed: {bp.errors}",
                )
            return bp.validated_data
        raise CastFault(
            self.name or "<unbound>",
            f"Expected object, got {type(value).__name__}",
        )

    def _cast_many(self, value: Any) -> list:
        """Cast a list of nested values."""
        if not isinstance(value, (list, tuple)):
            raise CastFault(
                self.name or "<unbound>",
                f"Expected list, got {type(value).__name__}",
            )
        results = []
        errors = {}
        for i, item in enumerate(value):
            if isinstance(item, dict):
                bp = self._blueprint_cls(data=item)
                if bp.is_sealed():
                    results.append(bp.validated_data)
                else:
                    errors[f"{self.name or '<unbound>'}[{i}]"] = bp.errors
            else:
                errors[f"{self.name or '<unbound>'}[{i}]"] = [f"Expected object, got {type(item).__name__}"]
        if errors:
            raise CastFault(
                self.name or "<unbound>",
                f"List validation failed: {errors}",
            )
        return results

    def seal(self, value: Any) -> Any:
        """Already validated during cast -- pass through."""
        return super().seal(value)

    def mold(self, value: Any) -> Any:
        """Mold output through the nested Blueprint."""
        if value is None:
            return None
        if self.many:
            if hasattr(value, "__iter__"):
                bp = self._blueprint_cls(instance=None, many=True)
                return bp.to_dict_many(value)
            return []
        bp = self._blueprint_cls(instance=value)
        return bp.to_dict()

    def extract(self, instance: Any) -> Any:
        """Extract the nested value from a model instance."""
        if self.source == "*":
            return instance
        parts = self.source.split(".") if self.source else []
        obj = instance
        for part in parts:
            if obj is None:
                return None
            obj = obj.get(part) if isinstance(obj, dict) else getattr(obj, part, None)
        return obj

    def to_schema(self) -> dict[str, Any]:
        """Generate JSON Schema with $ref to nested Blueprint."""
        ref_name = self._blueprint_cls.__name__
        if self.many:
            return {
                "type": "array",
                "items": {"$ref": f"#/components/schemas/{ref_name}"},
            }
        return {"$ref": f"#/components/schemas/{ref_name}"}


# ── LazyBlueprintFacet ──────────────────────────────────────────────────


class LazyBlueprintFacet(Facet):
    """
    A Facet that delays resolution of a Blueprint class via its string name.
    Used for self-referential tree structures or forward references.
    """

    _type_name = "object"

    def __init__(self, ref: str, *, many: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.ref = ref
        self.many = many
        self._resolved_facet: NestedBlueprintFacet | None = None

    def _get_resolved(self) -> NestedBlueprintFacet:
        if self._resolved_facet is not None:
            return self._resolved_facet

        from .core import _blueprint_registry

        blueprint_cls = _blueprint_registry.get(self.ref)
        if blueprint_cls is None:
            from aquilia.faults.domains import RegistryFault

            raise RegistryFault(
                name=self.ref,
                message=f"Cannot resolve forward reference '{self.ref}'. Blueprint not found.",
            )

        kwargs = {
            "source": self.source,
            "required": self.required,
            "read_only": self.read_only,
            "write_only": self.write_only,
            "allow_null": self.allow_null,
            "label": self.label,
            "help_text": self.help_text,
            "default": self.default,
        }
        self._resolved_facet = NestedBlueprintFacet(blueprint_cls, many=self.many, **kwargs)
        self._resolved_facet.name = self.name

        # Merge validators if any were added to the lazy facet
        if self.validators:
            self._resolved_facet.validators.extend(self.validators)

        return self._resolved_facet

    @property
    def target(self) -> type:
        return self._get_resolved().target

    def cast(self, value: Any) -> Any:
        return self._get_resolved().cast(value)

    def seal(self, value: Any) -> Any:
        return self._get_resolved().seal(value)

    def mold(self, value: Any) -> Any:
        return self._get_resolved().mold(value)

    def extract(self, instance: Any) -> Any:
        return self._get_resolved().extract(instance)

    def to_schema(self) -> dict[str, Any]:
        return self._get_resolved().to_schema()


# ── @computed Decorator ─────────────────────────────────────────────────


class _ComputedMarker:
    """Internal marker for methods decorated with @computed."""

    __slots__ = ("func", "_order")

    def __init__(self, func: Callable):
        self.func = func
        Facet._creation_order += 1
        self._order = Facet._creation_order

    def to_facet(self) -> Computed:
        """Convert to a Computed facet."""
        facet = Computed(self.func)
        facet._order = self._order
        return facet


def computed(func: Callable) -> _ComputedMarker:
    """
    Decorator to mark a Blueprint method as a computed output field.

    The method receives ``(self, instance)`` and returns the computed value.
    The field is read-only -- never accepted as input.

    Usage::

        class UserBlueprint(Blueprint):
            first_name: str
            last_name: str

            @computed
            def full_name(self, instance) -> str:
                return f"{instance.first_name} {instance.last_name}"
    """
    return _ComputedMarker(func)


# ── Annotation Introspection ────────────────────────────────────────────

from typing import ForwardRef


def _is_blueprint_class(cls: Any) -> bool:
    """Check if cls is a Blueprint subclass (avoiding circular import)."""
    if isinstance(cls, str):
        return True
    if isinstance(cls, ForwardRef):
        return True
    # Walk MRO to find Blueprint without importing it
    if not isinstance(cls, type):
        return False
    for base in cls.__mro__:
        if base.__name__ == "Blueprint" and base.__module__.startswith("aquilia.blueprints"):
            if cls is not base:
                return True
    return False


def _extract_ref_name(cls: Any) -> str:
    """Extract string name from string or ForwardRef."""
    if isinstance(cls, ForwardRef):
        return cls.__forward_arg__
    return str(cls)


def _make_forward_ref(annotation_str: str) -> Any:
    """Create a ForwardRef, falling back to a string wrapper on SyntaxError.

    Python 3.10's ``ForwardRef.__init__`` calls ``compile()`` on the string
    and raises ``SyntaxError`` for anything that isn't valid Python expression
    syntax.  Python 3.12+ removed that restriction.  We catch the error so
    the caller always gets a usable sentinel back.
    """
    try:
        return ForwardRef(annotation_str)
    except SyntaxError:
        # Craft a ForwardRef with a sanitised placeholder so downstream
        # code that reads ``__forward_arg__`` still sees the original text.
        ref = ForwardRef("_")
        ref.__forward_arg__ = annotation_str
        return ref


def _safe_resolve_annotation(annotation_str: str, namespace: dict) -> Any:
    """
    Safely resolve a string annotation to a type without using eval().

    Handles common patterns:
        - Simple names: "str", "int", "MyBlueprint"
        - Generic subscripts: "list[str]", "Optional[int]", "dict[str, int]"
        - Union syntax: "str | None" (PEP 604)
        - Nested generics: "list[Optional[str]]"

    Security: This NEVER calls eval(). Only known type names from the
    namespace are resolved. Unknown names become ForwardRef.
    """

    annotation_str = annotation_str.strip()

    # Simple name lookup
    if annotation_str.isidentifier():
        result = namespace.get(annotation_str)
        if result is not None:
            return result
        return _make_forward_ref(annotation_str)

    # Handle PEP 604 union syntax: "X | Y | None"
    if "|" in annotation_str:
        parts = [p.strip() for p in annotation_str.split("|")]
        resolved_parts = []
        for part in parts:
            if part == "None":
                resolved_parts.append(type(None))
            else:
                resolved_parts.append(_safe_resolve_annotation(part, namespace))
        if len(resolved_parts) == 2 and type(None) in resolved_parts:
            non_none = [p for p in resolved_parts if p is not type(None)]
            return Optional[non_none[0]]  # noqa: UP045
        return Union[tuple(resolved_parts)]  # noqa: UP007

    # Handle generic subscript: "list[str]", "Optional[int]", "dict[str, int]"
    bracket_start = annotation_str.find("[")
    if bracket_start > 0 and annotation_str.endswith("]"):
        origin_str = annotation_str[:bracket_start].strip()
        args_str = annotation_str[bracket_start + 1 : -1].strip()

        origin = namespace.get(origin_str)
        if origin is None:
            return _make_forward_ref(annotation_str)

        # Parse args (handle nested brackets)
        args = _split_type_args(args_str)
        resolved_args = tuple(_safe_resolve_annotation(arg.strip(), namespace) for arg in args)

        if origin is Optional and len(resolved_args) == 1:
            return Optional[resolved_args[0]]  # noqa: UP045
        if origin is Union:
            return Union[resolved_args]  # noqa: UP007

        try:
            return origin[resolved_args] if len(resolved_args) > 1 else origin[resolved_args[0]]
        except (TypeError, KeyError):
            return _make_forward_ref(annotation_str)

    return _make_forward_ref(annotation_str)


def _split_type_args(args_str: str) -> list[str]:
    """Split type arguments respecting bracket nesting."""
    args = []
    depth = 0
    current = []
    for char in args_str:
        if char == "[":
            depth += 1
            current.append(char)
        elif char == "]":
            depth -= 1
            current.append(char)
        elif char == "," and depth == 0:
            args.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if current:
        args.append("".join(current).strip())
    return args


def _unwrap_optional(annotation: Any) -> tuple[Any, bool]:
    """
    Unwrap Optional[T] or T | None → (T, is_optional).

    Handles:
        - typing.Optional[T] → (T, True)
        - T | None (PEP 604) → (T, True)
        - T → (T, False)
    """
    origin = get_origin(annotation)

    # Union types: Optional[T] is Union[T, None]
    if origin is Union:
        args = get_args(annotation)
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1 and type(None) in args:
            return non_none[0], True
        # Multi-type union without None -- not optional
        if type(None) not in args:
            return annotation, False
        # Multi-type union with None -- take first non-None
        return non_none[0] if non_none else annotation, True

    # PEP 604: types.UnionType (Python 3.10+)
    if hasattr(types, "UnionType") and isinstance(annotation, types.UnionType):
        args = get_args(annotation)
        non_none = [a for a in args if a is not type(None)]
        if type(None) in args and len(non_none) == 1:
            return non_none[0], True
        if type(None) not in args:
            return annotation, False
        return non_none[0] if non_none else annotation, True

    return annotation, False


def _resolve_list_child(annotation: Any) -> tuple[bool, Any]:
    """
    Check if annotation is list[T] and extract T.

    Returns:
        (is_list, child_type) -- child_type is None if not parameterised.
    """
    origin = get_origin(annotation)
    if origin is list:
        args = get_args(annotation)
        if args:
            return True, args[0]
        return True, None
    return False, None


def _build_facet_from_annotation(
    name: str,
    annotation: Any,
    field_spec: Field | None,
    class_default: Any,
) -> Facet | None:
    """
    Build a Facet instance from a type annotation and optional Field spec.

    Args:
        name:          Field name.
        annotation:    The resolved type annotation.
        field_spec:    Field() descriptor (if provided as default value).
        class_default: The raw class-level default (may be Field, UNSET, or a value).

    Returns:
        A configured Facet instance, or None if unrecognised.
    """
    # Unwrap Optional
    inner_type, is_optional = _unwrap_optional(annotation)

    # Collect kwargs from Field descriptor
    kwargs: dict[str, Any] = {}

    if field_spec is not None:
        if field_spec.source is not None:
            kwargs["source"] = field_spec.source
        if field_spec.read_only:
            kwargs["read_only"] = True
        if field_spec.write_only:
            kwargs["write_only"] = True
        if field_spec.allow_null or is_optional:
            kwargs["allow_null"] = True
        if field_spec.allow_blank:
            kwargs["allow_blank"] = True
        if field_spec.label is not None:
            kwargs["label"] = field_spec.label
        if field_spec.help_text is not None:
            kwargs["help_text"] = field_spec.help_text
        if field_spec.validators:
            kwargs["validators"] = field_spec.validators

        # Default handling
        if field_spec.default is not UNSET:
            kwargs["default"] = field_spec.default
        elif field_spec.default_factory is not None:
            kwargs["default"] = field_spec.default_factory

        # Required override
        if field_spec.required is not None:
            kwargs["required"] = field_spec.required
        elif is_optional and "default" not in kwargs:
            kwargs["required"] = False
    else:
        # No Field() -- derive from annotation + raw default
        if is_optional:
            kwargs["allow_null"] = True
            kwargs["required"] = False
        if class_default is not UNSET and not isinstance(class_default, Field):
            kwargs["default"] = class_default

    # ── Choices override ─────────────────────────────────────────────
    if field_spec is not None and field_spec.choices is not None:
        choice_kwargs = dict(kwargs)
        return ChoiceFacet(choices=field_spec.choices, **choice_kwargs)

    # ── Nested Blueprint ─────────────────────────────────────────────
    if _is_blueprint_class(inner_type):
        nested_kwargs = {k: v for k, v in kwargs.items() if k not in ("allow_blank",)}
        if isinstance(inner_type, (str, ForwardRef)):
            ref_name = _extract_ref_name(inner_type)
            return LazyBlueprintFacet(ref_name, many=False, **nested_kwargs)
        return NestedBlueprintFacet(inner_type, many=False, **nested_kwargs)

    # ── Polymorphic / Union Nesting ──────────────────────────────────
    if get_origin(inner_type) is Union:
        union_args = get_args(inner_type)
        choices = []
        for arg in union_args:
            if _is_blueprint_class(arg):
                if isinstance(arg, (str, ForwardRef)):
                    ref_name = _extract_ref_name(arg)
                    choices.append(LazyBlueprintFacet(ref_name, many=False))
                else:
                    choices.append(NestedBlueprintFacet(arg, many=False))
            else:
                arg_facet_cls = ANNOTATION_TO_FACET.get(arg)
                if arg_facet_cls is not None:
                    choices.append(arg_facet_cls())

        if choices:
            poly_kwargs = {k: v for k, v in kwargs.items() if k not in ("allow_blank", "min_length", "max_length")}
            return PolymorphicFacet(choices=choices, **poly_kwargs)

    # ── list[T] ──────────────────────────────────────────────────────
    is_list, child_type = _resolve_list_child(inner_type)
    if is_list:
        list_kwargs: dict[str, Any] = {}
        for k in (
            "allow_null",
            "required",
            "read_only",
            "write_only",
            "default",
            "source",
            "label",
            "help_text",
            "validators",
        ):
            if k in kwargs:
                list_kwargs[k] = kwargs[k]

        if field_spec is not None:
            if field_spec.min_items is not None:
                list_kwargs["min_items"] = field_spec.min_items
            if field_spec.max_items is not None:
                list_kwargs["max_items"] = field_spec.max_items

        # Build child facet recursively
        child_facet = None
        if child_type is not None:
            child_name = f"{name or '<unbound>'}[*]"
            child_facet = _build_facet_from_annotation(
                name=child_name,
                annotation=child_type,
                field_spec=None,
                class_default=UNSET,
            )

        return ListFacet(child=child_facet, **list_kwargs)

    # ── dict ─────────────────────────────────────────────────────────
    if inner_type is dict or get_origin(inner_type) is dict:
        dict_kwargs = {k: v for k, v in kwargs.items() if k not in ("allow_blank", "min_length", "max_length")}

        args = get_args(inner_type)
        value_facet = None
        if len(args) == 2:
            val_type = args[1]
            if _is_blueprint_class(val_type):
                if isinstance(val_type, (str, ForwardRef)):
                    ref_name = _extract_ref_name(val_type)
                    value_facet = LazyBlueprintFacet(ref_name, many=False)
                else:
                    value_facet = NestedBlueprintFacet(val_type, many=False)
            else:
                child_facet_cls = ANNOTATION_TO_FACET.get(val_type)
                if child_facet_cls is not None:
                    value_facet = child_facet_cls()

        return DictFacet(value_facet=value_facet, **dict_kwargs)

    # ── Scalar types ─────────────────────────────────────────────────
    facet_cls = ANNOTATION_TO_FACET.get(inner_type)
    if facet_cls is None:
        # Unknown type -- use generic Facet
        return Facet(**{k: v for k, v in kwargs.items() if k not in ("min_length", "max_length", "allow_blank")})

    # Build type-specific kwargs
    type_kwargs = dict(kwargs)

    if facet_cls in (TextFacet, EmailFacet, URLFacet):
        if field_spec is not None:
            if field_spec.min_length is not None:
                type_kwargs["min_length"] = field_spec.min_length
            if field_spec.max_length is not None:
                type_kwargs["max_length"] = field_spec.max_length
            if field_spec.pattern is not None:
                type_kwargs["pattern"] = field_spec.pattern
    elif facet_cls in (IntFacet, FloatFacet):
        if field_spec is not None:
            min_val = (
                field_spec.ge
                if field_spec.ge is not None
                else (field_spec.gt + 1 if field_spec.gt is not None and facet_cls is IntFacet else field_spec.gt)
            )
            max_val = (
                field_spec.le
                if field_spec.le is not None
                else (field_spec.lt - 1 if field_spec.lt is not None and facet_cls is IntFacet else field_spec.lt)
            )
            if min_val is not None:
                type_kwargs["min_value"] = min_val
            if max_val is not None:
                type_kwargs["max_value"] = max_val
        # Remove text-specific kwargs
        type_kwargs.pop("allow_blank", None)
        type_kwargs.pop("min_length", None)
        type_kwargs.pop("max_length", None)
    elif facet_cls is DecimalFacet:
        if field_spec is not None:
            if field_spec.max_digits is not None:
                type_kwargs["max_digits"] = field_spec.max_digits
            if field_spec.decimal_places is not None:
                type_kwargs["decimal_places"] = field_spec.decimal_places
            if field_spec.ge is not None:
                type_kwargs["min_value"] = field_spec.ge
            if field_spec.le is not None:
                type_kwargs["max_value"] = field_spec.le
        type_kwargs.pop("allow_blank", None)
        type_kwargs.pop("min_length", None)
        type_kwargs.pop("max_length", None)
    elif facet_cls is BoolFacet:
        type_kwargs.pop("allow_blank", None)
        type_kwargs.pop("min_length", None)
        type_kwargs.pop("max_length", None)
    else:
        # Date/Time/UUID/Duration -- remove text-specific kwargs
        type_kwargs.pop("allow_blank", None)
        type_kwargs.pop("min_length", None)
        type_kwargs.pop("max_length", None)

    return facet_cls(**type_kwargs)


def _build_constraint_validators(field_spec: Field) -> list[Callable]:
    """Build extra validators from Field gt/lt constraints (for float)."""
    extra = []
    if field_spec.gt is not None:
        bound = field_spec.gt

        def _gt_validator(v, _b=bound):
            if v <= _b:
                from aquilia.faults.domains import FieldValidationFault

                raise FieldValidationFault(
                    field_name="value",
                    message=f"Must be greater than {_b}",
                )

        extra.append(_gt_validator)

    if field_spec.lt is not None:
        bound = field_spec.lt

        def _lt_validator(v, _b=bound):
            if v >= _b:
                from aquilia.faults.domains import FieldValidationFault

                raise FieldValidationFault(
                    field_name="value",
                    message=f"Must be less than {_b}",
                )

        extra.append(_lt_validator)

    return extra


def introspect_annotations(
    cls: type,
    namespace: dict[str, Any],
    bases: tuple,
    *,
    include_explicit_facets: bool = False,
) -> dict[str, Facet]:
    """
    Introspect a Blueprint class's type annotations and produce Facet instances.

    This is called from BlueprintMeta.__new__ after explicit Facets have been
    collected.  Annotation-derived facets are returned in declaration order.

    Handles PEP 563 (from __future__ import annotations) by resolving
    string annotations back to actual types using the defining module's
    globals.

    Rules:
        1. Skip annotations that already have an explicit Facet in namespace.
        2. ``Field()`` as a default → constraint descriptor.
        3. Plain default value → ``Facet(default=value)``.
        4. ``Optional[T]`` / ``T | None`` → ``allow_null=True, required=False``.
        5. ``list[T]`` → ``ListFacet(child=T_facet)``.
        6. ``SomeBlueprint`` → ``NestedBlueprintFacet(SomeBlueprint)``.
        7. ``@computed`` methods → ``Computed`` facets.

    Args:
        cls:       The class being created (may be None during __new__).
        namespace: The class namespace dict.
        bases:     The base classes.

    Returns:
        Dict of field_name → Facet, in declaration order.
    """
    result: dict[str, Facet] = {}

    # Gather annotations from the class itself (not inherited)
    raw_annotations = namespace.get("__annotations__", {})
    if not raw_annotations:
        raw_annotations = getattr(cls, "__annotations__", {}) if cls is not None else {}

    if not raw_annotations:
        # Still check for @computed markers
        for attr_name, attr_value in list(namespace.items()):
            if isinstance(attr_value, _ComputedMarker):
                facet = attr_value.to_facet()
                result[attr_name] = facet
                namespace[attr_name] = facet
        return result

    class AutoResolveMapping(dict):
        """Auto-wrap unknown names as ForwardRefs during eval()."""

        def __missing__(self, key: str) -> Any:
            return ForwardRef(key)

    # Build a resolution namespace for evaluating string annotations.
    # We need to capture the defining module's globals for PEP 563 resolution.
    resolve_ns = AutoResolveMapping()

    # Import standard types that annotations commonly reference
    import builtins

    resolve_ns.update(vars(builtins))
    resolve_ns["Optional"] = Optional
    resolve_ns["Union"] = Union
    resolve_ns["List"] = list
    resolve_ns["Dict"] = dict
    resolve_ns["Set"] = set
    resolve_ns["Tuple"] = tuple
    resolve_ns["FrozenSet"] = frozenset
    resolve_ns["Sequence"] = Sequence
    resolve_ns["Any"] = Any
    resolve_ns["Type"] = type

    # Standard library types
    resolve_ns["datetime"] = datetime
    resolve_ns["date"] = date
    resolve_ns["time"] = time
    resolve_ns["timedelta"] = timedelta
    resolve_ns["Decimal"] = Decimal
    resolve_ns["UUID"] = uuid.UUID
    resolve_ns["uuid"] = uuid

    # Include the class namespace itself (for forward references to other Blueprints)
    resolve_ns.update(namespace)

    # Include parent class namespaces
    for base in bases:
        if hasattr(base, "__module__"):
            mod = sys.modules.get(base.__module__)
            if mod is not None:
                resolve_ns.update(vars(mod))

    # Try to get the defining module's globals
    # Walk the call stack to find the frame where the class was defined
    frame = sys._getframe(0)
    caller_globals = {}
    try:
        # Walk up to find the module-level frame
        f = frame
        while f is not None:
            if f.f_locals is not namespace:
                caller_globals.update(f.f_globals)
            f = f.f_back
    except (AttributeError, ValueError):
        pass
    finally:
        del frame

    resolve_ns.update(caller_globals)

    # Resolve string annotations to actual types
    resolved_annotations: dict[str, Any] = {}
    for field_name, annotation in raw_annotations.items():
        if isinstance(annotation, str):
            # Security: Use safe resolution instead of eval()
            # First try to find the type in our known namespace
            resolved = resolve_ns.get(annotation)
            if resolved is not None:
                resolved_annotations[field_name] = resolved
            else:
                # Try safe AST-based resolution for simple expressions
                # like "list[str]", "Optional[int]", etc.
                try:
                    resolved = _safe_resolve_annotation(annotation, resolve_ns)
                    resolved_annotations[field_name] = resolved
                except Exception:
                    # Fall back to ForwardRef for unresolvable annotations
                    resolved_annotations[field_name] = ForwardRef(annotation)
        else:
            resolved_annotations[field_name] = annotation

    # Collect @computed markers from namespace
    for attr_name, attr_value in list(namespace.items()):
        if isinstance(attr_value, _ComputedMarker):
            facet = attr_value.to_facet()
            result[attr_name] = facet
            # Remove the marker from namespace so it doesn't interfere
            namespace[attr_name] = facet

    for field_name, annotation in resolved_annotations.items():
        # Skip private/dunder
        if field_name.startswith("_"):
            continue

        # Skip if there's already an explicit Facet declared unless
        # the caller requested overlap introspection for deterministic
        # annotation+facet merge handling.
        if not include_explicit_facets and field_name in namespace and isinstance(namespace[field_name], Facet):
            continue

        # Skip if it's a classmethod, staticmethod, property, or callable
        ns_value = namespace.get(field_name, UNSET)
        if isinstance(ns_value, (classmethod, staticmethod, property)):
            continue
        if isinstance(ns_value, _ComputedMarker):
            continue  # Already handled above

        # Determine Field spec and default
        field_spec: Field | None = None
        class_default: Any = UNSET

        if isinstance(ns_value, Field):
            field_spec = ns_value
        elif ns_value is not UNSET:
            class_default = ns_value

        # Build the facet
        facet = _build_facet_from_annotation(
            field_name,
            annotation,
            field_spec,
            class_default,
        )

        if facet is not None:
            # Inject gt/lt validators for float types
            if field_spec is not None:
                extra_validators = _build_constraint_validators(field_spec)
                if extra_validators:
                    facet.validators.extend(extra_validators)

            result[field_name] = facet

    return result

"""
Aquilia VectorDB fields -- descriptor-based field declarations for VectorModel.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Callable, Sequence
from typing import Any

__all__ = [
    "UNSET",
    "VectorFieldValidationError",
    "BaseVectorField",
    "MetaField",
    "MetaText",
    "MetaInt",
    "MetaFloat",
    "MetaBool",
    "MetaChoice",
    "MetaJSON",
    "DocumentField",
    "EmbeddingField",
    "KeyField",
]


class _Unset:
    """Sentinel distinguishing 'no default configured' from a real default of ``None``."""

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


class VectorFieldValidationError(ValueError):
    """Raised by ``field.validate()`` on a bad value. Converted to ``VectorFieldValidationFault`` by callers."""

    def __init__(self, field_name: str, reason: str, value: Any = None):
        self.field_name = field_name
        self.reason = reason
        self.value = value
        super().__init__(f"Field '{field_name}': {reason}")


class BaseVectorField:
    """
    Base descriptor for all vectordb field declarations.

    A real data descriptor: instance access reads/writes
    ``instance.__dict__[attr_name]``; class access returns the field object
    itself (mirrors ``aquilia.models.fields_module.Field``).
    """

    _creation_counter = 0

    def __init__(self) -> None:
        self.name: str = ""
        self.attr_name: str = ""
        self.model: type | None = None
        self._order = BaseVectorField._creation_counter
        BaseVectorField._creation_counter += 1

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name
        self.attr_name = name

    def __get__(self, instance: Any, owner: type | None = None) -> Any:
        if instance is None:
            return self
        return instance.__dict__.get(self.attr_name)

    def __set__(self, instance: Any, value: Any) -> None:
        instance.__dict__[self.attr_name] = value

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"

    def clone(self) -> BaseVectorField:
        """Return a shallow, independent copy of this field (for inheritance/reuse)."""
        new = copy.copy(self)
        return new

    def validate(self, value: Any) -> Any:
        """Validate and coerce *value*. Override in subclasses."""
        return value


class MetaField(BaseVectorField):
    """Base class for scalar metadata fields stored in an Elips record's ``meta`` dict."""

    def __init__(
        self,
        *,
        null: bool = False,
        default: Any = UNSET,
        indexed: bool = False,
        choices: Sequence[tuple[Any, str]] | None = None,
        db_column: str | None = None,
        validators: list[Callable] | None = None,
        help_text: str = "",
        verbose_name: str | None = None,
    ) -> None:
        super().__init__()
        self.null = null
        self.default = default
        self.indexed = indexed
        self.choices = choices
        self.db_column = db_column
        self.validators = validators or []
        self.help_text = help_text
        self.verbose_name = verbose_name

    def __set_name__(self, owner: type, name: str) -> None:
        super().__set_name__(owner, name)
        if self.verbose_name is None:
            self.verbose_name = name.replace("_", " ").title()

    @property
    def meta_key(self) -> str:
        """Key used inside the Elips record's ``meta`` dict."""
        return self.db_column or self.name

    def has_default(self) -> bool:
        return self.default is not UNSET

    def get_default(self) -> Any:
        if self.default is UNSET:
            return None
        if callable(self.default):
            return self.default()
        return copy.deepcopy(self.default)

    def validate(self, value: Any) -> Any:
        if value is None:
            if not self.null:
                raise VectorFieldValidationError(self.name, "Cannot be null")
            return None

        if self.choices:
            valid_values = [c[0] for c in self.choices]
            if value not in valid_values:
                raise VectorFieldValidationError(
                    self.name,
                    f"Invalid choice {value!r}. Must be one of: {valid_values}",
                    value,
                )

        for validator in self.validators:
            validator(value)

        return value

    def to_meta(self, value: Any) -> Any:
        """Convert a Python value to an Elips-safe meta primitive (bool/int/float/str)."""
        return value

    def from_meta(self, value: Any) -> Any:
        """Convert a raw meta primitive back into the field's Python representation."""
        return value


class MetaText(MetaField):
    """Text metadata field."""

    def __init__(self, *, max_length: int | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.max_length = max_length

    def validate(self, value: Any) -> Any:
        value = super().validate(value)
        if value is None:
            return None
        value = str(value)
        if self.max_length is not None and len(value) > self.max_length:
            raise VectorFieldValidationError(
                self.name,
                f"Value exceeds max_length={self.max_length}",
                value,
            )
        return value

    def to_meta(self, value: Any) -> Any:
        return None if value is None else str(value)

    def from_meta(self, value: Any) -> Any:
        return None if value is None else str(value)


class MetaInt(MetaField):
    """Integer metadata field."""

    def validate(self, value: Any) -> Any:
        value = super().validate(value)
        if value is None:
            return None
        return int(value)

    def to_meta(self, value: Any) -> Any:
        return None if value is None else int(value)

    def from_meta(self, value: Any) -> Any:
        return None if value is None else int(value)


class MetaFloat(MetaField):
    """Float metadata field."""

    def validate(self, value: Any) -> Any:
        value = super().validate(value)
        if value is None:
            return None
        return float(value)

    def to_meta(self, value: Any) -> Any:
        return None if value is None else float(value)

    def from_meta(self, value: Any) -> Any:
        return None if value is None else float(value)


class MetaBool(MetaField):
    """Boolean metadata field."""

    def validate(self, value: Any) -> Any:
        value = super().validate(value)
        if value is None:
            return None
        return bool(value)

    def to_meta(self, value: Any) -> Any:
        return None if value is None else bool(value)

    def from_meta(self, value: Any) -> Any:
        return None if value is None else bool(value)


class MetaChoice(MetaText):
    """Text metadata field with a required set of ``choices``."""

    def __init__(self, choices: Sequence[tuple[Any, str]], **kwargs: Any) -> None:
        if not choices:
            raise VectorFieldValidationError("<MetaChoice>", "choices is required and cannot be empty")
        super().__init__(choices=choices, **kwargs)


class MetaJSON(MetaField):
    """JSON-serializable metadata field, stored as a string in Elips."""

    def to_meta(self, value: Any) -> Any:
        return None if value is None else json.dumps(value)

    def from_meta(self, value: Any) -> Any:
        return None if value is None else json.loads(value)


class DocumentField(MetaField):
    """
    Document text field.

    Stored as Elips document text (``arena.write(text=...)`` /
    ``elips.DocumentAttachment``), never included in the ``meta`` payload.
    """

    def __init__(self, *, mime_type: str = "text/plain", null: bool = True, **kwargs: Any) -> None:
        super().__init__(null=null, **kwargs)
        self.mime_type = mime_type

    def validate(self, value: Any) -> Any:
        if value is None:
            if not self.null:
                raise VectorFieldValidationError(self.name, "Cannot be null")
            return None
        return str(value)


class EmbeddingField(BaseVectorField):
    """Embedding vector field -- a ``list[float]`` written as the Elips record's vector."""

    def __init__(
        self,
        *,
        dimension: int | None = None,
        metric: str | None = None,
        auto_from: str | None = None,
        embedder: Callable | None = None,
    ) -> None:
        super().__init__()
        self.dimension = dimension
        self.metric = metric
        self.auto_from = auto_from
        self.embedder = embedder

    def validate(self, value: Any) -> Any:
        if value is None:
            return None
        if not isinstance(value, (list, tuple)):
            raise VectorFieldValidationError(self.name, "Embedding must be a list of floats", value)
        try:
            floats = [float(v) for v in value]
        except (TypeError, ValueError) as exc:
            raise VectorFieldValidationError(self.name, "Embedding must be a list of floats", value) from exc
        if self.dimension is not None and len(floats) != self.dimension:
            raise VectorFieldValidationError(
                self.name,
                f"Embedding dimension mismatch: expected {self.dimension}, got {len(floats)}",
                value,
            )
        return floats


class KeyField(BaseVectorField):
    """Primary key field -- the Elips-assigned (or user-supplied) UUID key string."""

    def validate(self, value: Any) -> Any:
        if value is None:
            return None
        return str(value)

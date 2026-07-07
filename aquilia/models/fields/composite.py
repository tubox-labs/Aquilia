"""
Aquilia Composite Fields -- group multiple primitives into one logical attribute.

Provides:
- CompositeField: Groups multiple primitive fields with serialization
- CompositePrimaryKey: Composite primary key definition
- CompositeAttribute: Read/write descriptor for composite access

Usage:
    class Address(CompositeField):
        street = CharField(max_length=200)
        city = CharField(max_length=100)
        zip_code = CharField(max_length=20)

    class Order(Model):
        shipping_address = Address(prefix="ship")
        # Creates columns: ship_street, ship_city, ship_zip_code
"""

from __future__ import annotations

import json
from typing import Any

from ..fields_module import Field, FieldValidationError

__all__ = [
    "CompositeField",
    "CompositePrimaryKey",
    "CompositeAttribute",
]


class CompositeAttribute:
    """
    Descriptor that provides read/write access to a group of columns
    as a single Python dict/namedtuple.

    Usage:
    ```
        class Order(Model):
            _ship_street = CharField(max_length=200)
            _ship_city = CharField(max_length=100)

            shipping = CompositeAttribute(
                fields=["_ship_street", "_ship_city"],
                keys=["street", "city"],
            )

        order = Order(...)
        order.shipping  # → {"street": "123 Main", "city": "NYC"}
        order.shipping = {"street": "456 Oak", "city": "LA"}
    ```
    """

    def __init__(
        self,
        *,
        fields: list[str],
        keys: list[str] | None = None,
    ):
        """
        Args:
            fields: Names of the underlying model attributes (fields)
                that back this composite, in order.
            keys: Dict keys exposed to callers, in the same order as
                ``fields``. Defaults to ``fields`` itself (dict keys ==
                attribute names) when omitted.
        """
        self.fields = fields
        self.keys = keys or fields

    def __set_name__(self, owner: type, name: str) -> None:
        """Record the attribute name this descriptor is bound to on the owning class."""
        self.attr_name = name

    def __get__(self, instance, owner=None):
        """
        Read the composite value.

        Class-level access (``Model.attr``) returns the descriptor
        itself. Instance-level access returns a ``dict`` built by
        reading each attribute named in ``self.fields`` off ``instance``
        (missing attributes default to ``None``) and pairing the results
        with ``self.keys``.

        If ``fields`` and ``keys`` have different lengths, the pairing
        (``zip(..., strict=False)``) silently truncates to the shorter one.
        """
        if instance is None:
            return self
        result = {}
        for field_name, key in zip(self.fields, self.keys, strict=False):
            result[key] = getattr(instance, field_name, None)
        return result

    def __set__(self, instance, value):
        """
        Write the composite value.

        Accepts either:
            - a ``dict``: only keys present in ``self.keys`` are applied
              (other keys in ``value`` are ignored; keys of ``self.keys``
              missing from ``value`` leave the corresponding attribute
              untouched).
            - a ``list``/``tuple``: values are assigned positionally to
              ``self.fields`` in order (``zip(..., strict=False)``, so a
              shorter sequence leaves the remaining fields untouched and
              a longer one has its extra items ignored).

        Any other type is silently ignored -- no assignment, no error.
        """
        if isinstance(value, dict):
            for field_name, key in zip(self.fields, self.keys, strict=False):
                if key in value:
                    setattr(instance, field_name, value[key])
        elif isinstance(value, (list, tuple)):
            for field_name, val in zip(self.fields, value, strict=False):
                setattr(instance, field_name, val)


class CompositeField(Field):
    """
    Groups multiple primitive fields into one logical attribute.

    The sub-fields are stored as individual columns but accessed
    as a single dict-like attribute on the model.

    Serialization strategy: JSON (stored as TEXT column for simplicity)
    or expanded columns (one per sub-field, with a prefix).

    Args:
        schema: Dict mapping sub-field names to Field instances
        prefix: Column name prefix for expanded storage
        strategy: "json" (single TEXT column) or "expand" (multiple columns)

    Usage (JSON strategy -- single column):
    ```
        coordinates = CompositeField(
            schema={"lat": FloatField(), "lng": FloatField()},
            strategy="json",
        )

    Usage (Expanded strategy -- multiple columns):
        address = CompositeField(
            schema={
                "street": CharField(max_length=200),
                "city": CharField(max_length=100),
                "zip": CharField(max_length=20),
            },
            prefix="addr",
            strategy="expand",
        )
        ```
    """

    _field_type = "COMPOSITE"

    def __init__(
        self,
        *,
        schema: dict[str, Field],
        prefix: str = "",
        strategy: str = "json",
        **kwargs,
    ):
        """
        Args:
            schema: Mapping of sub-field name to ``Field`` instance
                describing the shape of this composite.
            prefix: Column name prefix used by the ``"expand"`` strategy.
                Ignored by the ``"json"`` strategy.
            strategy: ``"json"`` to serialize the whole dict into a single
                TEXT/JSONB column, or ``"expand"`` to store each sub-field
                as its own column (prefixed with ``prefix``).
            **kwargs: Passed through to ``Field.__init__`` (``null``,
                ``default``, etc.).
        """
        self.schema = schema
        self.prefix = prefix
        self.strategy = strategy
        super().__init__(**kwargs)

    def validate(self, value: Any) -> Any:
        """
        Validate a composite value.

        Args:
            value: Must be a ``dict`` (or ``None``).

        Returns:
            A new dict with each sub-field's value run through that
            sub-field's own ``validate()`` (so per-key validators/type
            coercion apply).

        Raises:
            FieldValidationError: If ``value`` is ``None`` and the field
                isn't nullable, or if ``value`` is not a ``dict``.

        Keys declared in ``self.schema`` but absent from ``value`` are
        looked up via ``value.get(key)`` (yielding ``None``), so an
        incomplete dict doesn't raise here -- each sub-field's own
        ``validate()`` decides whether ``None`` is acceptable for it
        (based on that sub-field's ``null``/``blank``).
        """
        if value is None:
            if self.null:
                return None
            raise FieldValidationError(self.name, "Cannot be null")
        if not isinstance(value, dict):
            raise FieldValidationError(self.name, f"Expected dict, got {type(value).__name__}")
        # Validate each sub-field
        cleaned = {}
        for key, field in self.schema.items():
            sub_val = value.get(key)
            cleaned[key] = field.validate(sub_val)
        return cleaned

    def to_python(self, value: Any) -> Any:
        """
        Convert a raw database value back to a Python dict.

        If ``value`` is a JSON-encoded string, parse it; if parsing
        fails, return the raw string unchanged rather than raising.
        Non-string values (already a dict, or ``None``) pass through
        unchanged.
        """
        if value is None:
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    def to_db(self, value: Any) -> Any:
        """
        Convert a Python dict to its database-ready form.

        Under the ``"json"`` strategy, serializes ``value`` to a JSON
        string via ``json.dumps``. Under ``"expand"`` (or any other
        strategy), returns ``value`` unchanged -- expanded storage is
        handled by the individual sub-field columns, not by this method.
        ``None`` passes through unchanged.
        """
        if value is None:
            return None
        if self.strategy == "json":
            return json.dumps(value)
        return value

    def sql_type(self, dialect: str = "sqlite") -> str:
        """
        Return the SQL column type for this field's own column.

        Only meaningful for the ``"json"`` strategy, where the whole
        composite lives in one column: ``JSONB`` on PostgreSQL, ``TEXT``
        elsewhere. Under the ``"expand"`` strategy this field doesn't
        itself produce a column (each sub-field does); the ``"TEXT"``
        fallback returned here is not meant to be used to create a
        column in that case -- callers using expand storage should
        generate columns from ``self.schema`` directly.
        """
        if self.strategy == "json":
            if dialect == "postgresql":
                return "JSONB"
            return "TEXT"
        # For expanded strategy, this field itself doesn't produce a column
        return "TEXT"

    def deconstruct(self) -> dict[str, Any]:
        """
        Serialize this field's definition for migrations.

        Extends the base ``deconstruct()`` output with ``strategy``,
        ``prefix``, and a recursively deconstructed ``schema`` (each
        sub-field's own ``deconstruct()`` output), so migration diffing
        can detect changes to the composite's shape.
        """
        d = super().deconstruct()
        d["strategy"] = self.strategy
        d["prefix"] = self.prefix
        d["schema"] = {k: v.deconstruct() for k, v in self.schema.items()}
        return d


class CompositePrimaryKey:
    """
    Declares a composite primary key across multiple fields.

    This is not a Field itself -- it's a Meta-level declaration.

    Usage:
        class OrderItem(Model):
            order_id = IntegerField()
            product_id = IntegerField()

            class Meta:
                primary_key = CompositePrimaryKey(fields=["order_id", "product_id"])

    The metaclass reads this from Meta and generates:
        PRIMARY KEY ("order_id", "product_id")
    as a table-level constraint instead of a column-level PK.
    """

    def __init__(self, *, fields: list[str]):
        """
        Args:
            fields: Column names participating in the composite primary
                key, in the order they should appear in the
                ``PRIMARY KEY (...)`` clause. Must contain at least 2
                names -- a single-column PK should use that field's own
                ``primary_key=True`` instead.

        Raises:
            ConfigInvalidFault: If fewer than 2 fields are supplied.
        """
        if len(fields) < 2:
            from aquilia.faults.domains import ConfigInvalidFault

            raise ConfigInvalidFault(
                key="composite_primary_key.fields",
                reason="CompositePrimaryKey requires at least 2 fields",
            )
        self.fields = fields

    def sql(self) -> str:
        """
        Generate the SQL ``PRIMARY KEY`` table constraint.

        Each field name is double-quote-identifier-quoted, e.g.
        ``PRIMARY KEY ("order_id", "product_id")``.
        """
        cols = ", ".join(f'"{f}"' for f in self.fields)
        return f"PRIMARY KEY ({cols})"

    def deconstruct(self) -> dict[str, Any]:
        """Serialize for migrations as ``{"type": "CompositePrimaryKey", "fields": [...]}``."""
        return {"type": "CompositePrimaryKey", "fields": self.fields}

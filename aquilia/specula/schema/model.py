"""
ORM Model → JSON Schema bridge.

Walks ``Model._fields`` (the registered Field instances) and maps each Field
subclass to a JSON Schema 3.1.0 fragment.
"""

from __future__ import annotations

import logging
from typing import Any

from aquilia.models.fields import (
    ArrayField,
    AutoField,
    BigAutoField,
    BigIntegerField,
    BinaryField,
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    DecimalField,
    DurationField,
    EmailField,
    FileField,
    FloatField,
    ForeignKey,
    GenericIPAddressField,
    ImageField,
    IntegerField,
    JSONField,
    ManyToManyField,
    OneToOneField,
    PositiveIntegerField,
    SlugField,
    SmallIntegerField,
    TextField,
    TimeField,
    URLField,
    UUIDField,
)

from ..faults import SchemaResolutionFault

logger = logging.getLogger("aquilia.specula.model")

#: Canonical Field → JSON Schema mapping. Order matters — subclasses first
#: (e.g. BigAutoField before AutoField, EmailField before CharField).
FIELD_SCHEMA_MAP: list[tuple[type, dict[str, Any]]] = [
    (BigAutoField, {"type": "integer", "format": "int64", "readOnly": True}),
    (AutoField, {"type": "integer", "readOnly": True}),
    (EmailField, {"type": "string", "format": "email"}),
    (URLField, {"type": "string", "format": "uri"}),
    (SlugField, {"type": "string", "pattern": r"^[-a-zA-Z0-9_]+$"}),
    (UUIDField, {"type": "string", "format": "uuid"}),
    (GenericIPAddressField, {"type": "string", "format": "ip"}),
    (TextField, {"type": "string"}),
    (CharField, {"type": "string"}),
    (BigIntegerField, {"type": "integer", "format": "int64"}),
    (SmallIntegerField, {"type": "integer", "format": "int16"}),
    (PositiveIntegerField, {"type": "integer", "minimum": 0}),
    (IntegerField, {"type": "integer", "format": "int32"}),
    (FloatField, {"type": "number", "format": "double"}),
    (DecimalField, {"type": "string", "format": "decimal"}),
    (BooleanField, {"type": "boolean"}),
    (DateTimeField, {"type": "string", "format": "date-time"}),
    (DateField, {"type": "string", "format": "date"}),
    (TimeField, {"type": "string", "format": "time"}),
    (DurationField, {"type": "string", "format": "duration"}),
    (JSONField, {"type": "object", "additionalProperties": True}),
    (BinaryField, {"type": "string", "format": "binary"}),
    (ImageField, {"type": "string", "format": "uri"}),
    (FileField, {"type": "string", "format": "uri"}),
    (ArrayField, {"type": "array"}),
]


def _field_schema(field: Any, *, include_relations: bool) -> dict[str, Any] | None:
    """Map one Field instance to a JSON Schema fragment (None = skip)."""
    # Relations first
    if isinstance(field, ManyToManyField):
        related = getattr(field, "to", None) or getattr(field, "related_model", None)
        if include_relations and isinstance(related, type):
            return {"type": "array", "items": {"$ref": f"#/components/schemas/{related.__name__}"}}
        return {"type": "array", "items": {"type": "integer"}}

    if isinstance(field, (ForeignKey, OneToOneField)):
        related = getattr(field, "to", None) or getattr(field, "related_model", None)
        if include_relations and isinstance(related, type):
            return {"$ref": f"#/components/schemas/{related.__name__}"}
        return {"type": "integer", "description": f"Foreign key to {getattr(related, '__name__', 'related')}"}

    for field_cls, fragment in FIELD_SCHEMA_MAP:
        if isinstance(field, field_cls):
            return dict(fragment)

    logger.debug("Specula: unmapped model field %s mapped to string", type(field).__name__)
    return {"type": "string"}


def model_to_schema(
    model_cls: type,
    *,
    include_relations: bool = False,
    read_only_pk: bool = True,
    exclude_fields: list[str] | None = None,
) -> dict[str, Any]:
    """
    Generate an OpenAPI 3.1.0 schema dict for an Aquilia ORM Model.

    - Iterates ``model_cls._fields`` (the registered Field instances).
    - Maps each Field subclass via :data:`FIELD_SCHEMA_MAP`.
    - Applies field-level constraints: ``max_length``, ``choices``, ``null``.
    - Auto-marks pk/auto fields as ``readOnly`` when ``read_only_pk=True``.
    - ``null=True`` fields use ``oneOf`` with ``{"type": "null"}`` (3.1.0).

    Raises:
        SchemaResolutionFault: If the class has no ``_fields`` registry.
    """
    fields = getattr(model_cls, "_fields", None)
    if not isinstance(fields, dict):
        raise SchemaResolutionFault(
            f"'{model_cls.__name__}' is not an Aquilia Model (no _fields registry)",
            detail={"model": model_cls.__name__},
        )

    excluded = set(exclude_fields or [])
    properties: dict[str, Any] = {}
    required: list[str] = []

    for attr_name, field in fields.items():
        if attr_name in excluded:
            continue

        schema = _field_schema(field, include_relations=include_relations)
        if schema is None:
            continue

        max_length = getattr(field, "max_length", None)
        if max_length and schema.get("type") == "string":
            schema["maxLength"] = max_length

        choices = getattr(field, "choices", None)
        if choices:
            schema["enum"] = [c[0] for c in choices]

        help_text = getattr(field, "help_text", "")
        if help_text:
            schema.setdefault("description", help_text)

        if read_only_pk and getattr(field, "primary_key", False):
            schema["readOnly"] = True

        if getattr(field, "null", False):
            schema = {"oneOf": [schema, {"type": "null"}]}

        properties[attr_name] = schema

        is_required = (
            not getattr(field, "null", False)
            and not getattr(field, "blank", False)
            and not getattr(field, "primary_key", False)
            and not getattr(field, "has_default", False)
        )
        if is_required:
            required.append(attr_name)

    schema_obj: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema_obj["required"] = required

    doc = (model_cls.__doc__ or "").strip()
    if doc:
        schema_obj["description"] = doc.split("\n")[0]

    return schema_obj


def model_components(
    *model_classes: type,
    include_relations: bool = False,
) -> dict[str, dict[str, Any]]:
    """Produce a ``components.schemas`` dict for a set of ORM Models."""
    return {cls.__name__: model_to_schema(cls, include_relations=include_relations) for cls in model_classes}

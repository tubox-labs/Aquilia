"""
Aquilia Model Metaclass -- field collection, auto-PK, Meta parsing, registration.

Separates the metaclass logic from the Model base class for cleaner architecture.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from .fields_module import (
    BigAutoField,
    Field,
    ManyToManyField,
)
from .manager import BaseManager, Manager
from .options import Options

if TYPE_CHECKING:
    from .base import Model

__all__ = ["ModelMeta"]


class ModelMeta(type):
    """
    Metaclass for Aquilia models.

    Handles:
    - Field collection and ordering
    - Auto-PK injection (BigAutoField)
    - Meta class parsing → Options
    - Model registration in ModelRegistry
    - Auto-injection of default Manager
    - Reverse relation descriptors
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs,
    ) -> ModelMeta:
        # Don't process the base Model class itself
        parents = [b for b in bases if isinstance(b, ModelMeta)]
        if not parents:
            return super().__new__(mcs, name, bases, namespace)

        # Extract Meta class
        meta_class = namespace.pop("Meta", None)

        # Extract `table = "..."`, `table_name = "..."`, or `__tablename__ = "..."` attribute
        table_attr = (
            namespace.pop("table", None) or namespace.pop("table_name", None) or namespace.pop("__tablename__", None)
        )

        # Collect fields from current class
        fields: dict[str, Field] = {}
        m2m_fields: dict[str, ManyToManyField] = {}

        # Inherit fields from parents
        for parent in bases:
            if hasattr(parent, "_fields"):
                fields.update(parent._fields)
            if hasattr(parent, "_m2m_fields"):
                m2m_fields.update(parent._m2m_fields)

        # Collect new fields
        new_fields: dict[str, Field] = {}
        for key, value in list(namespace.items()):
            if isinstance(value, ManyToManyField):
                m2m_fields[key] = value
                new_fields[key] = value
            elif isinstance(value, Field):
                fields[key] = value
                new_fields[key] = value

        # Parse options
        opts = Options(name, meta_class, table_attr)

        # Auto-inject PK if no primary key defined (and not abstract)
        if not opts.abstract:
            has_pk = any(f.primary_key for f in fields.values())
            if not has_pk:
                pk_field = BigAutoField()
                fields["id"] = pk_field
                namespace["id"] = pk_field

        # Create class
        cls = super().__new__(mcs, name, bases, namespace)
        model_cls = cast("type[Model]", cls)

        # Attach metadata
        model_cls._fields = fields
        model_cls._m2m_fields = m2m_fields
        model_cls._meta = opts
        model_cls._table_name = opts.table_name
        model_cls._db = None
        model_cls._reverse_fk_cache = None

        # Determine PK
        model_cls._pk_name = "id"
        model_cls._pk_attr = "id"
        for fname, field in fields.items():
            if field.primary_key:
                model_cls._pk_name = field.column_name
                model_cls._pk_attr = fname
                break

        # Set name on all fields
        for fname, field in new_fields.items():
            field.__set_name__(model_cls, fname)
            field.model = model_cls

        # Collect column names (excludes M2M)
        model_cls._column_names = [f.column_name for f in fields.values() if not isinstance(f, ManyToManyField)]

        # Collect attr names (excludes M2M)
        model_cls._attr_names = [fname for fname, f in fields.items() if not isinstance(f, ManyToManyField)]

        # Pre-built list of (attr_name, field) for non-M2M fields.
        # Used by __init__, from_row, save, create etc. to avoid
        # isinstance(field, ManyToManyField) on every access.
        model_cls._non_m2m_fields = [(fname, f) for fname, f in fields.items() if not isinstance(f, ManyToManyField)]

        # Column-name → (attr_name, field) mapping for from_row()
        model_cls._col_to_attr = {}
        for fname, f in model_cls._non_m2m_fields:
            model_cls._col_to_attr[f.column_name] = (fname, f)
            model_cls._col_to_attr[fname] = (fname, f)  # also allow attr-name lookup

        # Auto-inject default Manager if none declared
        if not opts.abstract and not any(isinstance(v, BaseManager) for v in namespace.values()):
            mgr = Manager()
            mgr.__set_name__(model_cls, "objects")
            model_cls.objects = mgr

        # Register in global registry (skip abstract)
        if not opts.abstract:
            from .registry import ModelRegistry as _NewRegistry

            _NewRegistry.register(model_cls)

            # Signal: class_prepared (fired after model class is fully created)
            from .signals import class_prepared

            class_prepared.send_sync(sender=model_cls)

        return cls

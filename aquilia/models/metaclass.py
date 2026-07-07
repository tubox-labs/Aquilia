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
        """
        Build a concrete model class: collect fields, resolve the primary
        key, parse ``Meta`` into ``Options``, wire up the default
        ``Manager``, and register the class globally.

        Args:
            mcs: This metaclass (``ModelMeta``).
            name: Name of the class being created (e.g. ``"User"``).
            bases: Base classes, e.g. ``(Model,)`` or ``(SomeAbstractModel,)``.
            namespace: The class body's attribute dict as collected by
                Python before ``type.__new__`` runs -- this is mutated
                in-place (``Meta``/``table`` popped, ``id`` PK injected)
                before being handed to ``super().__new__()``.
            **kwargs: Accepted for cooperative-metaclass compatibility;
                unused.

        Returns:
            The newly created model class (with ``_fields``, ``_meta``,
            ``_pk_name``/``_pk_attr``, ``objects``, etc. all attached), or
            in the two early-return cases below, a plain, minimally
            processed class.

        Processing steps (in order), once past the two early returns:

        1. **Meta / table-name extraction.** Pops the inner ``Meta`` class
           and any of ``table`` / ``table_name`` / ``__tablename__`` out of
           ``namespace`` (first match wins) so they don't leak onto the
           model as regular class attributes.
        2. **Field inheritance.** Copies ``_fields``/``_m2m_fields`` from
           every base that already has them, so subclassing an (abstract
           or concrete) model class inherits its parent's columns.
        3. **New-field collection.** Scans the current class body for
           ``Field``/``ManyToManyField`` instances declared directly on
           this class, layering them over the inherited ones (a
           re-declared name overrides the parent's field of the same
           name).
        4. **Options parsing.** ``Options(name, meta_class, table_attr)``
           turns the raw ``Meta`` class (or its absence) into a concrete,
           attribute-complete options object -- see ``options.py``.
        5. **Auto-PK injection.** If the model isn't abstract and declares
           no field with ``primary_key=True``, injects an ``id =
           BigAutoField()`` into both ``fields`` and ``namespace`` so every
           concrete model has a primary key without boilerplate.
        6. **Class creation.** Calls ``super().__new__()`` to actually
           create the Python class via ``type``, now that ``namespace`` has
           its final shape.
        7. **Metadata attachment.** Stamps ``_fields``, ``_m2m_fields``,
           ``_meta``, ``_table_name``, resets ``_db`` to ``None`` and
           ``_reverse_fk_cache`` to ``None`` (fresh per class -- caches are
           lazily rebuilt on first relationship use, see base.py).
        8. **PK resolution.** Walks ``fields`` to find the (single)
           ``primary_key=True`` field and records its column name
           (``_pk_name``) and attribute name (``_pk_attr``); defaults to
           ``"id"``/``"id"`` if none is found (shouldn't happen post-step 5
           for non-abstract models).
        9. **Descriptor binding.** Calls ``field.__set_name__(model_cls,
           fname)`` and sets ``field.model`` for every *newly declared*
           field (not inherited ones, which are already bound to their
           original owner) so each ``Field`` descriptor knows its owning
           class and attribute name.
        10. **Column/attribute caches.** Precomputes ``_column_names``,
            ``_attr_names``, ``_non_m2m_fields`` (an ``(attr_name, field)``
            list excluding M2M, reused by ``__init__``/``create``/``save``/
            ``from_row`` to avoid repeated ``isinstance`` checks), and
            ``_col_to_attr`` (a dict keyed by *both* column name and
            attribute name, mapping to ``(attr_name, field)``, used by
            ``from_row()`` to map a raw DB row back onto instance attrs).
        11. **Manager injection.** If the model isn't abstract and no
            ``BaseManager`` instance (e.g. a custom ``Manager``) was
            declared in the class body, creates and binds a default
            ``Manager()`` as ``.objects``.
        12. **Registration.** Unless the model is abstract, registers it
            with the global ``ModelRegistry`` (which also resolves any
            pending string-based forward FK/M2M references) and fires the
            ``class_prepared`` signal so listeners can react once the
            model is fully built.

        Two early returns skip all of the above:

        - **No ``ModelMeta`` parents** (i.e. this *is* the base ``Model``
          class being defined): falls straight through to
          ``type.__new__`` with no field/Options/registry processing.
        - **``namespace["__deferred_guard__"]`` is truthy**: this is the
          lightweight per-model subclass created on the fly by
          ``base.py``'s ``_deferred_guard_class()`` purely to override
          ``__getattribute__`` for deferred-field access. Reprocessing it
          as a full model would give it a mangled table name and a
          duplicate (colliding) registry entry, so it's created as a bare
          subclass instead -- everything else is inherited unchanged from
          the real model class.
        """
        # Don't process the base Model class itself
        parents = [b for b in bases if isinstance(b, ModelMeta)]
        if not parents:
            return super().__new__(mcs, name, bases, namespace)

        # Lightweight guard subclass for deferred-field access (see
        # models/base.py _deferred_guard_class). It only overrides
        # __getattribute__; skip Options/registry/manager reprocessing so
        # it doesn't get a mangled table name or a duplicate registry
        # entry -- everything else is inherited from the real model class.
        if namespace.get("__deferred_guard__"):
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

        # Collect new fields declared directly in this class body,
        # layering them over any inherited fields of the same name.
        new_fields: dict[str, Field] = {}
        for key, value in list(namespace.items()):
            if isinstance(value, ManyToManyField):
                m2m_fields[key] = value
                new_fields[key] = value
            elif isinstance(value, Field):
                fields[key] = value
                new_fields[key] = value

        # Parse options (table name, ordering, indexes, constraints, etc.)
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

        # Determine PK -- record both the DB column name and the Python
        # attribute name of whichever field has primary_key=True.
        model_cls._pk_name = "id"
        model_cls._pk_attr = "id"
        for fname, field in fields.items():
            if field.primary_key:
                model_cls._pk_name = field.column_name
                model_cls._pk_attr = fname
                break

        # Set name on all fields declared directly on this class (inherited
        # fields are already bound to their original owner class).
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

        # Column-name → (attr_name, field) mapping for from_row(). Indexed
        # by both the DB column name and the attribute name so a row dict
        # keyed either way (e.g. raw() results vs. ORM-fetched rows) resolves.
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

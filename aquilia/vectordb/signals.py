"""
AquilaVectorDB — Signals.

Reuses the ``Signal`` implementation from :mod:`aquilia.models.signals` rather
than defining a parallel bus, so a single ``connect()`` idiom and one dispatch
path cover both model worlds. Importing ``aquilia.models.signals`` does not pull
in the ORM's database machinery — it is a standalone dispatcher.

Signals
-------

``vector_class_prepared``
    Fired once per concrete ``VectorModel`` subclass, after the metaclass has
    finished building it. ``sender`` is the model class. Listeners see a fully
    formed class: schema attached, manager bound, registry entry present.

``vector_pre_save`` / ``vector_post_save``
    Fired around ``VectorModel.save()``. ``sender`` is the model class,
    ``instance`` the record, ``created`` whether the key was newly assigned.

``vector_pre_delete`` / ``vector_post_delete``
    Fired around ``VectorModel.delete_instance()``.

Notes:
    Save/delete signals fire only on the per-instance paths. Bulk operations
    (``add_many``, ``VectorQuery.delete()``) deliberately do not fire them —
    matching the ORM, where ``bulk_create`` is likewise signal-free — because a
    per-record dispatch would dominate the cost of a batched write. That is the
    same blind spot ``aq vectordb reindex`` exists to repair.
"""

from __future__ import annotations

from aquilia.models.signals import Signal

#: Fired after a ``VectorModel`` subclass is fully constructed.
vector_class_prepared = Signal("vector_class_prepared")

#: Fired before a record is written by ``save()``.
vector_pre_save = Signal("vector_pre_save")

#: Fired after a record is written by ``save()``.
vector_post_save = Signal("vector_post_save")

#: Fired before a record is removed by ``delete_instance()``.
vector_pre_delete = Signal("vector_pre_delete")

#: Fired after a record is removed by ``delete_instance()``.
vector_post_delete = Signal("vector_post_delete")


__all__ = [
    "vector_class_prepared",
    "vector_post_delete",
    "vector_post_save",
    "vector_pre_delete",
    "vector_pre_save",
]

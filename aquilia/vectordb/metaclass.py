"""
Aquilia VectorDB metaclass -- field collection, Meta parsing, and model registration.
"""

from __future__ import annotations

from typing import Any

from aquilia.models.signals import class_prepared

from .fields import (
    BaseVectorField,
    DocumentField,
    EmbeddingField,
    KeyField,
    MetaField,
)

__all__ = ["VaultOptions", "VectorModelMeta"]


class VaultOptions:
    """
    Parsed options from a ``VectorModel``'s inner ``Meta`` class.

    Mirrors ``aquilia.models.options.Options``.
    """

    __slots__ = (
        "vault_name",
        "dimension",
        "metric",
        "abstract",
        "app_label",
        "verbose_name",
        "verbose_name_plural",
    )

    def __init__(self, model_name: str, meta: type | None, vault_attr: str | None):
        self.vault_name: str = (
            vault_attr
            or (getattr(meta, "vault", None) if meta else None)
            or (getattr(meta, "vault_name", None) if meta else None)
            or model_name.lower()
        )
        self.dimension: int = getattr(meta, "dimension", 0) if meta else 0
        self.metric: str = getattr(meta, "metric", "cosine") if meta else "cosine"
        self.abstract: bool = getattr(meta, "abstract", False) if meta else False
        self.app_label: str = getattr(meta, "app_label", "") if meta else ""
        self.verbose_name: str = getattr(meta, "verbose_name", model_name) if meta else model_name
        self.verbose_name_plural: str = (
            getattr(meta, "verbose_name_plural", f"{self.verbose_name}s") if meta else f"{model_name}s"
        )


class VectorModelMeta(type):
    """
    Metaclass for ``VectorModel``. Mirrors ``aquilia.models.metaclass.ModelMeta``.

    Collects fields, auto-injects a ``KeyField`` + ``EmbeddingField`` when
    absent, parses ``VaultOptions``, wires the default ``VectorManager``,
    and registers the class with ``VectorModelRegistry``.
    """

    def __new__(mcs, name: str, bases: tuple[type, ...], namespace: dict[str, Any], **kwargs: Any):
        parents = [b for b in bases if isinstance(b, VectorModelMeta)]
        if not parents:
            return super().__new__(mcs, name, bases, namespace)

        meta_class = namespace.pop("Meta", None)
        vault_attr = namespace.pop("vault", None) or namespace.pop("vault_name", None)

        meta_fields: dict[str, MetaField] = {}
        document_field: tuple[str, DocumentField] | None = None
        embedding_field: tuple[str, EmbeddingField] | None = None
        key_field: tuple[str, KeyField] | None = None

        for parent in bases:
            if hasattr(parent, "_meta_fields"):
                meta_fields.update(parent._meta_fields)
            if getattr(parent, "_document_field", None):
                document_field = parent._document_field
            if getattr(parent, "_embedding_field", None):
                embedding_field = parent._embedding_field
            if getattr(parent, "_key_field", None):
                key_field = parent._key_field

        new_fields: dict[str, BaseVectorField] = {}
        for key, value in list(namespace.items()):
            if isinstance(value, KeyField):
                key_field = (key, value)
                new_fields[key] = value
            elif isinstance(value, EmbeddingField):
                embedding_field = (key, value)
                new_fields[key] = value
            elif isinstance(value, DocumentField):
                meta_fields[key] = value
                document_field = (key, value)
                new_fields[key] = value
            elif isinstance(value, MetaField):
                meta_fields[key] = value
                new_fields[key] = value

        opts = VaultOptions(name, meta_class, vault_attr)

        if key_field is None and not opts.abstract:
            kf = KeyField()
            key_field = ("key", kf)
            namespace["key"] = kf
            new_fields["key"] = kf

        if embedding_field is None and not opts.abstract:
            ef = EmbeddingField()
            embedding_field = ("embedding", ef)
            namespace["embedding"] = ef
            new_fields["embedding"] = ef

        cls = super().__new__(mcs, name, bases, namespace)

        cls._meta_fields = meta_fields
        cls._document_field = document_field
        cls._embedding_field = embedding_field
        cls._key_field = key_field
        cls._vault_options = opts
        cls._vault_name = opts.vault_name
        cls._engine = None

        for fname, field in new_fields.items():
            field.__set_name__(cls, fname)
            field.model = cls

        if not opts.abstract:
            from .base import VectorManager

            if not any(isinstance(v, VectorManager) for v in namespace.values()):
                mgr = VectorManager()
                mgr.__set_name__(cls, "objects")
                cls.objects = mgr

        if not opts.abstract:
            from .registry import VectorModelRegistry

            VectorModelRegistry.register(cls)
            class_prepared.send_sync(sender=cls)

        return cls

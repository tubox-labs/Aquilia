"""
Aquilia VectorDB base -- VectorModel and VectorManager.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from aquilia.models.signals import post_delete, post_init, post_save, pre_delete, pre_init, pre_save

from .faults import (
    EmbeddingFault,
    VectorEngineFault,
    VectorFieldValidationFault,
    VectorModelNotFoundFault,
    VectorQueryFault,
)
from .fields import DocumentField, MetaText, VectorFieldValidationError
from .metaclass import VaultOptions, VectorModelMeta

if TYPE_CHECKING:
    from .engine import ElipsEngine
    from .query import VQ

logger = logging.getLogger("aquilia.vectordb.base")

__all__ = ["VectorModel", "VectorManager"]


def _write_payload(vector: list[float] | None, text: str | None) -> dict[str, Any]:
    """
    Build the ``vector=``/``text=``/``document=`` kwargs for ``arena.write()``.

    Elips does not accept ``vector=`` and ``text=`` together -- when both an
    explicit vector and document text are present, the text is carried via
    ``elips.DocumentAttachment`` instead.
    """
    if vector is not None and text:
        import elips

        return {"vector": vector, "document": elips.DocumentAttachment(text=text)}
    if vector is not None:
        return {"vector": vector}
    return {"text": text}


class VectorManager:
    """
    Class-only descriptor providing ``VectorModel.objects``.

    Mirrors ``aquilia.models.manager.Manager``.
    """

    _model_cls: type[VectorModel] | None = None

    def __set_name__(self, owner: type, name: str) -> None:
        self._model_cls = owner

    def __get__(self, instance: Any, owner: type) -> VectorManager:
        self._model_cls = owner
        if instance is not None:
            raise AttributeError("VectorManager is accessible only via the model class, not instances.")
        return self

    def get_queryset(self) -> VQ:
        return self._model_cls.query()

    def filter(self, *vf: Any, **kwargs: Any) -> VQ:
        return self.get_queryset().filter(*vf, **kwargs)

    def exclude(self, *vf: Any, **kwargs: Any) -> VQ:
        return self.get_queryset().exclude(*vf, **kwargs)

    def near(self, vec: list[float], **kw: Any) -> VQ:
        return self.get_queryset().near(vec, **kw)

    def near_text(self, txt: str, **kw: Any) -> VQ:
        return self.get_queryset().near_text(txt, **kw)

    def hybrid(self, v: list[float], t: str, **kw: Any) -> VQ:
        return self.get_queryset().hybrid(v, t, **kw)

    def none(self) -> VQ:
        return self.get_queryset().none()

    async def all(self) -> list:
        return await self.get_queryset().all()

    async def count(self) -> int:
        return await self.get_queryset().count()

    def __aiter__(self):
        return self.get_queryset().__aiter__()

    def __repr__(self) -> str:
        model_name = self._model_cls.__name__ if self._model_cls else "<unbound>"
        return f"<VectorManager for {model_name}>"


class VectorModel(metaclass=VectorModelMeta):
    """
    Base class for all Elips vector models.

    Declare a model by subclassing and adding field descriptors::

        class Article(VectorModel):
            vault     = "articles"
            title     = MetaText()
            content   = DocumentField()
            embedding = EmbeddingField(auto_from="content")

            class Meta:
                dimension = 1536
    """

    _meta_fields: ClassVar[dict] = {}
    _document_field: ClassVar[tuple | None] = None
    _embedding_field: ClassVar[tuple | None] = None
    _key_field: ClassVar[tuple | None] = None
    _vault_options: ClassVar[VaultOptions]
    _vault_name: ClassVar[str] = ""
    _engine: ClassVar[ElipsEngine | None] = None
    objects: ClassVar[VectorManager]

    def __init__(self, **kwargs: Any) -> None:
        pre_init.send_sync(sender=self.__class__, kwargs=kwargs)

        if self._key_field:
            attr = self._key_field[0]
            setattr(self, attr, kwargs.pop(attr, None))

        if self._embedding_field:
            attr = self._embedding_field[0]
            setattr(self, attr, kwargs.pop(attr, None))

        if self._document_field:
            attr = self._document_field[0]
            setattr(self, attr, kwargs.pop(attr, None))

        for attr_name, field in self._meta_fields.items():
            if isinstance(field, DocumentField):
                continue
            if attr_name in kwargs:
                setattr(self, attr_name, kwargs[attr_name])
            elif field.has_default():
                setattr(self, attr_name, field.get_default())
            else:
                setattr(self, attr_name, None)

        post_init.send_sync(sender=self.__class__, instance=self)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} key={self.key!r}>"

    def __str__(self) -> str:
        for attr_name, field in self._meta_fields.items():
            if isinstance(field, MetaText) and not isinstance(field, DocumentField):
                val = getattr(self, attr_name, None)
                if val is not None:
                    return str(val)
        return repr(self)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.key == other.key

    def __hash__(self) -> int:
        return hash((self.__class__.__name__, self.key))

    # ── key / embedding properties ─────────────────────────────────

    @property
    def key(self) -> str | None:
        if self._key_field:
            return getattr(self, self._key_field[0], None)
        return None

    @key.setter
    def key(self, value: str | None) -> None:
        if self._key_field:
            setattr(self, self._key_field[0], value)

    @property
    def embedding(self) -> list[float] | None:
        if self._embedding_field:
            return getattr(self, self._embedding_field[0], None)
        return None

    @embedding.setter
    def embedding(self, value: list[float] | None) -> None:
        if self._embedding_field:
            setattr(self, self._embedding_field[0], value)

    # ── Internals ────────────────────────────────────────────────────

    @classmethod
    def _get_engine(cls) -> ElipsEngine:
        from .registry import VectorModelRegistry

        engine = cls._engine or VectorModelRegistry.get_engine()
        if engine is None:
            raise VectorEngineFault(
                reason="No ElipsEngine configured. Call VectorModelRegistry.set_engine(engine) "
                "before using vector models.",
                path="(none)",
            )
        return engine

    @classmethod
    def _validate_instance(cls, instance: VectorModel) -> None:
        for attr_name, field in cls._meta_fields.items():
            if isinstance(field, DocumentField):
                attr = cls._document_field[0]
                value = getattr(instance, attr, None)
            else:
                value = getattr(instance, attr_name, None)
            try:
                validated = field.validate(value)
                if isinstance(field, DocumentField):
                    setattr(instance, cls._document_field[0], validated)
                else:
                    setattr(instance, attr_name, validated)
            except VectorFieldValidationError as exc:
                raise VectorFieldValidationFault(exc.field_name, exc.reason) from exc

        if cls._embedding_field:
            ef_name, ef = cls._embedding_field
            try:
                validated = ef.validate(getattr(instance, ef_name, None))
            except VectorFieldValidationError as exc:
                raise VectorFieldValidationFault(exc.field_name, exc.reason) from exc
            setattr(instance, ef_name, validated)

    @classmethod
    async def _resolve_vector(cls, instance: VectorModel) -> list[float] | None:
        """
        Resolve the vector to write, or ``None`` (Elips embeds the document
        text natively at write time).

        Priority: explicit value on the embedding attribute, then
        ``auto_from`` (embedding the referenced text field), then ``None``.
        """
        if not cls._embedding_field:
            return None

        ef_name, ef = cls._embedding_field
        vector = getattr(instance, ef_name, None)

        if vector is not None:
            return [float(v) for v in vector]

        if ef.auto_from:
            text = getattr(instance, ef.auto_from, None)
            if text and isinstance(text, str):
                engine = cls._get_engine()
                embedder = ef.embedder or engine._config.embedder
                if embedder is not None:
                    vectors = await engine.run_sync(embedder, [text])
                    if vectors:
                        result = [float(v) for v in vectors[0]]
                        setattr(instance, ef_name, result)
                        return result

        return None

    @classmethod
    def _build_meta_payload(cls, instance: VectorModel) -> dict:
        """Serialize ``MetaField``s to Elips-safe primitives. ``DocumentField`` is excluded."""
        payload = {}
        for attr_name, field in cls._meta_fields.items():
            if isinstance(field, DocumentField):
                continue
            value = getattr(instance, attr_name, None)
            if value is not None:
                payload[field.meta_key] = field.to_meta(value)
        return payload

    @classmethod
    def _get_document_text(cls, instance: VectorModel) -> str | None:
        if cls._document_field:
            return getattr(instance, cls._document_field[0], None)
        return None

    @classmethod
    def _from_row(cls, record: Any) -> VectorModel:
        """Convert an ``elips.Row`` or ``elips.Hit`` to a model instance (duck-typed: both share the same fields)."""
        instance = cls.__new__(cls)

        if cls._key_field:
            setattr(instance, cls._key_field[0], record.key)

        if cls._embedding_field:
            ef_name = cls._embedding_field[0]
            setattr(instance, ef_name, list(record.vector) if record.vector else None)

        if cls._document_field:
            df_name = cls._document_field[0]
            setattr(instance, df_name, record.text)

        for attr_name, field in cls._meta_fields.items():
            if isinstance(field, DocumentField):
                continue
            raw = record.meta.get(field.meta_key)
            if raw is not None:
                setattr(instance, attr_name, field.from_meta(raw))
            elif field.has_default():
                setattr(instance, attr_name, field.get_default())
            else:
                setattr(instance, attr_name, None)

        return instance

    # Search hits (elips.Hit) share the same fields as Row -- same deserialization.
    _from_row_like = _from_row

    # ── CRUD ─────────────────────────────────────────────────────────

    @classmethod
    async def create(cls, **data: Any) -> VectorModel:
        instance = cls(**data)
        await pre_save.send(sender=cls, instance=instance, created=True)

        cls._validate_instance(instance)
        vector = await cls._resolve_vector(instance)
        meta = cls._build_meta_payload(instance)
        text = cls._get_document_text(instance)

        engine = cls._get_engine()
        arena = await engine.arena(cls._vault_name)

        key_attr = cls._key_field[0] if cls._key_field else "key"
        explicit_key = getattr(instance, key_attr, None)

        key = await engine.run_sync(
            arena.write,
            meta=meta or None,
            key=explicit_key,
            **_write_payload(vector, text),
        )
        setattr(instance, key_attr, key)

        await post_save.send(sender=cls, instance=instance, created=True)
        return instance

    @classmethod
    async def get(cls, key: str) -> VectorModel:
        engine = cls._get_engine()
        arena = await engine.arena(cls._vault_name)
        rows = await engine.run_sync(arena.pull, [key], include_vectors=True)
        if not rows:
            raise VectorModelNotFoundFault(cls.__name__, key=key)
        return cls._from_row(rows[0])

    @classmethod
    async def get_or_none(cls, key: str) -> VectorModel | None:
        try:
            return await cls.get(key)
        except VectorModelNotFoundFault:
            return None

    @classmethod
    async def get_or_create(cls, key: str | None = None, *, defaults: dict | None = None) -> tuple[VectorModel, bool]:
        if key is not None:
            existing = await cls.get_or_none(key)
            if existing is not None:
                return existing, False
        create_data = dict(defaults or {})
        if key is not None:
            key_attr = cls._key_field[0] if cls._key_field else "key"
            create_data[key_attr] = key
        instance = await cls.create(**create_data)
        return instance, True

    async def save(self) -> None:
        cls = self.__class__
        is_create = self.key is None
        await pre_save.send(sender=cls, instance=self, created=is_create)

        cls._validate_instance(self)
        vector = await cls._resolve_vector(self)
        meta = cls._build_meta_payload(self)
        text = cls._get_document_text(self)

        engine = self._get_engine()
        arena = await engine.arena(self._vault_name)

        key = await engine.run_sync(
            arena.write,
            meta=meta or None,
            key=self.key,
            **_write_payload(vector, text),
        )
        if self.key is None:
            self.key = key

        await post_save.send(sender=cls, instance=self, created=is_create)

    async def delete(self) -> None:
        cls = self.__class__
        if self.key is None:
            raise VectorQueryFault(
                model=cls.__name__,
                operation="delete",
                reason="Cannot delete an unsaved instance (key is None)",
            )
        await pre_delete.send(sender=cls, instance=self)
        engine = self._get_engine()
        arena = await engine.arena(self._vault_name)
        await engine.run_sync(arena.discard, [self.key])
        await post_delete.send(sender=cls, instance=self)
        self.key = None

    async def refresh(self) -> None:
        if self.key is None:
            raise VectorQueryFault(
                model=self.__class__.__name__,
                operation="refresh",
                reason="Cannot refresh an unsaved instance (key is None)",
            )
        fresh = await self.__class__.get(self.key)
        for attr_name in self.__class__._meta_fields:
            setattr(self, attr_name, getattr(fresh, attr_name, None))
        if self.__class__._embedding_field:
            ef_name = self.__class__._embedding_field[0]
            setattr(self, ef_name, getattr(fresh, ef_name, None))
        if self.__class__._document_field:
            df_name = self.__class__._document_field[0]
            setattr(self, df_name, getattr(fresh, df_name, None))

    @classmethod
    async def bulk_create(cls, instances: list[VectorModel]) -> list[VectorModel]:
        from elips import RecordInput

        records = []
        for inst in instances:
            cls._validate_instance(inst)
            vector = await cls._resolve_vector(inst)
            meta = cls._build_meta_payload(inst)
            text = cls._get_document_text(inst)
            if vector is None and not text:
                ef_name = cls._embedding_field[0] if cls._embedding_field else "embedding"
                raise EmbeddingFault(ef_name, "record has neither an embedding vector nor document text")
            payload = _write_payload(vector, text)
            records.append(RecordInput(meta=meta or None, key=inst.key, **payload))

        engine = cls._get_engine()
        arena = await engine.arena(cls._vault_name)
        keys = await engine.run_sync(arena.write_many, records)

        for inst, key in zip(instances, keys):
            inst.key = key
        return instances

    @classmethod
    def query(cls) -> VQ:
        from .query import VQ

        return VQ(model_cls=cls, engine=cls._get_engine())

    def to_dict(self) -> dict:
        d: dict[str, Any] = {}
        if self._key_field:
            d[self._key_field[0]] = self.key
        for attr_name in self._meta_fields:
            d[attr_name] = getattr(self, attr_name, None)
        if self._embedding_field:
            ef_name = self._embedding_field[0]
            d[ef_name] = getattr(self, ef_name, None)
        if self._document_field:
            df_name = self._document_field[0]
            d[df_name] = getattr(self, df_name, None)
        return d

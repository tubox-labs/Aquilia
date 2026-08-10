"""
AquilaVectorDB — ``VectorModel`` base class.

The declarative face of the subsystem. A model is a typed description of one
elips collection:

```python
from typing import Annotated
from aquilia.vectordb import VectorModel, Key, Text, Payload, Dimension

class Document(VectorModel):
    key: Annotated[str, Key()]
    body: Annotated[str, Text()]
    vector: Annotated[list[float], Dimension(384)]
    source: Annotated[str, Payload(indexed=True)]
    score: Annotated[float | None, Score()] = None

    class Meta:
        collection = "documents"
        store = "default"
```

Every attribute is a real annotation, so a type checker sees ``doc.source`` as
``str`` and ``doc.score`` as ``float | None`` without a plugin. Compare the
field-assignment style (``source = CharField()``), where the checker sees a
``CharField`` and the string type is invisible.

Instances are plain objects with ``__slots__``-free ``__dict__`` storage; the
schema does the work, so there is no per-attribute descriptor overhead on reads.
"""

from __future__ import annotations

import sys
import uuid
from typing import TYPE_CHECKING, Annotated, Any, ClassVar

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from aquilia.vectordb.annotations import Score
from aquilia.vectordb.faults import VectorSchemaFault, VectorValidationFault
from aquilia.vectordb.metaclass import VectorModelMeta
from aquilia.vectordb.schema import VectorOptions, VectorSchema

if TYPE_CHECKING:
    from aquilia.vectordb.manager import VectorManager


class VectorModel(metaclass=VectorModelMeta):
    """
    Base class for typed vector models.

    Class attributes installed by the metaclass:

    - ``_vfields`` — the compiled :class:`VectorSchema`.
    - ``_meta`` — alias of ``_vfields``, matching the ORM's spelling so shared
      tooling can read either model world through one attribute name.
    - ``_voptions`` — the :class:`VectorOptions` from ``Meta``.
    - ``vectors`` — the :class:`VectorManager` entry point.

    Instance attributes:

    - ``_vstate`` — loaded/dirty tracking, see :class:`VectorState`.
    """

    _vfields: ClassVar[VectorSchema]
    _meta: ClassVar[VectorSchema]
    _voptions: ClassVar[VectorOptions]
    vectors: ClassVar[VectorManager]

    #: Populated by the manager on search results; ``None`` on records that were
    #: constructed locally or fetched by key.
    score: Annotated[float | None, Score()] = None

    class Meta:
        abstract = True

    def __init__(self, **kwargs: Any) -> None:
        """
        Construct a record.

        Args:
            **kwargs: Attribute values. Unknown names raise rather than being
                silently dropped — a typo in a payload name would otherwise
                produce a record missing the field, discovered only at query time.

        Raises:
            VectorValidationFault: On an unknown attribute name.
        """
        schema = self._vfields
        known = schema.attribute_names

        unknown = [k for k in kwargs if k not in known]
        if unknown:
            raise VectorValidationFault(
                model=schema.model_name,
                errors={name: f"unknown attribute (declared: {', '.join(sorted(known))})" for name in unknown},
            )

        fields = schema.fields
        for attr in known:
            if attr in kwargs:
                value = kwargs[attr]
            else:
                declared = fields.get(attr)
                # A field's default_factory runs per instance, so two records
                # never share one mutable default.
                value = declared.get_default() if declared is not None else self._default_for(attr)
            self.__dict__[attr] = value

        object.__setattr__(self, "_vstate", VectorState())

    @classmethod
    def _default_for(cls, attr: str) -> Any:
        """
        Return the class-level default for ``attr``, or ``None``.

        Walks the MRO looking at ``__dict__`` rather than using ``getattr``, and
        rejects anything that is a descriptor or framework object. Otherwise a
        model whose key attribute is named ``key`` would take the ``key``
        *property object* as its default value, and every model would take its
        manager as the default for ``vectors``.
        """
        from aquilia.vectordb.fields import BaseVectorField
        from aquilia.vectordb.manager import BaseVectorManager

        for klass in cls.__mro__:
            if attr not in klass.__dict__:
                continue
            value = klass.__dict__[attr]
            if isinstance(value, BaseVectorField):
                return value.get_default()
            if isinstance(value, (property, classmethod, staticmethod, BaseVectorManager)):
                return None
            if isinstance(value, (VectorSchema, VectorOptions)):
                return None
            if hasattr(type(value), "__set__") or hasattr(type(value), "__get__"):
                # Any other descriptor (including functions) is not a value.
                if callable(value) or hasattr(type(value), "__set__"):
                    return None
            return value
        return None

    # ── Introspection ────────────────────────────────────────────────────

    @classmethod
    def schema(cls) -> VectorSchema:
        """Return the compiled schema."""
        return cls._vfields

    @classmethod
    def options(cls) -> VectorOptions:
        """Return the ``Meta``-derived options."""
        return cls._voptions

    @classmethod
    def collection_name(cls) -> str:
        """Return the elips collection (vault) name this model reads and writes."""
        return cls._voptions.collection

    # ── Values ───────────────────────────────────────────────────────────

    @property
    def key(self) -> str | None:
        """
        The record key, whatever the key attribute is named.

        Reads ``__dict__`` directly rather than via ``getattr``: a property is a
        data descriptor, so it is *not* shadowed by an instance value, and a
        model whose key attribute is literally named ``key`` would recurse
        through this getter forever.
        """
        attr = self._vfields.key_attr
        return self.__dict__.get(attr) if attr else None

    @key.setter
    def key(self, value: str | None) -> None:
        """Assign the key through whichever attribute carries ``Key()``."""
        attr = self._vfields.key_attr
        if not attr:
            raise VectorSchemaFault(
                model=self._vfields.model_name,
                reason="cannot set key on a model with no Key() attribute",
            )
        self.__dict__[attr] = value
        state = self.__dict__.get("_vstate")
        if state is not None:
            state.mark_dirty(attr)

    def vector_value(self) -> list[float] | None:
        """Return the vector, or ``None`` when the model has no vector attribute."""
        attr = self._vfields.vector_attr
        if not attr:
            return None
        value = getattr(self, attr, None)
        return list(value) if value is not None else None

    def text_value(self) -> str | None:
        """Return the text, or ``None`` when the model has no ``Text()`` attribute."""
        attr = self._vfields.text_attr
        if not attr:
            return None
        value = getattr(self, attr, None)
        return str(value) if value is not None else None

    def payload_values(self) -> dict[str, Any]:
        """Return ``{attribute: value}`` for every declared payload."""
        return {attr: getattr(self, attr, None) for attr in self._vfields.payloads}

    def to_dict(self, *, include_vector: bool = False) -> dict[str, Any]:
        """
        Return a plain-dict view of the record.

        Args:
            include_vector: Include the raw vector. Off by default: a 1536-float
                list dwarfs the rest of the record in any log line or API
                response that forgets to strip it.
        """
        schema = self._vfields
        data: dict[str, Any] = {}

        if schema.key_attr:
            data[schema.key_attr] = getattr(self, schema.key_attr, None)
        if schema.text_attr:
            data[schema.text_attr] = getattr(self, schema.text_attr, None)
        for attr in schema.payloads:
            data[attr] = getattr(self, attr, None)
        if schema.score_attr:
            data[schema.score_attr] = getattr(self, schema.score_attr, None)
        if include_vector and schema.vector_attr:
            data[schema.vector_attr] = self.vector_value()

        return data

    # ── Validation ───────────────────────────────────────────────────────

    def validate(self) -> None:
        """
        Run every declared constraint, plus dimension and requiredness checks.

        Collects **all** errors before raising, so one round trip reports the
        whole picture rather than the first broken field.

        Field-level normalization (``strip_whitespace``) is applied *before*
        validation and written back to the instance, so a value that would only
        pass ``min_length`` because of trailing whitespace does not pass, and the
        value stored is the value validated.

        Raises:
            VectorValidationFault: When any check fails.
        """
        schema = self._vfields
        errors: dict[str, str] = {}

        for attr, declared in schema.fields.items():
            current = self.__dict__.get(attr)
            normalized = declared.prepare_value(current)
            if normalized is not current:
                self.__dict__[attr] = normalized

        for attr, validators in schema.validators.items():
            value = getattr(self, attr, None)
            for validator in validators:
                try:
                    validator(value)
                except VectorValidationFault as exc:
                    errors[attr] = exc.errors.get(attr) or exc.message
                    break
                except (TypeError, ValueError) as exc:
                    errors[attr] = str(exc)
                    break

        vector = self.vector_value()
        if vector is not None and schema.dimension and len(vector) != schema.dimension:
            errors[schema.vector_attr or "vector"] = f"expected {schema.dimension} dimensions, got {len(vector)}"

        if vector is None and self.text_value() is None:
            errors["__all__"] = (
                "record has neither a vector nor text — nothing to embed or index. "
                "Set the vector, or set the Text() attribute and configure an embedder."
            )

        if errors:
            raise VectorValidationFault(model=schema.model_name, errors=errors)

    # ── Persistence ──────────────────────────────────────────────────────

    async def save(self, *, embed: bool | None = None) -> Self:
        """
        Write this record to its collection.

        Args:
            embed: Force embedding on (``True``) or off (``False``). Default
                ``None`` embeds when the model has text, no vector, and an
                embedder is configured.

        Returns:
            ``self``, with ``key`` populated when it was newly assigned.

        Raises:
            VectorValidationFault: When :meth:`validate` fails.
            VectorWriteFault: When the underlying write fails.

        Notes:
            A record saved without a key gets a generated one —
            ``KeyField(prefix=...)`` shapes it, otherwise a bare ``uuid4()``.
            elips addresses records by UUID, so the manager folds any non-UUID
            key into a deterministic UUIDv5; that is what makes re-saving the
            same logical key overwrite rather than duplicate.

            ``KeyField(autogenerate=False)`` opts out, making an unkeyed save a
            validation error instead of a record under an invented identifier.
        """
        from aquilia.vectordb.signals import vector_post_save, vector_pre_save

        schema = self._vfields
        key_attr = schema.key_attr
        if not key_attr:
            raise VectorSchemaFault(
                model=schema.model_name,
                reason="cannot save a model with no key attribute",
            )

        created = getattr(self, key_attr, None) is None
        if created:
            key_field = schema.key_field
            if key_field is not None and not getattr(key_field, "autogenerate", True):
                raise VectorValidationFault(
                    model=schema.model_name,
                    errors={
                        key_attr: (
                            "no key set and this KeyField declares autogenerate=False — assign a key before saving"
                        )
                    },
                )
            generated = key_field.generate() if key_field is not None else str(uuid.uuid4())
            self.__dict__[key_attr] = generated

        await vector_pre_save.send(type(self), instance=self, created=created)

        manager = type(self).vectors
        await manager.add(self, embed=embed)

        self._vstate.mark_saved()

        await vector_post_save.send(type(self), instance=self, created=created)
        return self

    async def delete_instance(self) -> bool:
        """
        Remove this record from its collection.

        Returns:
            ``True`` when a record was removed, ``False`` when the key was absent.

        Raises:
            VectorSchemaFault: When the model has no key attribute.
            VectorValidationFault: When the instance has no key value.
        """
        from aquilia.vectordb.signals import vector_post_delete, vector_pre_delete

        schema = self._vfields
        key_attr = schema.key_attr
        if not key_attr:
            raise VectorSchemaFault(
                model=schema.model_name,
                reason="cannot delete a model with no Key() attribute",
            )

        key = getattr(self, key_attr, None)
        if key is None:
            raise VectorValidationFault(
                model=schema.model_name,
                errors={key_attr: "cannot delete a record with no key"},
            )

        await vector_pre_delete.send(type(self), instance=self)
        removed = await type(self).vectors.remove(str(key))
        await vector_post_delete.send(type(self), instance=self, removed=removed)
        return removed

    async def refresh(self) -> Self:
        """
        Reload this record's payloads from storage.

        Returns:
            ``self``, updated in place.

        Raises:
            VectorNotFoundFault: When the key is no longer present.
        """
        from aquilia.vectordb.faults import VectorNotFoundFault

        key = self.key
        if key is None:
            raise VectorValidationFault(
                model=self._vfields.model_name,
                errors={"key": "cannot refresh a record with no key"},
            )

        fresh = await type(self).vectors.get(str(key))
        if fresh is None:
            raise VectorNotFoundFault(model=self._vfields.model_name, key=str(key))

        for attr in self._vfields.attribute_names:
            if attr != self._vfields.score_attr:
                object.__setattr__(self, attr, getattr(fresh, attr, None))

        self._vstate.mark_saved()
        return self

    # ── Hydration ────────────────────────────────────────────────────────

    @classmethod
    def _from_hit(
        cls,
        key: str,
        meta: dict[str, Any],
        *,
        score: float | None = None,
        vector: list[float] | None = None,
        lineage: Any = None,
        chunk: Any = None,
    ) -> Self:
        """
        Build an instance from a raw elips record.

        Args:
            key: Record key.
            meta: Raw metadata mapping, keyed by *storage* key.
            score: Similarity score, when the record came from a search.
            vector: The vector, when it was requested.
            lineage: Native ``EmbeddingLineage``, when the record carries one.
            chunk: Native ``ChunkInfo``, when the record is a document chunk.

        Returns:
            A hydrated instance marked as loaded (not dirty).
        """
        from aquilia.vectordb.codecs import decode_value

        schema = cls._vfields
        instance = cls.__new__(cls)

        for attr in schema.attribute_names:
            instance.__dict__[attr] = None

        if schema.key_attr:
            instance.__dict__[schema.key_attr] = key

        for storage_key, spec in schema.payload_keys.items():
            if storage_key in meta:
                instance.__dict__[spec.attribute] = decode_value(meta[storage_key], spec.python_type)

        if schema.score_attr is not None and score is not None:
            instance.__dict__[schema.score_attr] = score

        if schema.vector_attr and vector is not None:
            instance.__dict__[schema.vector_attr] = list(vector)

        # Provenance and chunk placement travel outside the payload namespace:
        # they are engine-owned metadata, not user-declared fields, so binding
        # them to attributes would collide with a model that declares its own.
        object.__setattr__(instance, "_vlineage", lineage)
        object.__setattr__(instance, "_vchunk", chunk)
        object.__setattr__(instance, "_vstate", VectorState(loaded=True))
        return instance

    # ── Provenance ───────────────────────────────────────────────────────

    @property
    def lineage(self) -> Any:
        """
        Embedding provenance for this record, or ``None``.

        Populated on records read back from storage that were written through
        an embedder — ``provider``, ``model``, ``revision``, and free-form
        ``attributes``. A locally-constructed record has none until it is saved
        and re-read.
        """
        return self.__dict__.get("_vlineage")

    @property
    def chunk(self) -> Any:
        """
        Chunk placement for this record, or ``None`` when it is not a chunk.

        Carries ``document_key``, ``ordinal``, ``char_start``, and ``char_end``,
        locating this fragment inside its parent document.
        """
        return self.__dict__.get("_vchunk")

    # ── Dunders ──────────────────────────────────────────────────────────

    def __setattr__(self, name: str, value: Any) -> None:
        """Track mutation of declared attributes so ``save()`` can be selective."""
        object.__setattr__(self, name, value)
        state = self.__dict__.get("_vstate")
        if state is not None and name in self._vfields.attribute_names:
            state.mark_dirty(name)

    def __repr__(self) -> str:
        schema = self._vfields
        parts = [f"key={self.key!r}"]
        for attr in list(schema.payloads)[:3]:
            parts.append(f"{attr}={getattr(self, attr, None)!r}")
        if schema.score_attr and getattr(self, schema.score_attr, None) is not None:
            parts.append(f"score={getattr(self, schema.score_attr):.4f}")
        return f"<{type(self).__name__} {' '.join(parts)}>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VectorModel) or type(other) is not type(self):
            return NotImplemented
        if self.key is None or other.key is None:
            return self is other
        return self.key == other.key

    def __hash__(self) -> int:
        return hash((type(self).__name__, self.key)) if self.key else id(self)


class VectorState:
    """
    Per-instance persistence state.

    Attributes:
        loaded: ``True`` when the record came from storage.
        dirty: Attribute names mutated since the last save or load.
    """

    __slots__ = ("dirty", "loaded")

    def __init__(self, *, loaded: bool = False) -> None:
        self.loaded = loaded
        self.dirty: set[str] = set()

    def mark_dirty(self, attr: str) -> None:
        """Record that ``attr`` was mutated."""
        self.dirty.add(attr)

    def mark_saved(self) -> None:
        """Clear dirty tracking and mark the record as persisted."""
        self.dirty.clear()
        self.loaded = True

    def __repr__(self) -> str:
        return f"<VectorState loaded={self.loaded} dirty={sorted(self.dirty)}>"


__all__ = ["VectorModel", "VectorState"]

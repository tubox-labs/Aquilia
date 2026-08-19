"""
AquilaVectorDB — typed vector storage and similarity search.

An ORM-shaped layer over the embedded `elips <https://pypi.org/project/elips/>`_
vector database. Declare models with unified field descriptors (the modern and
recommended form)::

    from datetime import datetime
    from aquilia.vectordb import (
        VectorModel, Field, KeyField, TextField, VectorField, ScoreField,
    )

    class Document(VectorModel):
        key:        str          = KeyField(prefix="doc_")
        body:       str          = TextField(embed=True, min_length=1, max_length=8192)
        vector:     list[float]  = VectorField(dimension=384)
        source:     str          = Field(default="web", indexed=True, max_length=256)
        views:      int          = Field(default=0, ge=0)
        score:      float | None = ScoreField()
        created_at: datetime     = Field(default_factory=datetime.utcnow)

        class Meta:
            collection = "documents"
            store = "default"
            dimension = 384

    hits = await Document.vectors.search("release notes", limit=10)

The older :data:`typing.Annotated` marker form remains supported for existing
models and compatibility::

    from typing import Annotated
    from aquilia.vectordb import VectorModel, Key, Text, Payload, Dimension

    class CompatibilityDocument(VectorModel):
        key:    Annotated[str, Key()]
        body:   Annotated[str, Text()]
        vector: Annotated[list[float], Dimension(384)]
        source: Annotated[str, Payload(indexed=True)]

Use the unified form for new code: one field object carries its slot, defaults,
validation, aliases, indexing hints, embedding/chunking options, and query
expressions. Both forms compile to the same :class:`VectorSchema`.

Optional dependency
-------------------

``elips`` is an optional extra (``pip install 'aquilia[vectordb]'``). Importing
this package without it succeeds; the fault surfaces at first *use*, as
:class:`VectorNotInstalledFault` carrying the install hint. That is what lets
``aquilia`` import cleanly, and the test suite stay green, on an install that
never asked for vector support.

Nothing here imports ``elips`` at module scope, and no GPU symbol is touched
until a store is opened — on a CPU-only elips build the ``Gpu*`` classes are
absent from the extension entirely, not merely inert.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aquilia.vectordb.annotations import (
    URL,
    Choices,
    Constraint,
    Dimension,
    Email,
    Key,
    MaxLength,
    MaxValue,
    MinLength,
    MinValue,
    Pattern,
    Payload,
    Range,
    Score,
    Slug,
    Text,
    Validate,
)
from aquilia.vectordb.base import VectorModel, VectorState
from aquilia.vectordb.codecs import Codec
from aquilia.vectordb.configs import (
    EmbedderOptions,
    GpuOptions,
    QuantizationConfig,
    VectorStoreConfig,
)
from aquilia.vectordb.expressions import FieldExpression
from aquilia.vectordb.faults import (
    VECTORDB_DOMAIN,
    VectorChunkingFault,
    VectorConfigFault,
    VectorDimensionFault,
    VectorEmbedderFault,
    VectorEmbedderMismatchFault,
    VectorEncodingFault,
    VectorEQLFault,
    VectorFault,
    VectorGpuFault,
    VectorGpuUnavailableFault,
    VectorLockFault,
    VectorLookupFault,
    VectorMultipleFoundFault,
    VectorNotFoundFault,
    VectorNotInstalledFault,
    VectorQueryFault,
    VectorRegistryFault,
    VectorSchemaFault,
    VectorStoreFault,
    VectorTransactionFault,
    VectorValidationFault,
)
from aquilia.vectordb.fields import (
    BaseVectorField,
    Field,
    KeyField,
    LinkField,
    NumericConstraints,
    PayloadField,
    ScoreField,
    StringConstraints,
    TextField,
    VectorField,
)
from aquilia.vectordb.filters import VF
from aquilia.vectordb.manager import BaseVectorManager, VectorManager
from aquilia.vectordb.query import Hit, VectorQuery
from aquilia.vectordb.registry import VectorRegistry
from aquilia.vectordb.schema import PayloadSpec, VectorOptions, VectorSchema
from aquilia.vectordb.signals import (
    vector_class_prepared,
    vector_post_delete,
    vector_post_save,
    vector_pre_delete,
    vector_pre_save,
)

if TYPE_CHECKING:
    from aquilia.vectordb.chunking import (
        Chunk,
        Chunker,
        RecursiveCharacterChunker,
        SentenceChunker,
    )
    from aquilia.vectordb.embedders import (
        BaseEmbedder,
        CallableEmbedder,
        Embedder,
        EmbeddingLineage,
        FastEmbedder,
        LocalEmbedder,
        OllamaEmbedder,
        OpenAIEmbedder,
        SentenceTransformersEmbedder,
        resolve_embedder,
    )
    from aquilia.vectordb.engine import VectorEngine
    from aquilia.vectordb.eql import parse_eql
    from aquilia.vectordb.gpu import DeviceInfo, GpuInfo
    from aquilia.vectordb.interop import Link, as_models, mirror, reindex, resolve
    from aquilia.vectordb.pool import VectorPool
    from aquilia.vectordb.subsystem import VectorDBSubsystem

#: Submodules resolved on first attribute access rather than at import.
#:
#: ``engine``/``gpu`` are deferred because they reach into ``elips`` (and, for
#: ``gpu``, into symbols that do not exist on a CPU-only build). ``interop`` is
#: deferred because it imports ``aquilia.models`` — keeping that edge lazy is
#: what preserves the one-way dependency: vectordb may know about the ORM, the
#: ORM must never know about vectordb. ``embedders`` is deferred because each
#: adapter reaches for an optional provider package on load.
_LAZY_ATTRS: dict[str, str] = {
    "VectorEngine": "aquilia.vectordb.engine",
    "VectorPool": "aquilia.vectordb.pool",
    "GpuInfo": "aquilia.vectordb.gpu",
    "DeviceInfo": "aquilia.vectordb.gpu",
    "gpu_info": "aquilia.vectordb.gpu",
    "Link": "aquilia.vectordb.interop",
    "mirror": "aquilia.vectordb.interop",
    "as_models": "aquilia.vectordb.interop",
    "resolve": "aquilia.vectordb.interop",
    "reindex": "aquilia.vectordb.interop",
    "VectorDBSubsystem": "aquilia.vectordb.subsystem",
    # Embedders
    "BaseEmbedder": "aquilia.vectordb.embedders",
    "Embedder": "aquilia.vectordb.embedders",
    "EmbeddingLineage": "aquilia.vectordb.embedders",
    "SentenceTransformersEmbedder": "aquilia.vectordb.embedders",
    "OpenAIEmbedder": "aquilia.vectordb.embedders",
    "FastEmbedder": "aquilia.vectordb.embedders",
    "OllamaEmbedder": "aquilia.vectordb.embedders",
    "LocalEmbedder": "aquilia.vectordb.embedders",
    "CallableEmbedder": "aquilia.vectordb.embedders",
    "resolve_embedder": "aquilia.vectordb.embedders",
    # Chunking
    "Chunk": "aquilia.vectordb.chunking",
    "Chunker": "aquilia.vectordb.chunking",
    "RecursiveCharacterChunker": "aquilia.vectordb.chunking",
    "SentenceChunker": "aquilia.vectordb.chunking",
    "parent_key_of": "aquilia.vectordb.chunking",
    "is_chunk_key": "aquilia.vectordb.chunking",
    # EQL
    "parse_eql": "aquilia.vectordb.eql",
}


def __getattr__(name: str) -> Any:
    """Resolve lazily-exported names on first access."""
    module_path = _LAZY_ATTRS.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    import importlib

    module = importlib.import_module(module_path)
    # `gpu_info` is spelled `probe` on the module; everything else matches.
    value = getattr(module, "probe" if name == "gpu_info" else name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Include lazily-resolved names in completion."""
    return sorted({*__all__, *_LAZY_ATTRS})


def is_available() -> bool:
    """
    Return whether ``elips`` is importable.

    Use this to branch on optional vector support without catching a fault::

        if vectordb.is_available():
            ...
    """
    from aquilia.vectordb._compat import is_available as _is_available

    return _is_available()


__all__ = [
    "VECTORDB_DOMAIN",
    # Model layer
    "VectorModel",
    "VectorState",
    "VectorManager",
    "BaseVectorManager",
    "VectorQuery",
    "Hit",
    "VectorRegistry",
    # Schema
    "VectorSchema",
    "VectorOptions",
    "PayloadSpec",
    "Codec",
    # Unified field system (§2.2)
    "BaseVectorField",
    "Field",
    "PayloadField",
    "KeyField",
    "VectorField",
    "TextField",
    "ScoreField",
    "LinkField",
    "StringConstraints",
    "NumericConstraints",
    # Dual-syntax expressions (§4.2)
    "FieldExpression",
    # Compatibility annotation markers (backwards compatible)
    "Key",
    "Dimension",
    "Text",
    "Payload",
    "Score",
    "Constraint",
    "MinLength",
    "MaxLength",
    "MinValue",
    "MaxValue",
    "Range",
    "Pattern",
    "Email",
    "URL",
    "Slug",
    "Choices",
    "Validate",
    # Filters
    "VF",
    "parse_eql",
    # Configuration
    "VectorStoreConfig",
    "GpuOptions",
    "EmbedderOptions",
    "QuantizationConfig",
    # Embedders (§3.3, lazily exported)
    "BaseEmbedder",
    "Embedder",
    "EmbeddingLineage",
    "SentenceTransformersEmbedder",
    "OpenAIEmbedder",
    "FastEmbedder",
    "OllamaEmbedder",
    "LocalEmbedder",
    "CallableEmbedder",
    "resolve_embedder",
    # Chunking (§3.5, lazily exported)
    "Chunk",
    "Chunker",
    "RecursiveCharacterChunker",
    "SentenceChunker",
    "parent_key_of",
    "is_chunk_key",
    # Lazily exported (see _LAZY_ATTRS)
    "VectorEngine",
    "VectorPool",
    "GpuInfo",
    "DeviceInfo",
    "gpu_info",
    "Link",
    "mirror",
    "as_models",
    "resolve",
    "reindex",
    "VectorDBSubsystem",
    # Signals
    "vector_class_prepared",
    "vector_pre_save",
    "vector_post_save",
    "vector_pre_delete",
    "vector_post_delete",
    # Faults
    "VectorFault",
    "VectorNotInstalledFault",
    "VectorSchemaFault",
    "VectorEncodingFault",
    "VectorValidationFault",
    "VectorQueryFault",
    "VectorEQLFault",
    "VectorChunkingFault",
    "VectorLookupFault",
    "VectorNotFoundFault",
    "VectorMultipleFoundFault",
    "VectorStoreFault",
    "VectorLockFault",
    "VectorDimensionFault",
    "VectorConfigFault",
    "VectorTransactionFault",
    "VectorEmbedderFault",
    "VectorEmbedderMismatchFault",
    "VectorRegistryFault",
    "VectorGpuUnavailableFault",
    "VectorGpuFault",
    # Helpers
    "is_available",
]

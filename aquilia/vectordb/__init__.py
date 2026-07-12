"""
Aquilia VectorDB -- Elips vector database ORM for Aquilia.

Requires the ``elips`` extra: ``pip install aquilia[vectordb]``.

Quick start::

    from aquilia.vectordb import VectorModel, ElipsConfig, ElipsEngine, VectorModelRegistry
    from aquilia.vectordb.fields import EmbeddingField, DocumentField, MetaText
    from aquilia.vectordb.query import VF

    class Article(VectorModel):
        vault     = "articles"
        title     = MetaText()
        content   = DocumentField()
        embedding = EmbeddingField(auto_from="content")

    engine = ElipsEngine(ElipsConfig(path=":memory:", dimension=384))
    VectorModelRegistry.set_engine(engine)

    article = await Article.create(title="Hello", content="World")
    hits    = await Article.objects.near(query_vec, top=5).all()
"""

from __future__ import annotations

from .base import VectorManager, VectorModel
from .configs import ElipsConfig
from .engine import ElipsEngine
from .faults import (
    DimensionMismatchFault,
    EmbeddingFault,
    VectorEngineFault,
    VectorFault,
    VectorFieldValidationFault,
    VectorModelNotFoundFault,
    VectorModelRegistrationFault,
    VectorQueryFault,
)
from .fields import (
    UNSET,
    DocumentField,
    EmbeddingField,
    KeyField,
    MetaBool,
    MetaChoice,
    MetaFloat,
    MetaInt,
    MetaJSON,
    MetaText,
)
from .query import VF, VQ, VectorHit
from .registry import VectorModelRegistry

__all__ = [
    # Core
    "VectorModel",
    "VectorManager",
    "ElipsConfig",
    "ElipsEngine",
    "VectorModelRegistry",
    # Query
    "VF",
    "VQ",
    "VectorHit",
    # Fields
    "EmbeddingField",
    "DocumentField",
    "KeyField",
    "MetaText",
    "MetaInt",
    "MetaFloat",
    "MetaBool",
    "MetaChoice",
    "MetaJSON",
    "UNSET",
    # Faults
    "VectorFault",
    "VectorModelRegistrationFault",
    "VectorModelNotFoundFault",
    "VectorEngineFault",
    "VectorQueryFault",
    "DimensionMismatchFault",
    "EmbeddingFault",
    "VectorFieldValidationFault",
]

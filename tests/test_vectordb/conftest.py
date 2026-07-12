"""
Shared fixtures for aquilia.vectordb tests.

Requires the ``elips`` extra to be installed (``pip install aquilia[vectordb]``).
The whole test package is skipped when it isn't available.
"""

from __future__ import annotations

import pytest
import pytest_asyncio

elips = pytest.importorskip("elips")
if not hasattr(elips, "connect"):
    pytest.skip("elips extra is not installed (namespace package with no bindings)", allow_module_level=True)

from aquilia.vectordb import ElipsConfig, ElipsEngine, VectorModel, VectorModelRegistry
from aquilia.vectordb.fields import DocumentField, EmbeddingField, MetaBool, MetaFloat, MetaInt, MetaText


def _fake_embedder(texts: list[str]) -> list[list[float]]:
    """Deterministic 4-dim embedder for tests -- avoids depending on a real model."""
    return [[float(len(t) % 7), 0.0, 0.0, 0.0] for t in texts]


@pytest_asyncio.fixture
async def engine():
    e = ElipsEngine(ElipsConfig(path=":memory:", dimension=4, use_default_text_embedder=False, embedder=_fake_embedder))
    await e.connect()
    VectorModelRegistry.set_engine(e)
    yield e
    await e.disconnect()
    VectorModelRegistry.reset()


@pytest.fixture
def Article(engine):
    class Article(VectorModel):
        vault = "articles"
        title = MetaText()
        author = MetaText(null=True)
        score = MetaFloat(default=0.0)
        year = MetaInt(null=True)
        active = MetaBool(default=True)
        content = DocumentField()
        embedding = EmbeddingField()

    return Article

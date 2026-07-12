"""Declaration-time behavior: field collection, auto-injection, Meta parsing, registration."""

from __future__ import annotations

import pytest

from aquilia.vectordb import VectorModel, VectorModelRegistry
from aquilia.vectordb.base import VectorManager
from aquilia.vectordb.fields import EmbeddingField, KeyField, MetaFloat, MetaInt, MetaText


def test_fields_collected(Article):
    assert set(Article._meta_fields) == {"title", "author", "score", "year", "active", "content"}
    assert isinstance(Article._meta_fields["title"], MetaText)
    assert isinstance(Article._meta_fields["year"], MetaInt)
    assert isinstance(Article._meta_fields["score"], MetaFloat)


def test_key_injected(Article):
    assert Article._key_field is not None
    name, field = Article._key_field
    assert name == "key"
    assert isinstance(field, KeyField)


def test_embedding_injected(engine):
    class NoEmbedding(VectorModel):
        vault = "no_embedding"
        title = MetaText()

    name, field = NoEmbedding._embedding_field
    assert name == "embedding"
    assert isinstance(field, EmbeddingField)


def test_vault_name(Article):
    assert Article._vault_name == "articles"


def test_meta_options(engine):
    class Doc(VectorModel):
        vault = "docs"
        title = MetaText()

        class Meta:
            dimension = 1536
            metric = "euclidean"

    assert Doc._vault_options.dimension == 1536
    assert Doc._vault_options.metric == "euclidean"


def test_abstract_skips_register(engine):
    class AbstractBase(VectorModel):
        title = MetaText()

        class Meta:
            abstract = True

    assert VectorModelRegistry.get("AbstractBase") is None


def test_objects_manager(Article):
    assert isinstance(Article.objects, VectorManager)


def test_objects_instance_error(Article):
    article = Article(title="Hi")
    with pytest.raises(AttributeError):
        article.objects

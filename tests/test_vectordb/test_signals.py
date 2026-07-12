"""Signal dispatch: pre_save, post_save, pre_delete, post_delete, class_prepared."""

from __future__ import annotations

import pytest

from aquilia.models.signals import class_prepared, post_delete, post_save, pre_delete, pre_save
from aquilia.vectordb import VectorModel
from aquilia.vectordb.fields import MetaText


@pytest.mark.asyncio
async def test_pre_save_fires_on_create(Article):
    calls = []

    async def on_pre_save(sender, instance, created, **kwargs):
        calls.append((sender, created))

    pre_save.connect(on_pre_save, sender=Article)
    try:
        await Article.create(title="X", content="text")
    finally:
        pre_save.disconnect(on_pre_save, sender=Article)

    assert calls == [(Article, True)]


@pytest.mark.asyncio
async def test_post_save_fires_on_create(Article):
    calls = []

    async def on_post_save(sender, instance, created, **kwargs):
        calls.append((sender, created, instance.key))

    post_save.connect(on_post_save, sender=Article)
    try:
        article = await Article.create(title="X", content="text")
    finally:
        post_save.disconnect(on_post_save, sender=Article)

    assert calls == [(Article, True, article.key)]


@pytest.mark.asyncio
async def test_pre_save_fires_on_update(Article):
    article = await Article.create(title="X", content="text")
    calls = []

    async def on_pre_save(sender, instance, created, **kwargs):
        calls.append(created)

    pre_save.connect(on_pre_save, sender=Article)
    try:
        article.title = "Y"
        await article.save()
    finally:
        pre_save.disconnect(on_pre_save, sender=Article)

    assert calls == [False]


@pytest.mark.asyncio
async def test_post_save_fires_on_update(Article):
    article = await Article.create(title="X", content="text")
    calls = []

    async def on_post_save(sender, instance, created, **kwargs):
        calls.append(created)

    post_save.connect(on_post_save, sender=Article)
    try:
        article.title = "Y"
        await article.save()
    finally:
        post_save.disconnect(on_post_save, sender=Article)

    assert calls == [False]


@pytest.mark.asyncio
async def test_pre_delete_fires(Article):
    article = await Article.create(title="X", content="text")
    calls = []

    async def on_pre_delete(sender, instance, **kwargs):
        calls.append(instance.key)

    pre_delete.connect(on_pre_delete, sender=Article)
    try:
        await article.delete()
    finally:
        pre_delete.disconnect(on_pre_delete, sender=Article)

    assert len(calls) == 1


@pytest.mark.asyncio
async def test_post_delete_fires(Article):
    article = await Article.create(title="X", content="text")
    calls = []

    async def on_post_delete(sender, instance, **kwargs):
        calls.append(True)

    post_delete.connect(on_post_delete, sender=Article)
    try:
        await article.delete()
    finally:
        post_delete.disconnect(on_post_delete, sender=Article)

    assert calls == [True]


def test_class_prepared_fires_on_declaration(engine):
    calls = []

    def on_class_prepared(sender, **kwargs):
        calls.append(sender.__name__)

    class_prepared.connect(on_class_prepared)
    try:

        class SignalArticle(VectorModel):
            vault = "signal_articles"
            title = MetaText()

    finally:
        class_prepared.disconnect(on_class_prepared)

    assert "SignalArticle" in calls
